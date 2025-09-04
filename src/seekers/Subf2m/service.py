# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
import difflib
import os
import re
import string
import zipfile
from ..seeker import SubtitlesDownloadError, SubtitlesErrors
from bs4 import BeautifulSoup
from .Subf2mUtilities import geturl, get_language_info
from six.moves import html_parser
from six.moves.urllib.request import FancyURLopener
from six.moves.urllib.parse import quote_plus, urlencode
from ..utilities import log
import html
import urllib3
import requests, re
import requests , json, re,random,string,time,warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from six.moves import html_parser
warnings.simplefilter('ignore',InsecureRequestWarning)
from ..user_agents import get_random_ua


HDR= {'User-Agent': get_random_ua(),
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
      'Accept-Language': 'en-US,en;q=0.9,ar-EG;q=0.8,ar;q=0.7',
      'Upgrade-Insecure-Requests': '1',
      'Content-Type': 'application/x-www-form-urlencoded',
      'Referer': 'https://subf2m.co',
      'Connection': 'keep-alive',
      'Accept-Encoding':'gzip, deflate'}
      
     
main_url = "https://subf2m.co"
debug_pretext = ""

seasons = ["Specials", "First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]
seasons = seasons + ["Eleventh", "Twelfth", "Thirteenth", "Fourteenth", "Fifteenth", "Sixteenth", "Seventeenth",
                     "Eighteenth", "Nineteenth", "Twentieth"]
seasons = seasons + ["Twenty-first", "Twenty-second", "Twenty-third", "Twenty-fourth", "Twenty-fifth", "Twenty-sixth",
                     "Twenty-seventh", "Twenty-eighth", "Twenty-ninth"]

movie_season_pattern = ("<a href=\"(?P<link>/subscene/[^\"]*)\">(?P<title>[^<]+)\((?P<year>\d{4})\)</a>\s+"
                        "<div class=\"subtle count\">\s*(?P<numsubtitles>\d+\s+subtitles)</div>\s+")

# Don't remove it we need it here
subf2m_languages = {
    'Chinese BG code': 'Chinese',
    'Brazillian Portuguese': 'Portuguese (Brazil)',
    'Serbian': 'SerbianLatin',
    'Ukranian': 'Ukrainian',
    'Farsi/Persian': 'Persian'
}

def geturl(url):
    log(__name__, " Getting url: %s" % (url))
    try:
        response = urllib.request.urlopen(url)
        content = response.read()
        print(content)
    except:
        log(__name__, " Failed to get url:%s" % (url))
        content = None
    return(content)
    
def getSearchTitle(title, year=None):
    url = 'https://subf2m.co/subtitles/searchbytitle?query=%s&l=' % quote_plus(title)
    data = requests.get(url, headers=HDR, verify=False, allow_redirects=True).content
    data = data.decode('utf-8')
    soup = BeautifulSoup(data, 'html.parser')
    
    # Find the search results section
    search_results = soup.find('div', class_='search-result')
    if not search_results:
        return url
    
    # Find all list items in the search results
    result_items = search_results.find_all('li')
    
    for item in result_items:
        # Find the title div
        title_div = item.find('div', class_='title')
        if not title_div:
            continue
            
        # Find the link
        a_tag = title_div.find('a')
        if not a_tag:
            continue
            
        link = a_tag.get('href')
        full_title = a_tag.get_text(strip=True)
        
        # Extract year from title text using regex
        year_match = re.search(r'\((\d{4})\)', full_title)
        found_year = year_match.group(1) if year_match else None
        
        # Check if this is the right result
        if year and found_year == str(year):
            return 'https://subf2m.co' + link
        elif not year:
            # If no year specified, return the first result
            return 'https://subf2m.co' + link
    
    # If no match found, return the search URL
    return url

def find_movie(content, title, year):
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find the search results section
    search_results = soup.find('div', class_='search-result')
    if not search_results:
        return None
    
    # Find all list items in the search results
    result_items = search_results.find_all('li')
    
    for item in result_items:
        # Find the title div
        title_div = item.find('div', class_='title')
        if not title_div:
            continue
            
        # Find the link
        a_tag = title_div.find('a')
        if not a_tag:
            continue
            
        link = a_tag.get('href')
        full_title = a_tag.get_text(strip=True)
        
        # Extract year from title text using regex
        year_match = re.search(r'\((\d{4})\)', full_title)
        found_year = year_match.group(1) if year_match else None
        
        # Check if this is the right movie
        if (title.lower() in full_title.lower() and 
            found_year == str(year)):
            return link
    
    return None


def find_tv_show_season(content, tvshow, season):
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find the search results section
    search_results = soup.find('div', class_='search-result')
    if not search_results:
        return None
    
    # Find all list items in the search results
    result_items = search_results.find_all('li')
    
    # Convert season number to text representation
    season_num = int(season)
    season_text = seasons[season_num] if season_num < len(seasons) else f"Season {season}"
    
    for item in result_items:
        # Find the title div
        title_div = item.find('div', class_='title')
        if not title_div:
            continue
            
        # Find the link
        a_tag = title_div.find('a')
        if not a_tag:
            continue
            
        link = a_tag.get('href')
        full_title = a_tag.get_text(strip=True)
        
        # Check if this is the right TV show season using multiple patterns
        tvshow_lower = tvshow.lower()
        title_lower = full_title.lower()
        
        # Check for various season patterns
        season_patterns = [
            f"season {season}",  # "season 2"
            f"{season_text.lower()} season",  # "second season"
            f"- season {season}",  # "- season 2"
            f"- {season_text.lower()} season",  # "- second season"
        ]
        
        # Check if it's the right TV show and contains any season pattern
        if (tvshow_lower in title_lower and 
            any(pattern in title_lower for pattern in season_patterns)):
            return link
    
    return None                                                                    

def getallsubs(content, allowed_languages, filename="", search_string=""):
    soup = BeautifulSoup(content.text, 'html.parser')
    
    # Find the subtitles list container
    subtitles_list = soup.find('ul', class_='sublist')
    if subtitles_list is None:
        subtitles_list = soup.find('ul', class_='larglist')
    
    # Check if subtitles list is found
    if subtitles_list is None:
        log(__name__, "No subtitles list found on the page.")
        return []
    
    # Find all subtitle items
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
            
            if not language_info:
                # Try to map using subf2m_languages
                if lang_text in subf2m_languages:
                    language_info = get_language_info(subf2m_languages[lang_text])
            
            if not language_info or language_info['name'] not in allowed_languages:
                continue
            
            # Get download link
            download_link = item.find('a', class_='download')
            if not download_link or not download_link.get('href'):
                continue
                
            link = main_url + download_link['href']
            
            # Get subtitle filename
            scrolllist = item.find('ul', class_='scrolllist')
            subtitle_name = ""
            if scrolllist:
                first_li = scrolllist.find('li')
                if first_li:
                    subtitle_name = first_li.text.strip()
            
            # Get rating
            rating_span = item.find('span', class_='rate')
            rating = 'not rated'  # Default value
            
            if rating_span:
                rating_classes = rating_span.get('class', [])
                if 'good' in rating_classes:
                    rating = 'good'
                elif 'bad' in rating_classes:
                    rating = 'bad'
                elif 'neutral' in rating_classes:
                    rating = 'neutral'
            
            # Check if subtitle matches the search string
            sync = False
            if filename and subtitle_name:
                # Simple sync check - you might want to improve this
                if filename.lower() in subtitle_name.lower() or subtitle_name.lower() in filename.lower():
                    sync = True
            
            # For TV shows, check if it matches the episode pattern
            if search_string:
                if search_string.lower() in subtitle_name.lower():
                    subtitles.append({
                        'filename': subtitle_name, 
                        'sync': True, 
                        'link': link,
                        'language_name': language_info['name'], 
                        'lang': language_info,
                        'rating': rating  # Add rating to the dictionary
                    })
            else:
                subtitles.append({
                    'filename': subtitle_name, 
                    'sync': True, 
                    'link': link,
                    'language_name': language_info['name'], 
                    'lang': language_info,
                    'rating': rating  # Add rating to the dictionary
                })
                
        except Exception as e:
            log(__name__, "Error parsing subtitle item: %s" % str(e))
            continue
    
    # Sort by sync status and then by rating (good first, then neutral, then bad, then not rated)
    rating_order = {'good': 0, 'neutral': 1, 'bad': 2, 'not rated': 3}
    subtitles.sort(key=lambda x: (not x['sync'], rating_order.get(x['rating'], 4)))
    
    return subtitles


def prepare_search_string(s):
    s = s.replace("'", "").strip()
    s = re.sub(r'\(\d\d\d\d\)$', '', s)
    s = quote_plus(s)
    return s

def search_movie(title, year, languages, filename):
    try:
        title = title.replace("MISSION IMPOSSIBLE : ROGUE NATION", "Mission: Impossible - Rogue Nation").strip()
        print(("title", title))
        url = getSearchTitle(title, year)
        print(("true url", url))
        content = requests.get(url, headers=HDR, verify=False, allow_redirects=True)

        if content.status_code == 200:
            _list = getallsubs(content, languages, filename)
            return _list
        else:
            return []
    except Exception as error:
        print(("error", error))
        return []


def search_tvshow(tvshow, season, episode, languages, filename):
    tvshow = tvshow.strip()
    print(("tvshow", tvshow))
    
    # Prepare search string without adding season info
    search_string = prepare_search_string(tvshow)
    search_string = search_string.replace("+", " ")
    print(("search_string", search_string))
    
    log(__name__, "Search tvshow = %s" % search_string)
    url = main_url + "/subtitles/searchbytitle?query=" + quote_plus(search_string)
    print(("url", url))
    
    response = requests.get(url, headers=HDR, verify=False, allow_redirects=True)
    content = response.text
    
    if content is not None:
        log(__name__, "Multiple tv show seasons found, searching for the right one ...")
        tv_show_seasonurl = find_tv_show_season(content, tvshow, season)
        if tv_show_seasonurl is not None:
            log(__name__, "Tv show season found in list, getting subs ...")
            url = main_url + tv_show_seasonurl
            print(("season_url", url))
            
            # Get the content for the season page
            season_response = requests.get(url, headers=HDR, verify=False, allow_redirects=True)
            if season_response.status_code == 200:
                search_string = "s%02de%02d" % (int(season), int(episode))
                print(("search_string", search_string))
                return getallsubs(season_response, languages, filename, search_string)
    
    # Return empty list if no season found
    return []


def search_manual(searchstr, languages, filename):
    search_string = prepare_search_string(searchstr)
    url = main_url + "/subtitles/release?q=" + search_string + '&r=true'
    content, response_url = requests.get(url,headers=HDR,verify=False,allow_redirects=True).text

    if content is not None:
        return getallsubs(content, languages, filename)


def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack):  # standard input
    log(__name__, "%s Search_subtitles = '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s'" %
         (debug_pretext, file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack))
    if lang1 == 'Farsi':
        lang1 = 'Persian'
    if lang2 == 'Farsi':
        lang2 = 'Persian'
    if lang3 == 'Farsi':
        lang3 = 'Persian'
    if tvshow:
        sublist = search_tvshow(tvshow, season, episode, [lang1, lang2, lang3], file_original_path)
    elif title:
        sublist = search_movie(title, year, [lang1, lang2, lang3], file_original_path)
    else:
        try:
          sublist = search_manual(title, [lang1, lang2, lang3], file_original_path)
        except:
            print("error")
    return sublist, "", ""


def download_subtitles(subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):
    url = subtitles_list[pos]["link"]
    print(("selected_url", url))
    language = subtitles_list[pos]["language_name"]
    
    # Get the content as text, not the response object
    response = requests.get(url, headers=HDR, verify=False, allow_redirects=True)
    content_text = response.text
    
    # Use BeautifulSoup to find the download link
    soup = BeautifulSoup(content_text, 'html.parser')
    download_button = soup.find('a', id='downloadButton')
    
    if download_button and download_button.get('href'):
        downloadlink = main_url + download_button['href']
        print(("downloadlink", downloadlink))
        
        # Download the subtitle file
        sub_response = requests.get(downloadlink, headers=HDR, verify=False, allow_redirects=True)
        
        # Sanitize the filename to remove slashes
        sanitized_filename = re.sub(r'[\\/]', '_', zip_subs)
        local_tmp_file = os.path.join(tmp_sub_dir, sanitized_filename)

        try:
            log(__name__, "%s Saving subtitles to '%s'" % (debug_pretext, local_tmp_file))
            if not os.path.exists(tmp_sub_dir):
                os.makedirs(tmp_sub_dir)
            with open(local_tmp_file, 'wb') as local_file_handle:
                local_file_handle.write(sub_response.content)

            # Initialize packed to False
            packed = False
            subs_file = local_tmp_file

            # Check archive type (rar/zip/else) through the file header
            with open(local_tmp_file, "rb") as myfile:
                header = myfile.read(4)  # Read the first 4 bytes to check for ZIP header
                if header == b'PK\x03\x04':  # ZIP file header
                    packed = True
                    typeid = "zip"
                    log(__name__, "Discovered ZIP Archive")
                else:
                    typeid = "srt"
                    packed = False
                    log(__name__, "Discovered a non-archive file")

            log(__name__, "%s Saving to %s" % (debug_pretext, local_tmp_file))
        except Exception as e:
            log(__name__, "%s Failed to save subtitle to %s" % (debug_pretext, local_tmp_file))
            raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, str(e))

        if packed:
            # Extract the ZIP file
            try:
                with zipfile.ZipFile(local_tmp_file, 'r') as zip_ref:
                    zip_ref.extractall(tmp_sub_dir)
                    log(__name__, "%s Extracted ZIP file to %s" % (debug_pretext, tmp_sub_dir))
                    # Get the first extracted file (assuming it's the subtitle file)
                    extracted_files = zip_ref.namelist()
                    if extracted_files:
                        subs_file = os.path.join(tmp_sub_dir, extracted_files[0])
                        log(__name__, "%s Extracted subtitle file: %s" % (debug_pretext, subs_file))
            except Exception as e:
                log(__name__, "%s Failed to extract ZIP file: %s" % (debug_pretext, str(e)))
                raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, str(e))

        log(__name__, "%s Subtitles saved to '%s'" % (debug_pretext, local_tmp_file))
        return packed, language, subs_file  # standard output
    else:
        log(__name__, "%s No download link found" % (debug_pretext))
        raise SubtitlesDownloadError(SubtitlesErrors.UNKNOWN_ERROR, "No download link found")