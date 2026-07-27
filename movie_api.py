"""
movie_api.py

Fetches movie/show data. Uses the Streaming Availability API (via RapidAPI)
if you've set an API key, otherwise falls back to demo data so you can build
and test the rest of the app first without signing up for anything yet.

To use the real API later:
1. Sign up at https://rapidapi.com/movie-of-the-night-movie-of-the-night-default/api/streaming-availability
2. Set the RAPIDAPI_KEY environment variable (see README for how)
"""

import os
import json
import time
from pathlib import Path
import requests

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
RAPIDAPI_HOST = "streaming-availability.p.rapidapi.com"

# --- Local cache so repeated test runs with the same filters don't re-hit the API ---
CACHE_FILE = Path(__file__).parent / "api_cache.json"
CACHE_TTL_SECONDS = 24 * 60 * 60  # how long a cached result stays valid (24 hours)


def _load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}  # a corrupted/empty cache file just means "start fresh"
    return {}


def _save_cache(cache: dict):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def _cache_key(services, country, order_by, show_type, genres, min_rating, max_pages) -> str:
    """Builds a stable string identifying this exact combination of filters."""
    parts = [
        ",".join(sorted(services)),
        country,
        order_by,
        show_type,
        ",".join(sorted(genres or [])),
        str(min_rating),
        str(max_pages),
    ]
    return "|".join(parts)

# Fallback data so the app is testable with zero setup.
DEMO_MOVIES = [
    {
        "external_id": "demo-1",
        "title": "The Grand Budapest Hotel",
        "overview": "A concierge and his protégé become embroiled in a theft and murder mystery.",
        "poster_url": "",
        "streaming_service": "Demo",
        "rating": 8.1,
        "genres": "Comedy, Drama",
    },
    {
        "external_id": "demo-2",
        "title": "Spirited Away",
        "overview": "A young girl wanders into a world ruled by gods and spirits.",
        "poster_url": "",
        "streaming_service": "Demo",
        "rating": 8.6,
        "genres": "Animation, Fantasy",
    },
    {
        "external_id": "demo-3",
        "title": "Inception",
        "overview": "A thief who steals corporate secrets through dream-sharing technology.",
        "poster_url": "",
        "streaming_service": "Demo",
        "rating": 8.8,
        "genres": "Action, Sci-Fi, Thriller",
    },
    {
        "external_id": "demo-4",
        "title": "Parasite",
        "overview": "Greed and class discrimination threaten a newly formed symbiotic relationship.",
        "poster_url": "",
        "streaming_service": "Demo",
        "rating": 8.5,
        "genres": "Drama, Thriller",
    },
    {
        "external_id": "demo-5",
        "title": "The Grand Tour",
        "overview": "Three men travel the world and review cars.",
        "poster_url": "",
        "streaming_service": "Demo",
        "rating": 8.7,
        "genres": "Comedy, Adventure",
    },
]


def fetch_movies(
    services: list[str],
    country: str = "us",
    order_by: str = "popularity_1year",
    show_type: str = "movie",
    genres: list[str] | None = None,
    min_rating: float | None = None,
    max_pages: int = 5,
    force_refresh: bool = False,
) -> list[dict]:
    """
    Returns a list of dicts with keys:
    external_id, title, overview, poster_url, streaming_service, rating, genres

    order_by: "popularity_alltime", "popularity_1year", "popularity_1month", "popularity_1week"
    show_type: "movie" or "series"
    genres: list of genre ids (see the API's /genres endpoint for the full list),
            or None/[] for no genre filtering
    min_rating: minimum rating out of 10 (e.g. 7 for "7+"), or None for no minimum
    max_pages: the API paginates results (cursor-based) — this caps how many pages
               we fetch, since each page costs one request against the free tier's
               daily quota. 5 pages is normally enough for a solid-sized swipe deck
               without burning through the whole day's allowance in one session.
    force_refresh: skip the local cache and hit the API fresh, even if a cached
                   result for these exact filters is still within its TTL.

    Results are cached locally (in api_cache.json) for 24 hours per unique
    combination of filters, so repeated testing with the same settings doesn't
    re-query the API or use up your daily request quota.

    If no RAPIDAPI_KEY is set, returns demo data instead so you can
    keep building without needing an API key yet.
    """
    if not RAPIDAPI_KEY:
        print("[movie_api] No RAPIDAPI_KEY set — using demo data.")
        return DEMO_MOVIES

    key = _cache_key(services, country, order_by, show_type, genres, min_rating, max_pages)

    if not force_refresh:
        cache = _load_cache()
        cached_entry = cache.get(key)
        if cached_entry and (time.time() - cached_entry["cached_at"]) < CACHE_TTL_SECONDS:
            age_minutes = int((time.time() - cached_entry["cached_at"]) / 60)
            print(f"[movie_api] Using cached results ({age_minutes} min old) for: {key}")
            return cached_entry["movies"]

    url = f"https://{RAPIDAPI_HOST}/shows/search/filters"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    base_params = {
        "country": country,
        "catalogs": ",".join(services),
        "show_type": show_type,
        "order_by": order_by,
    }

    if genres:
        base_params["genres"] = ",".join(genres)

    if min_rating is not None:
        # The API's rating scale is 0-100; our UI works in a friendlier 0-10 scale.
        base_params["min_rating"] = int(min_rating * 10)

    all_shows = []
    cursor = None

    for page_num in range(max_pages):
        params = dict(base_params)
        if cursor:
            params["cursor"] = cursor

        response = requests.get(url, headers=headers, params=params, timeout=10)

        if not response.ok:
            # Print the API's own explanation of what went wrong — much more
            # useful than just "400 Bad Request" with no detail.
            print(f"[movie_api] API error {response.status_code}: {response.text}")

        response.raise_for_status()
        data = response.json()

        all_shows.extend(data.get("shows", []))

        if data.get("hasMore") and data.get("nextCursor"):
            cursor = data["nextCursor"]
        else:
            break  # no more pages — stop early rather than using all max_pages

    print(f"[movie_api] Fetched {len(all_shows)} shows across {page_num + 1} page(s).")

    # The API returns ALL streaming services a show is on in this country,
    # not just the ones we asked for — so we can't just grab the first one.
    requested_service_ids = set(services)

    movies = []
    for show in all_shows:
        streaming_options = show.get("streamingOptions", {}).get(country, [])

        # Prefer a streaming option that matches one of the services the
        # user actually selected (e.g. Crave). Fall back to the first
        # option only if none match, so we never crash on odd data.
        matching_option = next(
            (opt for opt in streaming_options if opt.get("service", {}).get("id") in requested_service_ids),
            streaming_options[0] if streaming_options else None
        )
        service_name = matching_option["service"]["name"] if matching_option else "Unknown"

        # Rating comes back on a 0-100 scale from the API; we store/display out of 10.
        raw_rating = show.get("rating")
        rating = round(raw_rating / 10, 1) if raw_rating is not None else None

        genre_names = ", ".join(g.get("name", "") for g in show.get("genres", []))

        movies.append({
            "external_id": show.get("id", ""),
            "title": show.get("title", "Untitled"),
            "overview": show.get("overview", ""),
            "poster_url": show.get("imageSet", {}).get("verticalPoster", {}).get("w360", ""),
            "streaming_service": service_name,
            "rating": rating,
            "genres": genre_names,
        })

    # Save to cache so identical requests within the TTL window skip the API entirely.
    cache = _load_cache()
    cache[key] = {"cached_at": time.time(), "movies": movies}
    _save_cache(cache)

    return movies
