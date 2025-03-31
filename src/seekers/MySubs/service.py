# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function
import difflib  # For fuzzy matching
from bs4 import BeautifulSoup
from .MySubsUtilities import get_language_info
from ..utilities import languageTranslate, log, getFileSize
from six.moves import html_parser
from six.moves.urllib.request import FancyURLopener
from six.moves.urllib.parse import quote_plus, urlencode
from ..utilities import log
import html
import urllib3
import os, requests , json, re, random, string, time, warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter('ignore',InsecureRequestWarning)

search_url = "https://my-subs.co/search.php?key="
main_url = "https://my-subs.co/"
main_url2 = "https://my-subs.co"
debug_pretext = "my-subs.co"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Mobile/15E148 Safari/604.1"
]

def get_random_ua():
    return random.choice(USER_AGENTS)

header = {
    "accept": 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    "accept-language": 'en-US,en;q=0.9,ar-EG;q=0.8,ar;q=0.7',
    "priority": "u=1, i",
    'Referer': 'https://www.google.com/',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Connection': 'keep-alive',
    "User-Agent": get_random_ua()
    }


      
session = requests.Session()   
debug_pretext = ""
session.headers.update({
    "User-Agent": get_random_ua(),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,ar-EG;q=0.8,ar;q=0.7",
    "Referer": "https://www.google.com/",
})
    
# Seasons as strings for searching  </div>
# Seasons as strings for searching
seasons = ["Specials", "First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth", "Tenth"]
seasons = seasons + ["Eleventh", "Twelfth", "Thirteenth", "Fourteenth", "Fifteenth", "Sixteenth", "Seventeenth",
                     "Eighteenth", "Nineteenth", "Twentieth"]
seasons = seasons + ["Twenty-first", "Twenty-second", "Twenty-third", "Twenty-fourth", "Twenty-fifth", "Twenty-sixth",
                     "Twenty-seventh", "Twenty-eighth", "Twenty-ninth"]


    
def getSearchTitle(title, year=None):
    search_string = prepare_search_string(title)
    print(f"search_string: {search_string}")
    url = search_url + search_string
    print(f"url: {url}")

    try:
        response = session.get(url)
        response.raise_for_status()  # Ensure the request was successful
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all subtitle result links
        results = soup.find_all('a', class_='list-group-item')

        # Extract title, year, and href from the search results
        for result in results:
            result_title = result.get('title')
            href = result.get('href')

            # Match the year in the text using regex
            match = re.search(r'\((\d{4})\)', result.text)
            if match:
                result_year = match.group(1)
                # Only process results with a valid year and matching year if provided
                if year is None or result_year == str(year):
                    linkName = href  # We set the matched result link here
                    print(f"linkName_search: {linkName}")
                    print(f"Found matching subtitle: Title: {result_title}, Year: {result_year}, URL: https://my-subs.co{linkName}")
                    return linkName  # Return the matched result linkName and stop further processing
            else:
                continue  # Skip if year is not found

    except Exception as e:
        print(f"Error in getSearchTitle: {e}")

    print("No matching subtitle found.")
    return None  # Return None if no match is found



def getSearchTitle_tv(title):
    url = __api + prepare_search_string(title)
    
    
    print(f"Searching for: {params}")  # Debugging step

    try:
        content = requests.post(url, headers=HDR, data=json.dumps(params), timeout=10).text
        response_json = json.loads(content)
    except Exception as e:
        print(f"Error fetching search results: {e}")
        return None

    if response_json.get("success"):
        found_shows = response_json.get("found", [])

        print(f"Total API Results: {len(found_shows)}")

        # Print raw API titles before filtering
        raw_titles = [show["title"] for show in found_shows]
        print(f"Raw API Returned Titles ({len(raw_titles)}): {raw_titles}")

        # Filter only TV shows
        tv_shows = [show for show in found_shows if show.get("type") == "TVSeries"]
        all_titles = [show["title"] for show in tv_shows]

        print(f"Filtered TV Shows ({len(all_titles)}): {all_titles}")

        # Select the best match for "Prison Break"
        best_match = next((show for show in tv_shows if show["title"].strip().lower() == title.strip().lower()), None)

        if best_match:
            name = best_match["title"]
            linkName = best_match["linkName"]
            seasons = best_match.get("seasons", [])

            if not linkName or not seasons:
                print("No valid linkName or seasons found!")
                return None

            # Extract valid seasons
            seasons_list = {s["number"]: s["id"] for s in seasons if s["number"] is not None}

            print(f"Matched TV Show: {name} -> {linkName}, Seasons: {seasons_list}")
            return {"title": linkName, "seasons": seasons_list}

    print("FAILED: No matching TV show found.")
    return None                             

def getallsubs(content, allowed_languages, filename="", search_string=""):
    # Find the list of subtitles in the panel-body
    subtitle_list = []
    panel_body = content.find("div", class_="panel-body")
    #print(f"panel_body: {panel_body}")

    if not panel_body:
        print("No subtitle panel body found.")
        return []

    try:
        # Get the language sections (one for each language with subtitles)
        language_sections = panel_body.find_all("h3")
        print(f"Found language sections: {len(language_sections)}")

        for lang_section in language_sections:
            # Check if the language name is in the section
            lang_name = lang_section.get("title", "").strip()
            if not lang_name:
                # If there's no 'title' attribute, we could use the inner text or other logic
                lang_name = lang_section.text.strip()
                
            print(f"Processing language: {lang_name}")

            # Check if the language is in the allowed languages list
            if lang_name.lower() not in [lang.lower() for lang in allowed_languages]:
                continue  # Skip if the language is not allowed

            # Find all subtitle links under this language section
            subtitle_links = lang_section.find_next("ul", class_="list-group").find_all("a", class_="list-group-item")

            for sub in subtitle_links:
                fullLink = sub.get('href')  # Subtitle download link
                subtitle_name = sub.find("small").strong.text.strip()  # Subtitle title (name)

                # Check if the filename matches the subtitle name for synchronization
                sync = filename and filename.lower() == subtitle_name.lower()

                # If search_string is provided, filter based on that
                if search_string and search_string.lower() not in subtitle_name.lower():
                    continue

                # Prepare the subtitle dictionary
                subtitle_info = {
                    'filename': subtitle_name,
                    'sync': sync,
                    'link': main_url2 + fullLink,
                    'language_name': lang_name,
                    'lang': lang_name
                }
                subtitle_list.append(subtitle_info)

        # Sort the subtitles by sync status (synced subtitles first)
        subtitle_list.sort(key=lambda x: not x['sync'])
        return subtitle_list

    except Exception as e:
        print(f"Error in getallsubs: {e}")
        return []




def prepare_search_string(s):
    s = s.replace("'", "").strip()
    s = re.sub(r'\(\d\d\d\d\)$', '', s)  # remove year from title
    #s = quote_plus(s).replace("+"," ")
    return s
    
def search_movie(title, year, languages, filename):
    try:
        # Prepare the search string for the movie title
        movie_title = prepare_search_string(title)
        print(f"movie_title: {movie_title}")

        # Fetch the linkName based on the movie title and year
        linkName = getSearchTitle(movie_title, year)
        print(f"linkName: {linkName}")

        if not linkName:
            print(f"No match found for {title} ({year})")
            return []

        # Build the full URL for the matched subtitle
        url = main_url + linkName
        print(f"true url: {url}")

        try:
            # Send the GET request to fetch the subtitle page
            response = session.get(url)
            response.raise_for_status()  # Ensure the request was successful
            
            # Parse the HTML content of the response
            content = BeautifulSoup(response.content, 'html.parser')

            if content:
                # Pass the content to get the list of subtitles
                _list = getallsubs(content, languages, filename)
                return _list
            else:
                return []

        except Exception as error:
            print(f"Error while fetching subtitle page: {error}")
            return []

    except Exception as error:
        print(f"Error in search_movie: {error}")
        return []



def search_tvshow(title, season, episode, languages, filename):
    try:
        title = title.strip()
        print(("title_search_tvshow", title))
        search_result = getSearchTitle_tv(title)
        print(("search_result", search_result))

        if not search_result:
            print(f"TV Show '{title}' not found.")
            return []

        linkName = search_result["title"]
        seasons = search_result["seasons"]

        season = int(season)  # Ensure season is an integer

        if season not in seasons:
            print(f"Season {season} not found for {title}. Available seasons: {list(seasons.keys())}")
            return []

        season_id = seasons[season]
        print(f"Using Season ID: {season_id} for {title} Season {season}")

        # Fix the season format in the request payload
        params = {
            "langs": [],
            "movieName": linkName,
            "season": f"season-{season}"  # Correct API format
        }
        
        try:
            content = s.post(__getMovie, headers=HDR, data=json.dumps(params), timeout=10).text
            response_json = json.loads(content)
        except requests.exceptions.Timeout:
            print(f"Timeout occurred when fetching subtitles for {title} Season {season}. Retrying once...")
            try:
                content = s.post(__getMovie, headers=HDR, data=json.dumps(params), timeout=15).text
                response_json = json.loads(content)
            except requests.exceptions.Timeout:
                print(f"Failed again due to timeout.")
                return []

        if content and response_json.get("success"):
            return getallsubs(content, languages, filename)

        return []

    except Exception as error:
        print(f"Error in search_tvshow: {error}")
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
    download_link = subtitles_list[pos]["link"]  # Use the 'link' from getallsubs
    filename = subtitles_list[pos]["filename"]
    language_name = subtitles_list[pos]["language_name"]
    print(f"download_link: {download_link}, filename: {filename}, language_name: {language_name}")

    # Send the GET request to fetch the page with the subtitle file
    response = session.get(download_link)
    response.raise_for_status()  # Ensure the request was successful

    # Parse the HTML content of the response
    content = BeautifulSoup(response.content, 'html.parser')

    # Look for the subtitle download link directly in the HTML content
    sub_download_link = content.find("div", id="content", class_="col-md-12")

    if sub_download_link:
        sub_download_link = sub_download_link.find("a")["href"]
        final_download_link = main_url2 + sub_download_link
        print(f"final_download_link: {final_download_link}")

        # Now initiate the download using the correct link
        subtitle_response = requests.get(final_download_link)
        subtitle_response.raise_for_status()  # Ensure the request was successful

        # Create the temporary folder if it doesn't exist
        if not os.path.exists(tmp_sub_dir):
            os.makedirs(tmp_sub_dir)

        # Define the local path to save the subtitle file
        local_tmp_file = os.path.join(tmp_sub_dir, filename)  # Ensure proper path creation
        print(f"local_tmp_file: {local_tmp_file}")

        # Save the subtitle file locally
        with open(local_tmp_file, 'wb') as local_file_handle:
            local_file_handle.write(subtitle_response.content)

        # Since it's an SRT file, we don't need to check archive type anymore
        packed = False
        subs_file = local_tmp_file

        language = subtitles_list[pos]["language_name"]  # Extract the language from the subtitle list
        log(__name__, f"Subtitles saved to '{local_tmp_file}'")
        return packed, language, subs_file  # Return packed status, language, and subtitle file path

    else:
        print("Failed to find the subtitle download link.")
        return False, None, None  # Return failure tuple
