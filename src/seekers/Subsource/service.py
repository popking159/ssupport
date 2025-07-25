# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
import difflib
from bs4 import BeautifulSoup
from .SubsourceUtilities import get_language_info
from six.moves.urllib.parse import quote_plus
import html
import os
import requests
import json
import re
import random
import warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning

warnings.simplefilter('ignore', InsecureRequestWarning)

# Updated with more recent and diverse User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0"
]

def get_random_ua():
    return random.choice(USER_AGENTS)

HDR = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "priority": "u=1, i",
    "User-Agent": get_random_ua()
}

HDRDL = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/x-www-form-urlencoded",
    "priority": "u=1, i",
    "User-Agent": get_random_ua()
}

__api = "https://api.subsource.net/api/"
main_url = "https://subsource.net"

LANGUAGE_MAP = {
    'arabic': 'arabic',
    'german': 'german',
    'spanish (spain)': 'spanish',
    'french': 'french',
    'english': 'english',
    'persian': 'persian'
}


def getSearchTitle(title, year=None):
    url = "https://api.subsource.net/v1/movie/search"
    print(("getSearchTitle_URL", url))
    
    params = {
        "query": prepare_search_string(title),
        "signal": {},
        "includeSeasons": False,
        "limit": 15
    }
    
    try:
        response = requests.post(url, headers=HDR, data=json.dumps(params), timeout=10)
        response.raise_for_status()
        response_json = response.json()
    except Exception as e:
        print(f"Error fetching search results: {e}")
        return None

    candidates = []
    if response_json.get("success"):
        for res in response_json.get("results", []):
            try:
                name = res.get('title')
                release_year = res.get('releaseYear')
                link = res.get('link')
                media_type = res.get('type', 'movie').lower()
                
                if not link:
                    continue
                    
                if media_type == 'movie':
                    linkName = link.replace('/subtitles/', '')
                else:
                    linkName = link.replace('/series/', '')
                
                candidate = {
                    'title': name,
                    'year': release_year,
                    'linkName': linkName,
                    'type': 'Movie' if media_type == 'movie' else 'TVSeries',
                    'score': res.get('score', 0)
                }
                candidates.append(candidate)
            except Exception as e:
                print(f"Error processing candidate: {e}")
                continue

    if not candidates:
        return None

    # Find best match
    exact_matches = [c for c in candidates 
                    if c['title'].lower() == title.lower() 
                    and c['type'] == 'Movie']
    
    if year and exact_matches:
        try:
            year_int = int(year)
            exact_matches = [c for c in exact_matches if c['year'] == year_int]
        except ValueError:
            pass
    
    if exact_matches:
        exact_matches.sort(key=lambda x: x['score'], reverse=True)
        return exact_matches[0]['linkName']
    
    contains_matches = [c for c in candidates 
                       if title.lower() in c['title'].lower()
                       and c['type'] == 'Movie']
    
    if year and contains_matches:
        try:
            year_int = int(year)
            contains_matches = [c for c in contains_matches if c['year'] == year_int]
        except ValueError:
            pass
    
    if contains_matches:
        contains_matches.sort(key=lambda x: x['score'], reverse=True)
        return contains_matches[0]['linkName']
    
    movie_candidates = [c for c in candidates if c['type'] == 'Movie']
    if movie_candidates:
        movie_candidates.sort(key=lambda x: x['score'], reverse=True)
        return movie_candidates[0]['linkName']
    
    return candidates[0]['linkName'] if candidates else None


def getSearchTitle_tv(title):
    url = "https://api.subsource.net/v1/movie/search"
    payload = {
        "query": prepare_search_string(title),
        "signal": {},
        "includeSeasons": False,
        "limit": 15
    }
    
    try:
        response = requests.post(url, headers=HDR, data=json.dumps(payload), timeout=10)
        response.raise_for_status()
        response_json = response.json()
    except Exception as e:
        print(f"Error fetching TV search results: {e}")
        return None

    if response_json.get("success"):
        tv_series = [res for res in response_json["results"] 
                    if res.get("type", "").lower() == "tvseries"
                    and res["title"].strip().lower() == title.strip().lower()]
        
        if not tv_series:
            return None
            
        series = tv_series[0]
        link_parts = series["link"].split('/')
        linkName = link_parts[-1] if link_parts else None
        
        if not linkName:
            print("Failed to extract linkName from series link")
            return None
            
        return {"title": linkName}
    
    return None


def prepare_search_string(s):
    s = s.replace("'", "").strip()
    s = re.sub(r'\(\d{4}\)$', '', s)
    return quote_plus(s).replace("+", " ")
    

def search_movie(title, year, languages, filename):
    try:
        movie_title = prepare_search_string(title)
        print(("movie_title", movie_title))
        if year:
            movie_title = f"{movie_title} {year}"

        linkName = getSearchTitle(movie_title, year)
        print(("linkNamemovie", linkName))
        if not linkName:
            return []

        language_codes = []
        for lang in languages:
            lang_info = get_language_info(lang)
            if lang_info:
                lang_name = lang_info['name'].lower()
                language_codes.append(LANGUAGE_MAP.get(lang_name, lang_name))
        
        if not language_codes:
            return []

        unique_langs = list(set(language_codes))
        languages_param = ",".join(unique_langs)
        url = f"https://api.subsource.net/v1/subtitles/{linkName}?language={languages_param}&sort_by_date=true"
        
        subtitles = []
        try:
            response = requests.get(url, headers=HDR, timeout=20)
            response.raise_for_status()
            response_json = response.json()
            
            if response_json.get("media_type") == "movie":
                for sub in response_json.get("subtitles", []):
                    subtitle_name = sub.get("release_info", "")
                    link = f"{main_url}/subtitles/{sub['link']}"
                    language_name = sub['language'].capitalize()
                    lang_info = get_language_info(language_name)
                    
                    if lang_info and lang_info['name'] in languages:
                        # Always set sync to True as requested
                        subtitles.append({
                            'filename': subtitle_name,
                            'sync': True,  # Always True
                            'link': link,
                            'language_name': language_name,
                            'lang': lang_info,
                            'sub_id': sub['id'],
                            'linkName': linkName,
                            'year': year,
                            'upload_date': sub.get('upload_date', '')
                        })
        except Exception as e:
            print(f"Error fetching subtitles: {e}")
            return subtitles

        # Remove sorting since it's not needed
        return subtitles

    except Exception as error:
        print(("error", error))
        return []


def search_tvshow(title, season, episode, languages, filename):
    try:
        title = title.strip()
        search_result = getSearchTitle_tv(title)
        print(("tv_title", search_result))
        if not search_result:
            return []

        linkName = search_result["title"]
        print(("linkNametv", linkName))
        
        language_codes = []
        for lang in languages:
            lang_info = get_language_info(lang)
            if lang_info:
                lang_name = lang_info['name'].lower()
                language_codes.append(LANGUAGE_MAP.get(lang_name, lang_name))
        
        if not language_codes:
            return []
            
        languages_param = ",".join(set(language_codes))
        url = f"https://api.subsource.net/v1/subtitles/{linkName}/season-{season}?language={languages_param}&sort_by_date=true"
        
        try:
            response = requests.get(url, headers=HDR, timeout=15)
            response.raise_for_status()
            response_json = response.json()
        except Exception as e:
            print(f"Error fetching TV subtitles: {e}")
            return []
            
        subtitles = []
        for sub in response_json.get("subtitles", []):
            language_name = sub['language'].capitalize()
            lang_info = get_language_info(language_name)
            
            if not lang_info or lang_info['name'] not in languages:
                continue
                
            subtitle_name = sub.get('release_info', '')
            link = f"{main_url}/{sub['link']}"
            api_path = sub['link']
            
            # Always set sync to True as requested
            sync = True
            
            if episode:
                ep_pattern = re.compile(rf"S\d{{2}}E{int(episode):02d}", re.IGNORECASE)
                if not ep_pattern.search(subtitle_name):
                    continue
                    
            subtitles.append({
                'filename': subtitle_name,
                'sync': True,  # Always True
                'link': link,
                'language_name': language_name,
                'lang': lang_info,
                'sub_id': sub['id'],
                'linkName': linkName,
                'api_path': api_path,
                'year': None,
                'upload_date': sub.get('upload_date', '')
            })
        
        # Remove sorting since it's not needed
        return subtitles
        
    except Exception as error:
        print(f"Error in search_tvshow: {error}")
        return []


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):
    sublist = []
    
    # Handle language aliases
    langs = [lang.replace('Farsi', 'Persian') for lang in [lang1, lang2, lang3] if lang]
    
    if not title and not tvshow and not file_original_path:
        return sublist, "", ""
    
    try:
        if tvshow:
            sublist = search_tvshow(tvshow, season, episode, langs, file_original_path)
        elif title:
            sublist = search_movie(title, year, langs, file_original_path)
        else:
            if file_original_path:
                try:
                    filename = os.path.basename(file_original_path)
                    match = re.match(r'^(.*?)(?:\.\d{4}|\.S\d{2}E\d{2}|\.\d{3,4}p|\.\w{2,3})?\.\w+$', filename)
                    if match:
                        derived_title = match.group(1).replace('.', ' ').strip()
                        sublist = search_movie(derived_title, year, langs, file_original_path)
                except Exception as e:
                    pass
        
        return sublist, "", ""
    
    except Exception as e:
        return sublist, "", ""


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):
    try:
        sub_id = subtitles_list[pos]["sub_id"]
        language = subtitles_list[pos]["language_name"]
        linkName = subtitles_list[pos]["linkName"]
        api_path = subtitles_list[pos].get("api_path")
        
        token_url = f"https://api.subsource.net/v1/subtitle/{api_path}" if api_path \
            else f"https://api.subsource.net/v1/subtitle/{linkName}/{language.lower()}/{sub_id}"
        
        response = requests.get(token_url, headers=HDR, timeout=10)
        response.raise_for_status()
        response_json = response.json()
        
        if not response_json.get("subtitle"):
            return False, "", ""
        
        download_token = response_json["subtitle"].get("download_token")
        if not download_token:
            return False, "", ""
        
        download_url = f"https://api.subsource.net/v1/subtitle/download/{download_token}"
        print(("download_url", download_url))
        response = requests.get(download_url, headers=HDRDL, verify=False, allow_redirects=True, timeout=30)
        response.raise_for_status()
        
        local_tmp_file = os.path.join(tmp_sub_dir, zip_subs)
        if not os.path.exists(tmp_sub_dir):
            os.makedirs(tmp_sub_dir)
        
        with open(local_tmp_file, 'wb') as f:
            f.write(response.content)
        
        with open(local_tmp_file, "rb") as myfile:
            header = myfile.read(4).decode('latin-1')
            
            if header.startswith('Rar!'):
                return True, language, "rar"
            elif header.startswith('PK'):
                return True, language, "zip"
            else:
                return False, language, local_tmp_file
        
    except Exception as e:
        return False, "", ""