# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

import os
import re
import zipfile
import html
import time
import random
import string
import warnings
from bs4 import BeautifulSoup
from six.moves import html_parser
from six.moves.urllib.request import FancyURLopener
from six.moves.urllib.parse import quote_plus, urlencode
import urllib3
from urllib3.exceptions import InsecureRequestWarning
import requests

from ..seeker import SubtitlesDownloadError, SubtitlesErrors
from ..utilities import log
from ..user_agents import get_random_ua
from .Subf2mUtilities import get_language_info

# Suppress insecure request warnings
urllib3.disable_warnings(InsecureRequestWarning)

HDR = {
    'User-Agent': get_random_ua(),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en-US,en;q=0.9,ar-EG;q=0.8,ar;q=0.7',
    'Upgrade-Insecure-Requests': '1',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Referer': 'https://subf2m.co',
    'Connection': 'keep-alive',
    'Accept-Encoding': 'gzip, deflate'
}

main_url = "https://subf2m.co"
debug_pretext = ""

seasons = [
    "Specials", "First", "Second", "Third", "Fourth", "Fifth", "Sixth", 
    "Seventh", "Eighth", "Ninth", "Tenth", "Eleventh", "Twelfth", 
    "Thirteenth", "Fourteenth", "Fifteenth", "Sixteenth", "Seventeenth",
    "Eighteenth", "Nineteenth", "Twentieth", "Twenty-first", "Twenty-second", 
    "Twenty-third", "Twenty-fourth", "Twenty-fifth", "Twenty-sixth",
    "Twenty-seventh", "Twenty-eighth", "Twenty-ninth"
]

movie_season_pattern = (
    "<a href=\"(?P<link>/subscene/[^\"]*)\">(?P<title>[^<]+)\((?P<year>\d{4})\)</a>\s+"
    "<div class=\"subtle count\">\s*(?P<numsubtitles>\d+\s+subtitles)</div>\s+"
)

# Language mappings
subf2m_languages = {
    'Chinese BG code': 'Chinese',
    'Brazillian Portuguese': 'Portuguese (Brazil)',
    'Serbian': 'SerbianLatin',
    'Ukranian': 'Ukrainian',
    'Farsi/Persian': 'Persian'
}


def getSearchTitle(title, year=None):
    """Search for title and return appropriate URL"""
    url = f'https://subf2m.co/subtitles/searchbytitle?query={quote_plus(title)}&l='
    response = requests.get(url, headers=HDR, verify=False, allow_redirects=True)
    data = response.content.decode('utf-8')
    soup = BeautifulSoup(data, 'html.parser')
    
    search_results = soup.find('div', class_='search-result')
    if not search_results:
        return url
    
    result_items = search_results.find_all('li')
    
    for item in result_items:
        title_div = item.find('div', class_='title')
        if not title_div:
            continue
            
        a_tag = title_div.find('a')
        if not a_tag:
            continue
            
        link = a_tag.get('href')
        full_title = a_tag.get_text(strip=True)
        
        year_match = re.search(r'\((\d{4})\)', full_title)
        found_year = year_match.group(1) if year_match else None
        
        if year and found_year == str(year):
            return f'https://subf2m.co{link}'
        elif not year:
            return f'https://subf2m.co{link}'
    
    return url


def find_movie(content, title, year):
    """Find movie in search results"""
    soup = BeautifulSoup(content, 'html.parser')
    search_results = soup.find('div', class_='search-result')
    
    if not search_results:
        return None
    
    result_items = search_results.find_all('li')
    
    for item in result_items:
        title_div = item.find('div', class_='title')
        if not title_div:
            continue
            
        a_tag = title_div.find('a')
        if not a_tag:
            continue
            
        link = a_tag.get('href')
        full_title = a_tag.get_text(strip=True)
        
        year_match = re.search(r'\((\d{4})\)', full_title)
        found_year = year_match.group(1) if year_match else None
        
        if (title.lower() in full_title.lower() and 
            found_year == str(year)):
            return link
    
    return None


def find_tv_show_season(content, tvshow, season):
    """Find TV show season in search results"""
    soup = BeautifulSoup(content, 'html.parser')
    search_results = soup.find('div', class_='search-result')
    
    if not search_results:
        return None
    
    result_items = search_results.find_all('li')
    season_num = int(season)
    season_text = seasons[season_num] if season_num < len(seasons) else f"Season {season}"
    
    for item in result_items:
        title_div = item.find('div', class_='title')
        if not title_div:
            continue
            
        a_tag = title_div.find('a')
        if not a_tag:
            continue
            
        link = a_tag.get('href')
        full_title = a_tag.get_text(strip=True)
        
        tvshow_lower = tvshow.lower()
        title_lower = full_title.lower()
        
        season_patterns = [
            f"season {season}",
            f"{season_text.lower()} season",
            f"- season {season}",
            f"- {season_text.lower()} season",
        ]
        
        if (tvshow_lower in title_lower and 
            any(pattern in title_lower for pattern in season_patterns)):
            return link
    
    return None


def getallsubs(content, allowed_languages, filename="", search_string=""):
    """Extract all subtitles from page content"""
    soup = BeautifulSoup(content.text, 'html.parser')
    
    subtitles_list = (soup.find('ul', class_='sublist') or 
                     soup.find('ul', class_='larglist'))
    
    if subtitles_list is None:
        log(__name__, "No subtitles list found on the page.")
        return []
    
    items = subtitles_list.find_all('li', class_='item')
    subtitles = []
    
    for item in items:
        try:
            # Get language
            lang_span = item.find('span', class_='language')
            if not lang_span:
                continue
                
            lang_text = lang_span.text.strip()
            language_info = get_language_info(lang_text)
            
            if not language_info and lang_text in subf2m_languages:
                language_info = get_language_info(subf2m_languages[lang_text])
            
            if not language_info or language_info['name'] not in allowed_languages:
                continue
            
            # Get download link
            download_link = item.find('a', class_='download')
            if not download_link or not download_link.get('href'):
                continue
                
            link = f"{main_url}{download_link['href']}"
            
            # Get subtitle filename
            subtitle_name = ""
            scrolllist = item.find('ul', class_='scrolllist')
            if scrolllist:
                first_li = scrolllist.find('li')
                if first_li:
                    subtitle_name = first_li.text.strip()
            
            # Get rating
            rating_span = item.find('span', class_='rate')
            rating = 'not rated'
            
            if rating_span:
                rating_classes = rating_span.get('class', [])
                if 'good' in rating_classes:
                    rating = 'good'
                elif 'bad' in rating_classes:
                    rating = 'bad'
                elif 'neutral' in rating_classes:
                    rating = 'neutral'
            
            # Check sync
            sync = False
            if filename and subtitle_name:
                if (filename.lower() in subtitle_name.lower() or 
                    subtitle_name.lower() in filename.lower()):
                    sync = True
            
            if search_string:
                if search_string.lower() in subtitle_name.lower():
                    subtitles.append({
                        'filename': subtitle_name, 
                        'sync': sync, 
                        'link': link,
                        'language_name': language_info['name'], 
                        'lang': language_info,
                        'rating': rating
                    })
            else:
                subtitles.append({
                    'filename': subtitle_name, 
                    'sync': sync, 
                    'link': link,
                    'language_name': language_info['name'], 
                    'lang': language_info,
                    'rating': rating
                })
                
        except Exception as e:
            log(__name__, f"Error parsing subtitle item: {str(e)}")
            continue
    
    # Sort by sync status and rating
    rating_order = {'good': 0, 'neutral': 1, 'bad': 2, 'not rated': 3}
    subtitles.sort(key=lambda x: (not x['sync'], rating_order.get(x['rating'], 4)))
    
    return subtitles


def prepare_search_string(s):
    """Prepare search string for URL encoding"""
    s = s.replace("'", "").strip()
    s = re.sub(r'\(\d\d\d\d\)$', '', s)
    return quote_plus(s)


def search_movie(title, year, languages, filename):
    """Search for movie subtitles"""
    try:
        title = title.replace("MISSION IMPOSSIBLE : ROGUE NATION", 
                             "Mission: Impossible - Rogue Nation").strip()
        log(__name__, f"Searching movie: {title}")
        
        url = getSearchTitle(title, year)
        log(__name__, f"Movie search URL: {url}")
        
        response = requests.get(url, headers=HDR, verify=False, allow_redirects=True)
        
        if response.status_code == 200:
            return getallsubs(response, languages, filename)
        else:
            return []
    except Exception as error:
        log(__name__, f"Error searching movie: {error}")
        return []


def search_tvshow(tvshow, season, episode, languages, filename):
    """Search for TV show subtitles"""
    tvshow = tvshow.strip()
    log(__name__, f"Searching TV show: {tvshow}")
    
    search_string = prepare_search_string(tvshow).replace("+", " ")
    url = f"{main_url}/subtitles/searchbytitle?query={quote_plus(search_string)}"
    
    log(__name__, f"TV show search URL: {url}")
    response = requests.get(url, headers=HDR, verify=False, allow_redirects=True)
    content = response.text
    
    if content:
        log(__name__, "Multiple TV show seasons found, searching for the right one...")
        tv_show_seasonurl = find_tv_show_season(content, tvshow, season)
        
        if tv_show_seasonurl:
            log(__name__, "TV show season found, getting subtitles...")
            url = f"{main_url}{tv_show_seasonurl}"
            
            season_response = requests.get(url, headers=HDR, verify=False, allow_redirects=True)
            if season_response.status_code == 200:
                search_string = f"s{int(season):02d}e{int(episode):02d}"
                return getallsubs(season_response, languages, filename, search_string)
    
    return []


def search_manual(searchstr, languages, filename):
    """Manual search for subtitles"""
    search_string = prepare_search_string(searchstr)
    url = f"{main_url}/subtitles/release?q={search_string}&r=true"
    
    response = requests.get(url, headers=HDR, verify=False, allow_redirects=True)
    content = response.text
    
    if content:
        return getallsubs(response, languages, filename)
    return []


def search_subtitles(file_original_path, title, tvshow, year, season, episode, 
                    set_temp, rar, lang1, lang2, lang3, stack):
    """Main search function - standard input"""
    log(__name__, 
        f"{debug_pretext} Search_subtitles = '{file_original_path}', '{title}', "
        f"'{tvshow}', '{year}', '{season}', '{episode}', '{set_temp}', '{rar}', "
        f"'{lang1}', '{lang2}', '{lang3}', '{stack}'")
    
    # Handle Farsi language mapping
    for i, lang in enumerate([lang1, lang2, lang3]):
        if lang == 'Farsi':
            if i == 0: lang1 = 'Persian'
            elif i == 1: lang2 = 'Persian'
            elif i == 2: lang3 = 'Persian'
    
    languages = [lang1, lang2, lang3]
    
    try:
        if tvshow:
            sublist = search_tvshow(tvshow, season, episode, languages, file_original_path)
        elif title:
            sublist = search_movie(title, year, languages, file_original_path)
        else:
            sublist = search_manual(title, languages, file_original_path)
    except Exception as e:
        log(__name__, f"Search error: {e}")
        sublist = []
    
    return sublist, "", ""


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):
    """Download selected subtitles"""
    url = subtitles_list[pos]["link"]
    language = subtitles_list[pos]["language_name"]
    
    log(__name__, f"Downloading from: {url}")
    response = requests.get(url, headers=HDR, verify=False, allow_redirects=True)
    content_text = response.text
    
    soup = BeautifulSoup(content_text, 'html.parser')
    download_button = soup.find('a', id='downloadButton')
    
    if download_button and download_button.get('href'):
        downloadlink = f"{main_url}{download_button['href']}"
        log(__name__, f"Download link: {downloadlink}")
        
        sub_response = requests.get(downloadlink, headers=HDR, verify=False, allow_redirects=True)
        
        # Sanitize filename
        sanitized_filename = re.sub(r'[\\/]', '_', zip_subs)
        local_tmp_file = os.path.join(tmp_sub_dir, sanitized_filename)

        try:
            log(__name__, f"{debug_pretext} Saving subtitles to '{local_tmp_file}'")
            os.makedirs(tmp_sub_dir, exist_ok=True)
            
            with open(local_tmp_file, 'wb') as f:
                f.write(sub_response.content)

            # Check file type
            packed = False
            subs_file = local_tmp_file

            with open(local_tmp_file, "rb") as f:
                header = f.read(4)
                if header == b'PK\x03\x04':  # ZIP file
                    packed = True
                    log(__name__, "Discovered ZIP Archive")
                else:
                    log(__name__, "Discovered a non-archive file")

            if packed:
                try:
                    with zipfile.ZipFile(local_tmp_file, 'r') as zip_ref:
                        zip_ref.extractall(tmp_sub_dir)
                        extracted_files = zip_ref.namelist()
                        if extracted_files:
                            subs_file = os.path.join(tmp_sub_dir, extracted_files[0])
                            log(__name__, f"{debug_pretext} Extracted subtitle file: {subs_file}")
                except Exception as e:
                    log(__name__, f"{debug_pretext} Failed to extract ZIP file: {e}")
                    raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, str(e))

            log(__name__, f"{debug_pretext} Subtitles saved to '{local_tmp_file}'")
            return packed, language, subs_file
            
        except Exception as e:
            log(__name__, f"{debug_pretext} Failed to save subtitle: {e}")
            raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, str(e))
    else:
        log(__name__, f"{debug_pretext} No download link found")
        raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, "No download link found")