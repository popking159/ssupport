import json
import logging
import random
import re
import time
from typing import Any, Dict, List, Optional

import requests
import urllib3
from bs4 import BeautifulSoup
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)

DEBUG = False

logger = logging.getLogger("SubsSupport.TMDB")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] [TMDB] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Mobile/15E148 Safari/604.1",
]


def get_random_ua() -> str:
    return random.choice(user_agents)


def build_headers() -> Dict[str, str]:
    return {
        "User-Agent": get_random_ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9,ar-EG;q=0.8,ar;q=0.7",
        "Referer": "https://www.themoviedb.org",
        "Connection": "keep-alive",
    }


headers = build_headers()


def _safe_request(url: str, context: str, timeout: int = 10) -> Optional[requests.Response]:
    try:
        logger.debug("HTTP GET start | context=%s | url=%s", context, url)
        response = requests.get(url, headers=build_headers(), verify=False, timeout=timeout)
        logger.debug(
            "HTTP GET done | context=%s | status=%s | url=%s",
            context,
            response.status_code,
            url,
        )
        response.raise_for_status()
        return response
    except requests.RequestException:
        logger.exception("HTTP GET failed | context=%s | url=%s", context, url)
        return None


def _parse_html(response: requests.Response, context: str) -> Optional[BeautifulSoup]:
    try:
        soup = BeautifulSoup(response.text, "html.parser")
        logger.debug("HTML parsed successfully | context=%s", context)
        return soup
    except Exception:
        logger.exception("HTML parse failed | context=%s", context)
        return None


def extract_title_from_card(card) -> str:
    title_span = card.select_one("h2 span")
    if title_span:
        title = title_span.get_text(strip=True)
        if title:
            return title

    h2_tag = card.find("h2")
    if h2_tag:
        for span in h2_tag.find_all("span", class_="title"):
            span.decompose()
        title = h2_tag.get_text(strip=True)
        if title:
            return title

    a_tag = card.select_one('a[href^="/movie/"]') or card.select_one('a[href^="/tv/"]') or card.find("a", class_="result")
    if a_tag:
        for span in a_tag.find_all("span", class_="title"):
            span.decompose()
        title = a_tag.get_text(strip=True)
        if title:
            return title

    img_tag = card.find("img", class_="poster")
    if img_tag and img_tag.has_attr("alt"):
        return img_tag["alt"]

    if a_tag and a_tag.has_attr("href"):
        url_parts = a_tag["href"].split("/")
        if len(url_parts) > 2:
            title_part = url_parts[-1]
            if "-" in title_part:
                title_part = title_part.split("-", 1)[1]
            return title_part.replace("-", " ").title()

    return "Unknown Title"


def extract_alternative_title(card) -> Optional[str]:
    alt_title_span = card.find("span", class_="title")
    if alt_title_span:
        return alt_title_span.get_text(strip=True)
    return None


def extract_poster_url(card) -> Optional[str]:
    img_tag = card.find("img", class_="poster")
    if img_tag and img_tag.has_attr("src"):
        poster_url = img_tag["src"]
        replacements = {
            "w94_and_h141_bestv2": "w220_and_h330_face",
            "w130_and_h195_bestv2": "w220_and_h330_face",
            "w94_and_h141_face": "w220_and_h330_face",
            "w188_and_h282_face": "w220_and_h330_face",
        }
        for old, new in replacements.items():
            if old in poster_url:
                return poster_url.replace(old, new)
        return poster_url
    return None


def extract_tmdb_id(card) -> Optional[str]:
    a_tag = card.select_one('a[href^="/movie/"]') or card.select_one('a[href^="/tv/"]') or card.find("a", class_="result")
    if a_tag and a_tag.has_attr("href"):
        href = a_tag["href"]
        match = re.search(r"/(?:movie|tv)/(\d+)", href)
        if match:
            return match.group(1)
    return None


def scrape_tmdb_movies(movie_title: str) -> List[Dict[str, Any]]:
    title = movie_title.replace(" ", "+").lower()
    url = f"https://www.themoviedb.org/search?query={title}"
    logger.info("Searching TMDB movies | title=%s | url=%s", movie_title, url)

    response = _safe_request(url, "tmdb search")
    if not response:
        return []

    soup = _parse_html(response, "tmdb search")
    if soup is None:
        return []

    results_container = soup.select_one("div.media-card-list")
    if not results_container:
        logger.warning("TMDB search results container not found | title=%s", movie_title)
        logger.debug("Search HTML snippet: %s", response.text[:2000])
        return []

    movie_cards = results_container.select("div.comp\\:media-card")
    logger.info("Found %d movie cards for title=%s", len(movie_cards), movie_title)

    if not movie_cards:
        logger.warning("No movie cards found for title=%s", movie_title)
        logger.debug("Results container snippet: %s", str(results_container)[:3000])
        return []

    movies_data: List[Dict[str, Any]] = []

    for index, card in enumerate(movie_cards, 1):
        try:
            movie: Dict[str, Any] = {}

            a_tag = card.select_one('a[href^="/movie/"]') or card.select_one('a[href^="/tv/"]')

            movie["title"] = extract_title_from_card(card)

            alt_title = extract_alternative_title(card)
            if alt_title:
                movie["alternative_title"] = alt_title

            if a_tag and a_tag.has_attr("href"):
                movie["url"] = "https://www.themoviedb.org" + a_tag["href"]

            release_date = card.select_one("span.release_date")
            if release_date:
                movie["release_date"] = release_date.get_text(" ", strip=True)

            overview_p = card.select_one("div p")
            if overview_p:
                overview_text = overview_p.get_text(" ", strip=True)
                if overview_text:
                    movie["overview"] = overview_text

            poster_url = extract_poster_url(card)
            if poster_url:
                movie["poster_url"] = poster_url

            if a_tag and a_tag.has_attr("data-media-type"):
                movie["media_type"] = a_tag["data-media-type"]

            if a_tag and a_tag.has_attr("data-media-adult"):
                movie["adult_content"] = a_tag["data-media-adult"] == "true"

            tmdb_id = extract_tmdb_id(card)
            if tmdb_id:
                movie["tmdb_id"] = tmdb_id

            logger.debug(
                "Parsed card %d | title=%s | release_date=%s | tmdb_id=%s | media_type=%s",
                index,
                movie.get("title"),
                movie.get("release_date"),
                movie.get("tmdb_id"),
                movie.get("media_type"),
            )
            movies_data.append(movie)
        except Exception:
            logger.exception("Failed parsing movie card index=%d", index)

    return movies_data


def scrape_movie_logos(movie_url: str) -> List[str]:
    logos_url = movie_url + "/images/logos"

    try:
        time.sleep(0.5)
        response = _safe_request(logos_url, "movie logos")
        if not response:
            return []

        soup = _parse_html(response, "movie logos")
        if soup is None:
            return []

        logos_section = soup.find("section", class_="panel user_images")
        if not logos_section:
            logger.debug("No logos section found | movie_url=%s", movie_url)
            return []

        logo_images = []
        logo_elements = logos_section.select('img[src*="w500"]')

        for logo_element in logo_elements:
            if logo_element.has_attr("src"):
                logo_images.append(logo_element["src"])

        logger.debug("Scraped %d logos | movie_url=%s", len(logo_images), movie_url)
        return logo_images

    except Exception:
        logger.exception("Error scraping logos | movie_url=%s", movie_url)
        return []


def scrape_movie_backdrops(movie_url: str) -> List[str]:
    backdrops_url = movie_url + "/images/backdrops"

    try:
        time.sleep(0.5)
        response = _safe_request(backdrops_url, "movie backdrops")
        if not response:
            return []

        soup = _parse_html(response, "movie backdrops")
        if soup is None:
            return []

        backdrops_section = soup.find("section", class_="panel user_images")
        if not backdrops_section:
            logger.debug("No backdrops section found | movie_url=%s", movie_url)
            return []

        backdrop_images = []
        backdrop_elements = backdrops_section.select('img[src*="w500_and_h282_face"]')

        for backdrop_element in backdrop_elements:
            if backdrop_element.has_attr("src"):
                backdrop_images.append(backdrop_element["src"])

        logger.debug("Scraped %d backdrops | movie_url=%s", len(backdrop_images), movie_url)
        return backdrop_images

    except Exception:
        logger.exception("Error scraping backdrops | movie_url=%s", movie_url)
        return []


def scrape_movie_posters(movie_url: str) -> List[str]:
    posters_url = movie_url + "/images/posters"

    try:
        time.sleep(0.5)
        response = _safe_request(posters_url, "movie posters")
        if not response:
            return []

        soup = _parse_html(response, "movie posters")
        if soup is None:
            return []

        posters_section = soup.find("section", class_="panel user_images")
        if not posters_section:
            logger.debug("No posters section found | movie_url=%s", movie_url)
            return []

        poster_images = []
        poster_elements = posters_section.select('img[src*="w220_and_h330_face"]')

        for poster_element in poster_elements:
            if poster_element.has_attr("src"):
                poster_images.append(poster_element["src"])

        logger.debug("Scraped %d posters | movie_url=%s", len(poster_images), movie_url)
        return poster_images

    except Exception:
        logger.exception("Error scraping posters | movie_url=%s", movie_url)
        return []


def scrape_movie_trailers(movie_url: str) -> List[Dict[str, Any]]:
    trailers_url = movie_url + "/videos?active_nav_item=Trailers"

    try:
        time.sleep(0.5)
        response = _safe_request(trailers_url, "movie trailers")
        if not response:
            return []

        soup = _parse_html(response, "movie trailers")
        if soup is None:
            return []

        trailers_section = soup.find("section", class_="panel video")
        if not trailers_section:
            logger.debug("No trailers section found | movie_url=%s", movie_url)
            return []

        trailers = []
        trailer_elements = trailers_section.find_all("div", class_="video card default")

        for trailer_element in trailer_elements:
            trailer: Dict[str, Any] = {}

            play_button = trailer_element.find("a", class_="play_trailer")
            if play_button and play_button.has_attr("data-id"):
                trailer["youtube_id"] = play_button["data-id"]
                trailer["youtube_url"] = f"https://www.youtube.com/watch?v={play_button['data-id']}"

            title_element = trailer_element.find("h2")
            if title_element:
                trailer["title"] = title_element.get_text(strip=True)

            sub_element = trailer_element.find("h3", class_="sub")
            if sub_element:
                trailer["details"] = sub_element.get_text(strip=True)

            if play_button and play_button.has_attr("data-site"):
                trailer["site"] = play_button["data-site"]

            channel_element = trailer_element.find("h4")
            if channel_element:
                trailer["channel"] = channel_element.get_text(strip=True)

            if trailer:
                trailers.append(trailer)

        logger.debug("Scraped %d trailers | movie_url=%s", len(trailers), movie_url)
        return trailers

    except Exception:
        logger.exception("Error scraping trailers | movie_url=%s", movie_url)
        return []


def scrape_movie_cast(movie_url: str) -> List[Dict[str, Any]]:
    cast_url = movie_url + "/cast"

    try:
        time.sleep(0.5)
        response = _safe_request(cast_url, "movie cast")
        if not response:
            return []

        soup = _parse_html(response, "movie cast")
        if soup is None:
            return []

        cast_section = soup.find("section", class_="panel pad")
        if not cast_section:
            logger.warning("No cast section found | movie_url=%s", movie_url)
            return []

        cast = []
        cast_elements = cast_section.find_all("li", attrs={"data-order": True})

        for i, cast_element in enumerate(cast_elements[:6]):
            actor: Dict[str, Any] = {}

            info_div = cast_element.find("div", class_="info")
            if info_div:
                p_tag = info_div.find("p")
                if p_tag:
                    a_tag = p_tag.find("a")
                    if a_tag:
                        actor["name"] = a_tag.get_text(strip=True)

            character_element = cast_element.find("p", class_="character")
            if character_element:
                actor["character"] = character_element.get_text(strip=True)

            profile_img = cast_element.find("img", class_="profile")
            if profile_img and profile_img.has_attr("src"):
                profile_url = profile_img["src"]
                if "w66_and_h66_face" in profile_url:
                    profile_url = profile_url.replace("w66_and_h66_face", "w132_and_h132_face")
                actor["profile_url"] = profile_url

            if actor.get("name"):
                cast.append(actor)
            else:
                logger.warning("No name found for cast member index=%d | movie_url=%s", i, movie_url)

        logger.debug("Scraped %d cast members | movie_url=%s", len(cast), movie_url)
        return cast

    except Exception:
        logger.exception("Error scraping cast | movie_url=%s", movie_url)
        return []


def scrape_movie_details(movie_url: str) -> Optional[Dict[str, Any]]:
    try:
        logger.info("Scraping movie details | movie_url=%s", movie_url)
        response = _safe_request(movie_url, "movie details")
        if not response:
            return None

        soup = _parse_html(response, "movie details")
        if soup is None:
            return None

        details: Dict[str, Any] = {}

        title_element = soup.find("h2", class_="title")
        if title_element:
            details["title"] = title_element.get_text(strip=True)

        tagline_element = soup.find("h3", class_="tagline")
        if tagline_element:
            details["tagline"] = tagline_element.get_text(strip=True)

        overview_element = soup.find("div", class_="overview")
        if overview_element:
            details["overview"] = (
                overview_element.find("p").get_text(strip=True)
                if overview_element.find("p")
                else overview_element.get_text(strip=True)
            )

        release_date_element = soup.find("span", class_="release")
        if release_date_element:
            details["release_date"] = release_date_element.get_text(strip=True)

        runtime_element = soup.find("span", class_="runtime")
        if runtime_element:
            details["runtime"] = runtime_element.get_text(strip=True)

        genres = []
        genres_elements = soup.find("span", class_="genres")
        if genres_elements:
            for genre in genres_elements.find_all("a"):
                genres.append(genre.get_text(strip=True))
            details["genres"] = genres

        rating_element = soup.find("div", class_="user_score_chart")
        if rating_element and rating_element.has_attr("data-percent"):
            details["rating"] = rating_element["data-percent"]

        poster_element = soup.find("img", class_="poster")
        if poster_element and poster_element.has_attr("src"):
            details["poster_url"] = poster_element["src"]

        logos = scrape_movie_logos(movie_url)
        if logos:
            details["logo_urls"] = logos

        backdrops = scrape_movie_backdrops(movie_url)
        if backdrops:
            details["backdrop_urls"] = backdrops

        posters = scrape_movie_posters(movie_url)
        if posters:
            details["additional_poster_urls"] = posters

        trailers = scrape_movie_trailers(movie_url)
        if trailers:
            details["trailers"] = trailers

        cast = scrape_movie_cast(movie_url)
        if cast:
            details["cast"] = cast

        director_elements = soup.select("ol.people li.profile")
        for director_element in director_elements:
            job_element = director_element.find("p", class_="job")
            if job_element and "director" in job_element.get_text(strip=True).lower():
                name_element = director_element.find("p", class_="name")
                if name_element:
                    details["director"] = (
                        name_element.find("a").get_text(strip=True)
                        if name_element.find("a")
                        else name_element.get_text(strip=True)
                    )
                break

        logger.info(
            "Scraped movie details complete | movie_url=%s | fields=%s",
            movie_url,
            sorted(details.keys()),
        )
        return details

    except Exception:
        logger.exception("Error scraping movie details | movie_url=%s", movie_url)
        return None


def main() -> None:
    title = input("Please enter movie name: ")

    try:
        movies = scrape_tmdb_movies(title)

        if not movies:
            print("No movies found!")
            return

        print(f"\nFound {len(movies)} movies:\n")

        for i, movie in enumerate(movies, 1):
            print(f"{i}. {movie.get('title', 'N/A')} ({movie.get('release_date', 'N/A')})")

        selection = input("\nEnter the number of the movie you want to scrape details for (or 'all' for all movies): ")

        if selection.lower() == "all":
            detailed_movies = []
            for i, movie in enumerate(movies, 1):
                print(f"Scraping details for movie {i}/{len(movies)}: {movie.get('title', 'N/A')}")
                if "url" in movie:
                    details = scrape_movie_details(movie["url"])
                    if details:
                        if "cast" in details:
                            for actor in details["cast"]:
                                if "profile_url" in actor and "w66_and_h66_face" in actor["profile_url"]:
                                    actor["profile_url"] = actor["profile_url"].replace("w66_and_h66_face", "w132_and_h132_face")

                        merged_info = {**movie, **details}
                        detailed_movies.append(merged_info)

            filename = f"tmdb_{title.replace(' ', '_')}_detailed_results.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(detailed_movies, f, indent=2, ensure_ascii=False)
            print(f"All detailed results saved to {filename}")
            logger.info("Saved all detailed results | file=%s | count=%d", filename, len(detailed_movies))

        else:
            try:
                selection_idx = int(selection) - 1
                if 0 <= selection_idx < len(movies):
                    selected_movie = movies[selection_idx]
                    print(f"\nScraping details for: {selected_movie.get('title', 'N/A')}")

                    if "url" in selected_movie:
                        details = scrape_movie_details(selected_movie["url"])
                        if details:
                            if "cast" in details:
                                for actor in details["cast"]:
                                    if "profile_url" in actor and "w66_and_h66_face" in actor["profile_url"]:
                                        actor["profile_url"] = actor["profile_url"].replace("w66_and_h66_face", "w132_and_h132_face")

                            merged_info = {**selected_movie, **details}

                            year = ""
                            if "release_date" in merged_info:
                                year_match = re.search(r"\d{4}", merged_info["release_date"])
                                if year_match:
                                    year = f"_{year_match.group()}"

                            filename = f"tmdb_{merged_info.get('title', 'unknown').replace(' ', '_')}{year}_details.json"

                            print("\nDetailed Movie Information:")
                            print("=" * 50)
                            for key, value in merged_info.items():
                                if key == "cast":
                                    print("Cast:")
                                    for i, actor in enumerate(value, 1):
                                        print(f"  {i}. {actor.get('name', 'N/A')} as {actor.get('character', 'N/A')}")
                                        if "profile_url" in actor:
                                            print(f"     Profile: {actor['profile_url']}")
                                elif key == "logo_urls":
                                    print("Logos:")
                                    for i, logo_url in enumerate(value, 1):
                                        print(f"  {i}. {logo_url}")
                                elif key == "backdrop_urls":
                                    print("Backdrops:")
                                    for i, backdrop_url in enumerate(value, 1):
                                        print(f"  {i}. {backdrop_url}")
                                elif key == "additional_poster_urls":
                                    print("Additional Posters:")
                                    for i, poster_url in enumerate(value, 1):
                                        print(f"  {i}. {poster_url}")
                                elif key == "trailers":
                                    print("Trailers:")
                                    for i, trailer in enumerate(value, 1):
                                        print(f"  {i}. {trailer.get('title', 'N/A')}")
                                        print(f"     YouTube ID: {trailer.get('youtube_id', 'N/A')}")
                                        print(f"     YouTube URL: {trailer.get('youtube_url', 'N/A')}")
                                        print(f"     Details: {trailer.get('details', 'N/A')}")
                                        print(f"     Site: {trailer.get('site', 'N/A')}")
                                        if "channel" in trailer:
                                            print(f"     Channel: {trailer['channel']}")
                                elif isinstance(value, list):
                                    print(f"{key.replace('_', ' ').title()}: {', '.join(value)}")
                                else:
                                    print(f"{key.replace('_', ' ').title()}: {value}")

                            save = input("\nDo you want to save the detailed results to a JSON file? (y/n): ")
                            if save.lower() == "y":
                                with open(filename, "w", encoding="utf-8") as f:
                                    json.dump(merged_info, f, indent=2, ensure_ascii=False)
                                print(f"Detailed results saved to {filename}")
                                logger.info("Saved detailed result | file=%s | title=%s", filename, merged_info.get("title"))
                        else:
                            print("Failed to scrape detailed information.")
                    else:
                        print("No URL found for the selected movie.")
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Please enter a valid number or 'all'.")

    except requests.RequestException as e:
        print(f"Error making request: {e}")
        logger.exception("Request error in main")
    except Exception as e:
        print(f"An error occurred: {e}")
        logger.exception("Unhandled error in main")


if __name__ == "__main__":
    main()
