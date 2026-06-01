# -*- coding: UTF-8 -*-
from __future__ import absolute_import

import os
import re
import requests
from .OpenSubtitles2Utilities import get_language_info
from .OpenSubtitles2Utilities import LANGUAGES
import os.path
import http.client
import json
import sys
from urllib.request import HTTPCookieProcessor, build_opener, install_opener, Request, urlopen
from urllib.parse import urlencode
from ..utilities import languageTranslate, getFileSize, log
from ..seeker import SubtitlesDownloadError, SubtitlesErrors
from ..user_agents import get_api_user_agent, get_random_ua

def build_api_headers(api_key, token=None, content_type=None):
    """Build headers for api.opensubtitles.com REST requests.

    The REST API expects a stable application name and version in User-Agent.
    Random browser User-Agent strings are intentionally not used here.
    """
    headers = {
        "User-Agent": get_api_user_agent(),
        "Api-Key": api_key,
        "Accept": "application/json",
    }
    if token:
        headers["Authorization"] = "Bearer %s" % token
    if content_type:
        headers["Content-Type"] = content_type
    return headers


def build_browser_headers():
    """Build headers for ordinary website or temporary-file requests."""
    return {
        "User-Agent": get_random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3",
        "Content-Type": "text/html; charset=UTF-8",
        "Referer": "https://www.opensubtitles.com",
        "Upgrade-Insecure-Requests": "1",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip, deflate",
    }

s = requests.Session()

main_url = "https://www.opensubtitles.com"
debug_pretext = "opensubtitles.com"


BASE_URL = "https://api.opensubtitles.com/api/v1"

_cached_token = None


def get_opensubtitles_token(force_refresh=False):
    """Authenticate once and reuse the JWT token for later downloads."""
    global settings_provider, _cached_token

    if _cached_token and not force_refresh:
        return _cached_token

    api_key = settings_provider.getSetting("OpenSubtitles_API_KEY")
    username = settings_provider.getSetting("OpenSubtitles_username")
    password = settings_provider.getSetting("OpenSubtitles_password")
    if not api_key or not username or not password:
        print("Error: Missing OpenSubtitles credentials.")
        return None

    url = "%s/login" % BASE_URL
    payload = {"username": username, "password": password}
    headers = build_api_headers(api_key, content_type="application/json")

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        _cached_token = response.json().get("token")
        return _cached_token
    except requests.exceptions.RequestException as e:
        print("Error getting token:", e)
        return None

def get_url(url, referer=None):
    if referer is None:
        headers = {'User-agent': get_random_ua()}
    else:
        headers = {'User-agent': get_random_ua(), 'Referer': referer}
    req = Request(url, None, headers)
    response = urlopen(req)
    content = response.read().decode('utf-8')
    response.close()
    content = content.replace('\n', '')
    return content


def get_rating(downloads):
    rating = int(downloads)
    if (rating < 50):
        rating = 1
    elif (rating >= 50 and rating < 100):
        rating = 2
    elif (rating >= 100 and rating < 150):
        rating = 3
    elif (rating >= 150 and rating < 200):
        rating = 4
    elif (rating >= 200 and rating < 250):
        rating = 5
    elif (rating >= 250 and rating < 300):
        rating = 6
    elif (rating >= 300 and rating < 350):
        rating = 7
    elif (rating >= 350 and rating < 400):
        rating = 8
    elif (rating >= 400 and rating < 450):
        rating = 9
    elif (rating >= 450):
        rating = 10
    return rating


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):  # standard input
    # Create a list of all provided languages (lang1, lang2, lang3) that are not empty
    languages = [lang for lang in [lang1, lang2, lang3] if lang]
    
    # Get language info for all specified languages
    language_infos = []
    for lang in languages:
        language_info = get_language_info(lang)
        language_infos.append({
            'name': language_info['name'],
            '2et': language_info['2et'],
            '3et': language_info['3et']
        })
    
    # Create comma-separated string of language codes (2-letter codes)
    languageshort = ",".join([info['2et'] for info in language_infos])
    
    # For backward compatibility, keep the first language's info in separate variables
    language_info1 = language_infos[0]['name']
    language_info2 = language_infos[0]['2et']
    language_info3 = language_infos[0]['3et']

    subtitles_list = []
    msg = ""

    if len(tvshow) == 0 and year:  # Movie
        searchstring = "%s (%s)" % (title, year)
        print(("searchstringtv", searchstring))
        get_subtitles_list_movie(searchstring, languageshort, language_info1, subtitles_list)  # Pass languageshort instead of language_info2
    elif len(tvshow) > 0 and title == tvshow:  # Movie not in Library
        searchstring = "%s" % (tvshow)
        print(("searchstringtv", searchstring))
        get_subtitles_list_tv(searchstring, tvshow, season, episode, languageshort, language_info1, subtitles_list)  # Pass languageshort
    elif len(tvshow) > 0:  # TVShow
        searchstring = "%s S%#02dE%#02d" % (tvshow, int(season), int(episode))
        print(("searchstringtv", searchstring))
        get_subtitles_list_tv(searchstring, tvshow, season, episode, languageshort, language_info1, subtitles_list)  # Pass languageshort
    else:
        searchstring = title
        print(("searchstring_movie", searchstring))
        get_subtitles_list_movie(searchstring, languageshort, language_info1, subtitles_list)  # Pass languageshort
    log(__name__, "%s Search string = %s" % (debug_pretext, searchstring))
    return subtitles_list, "", msg  # standard output


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id, session=None):
    """Download subtitles and show remaining downloads as a message."""
    token = get_opensubtitles_token()
    #print(f"TOKEN_download: {token}")
    global settings_provider
    API_KEY = settings_provider.getSetting("OpenSubtitles_API_KEY")
    #print(f"API_KEY_down: {API_KEY}")
    language = subtitles_list[pos]["language_name"]
    #print(f"language_down: {language}")
    file_id = subtitles_list[pos]["id"]
    print(f"file_id_down: {file_id}")
    url = f"{BASE_URL}/download"
    
    if not token:
        log(__name__, "Cannot download subtitle: OpenSubtitles login failed")
        return None

    headers = build_api_headers(API_KEY, token=token)
    payload = {"file_id": file_id}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 401:
            # The cached JWT can expire. Refresh it once and retry.
            token = get_opensubtitles_token(force_refresh=True)
            if token:
                headers = build_api_headers(API_KEY, token=token)
                response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        #print(json.dumps(data, indent=4))
        download_url = data.get("link")
        #print(f"download_url: {download_url}")
        remaining_downloads = data.get("remaining")
        #print(f"remaining_downloads: {remaining_downloads}")


    except requests.exceptions.RequestException as e:
        log(__name__, f"Error downloading subtitle: {e}")
        return None

        
    downloadlink = download_url
    if downloadlink:
        #print(downloadlink)
        log(__name__, "%s Downloadlink: %s " % (debug_pretext, downloadlink))
        viewstate = 0
        previouspage = 0
        subtitleid = 0
        typeid = "zip"
        filmid = 0
        postparams = urlencode({'__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '', '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid})
        log(__name__, "%s Fetching subtitles using url with referer header '%s' and post parameters '%s'" % (debug_pretext, downloadlink, postparams))
        response = s.get(downloadlink, data=postparams, headers=build_browser_headers(), verify=False, allow_redirects=True, timeout=20)
        local_tmp_file = zip_subs
        packed = False
        subs_file = local_tmp_file
        try:
            log(__name__, "%s Saving subtitles to '%s'" % (debug_pretext, local_tmp_file))
            if not os.path.exists(tmp_sub_dir):
                os.makedirs(tmp_sub_dir)
            local_file_handle = open(local_tmp_file, 'wb')
            local_file_handle.write(response.content)
            local_file_handle.close()
            myfile = open(local_tmp_file, "rb")
            myfile.seek(0)
            if (myfile.read(1).decode('utf-8') == 'R'):
                typeid = "rar"
                packed = True
                log(__name__, "Discovered RAR Archive")
            else:
                myfile.seek(0)
                if (myfile.read(1).decode('utf-8') == 'P'):
                    typeid = "zip"
                    packed = True
                    log(__name__, "Discovered ZIP Archive")
                else:
                    typeid = "srt"
                    packed = False
                    subs_file = local_tmp_file
                    log(__name__, "Discovered a non-archive file")
            myfile.close()
            log(__name__, "%s Saving to %s" % (debug_pretext, local_tmp_file))
        except:
            log(__name__, "%s Failed to save subtitle to %s" % (debug_pretext, local_tmp_file))
        if packed:
            subs_file = typeid
        log(__name__, "%s Subtitles saved to '%s'" % (debug_pretext, local_tmp_file))
        return packed, language, subs_file  # standard output


def get_subtitles_list_movie(searchstring, languageshort, languagelong, subtitles_list):
    """Fetch subtitle list for movies from OpenSubtitles API."""
    global settings_provider
    API_KEY = settings_provider.getSetting("OpenSubtitles_API_KEY")
    if not API_KEY:
        print("Error: Missing OpenSubtitles API key.")
        return

    url = "https://api.opensubtitles.com/api/v1/subtitles"
    params = {
        "query": searchstring,
        "type": "movie",
        "languages": languageshort
    }
    print(f"params_listmovies: {params}")
    headers = build_api_headers(API_KEY)

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Create a mapping of language codes to full names from LANGUAGES
        lang_mapping = {}
        for lang in LANGUAGES:
            lang_mapping[lang[2]] = lang[0]  # lang[2] is the 2-letter code, lang[0] is full name

        # Extract subtitles from the response
        for subtitle in data.get("data", []):
            attributes = subtitle.get("attributes", {})
            sub_language = attributes.get("language", "")
            
            # Get the correct language name from our mapping
            language_name = lang_mapping.get(sub_language, sub_language)
            
            feature_details = attributes.get("feature_details", {})
            uploader = attributes.get("uploader", {})
            files = attributes.get("files", [])

            file_id = files[0]["file_id"] if files else None
            filename = attributes.get("release", "Unknown")
            download_count = attributes.get("download_count", 0)
            rating = get_rating(download_count)
            imdb_id = feature_details.get("imdb_id", "N/A")
            tmdb_id = feature_details.get("tmdb_id", "N/A")
            uploader_name = uploader.get("name", "Anonymous")
            upload_date = attributes.get("upload_date", "Unknown")
            subtitle_url = attributes.get("url", "")

            subtitles_list.append({
                "rating": str(rating),
                "no_files": len(files),
                "filename": filename,
                "sync": True,
                "id": file_id,
                "language_flag": f"flags/{sub_language}.gif",
                "language_name": language_name,  # Use the correct language name
                "imdb_id": imdb_id,
                "tmdb_id": tmdb_id,
                "uploader": uploader_name,
                "upload_date": upload_date,
                "url": subtitle_url
            })
            log(__name__, f"{debug_pretext} Subtitles found: {filename} (id = {file_id}, language: {language_name})")

    except requests.exceptions.RequestException as e:
        log(__name__, f"Error fetching subtitles: {e}")


def get_subtitles_list_tv(searchstring, tvshow, season, episode, languageshort, languagelong, subtitles_list):
    """Fetch subtitle list for TV episodes from OpenSubtitles API."""
    global settings_provider
    API_KEY = settings_provider.getSetting("OpenSubtitles_API_KEY")
    if not API_KEY:
        print("Error: Missing OpenSubtitles API key.")
        return

    url = f"{BASE_URL}/subtitles"
    params = {
        "query": tvshow,  # Use only the TV show title
        "type": "episode",  # Specify TV episode search
        "season_number": season,
        "episode_number": episode,
        "languages": languageshort
    }
    headers = build_api_headers(API_KEY)

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Create a mapping of language codes to full names from LANGUAGES
        lang_mapping = {}
        for lang in LANGUAGES:
            lang_mapping[lang[2]] = lang[0]  # lang[2] is the 2-letter code, lang[0] is full name

        # Extract subtitles from the response
        for subtitle in data.get("data", []):
            attributes = subtitle.get("attributes", {})
            sub_language = attributes.get("language", "")
            
            # Get the correct language name from our mapping
            language_name = lang_mapping.get(sub_language, sub_language)
            
            feature_details = attributes.get("feature_details", {})
            uploader = attributes.get("uploader", {})
            files = attributes.get("files", [])

            file_id = files[0]["file_id"] if files else None
            filename = attributes.get("release", "Unknown")
            download_count = attributes.get("download_count", 0)
            rating = get_rating(download_count)
            imdb_id = feature_details.get("imdb_id", "N/A")
            tmdb_id = feature_details.get("tmdb_id", "N/A")
            parent_title = feature_details.get("parent_title", "Unknown Show")
            upload_date = attributes.get("upload_date", "Unknown")
            subtitle_url = attributes.get("url", "")

            subtitles_list.append({
                "rating": str(rating),
                "no_files": len(files),
                "filename": filename,
                "sync": True,
                "id": file_id,
                "language_flag": f"flags/{sub_language}.gif",  # Use the actual subtitle language code
                "language_name": language_name,  # Use the correct language name from mapping
                "imdb_id": imdb_id,
                "tmdb_id": tmdb_id,
                "tv_show": parent_title,
                "season": season,
                "episode": episode,
                "upload_date": upload_date,
                "url": subtitle_url
            })
            log(__name__, f"{debug_pretext} Subtitles found: {filename} (id = {file_id}, language: {language_name})")

    except requests.exceptions.RequestException as e:
        log(__name__, f"Error fetching subtitles: {e}")


