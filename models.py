"""
models.py

Pydantic models define the "shape" of data going in and out of our API.
FastAPI uses these to automatically validate requests and generate docs.
"""

from pydantic import BaseModel


class SwipeRequest(BaseModel):
    user_name: str
    movie_id: int
    direction: str  # "left" or "right"


class SessionCreateResponse(BaseModel):
    session_id: str
