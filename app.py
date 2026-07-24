"""
app.py

The main FastAPI application. Run it with:
    uvicorn app:app --reload

Then open http://127.0.0.1:8000/docs to test every endpoint interactively
before building any frontend at all.
"""

import uuid

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

import database
import movie_api
from models import SwipeRequest, SessionCreateResponse

app = FastAPI(title="Movie Match")

# Create the database tables on startup (safe to run every time).
database.init_db()

# Serve style.css / swipe.js from the /static folder.
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_homepage():
    return FileResponse("templates/setup.html")


@app.get("/swipe/{session_id}")
def serve_swipe_page(session_id: str):
    return FileResponse("templates/swipe.html")


@app.get("/matches/{session_id}")
def serve_matches_page(session_id: str):
    return FileResponse("templates/matches.html")


@app.post("/session/create", response_model=SessionCreateResponse)
def create_session(
    services: str = "crave",
    country: str = "us",
    order_by: str = "popularity_1year",
    show_type: str = "movie",
    genres: str = "",
    min_rating: float | None = None,
):
    """
    Creates a new shared session and pre-loads it with movies from
    the given streaming services (comma-separated, e.g. "netflix,prime")
    available in the given country (ISO 3166-1 alpha-2 code, e.g. "ca"),
    ranked by the given order_by value (see movie_api.fetch_movies).

    show_type: "movie" or "series"
    genres: comma-separated genre ids (e.g. "action,comedy"), or "" for any
    min_rating: minimum rating out of 10 (e.g. 7 for "7+"), or None for any
    """
    # Session codes are lowercase hex — normalizing here means it doesn't
    # matter if a code somehow gets typed/pasted in a different case later.
    session_id = str(uuid.uuid4())[:8].lower()
    database.create_session(session_id)

    service_list = [s.strip() for s in services.split(",") if s.strip()]
    genre_list = [g.strip() for g in genres.split(",") if g.strip()]

    movies = movie_api.fetch_movies(
        service_list,
        country=country,
        order_by=order_by,
        show_type=show_type,
        genres=genre_list,
        min_rating=min_rating,
    )

    for movie in movies:
        database.add_movie(
            session_id=session_id,
            external_id=movie["external_id"],
            title=movie["title"],
            overview=movie["overview"],
            poster_url=movie["poster_url"],
            streaming_service=movie["streaming_service"],
            rating=movie.get("rating"),
            genres=movie.get("genres", ""),
        )

    return SessionCreateResponse(session_id=session_id)


@app.get("/session/{session_id}/next-movie")
def get_next_movie(session_id: str, user_name: str):
    """
    Returns the next movie this user hasn't swiped on yet.
    """
    session_id = session_id.lower()

    if not database.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    movie = database.get_next_movie(session_id, user_name)
    if movie is None:
        return {"movie": None, "message": "No more movies to swipe on"}

    return {"movie": movie}


@app.post("/session/{session_id}/swipe")
def swipe(session_id: str, swipe_request: SwipeRequest):
    """
    Records a swipe. If this makes 2 different people swipe right
    on the same movie, it's a match.
    """
    session_id = session_id.lower()

    if not database.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    if swipe_request.direction not in ("left", "right"):
        raise HTTPException(status_code=400, detail="direction must be 'left' or 'right'")

    database.record_swipe(
        session_id=session_id,
        user_name=swipe_request.user_name,
        movie_id=swipe_request.movie_id,
        direction=swipe_request.direction,
    )

    is_match = False
    if swipe_request.direction == "right":
        is_match = database.check_for_match(session_id, swipe_request.movie_id)

    return {"recorded": True, "match": is_match}


@app.get("/session/{session_id}/matches")
def get_matches(session_id: str):
    """
    Returns all movies matched so far in this session.
    The frontend polls this periodically to show match popups.
    """
    session_id = session_id.lower()

    if not database.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    matches = database.get_matches(session_id)
    return {"matches": matches}
