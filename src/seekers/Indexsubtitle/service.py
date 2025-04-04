# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from six.moves import html_parser
from six.moves.urllib.request import FancyURLopener
from six.moves.urllib.parse import quote_plus, urlencode
import urllib.request
import urllib.parse
from ..utilities import log
import html
import urllib3
import requests, re, random
import requests , json, re,random,string,time,warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from six.moves import html_parser
warnings.simplefilter('ignore',InsecureRequestWarning)
import os, os.path
from six.moves.urllib.request import HTTPCookieProcessor, build_opener, install_opener, Request, urlopen
from six.moves.urllib.parse import urlencode
from six.moves import http_cookiejar
from .IndexsubtitleUtilities import get_language_info
from ..utilities import languageTranslate, log, getFileSize
from ..utilities import log
import urllib3
from urllib import request, parse
from urllib.parse import urlencode
import urllib.request
import urllib.parse
import six
from six.moves import urllib
from six.moves import xmlrpc_client

import time
import calendar
import re
from six.moves import html_parser
from ..seeker import SubtitlesDownloadError, SubtitlesErrors
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Mobile/15E148 Safari/604.1"
]

def get_random_ua():
    return random.choice(USER_AGENTS)

HDRJSON = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/json",
    "priority": "u=1, i",
    "User-Agent": get_random_ua()}

HDR= {'User-Agent': get_random_ua(),
      'Accept': 'application/json, text/javascript, */*; q=0.01',
      'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
      'X-Requested-With': 'XMLHttpRequest',
      'Content-Type':'application/x-www-form-urlencoded',
      'Origin': 'https://indexsubtitle.cc',
      'Host': 'indexsubtitle.cc',
      'Referer': 'https://indexsubtitle.cc/subtitles/',
      'Upgrade-Insecure-Requests': '1',
      'Connection': 'keep-alive',
      'Accept-Encoding':'gzip, deflate'}
      
s = requests.Session()  
 

main_url = "https://indexsubtitle.cc"
url2="https://indexsubtitle.cc/subtitlesInfo"
debug_pretext = "indexsubtitle.cc"


indexsubtitle_languages = {
    'Chinese BG code': 'Chinese',
    'Brazillian Portuguese': 'Portuguese (Brazil)',
    'Serbian': 'SerbianLatin',
    'Ukranian': 'Ukrainian',
    'Farsi\/Persian': 'Persian'
}

def get_url(url, referer=None):
    if referer is None:
        headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
    else:
        headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0', 'Referer': referer}
    req = urllib.request.Request(url, None, headers)
    response = urllib.request.urlopen(req)
    content = response.read().decode('utf-8') 
    response.close()
    content = content.replace('\n', '')
    return content

def find_movie(content, title, year):
    d = content
    print(d)
    url_found = None
    h = html_parser.HTMLParser()
    for matches in re.finditer(movie_season_pattern, content, re.IGNORECASE | re.DOTALL):
        print((tuple(matches.groups())))
        found_title = matches.group('title')
        found_title = html.unescape(found_title) 
        print(("found_title", found_title))  
        log(__name__, "Found movie on search page: %s (%s)" % (found_title, matches.group('year')))
        if found_title.lower().find(title.lower()) > -1:
            if matches.group('year') == year:
                log(__name__, "Matching movie found on search page: %s (%s)" % (found_title, matches.group('year')))
                url_found = matches.group('link')
                break
    return url_found

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

def getSearchTitle(title, year=None):
    url = "https://indexsubtitle.cc/search"
    # Build the search query string.
    # Note: prepare_search_string already URL-encodes the title, so we remove the year afterward.
    search_query = prepare_search_string(title)
    if year:
        search_query += ' ' + str(year)
    params = {"query": search_query}
    
    try:
        # Use the HDR header that sets content-type to application/x-www-form-urlencoded
        # and form-encode the parameters.
        response = requests.post(url, headers=HDR, data=urllib.parse.urlencode(params), timeout=10)
        content = response.text
        if not content:
            print("No content returned from search")
            return None
        response_data = json.loads(content)
    except Exception as e:
        print(f"Error fetching search results: {e}")
        return None

    # Iterate through the results to find a matching title and year.
    for item in response_data:
        try:
            movie_title_year = item.get("title")
            url_id = item.get("url")
            if not movie_title_year or not url_id:
                continue
            # Extract the year from the result (if present)
            m = re.search(r'\((\d{4})\)', movie_title_year)
            result_year = m.group(1) if m else None
            # Remove the year from the title to get the clean movie title
            result_title = movie_title_year.replace(f" ({result_year})", "") if result_year else movie_title_year

            # Check if the result title contains the search title and, if provided, matches the year.
            if title.lower() in result_title.lower() and (not year or str(year) == str(result_year)):
                print(f"Found: {result_title} ({result_year}) -> {url_id}")
                return url_id
        except Exception as e:
            print(f"Error processing search result: {e}")
            continue

    print("FAILED to find matching title and year")
    return None




def search_subtitles(file_original_path, title, tvshow, year, season, episode, set_temp, rar, lang1, lang2, lang3, stack): #standard input
    languagefound = lang1
    language_info = get_language_info(languagefound)
    language_info1 = language_info['name']
    language_info2 = language_info['2et']
    language_info3 = language_info['3et']

    subtitles_list = []
    msg = ""   

    if len(tvshow) == 0 and year: # Movie
        searchstring = "%s (%s)" % (title, year)
    elif len(tvshow) > 0 and title == tvshow: # Movie not in Library
        searchstring = "%s (%#02d%#02d)" % (tvshow, int(season), int(episode))
    elif len(tvshow) > 0: # TVShow
        searchstring = "%s S%#02dE%#02d" % (tvshow, int(season), int(episode))
    else:
        searchstring = title
    log(__name__, "%s Search string = %s" % (debug_pretext, searchstring))
    get_subtitles_list(searchstring, title, year, language_info2, language_info1, subtitles_list)
    return subtitles_list, "", msg #standard output

def download_subtitles (subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):  # standard input
    language = subtitles_list[pos]["language_name"]
    print('language:', language)
    lang = subtitles_list[pos]["language_flag"]
    print('lang:', lang)
    name = subtitles_list[pos]["filename"]
    print('name:', name)    
    id = subtitles_list[pos]["id"]
    print('id:', id) 
    ID = id.split('/')[4]
    print('ID:', ID) 
    ttl = id.split('/')[5]
    print('ttl:', ttl)
    id = re.sub("/\\d+$", "", id)
    print('id2:', id)
    zp = id.replace('/[^\w ]/','').replace('/','_').replace('_subtitle_','[indexsubtitle.cc]_')
    print('zp:', zp)  
    #.replace('_subtitles_','[indexsubtitle.cc]_')
    check_data='id='+ID+'&lang='+language+'&url='+id+''
    print('check_data:', check_data)
    data=s.post(url2,headers=HDR,data=check_data,verify=False,allow_redirects=True).text
    print('data:', data)
    
    # regx='download_url":"(.*?)"'
    # try:download_url=re.findall(regx, data, re.M|re.I)[0]
    # except:pass   
    #print('download_url', download_url)
    downloadlink = '%s/d/%s/%s/%s.zip' % (main_url, ID, ttl, zp)
    print('downloadlink', downloadlink) 
    #print(downloadlink) 
    if downloadlink:    
        log(__name__ , "%s Downloadlink: %s " % (debug_pretext, downloadlink))
        viewstate = 0
        previouspage = 0
        subtitleid = 0
        typeid = "zip"
        filmid = 0
        #postparams = { '__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '' , '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid}
        #postparams = urllib3.request.urlencode({ '__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '' , '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid})
        postparams = urlencode({'__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '', '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid})
        #class MyOpener(urllib.FancyURLopener):
            #version = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.0'
        #my_urlopener = MyOpener()
        #my_urlopener.addheader('Referer', url)
        log(__name__ , "%s Fetching subtitles using url '%s' with referer header and post parameters '%s'" % (debug_pretext, downloadlink, postparams))
        #response = my_urlopener.open(downloadlink, postparams) response.
        response = s.get(downloadlink,headers=HDR,params=postparams,verify=False,allow_redirects=True)
        print(response.content)
        local_tmp_file = zip_subs
        try:
            log(__name__ , "%s Saving subtitles to '%s'" % (debug_pretext, local_tmp_file))
            if not os.path.exists(tmp_sub_dir):
                os.makedirs(tmp_sub_dir)
            local_file_handle = open(local_tmp_file, 'wb')
            local_file_handle.write(response.content)
            local_file_handle.close()
            # Check archive type (rar/zip/else) through the file header (rar=Rar!, zip=PK) urllib3.request.urlencode
            myfile = open(local_tmp_file, "rb")
            myfile.seek(0)
            if (myfile.read(1) == 'R'):
                typeid = "rar"
                packed = True
                log(__name__ , "Discovered RAR Archive")
            else:
                myfile.seek(0)
                if (myfile.read(1) == 'P'):
                    typeid = "zip"
                    packed = True
                    log(__name__ , "Discovered ZIP Archive")
                else:
                    typeid = "srt"
                    packed = True
                    subs_file = local_tmp_file
                    log(__name__ , "Discovered a non-archive file")
            myfile.close()
            log(__name__ , "%s Saving to %s" % (debug_pretext, local_tmp_file))
        except:
            log(__name__ , "%s Failed to save subtitle to %s" % (debug_pretext, local_tmp_file))
        if packed:
            subs_file = typeid
        log(__name__ , "%s Subtitles saved to '%s'" % (debug_pretext, local_tmp_file))
        return packed, language, subs_file  # standard output

def prepare_search_string(s):
    s = s.strip()
    s = re.sub(r'\(\d\d\d\d\)$', '', s)  # remove year from title
    s = quote_plus(s)
    print(s)
    return s
    
def get_subtitles_list(searchstring, title, year, languageshort, languagelong, subtitles_list):
    lang = languagelong
    title = title.strip().lower()
    hrf = quote_plus(title).replace("+", "-").replace(":", "-")
    print('hrf', hrf)
    print('lang', lang)
    
    # Get the url_id from the search function
    url_id = getSearchTitle(title, year)  # Get the URL ID from the search
    print('url_id', url_id)
    if not url_id:
        print("No matching movie found, returning.")
        return
    
    # Construct the full movie URL (adjusted)
    movie_url = f"{main_url}{url_id}"
    print(f"Fetching subtitles from: {movie_url}")
    
    try:
        content = get_url(movie_url, referer=main_url)  # Scrape the movie page for subtitles
        print('Content:', content)
    except Exception as e:
        print(f"Failed to get content from {movie_url}: {e}")
        return

    # Now you can scrape the subtitles from this page
    try:
        print(f"Fetching subtitles for language: {languageshort}")
        subtitles = re.compile('({"title.+?language":"'+lang+'".+?,{"title)').findall(content)
        ttl = re.compile('ttl = (.+?);').findall(content)[0]
    except Exception as e:
        print(f"Failed to get subtitles: {e}")
        return
    
    for subtitle in subtitles:
        try:
            filename = re.compile('title":"(.+?)"').findall(subtitle)[0]
            filename = filename.strip()
            subtitle_id = re.compile('.*url":"(.+?)"},{"title').findall(subtitle)[0].replace("\/", "/")
            subtitle_id = subtitle_id + "/" + ttl
            
            # Add subtitle information to the list
            subtitles_list.append({
                'filename': filename,
                'id': subtitle_id,
                'language_flag': languageshort,
                'language_name': languagelong,
                'rating': '0',
                'no_files': 1,
                'sync': True
            })
        except Exception as e:
            print(f"Error processing subtitle: {e}")
            continue
    return


