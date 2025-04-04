# -*- coding: UTF-8 -*-
from __future__ import absolute_import
from __future__ import print_function

from six.moves import html_parser
from six.moves.urllib.request import FancyURLopener
from six.moves.urllib.parse import quote_plus, urlencode
import urllib.request
import urllib.parse
from urllib.parse import quote
import html
import requests , json, random, string, time, warnings, calendar, difflib, re
from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore',InsecureRequestWarning)
import os, os.path
from six.moves.urllib.request import HTTPCookieProcessor, build_opener, install_opener, Request, urlopen
from six.moves import http_cookiejar
from .MoviesubtitlesUtilities import get_language_info
from ..utilities import languageTranslate, log, getFileSize
import urllib3
from urllib import request, parse
from urllib.parse import urlencode
import urllib.request
import urllib.parse
import six
from six.moves import urllib
from six.moves import xmlrpc_client
from ..seeker import SubtitlesDownloadError, SubtitlesErrors

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Mobile/15E148 Safari/604.1"
]

def get_random_ua():
    return random.choice(USER_AGENTS)

HDR= {'User-Agent': get_random_ua(),
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.',
      'Accept-Language': 'en-US,en;q=0.9,ar-EG;q=0.8,ar;q=0.7',
      'Upgrade-Insecure-Requests': '1',
      'Content-Type': 'application/x-www-form-urlencoded',
      'Host': 'www.moviesubtitles.org',
      'Referer': 'https://www.moviesubtitles.org/search.php',
      'Upgrade-Insecure-Requests': '1',
      'Connection': 'keep-alive',
      'Accept-Encoding':'gzip, deflate, br, zstd'}
      
s = requests.Session()  
 

main_url = "http://www.moviesubtitles.org"
debug_pretext = "moviesubtitles.org"


moviesubtitles_languages = {
    'Chinese BG code': 'Chinese',
    'Brazillian Portuguese': 'Portuguese (Brazil)',
    'Serbian': 'SerbianLatin',
    'Ukranian': 'Ukrainian',
    'Farsi/Persian': 'Persian'
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
    

def getSearchTitle(title, year=None):
    # Use the original title without altering its case.
    title_clean = title.strip()
    print("title_getSearchTitle:", title_clean)
    
    url = "https://www.moviesubtitles.org/search.php"
    # Send the title as-is in the POST data.
    params = {"q": title_clean}
    print("params:", params)
    
    # Send the POST request.
    data = s.post(url, data=params, headers=HDR, verify=False, allow_redirects=True).text
    # Remove newlines for easier regex matching.
    data = data.replace("\n", "")
    #print("data_all:", data)
    
    # Look for movie links that match the expected pattern.
    # For example: <a href="/movie-13392.html">Hotel Transylvania 2 (2015)</a>
    pattern = r'<a\s+href="(/movie-\d+\.html)">([^<]+)</a>'
    matches = re.findall(pattern, data, re.IGNORECASE)
    print("matches found:", matches)
    
    # Loop through the found links.
    for href, link_text in matches:
        # Compare titles in a case-insensitive manner.
        if title_clean.lower() in link_text.lower():
            if year is None or str(year) in link_text:
                #print("Match found:", href, link_text)
                return 'http://www.moviesubtitles.org' + href
                
    # Fallback: if no match meets the criteria, return the first movie link (if any).
    if matches:
        href, link_text = matches[0]
        print("Fallback match:", href, link_text)
        return 'http://www.moviesubtitles.org' + href
        
    print("No movie link found")
    return None





    
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
    get_subtitles_list(title, year, language_info2, language_info1, subtitles_list)
    return subtitles_list, "", msg #standard output

def download_subtitles (subtitles_list, pos, zip_subs, tmp_sub_dir, sub_folder, session_id):  # standard input
    language = subtitles_list[pos]["language_name"]
    lang = subtitles_list[pos]["language_flag"]
    filename = subtitles_list[pos]["filename"]
    print(("filename", filename))
    id = subtitles_list[pos]["id"]
    print(("id1", id))
    id = id.replace("subtitle","download")
    print(("id2", id))
    downloadlink = 'http://www.moviesubtitles.org%s' % (id)
    print(("downloadlink", downloadlink))
    #downloadlink_pattern = '<a id="download_'+lang+'" onclick=.+?href=\"(.+?)\" class="green-link">Download</a>'
    #print(downloadlink_pattern) 
    if downloadlink:
        log(__name__ , "%s Downloadlink: %s " % (debug_pretext, downloadlink))
        viewstate = 0
        previouspage = 0
        subtitleid = 0
        typeid = "zip"
        filmid = 0
        postparams = { '__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '' , '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid}
        print(("postparams", postparams))
        #postparams = urllib3.request.urlencode({ '__EVENTTARGET': 's$lc$bcr$downloadLink', '__EVENTARGUMENT': '' , '__VIEWSTATE': viewstate, '__PREVIOUSPAGE': previouspage, 'subtitleId': subtitleid, 'typeId': typeid, 'filmId': filmid})
        #class MyOpener(urllib.FancyURLopener):
            #version = 'User-Agent=Mozilla/5.0 (Windows NT 6.1; rv:109.0) Gecko/20100101 Firefox/115.0'
        #my_urlopener = MyOpener()
        #my_urlopener.addheader('Referer', url)
        log(__name__ , "%s Fetching subtitles using url with referer header '%s' and post parameters '%s'" % (debug_pretext, downloadlink, postparams))
        #response = my_urlopener.open(downloadlink, postparams)
        response = s.get(downloadlink,data=postparams,headers=HDR,verify=False,allow_redirects=True) 
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
            if (myfile.read(1).decode('utf-8') == 'R'):
                typeid = "rar"
                packed = True
                log(__name__ , "Discovered RAR Archive")
            else:
                myfile.seek(0)
                if (myfile.read(1).decode('utf-8') == 'P'):
                    typeid = "zip"
                    packed = True
                    log(__name__ , "Discovered ZIP Archive")
                else:
                    typeid = "srt"
                    packed = False
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
    return s
    
def get_subtitles_list(title, year, languageshort, languagelong, subtitles_list):
    # Prepare the search string and get the movie page URL.
    dst = languageshort.lower()
    title = title.strip()
    search_string = prepare_search_string(title)
    url = getSearchTitle(search_string, year)
    print(("true url", url))
    
    # Fetch the movie page content.
    content = s.get(url, headers=HDR, verify=False, allow_redirects=True).text
    #print(content)
    
    try:
        log(__name__, "%s Getting '%s' subs ..." % (debug_pretext, languageshort))
        # New regex pattern:
        # - First, find a <div class="subtitle"> block.
        # - Inside, look for the flag image matching the target language (e.g. flags/ar.gif).
        # - Then, look for an inner <a> tag immediately enclosing a <b> tag with the subtitle title.
        # - Finally, capture the downloads count from a <span> with red color.
        pattern = (
            r'<div\s+class="subtitle".*?'
            r'<img\s+[^>]*flags/' + dst + r'\.gif[^>]*>.*?'
            r'<a\s+href="(/subtitle-\d+\.html)"[^>]*>\s*<b>(.*?)</b>.*?'
            r'<span\s+style="[^"]*color\s*:\s*red">(\d+)</span>'
        )
        matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
        print("subtitles", matches)
    except Exception as e:
        log(__name__, "%s Failed to get subtitles: %s" % (debug_pretext, str(e)))
        return
    
    for match in matches:
        try:
            sub_url, filename, downloads = match
            filename = filename.strip()
            print(filename)
            # Now sub_url should be the inner link corresponding to the <b> tag.
            sub_id = sub_url
            print("sub_id", sub_id)
            downloads = re.sub("\D", "", downloads)  # ensure downloads is digits only
            try:
                rating = get_rating(downloads)
                print("rating", rating)
            except Exception:
                rating = 0
            log(__name__, "%s Subtitles found: %s (id = %s)" % (debug_pretext, filename, sub_id))
            subtitles_list.append({
                'rating': str(rating),
                'no_files': 1,
                'filename': filename,
                'sync': True,
                'id': sub_id,
                'language_flag': languageshort,
                'language_name': languagelong
            })
        except Exception as ex:
            print("Error processing subtitle block:", ex)
            pass
    return

