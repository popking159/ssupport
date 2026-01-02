# -*- coding: utf-8 -*-
##########################################
## updated 30/10/2025 popking159(MNASR) ##
##########################################
from __future__ import absolute_import
from __future__ import print_function
import difflib
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
try:
    from six.moves import urllib
except ImportError:
    import urllib

# Base URLs
__api = "https://api.subsource.net/api/v1"
__search = __api + "/movies/search"
__getSub = __api + "/subtitles"

def getsubsourceapi():
    global settings_provider  # Ensure we're using the existing instance
    API_KEY = settings_provider.getSetting("SubSource_API_KEY")
    if API_KEY:
        return API_KEY
    print("Error: SubSource API key is missing.")
    return None

def prepare_search_string(s):
    s = s.replace("'", "").strip()
    s = re.sub(r'\(\d{4}\)$', '', s)
    return quote_plus(s).replace("+", " ")

def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):
    subtitles_list = []
    langs = [lang.replace('Farsi', 'Persian') for lang in [lang1, lang2, lang3] if lang]
    if not title and not tvshow and not file_original_path:
        return subtitles_list, "", ""
    
    try:
        if tvshow:
            subtitles_list = search_tvshow(tvshow, year, season, episode, langs, file_original_path)
        elif title:
            subtitles_list = search_movie(title, year, langs, file_original_path)
        else:
            if file_original_path:
                try:
                    filename = os.path.basename(file_original_path)
                    match = re.match(r'^(.*?)(?:\.\d{4}|\.S\d{2}E\d{2}|\.\d{3,4}p|\.\w{2,3})?\.\w+$', filename)
                    if match:
                        derived_title = match.group(1).replace('.', ' ').strip()
                        subtitles_list = search_movie(derived_title, year, langs, file_original_path)
                except Exception as e:
                    pass
        
        return subtitles_list, "", ""
    
    except Exception as e:
        return subtitles_list, "", ""

def getSearchTitle(title, year=None):
    url = __search
    API_KEY = getsubsourceapi()
    headers = {"X-API-Key": API_KEY}
    name = prepare_search_string(title)
    params1 = {"searchType": "text", "q": name, "type": "all"}
    if year:
        params1["year"] = year

    try:
        response1 = requests.get(url, params=params1, headers=headers)
        response1.raise_for_status()
        response_json = response1.json()
    except Exception as e:
        print(("Error fetching search results:", str(e)))
        return []

    candidates = []
    if response_json.get("success") and response_json.get("data"):
        for item in response_json["data"]:
            movie_id = item.get("movieId")
            title = item.get("title", "")
            release_year = item.get("releaseYear", "")
            sub_count = item.get("subtitleCount", 0)
            m_type = item.get("type", "")
            poster = ""
            posters = item.get("posters") or {}
            if "medium" in posters:
                poster = posters["medium"]
            elif "small" in posters:
                poster = posters["small"]

            if movie_id:
                candidates.append({
                    "movieId": movie_id,
                    "title": title,
                    "year": release_year,
                    "subtitleCount": sub_count,
                    "type": m_type,
                    "poster": poster
                })

        print(("✅ Found %d results" % len(candidates)))
    else:
        print(("❌ No movie found or invalid response:", response_json))

    return candidates

def search_movie(title, year, languages, filename):
    try:
        movie_title = prepare_search_string(title)
        if year:
            movie_title = "%s %s" % (movie_title, year)

        # Get list of candidate movies (each with movieId)
        movie_candidates = getSearchTitle(movie_title, year)
        #print(("movie_candidates", movie_candidates))
        if not movie_candidates:
            print("❌ No movie found for this title")
            return []

        # Prepare language codes
        language_codes = []
        for lang in languages:
            lang_info = get_language_info(lang)
            if lang_info and "name" in lang_info:
                # get_language_info usually returns dict like {"code": "ar", "name": "Arabic"}
                language_codes.append(lang_info["name"].lower())

        if not language_codes:
            print("❌ No valid language codes found")
            return []

        unique_langs = list(set(language_codes))
        languages_param = ",".join(unique_langs)
        limit = 100

        API_KEY = getsubsourceapi()
        headers = {"X-API-Key": API_KEY}

        subtitles = []

        # 🔁 Loop through all movie IDs returned by getSearchTitle()
        for movie in movie_candidates:
            movie_id = movie.get("movieId")
            movie_name = movie.get("title", "")
            movie_year = movie.get("year", "")

            if not movie_id:
                continue

            #print(("🔍 Searching subtitles for movieId:", movie_id, "title:", movie_name))

            params2 = {
                "movieId": movie_id,
                "language": languages_param,
                "limit": limit,
                "sort": "newest"
            }

            try:
                response2 = requests.get(__getSub, params=params2, headers=headers)
                if response2.status_code != 200:
                    print(("❌ HTTP Error (get subtitles):", response2.status_code, response2.text))
                    continue

                json_data2 = response2.json()
                if not json_data2.get("success") or not json_data2.get("data"):
                    print(("❌ No subtitles found for this movie:", movie_name))
                    continue

                # ✅ Parse subtitles
                for item in json_data2["data"]:
                    subtitle_id = item.get("subtitleId")
                    language_name = item.get("language", "").capitalize()
                    downloads = item.get("downloads", 0)
                    release_infos = item.get("releaseInfo", [])

                    for release_name in release_infos:
                        subtitles.append({
                            "sub_id": subtitle_id,
                            "filename": release_name,
                            "language_name": language_name,
                            "sync": True,  # Always true as per your logic
                            "year": movie_year,
                            "downloads": downloads,
                            "rating": downloads,  # using downloads as rating
                            "linkName": "%s-%s" % (title.replace(" ", "-").lower(), movie_year) if movie_year else title.replace(" ", "-").lower()
                        })

            except Exception as e:
                print(("❌ Error fetching subtitles for movieId %s:" % movie_id, str(e)))
                continue

        print(("✅ Total subtitles found:", len(subtitles)))
        return subtitles

    except Exception as error:
        print(("❌ Error in search_movie:", str(error)))
        return []

def getSearchTvshow(tvshow_title, year=None, season=None, episode=None):
    url = __search
    API_KEY = getsubsourceapi()
    name = prepare_search_string(tvshow_title)
    params1 = {"searchType": "text", "q": name, "type": "tvseries"}
    if year:
        params1["year"] = year
    if season:
        params1["season"] = season

    try:
        response1 = requests.get(url, params=params1, headers=headers)
        response1.raise_for_status()
        response_json = response1.json()
    except Exception as e:
        print(("Error fetching search results:", str(e)))
        return []

    candidates = []
    if response_json.get("success") and response_json.get("data"):
        for item in response_json["data"]:
            movie_id = item.get("movieId")
            title = item.get("title", "")
            release_year = item.get("releaseYear", "")
            sub_count = item.get("subtitleCount", 0)
            m_type = item.get("type", "")
            poster = ""
            posters = item.get("posters") or {}
            if "medium" in posters:
                poster = posters["medium"]
            elif "small" in posters:
                poster = posters["small"]

            if movie_id:
                candidates.append({
                    "movieId": movie_id,
                    "title": title,
                    "year": release_year,
                    "subtitleCount": sub_count,
                    "type": m_type,
                    "poster": poster
                })

        print(("✅ Found %d results" % len(candidates)))
    else:
        print(("❌ No movie found or invalid response:", response_json))

    return candidates

def search_tvshow(tvshow, year, season, episode, languages, filename):
    try:
        tvshow_title = prepare_search_string(tvshow)
        if year:
            tvshow_title = "%s %s" % (tvshow_title, year)

        # Get list of candidate movies (each with movieId)
        movie_candidates = getSearchTvshow(tvshow_title, year, season, episode)
        print(("movie_candidates", movie_candidates))
        if not movie_candidates:
            print("❌ No tvshow found for this tvshow")
            return []

        # Prepare language codes
        language_codes = []
        for lang in languages:
            lang_info = get_language_info(lang)
            if lang_info and "name" in lang_info:
                # get_language_info usually returns dict like {"code": "ar", "name": "Arabic"}
                language_codes.append(lang_info["name"].lower())

        if not language_codes:
            print("❌ No valid language codes found")
            return []

        unique_langs = list(set(language_codes))
        languages_param = ",".join(unique_langs)
        limit = 100

        API_KEY = getsubsourceapi()
        headers = {"X-API-Key": API_KEY}

        subtitles = []

        # 🔁 Loop through all movie IDs returned by getSearchTitle()
        for movie in movie_candidates:
            movie_id = movie.get("movieId")
            movie_name = movie.get("title", "")
            movie_year = movie.get("year", "")

            if not movie_id:
                continue

            #print(("🔍 Searching subtitles for movieId:", movie_id, "tvshow:", movie_name))

            params2 = {
                "movieId": movie_id,
                "language": languages_param,
                "limit": limit,
                "sort": "newest"
            }

            try:
                response2 = requests.get(__getSub, params=params2, headers=headers)
                if response2.status_code != 200:
                    print(("❌ HTTP Error (get subtitles):", response2.status_code, response2.text))
                    continue

                json_data2 = response2.json()
                if not json_data2.get("success") or not json_data2.get("data"):
                    print(("❌ No subtitles found for this movie:", movie_name))
                    continue

                # ✅ Parse subtitles
                for item in json_data2["data"]:
                    subtitle_id = item.get("subtitleId")
                    language_name = item.get("language", "").capitalize()
                    downloads = item.get("downloads", 0)
                    release_infos = item.get("releaseInfo", [])

                    for release_name in release_infos:
                        subtitles.append({
                            "sub_id": subtitle_id,
                            "filename": release_name,
                            "language_name": language_name,
                            "sync": True,  # Always true as per your logic
                            "year": movie_year,
                            "downloads": downloads,
                            "rating": downloads,  # using downloads as rating
                            "linkName": "%s-%s" % (tvshow.replace(" ", "-").lower(), movie_year) if movie_year else tvshow.replace(" ", "-").lower()
                        })

            except Exception as e:
                print(("❌ Error fetching subtitles for tvshow with movieId %s:" % movie_id, str(e)))
                continue

        #print(("✅ Total subtitles found:", len(subtitles)))
        return subtitles

    except Exception as error:
        print(("❌ Error in search_tvshow:", str(error)))
        return []

def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):
    try:
        sub_id = subtitles_list[pos].get("sub_id")
        language = subtitles_list[pos].get("languagename", "Unknown")

        if not sub_id:
            print("[SubsourceSeeker][error] Missing subtitle ID")
            return False, language, ""

        # zip_subs can be "/var/volatile/tmp/<release>" (passed from xbmc_subtitles.py)
        base = os.path.basename(str(zip_subs))

        # sanitize filename only (keep tmp_sub_dir clean)
        safe = re.sub(r"[\\\\/]+", "_", base)
        safe = safe.replace("..", ".").strip("._ ")

        if not os.path.exists(tmp_sub_dir):
            os.makedirs(tmp_sub_dir)

        localtmpfile = os.path.join(tmp_sub_dir, safe)

        APIKEY = getsubsourceapi()
        headers = {"X-API-Key": APIKEY}

        __getSubdown = __getSub + "/" + str(sub_id) + "/download"
        print("⬇️ Download URL:", __getSubdown)

        response = requests.get(__getSubdown, headers=headers, verify=False, allow_redirects=True, timeout=30)
        if response.status_code != 200:
            print("❌ HTTP Error download:", response.status_code, response.text)
            return False, language, ""

        with open(localtmpfile, "wb") as f:
            f.write(response.content)

        print("✅ Subtitle downloaded successfully:", localtmpfile)

        with open(localtmpfile, "rb") as myfile:
            header = myfile.read(4)
        try:
            header = header.decode("latin-1")
        except Exception:
            pass

        if header.startswith("Rar!"):
            compressed = "rar"
        elif header.startswith("PK"):
            compressed = "zip"
        else:
            compressed = False

        # IMPORTANT: third value MUST be filepath (what seek.py will open/unpack)
        return compressed, language, localtmpfile

    except Exception as e:
        print("[SubsourceSeeker][error] downloadsubtitles exception:", e)
        return False, "", ""
