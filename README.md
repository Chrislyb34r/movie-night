# Movie Match

A tiny app where you and your partner swipe on movies, and get notified when you both swipe right on the same one.

## Setup

1. Open this folder in PyCharm.
2. Create a virtual environment (PyCharm will usually prompt you to do this automatically when it detects `requirements.txt`). Or manually:
   ```
   python -m venv venv
   source venv/bin/activate      # on Mac/Linux
   venv\Scripts\activate         # on Windows
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running it

```
uvicorn app:app --reload
```

Then open **http://127.0.0.1:8000/docs** in your browser.

This is FastAPI's auto-generated interactive docs page — you can test every
endpoint here without writing any frontend code. This is the recommended way
to build and test step 5 from our plan (backend logic) before touching HTML/JS.

### Try it out in /docs

1. **POST /session/create** → click "Try it out" → Execute. This creates a
   session pre-loaded with 5 demo movies (no API key needed yet) and returns
   a `session_id`. Copy it.
2. **GET /session/{session_id}/next-movie** → paste your session_id, and use
   `user_name = "alice"`. This returns the next unswiped movie.
3. **POST /session/{session_id}/swipe** → swipe right on that movie as
   `"alice"`.
4. Repeat step 2 but with `user_name = "bob"` — get the same movie, then
   swipe right as `"bob"` too.
5. **GET /session/{session_id}/matches** → you should now see that movie
   show up as a match!

Once this flow makes sense to you in `/docs`, the web page (swipe.html) is
just a UI wrapper that calls these same endpoints with JavaScript's `fetch()`.

## Using the real streaming API (later)

Right now `movie_api.py` returns demo data. When you're ready for real
streaming availability:

1. Sign up for a free RapidAPI account and subscribe to the free tier of the
   [Streaming Availability API](https://rapidapi.com/movie-of-the-night-movie-of-the-night-default/api/streaming-availability)
2. Set an environment variable with your key:
   ```
   export RAPIDAPI_KEY=your_key_here      # Mac/Linux
   set RAPIDAPI_KEY=your_key_here         # Windows (cmd)
   ```
   Or in PyCharm: Run > Edit Configurations > Environment Variables.
3. Restart the app — it'll automatically use the real API instead of demo data.

## What's next

- [ ] Build `templates/setup.html` — a page to create/join a session
- [ ] Build `templates/swipe.html` + `static/swipe.js` — the actual swipe UI
- [ ] Style it with `static/style.css`
- [ ] (Later) Push notifications instead of polling for matches
