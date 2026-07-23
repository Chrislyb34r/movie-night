"""
movie_api.py

Fetches movie data. Uses the Streaming Availability API (via RapidAPI) if
you've set an API key, otherwise falls back to demo data so you can build
and test the rest of the app first without signing up for anything yet.

To use the real API later:
1. Sign up at https://rapidapi.com/movie-of-the-night-movie-of-the-night-default/api/streaming-availability
2. Set the RAPIDAPI_KEY environment variable (see README for how)
"""

import os
import requests

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
RAPIDAPI_HOST = "streaming-availability.p.rapidapi.com"

# Fallback data so the app is testable with zero setup.
DEMO_MOVIES = [
    {
        "external_id": "demo-1",
        "title": "The Grand Budapest Hotel",
        "overview": "A concierge and his protégé become embroiled in a theft and murder mystery.",
        "poster_url": "",
        "streaming_service": "Demo",
    },
    {
        "external_id": "demo-2",
        "title": "Spirited Away",
        "overview": "A young girl wanders into a world ruled by gods and spirits.",
        "poster_url": "",
        "streaming_service": "Demo",
    },
    {
        "external_id": "demo-3",
        "title": "Inception",
        "overview": "A thief who steals corporate secrets through dream-sharing technology.",
        "poster_url": "",
        "streaming_service": "Demo",
    },
    {
        "external_id": "demo-4",
        "title": "Parasite",
        "overview": "Greed and class discrimination threaten a newly formed symbiotic relationship.",
        "poster_url": "",
        "streaming_service": "Demo",
    },
    {
        "external_id": "demo-5",
        "title": "The Grand Tour",
        "overview": "Three men travel the world and review cars.",
        "poster_url": "",
        "streaming_service": "Demo",
    },
]


def fetch_movies(services: list[str], country: str = "us") -> list[dict]:
    """
    Returns a list of movie dicts with keys:
    external_id, title, overview, poster_url, streaming_service

    If no RAPIDAPI_KEY is set, returns demo data instead so you can
    keep building without needing an API key yet.
    """
    if not RAPIDAPI_KEY:
        print("[movie_api] No RAPIDAPI_KEY set — using demo data.")
        return DEMO_MOVIES

    url = f"https://{RAPIDAPI_HOST}/shows/search/filters"
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    params = {
        "country": country,
        "services": ",".join(services),
        "show_type": "movie",
        "order_by": "popularity",
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    movies = []
    for show in data.get("shows", []):
        streaming_options = show.get("streamingOptions", {}).get(country, [])
        service_name = streaming_options[0]["service"]["name"] if streaming_options else "Unknown"

        movies.append({
            "external_id": show.get("id", ""),
            "title": show.get("title", "Untitled"),
            "overview": show.get("overview", ""),
            "poster_url": show.get("imageSet", {}).get("verticalPoster", {}).get("w360", ""),
            "streaming_service": service_name,
        })

    return movies
