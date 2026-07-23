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
def create_session(services: str = "netflix,prime"):
    """
    Creates a new shared session and pre-loads it with movies from
    the given streaming services (comma-separated, e.g. "netflix,prime").
    """
    session_id = str(uuid.uuid4())[:8]  # short, shareable code
    database.create_session(session_id)

    service_list = [s.strip() for s in services.split(",")]
    movies = movie_api.fetch_movies(service_list)

    for movie in movies:
        database.add_movie(
            session_id=session_id,
            external_id=movie["external_id"],
            title=movie["title"],
            overview=movie["overview"],
            poster_url=movie["poster_url"],
            streaming_service=movie["streaming_service"],
        )

    return SessionCreateResponse(session_id=session_id)


@app.get("/session/{session_id}/next-movie")
def get_next_movie(session_id: str, user_name: str):
    """
    Returns the next movie this user hasn't swiped on yet.
    """
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
    if not database.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    matches = database.get_matches(session_id)
    return {"matches": matches}
