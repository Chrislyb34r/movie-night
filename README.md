# 🎬 Movie Match

A Tinder-style app for couples (or roommates, or friend groups) to swipe through movies together and instantly find out what you both want to watch — no more 45-minute "what should we watch" scrolling sessions.

Built as a hands-on project to learn backend development with **FastAPI** and **SQLite**, with real-time streaming availability data pulled from a live API.

---

## How it works

1. One person creates a session, picks their streaming services and country, and gets a shareable session code (or invite link)
2. Their partner joins using that code
3. Both people swipe right (👍) or left (👎) on movies pulled from their selected streaming services
4. The moment **both** people swipe right on the same title, it's a match — shown instantly to both, and saved permanently in a **Matches** list you can revisit any time

---

## Features

- 🔗 **Real-time streaming availability** — movie data pulled live via the [Streaming Availability API](https://www.movieofthenight.com/about/api), reflecting what's actually on Netflix, Prime Video, Disney+, Max, and Crave right now
- 🌍 **Multi-country support** — availability differs by country (Canada, US, UK, Australia), and results are filtered accordingly
- 📊 **Flexible sorting** — sort by popularity over the last week, month, year, or all-time
- 👆 **Swipe gestures** — drag-to-swipe on touch and mouse, with animated LIKE/NOPE feedback
- 🎟️ **Shareable sessions** — one-tap code/link copying to invite a partner, no accounts or sign-up required
- ❤️ **Persistent match history** — every match is saved and viewable at any time, not just in the moment
- 🎨 **Custom themed UI** — a movie-ticket-inspired design (perforated card edges, ticket-stub styling) built from scratch, no UI framework

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | [FastAPI](https://fastapi.tiangolo.com/) (Python) |
| Database | SQLite (via Python's built-in `sqlite3`) |
| Frontend | Vanilla HTML/CSS/JavaScript (no framework) |
| External API | [Streaming Availability API](https://www.movieofthenight.com/about/api) (RapidAPI) |
| Server | [Uvicorn](https://www.uvicorn.org/) (ASGI) |

No frontend framework, no ORM, no build step — deliberately kept lightweight and dependency-light, both as a learning exercise and to keep the whole stack easy to reason about end to end.

---

## Project structure

```
movie-match/
├── app.py              # FastAPI routes — sessions, swipes, matches
├── database.py          # SQLite schema + queries
├── movie_api.py          # Streaming Availability API integration (with demo-data fallback)
├── models.py               # Pydantic request/response models
├── requirements.txt
├── static/
│   ├── style.css            # Movie-ticket themed styling
│   └── swipe.js               # Swipe gestures, API calls, match polling
└── templates/
    ├── setup.html              # Create/join a session
    ├── swipe.html                # The swipe screen
    └── matches.html                # Persistent match history
```

---

## Getting started

### Prerequisites
- Python 3.10+
- A free [RapidAPI](https://rapidapi.com/) account + subscription to the [Streaming Availability API](https://rapidapi.com/movie-of-the-night-movie-of-the-night-default/api/streaming-availability) (free tier: 500 requests/month) — optional, the app runs on demo data without it

### Setup

```bash
git clone https://github.com/Chrislyb34r/movie-match.git
cd movie-match

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Running it

```bash
uvicorn app:app --reload
```

Open **http://127.0.0.1:8000** in your browser.

To use real streaming data instead of the built-in demo movies, set your RapidAPI key before starting the server:

```bash
export RAPIDAPI_KEY=your_key_here      # Windows: set RAPIDAPI_KEY=your_key_here
```

### Testing the API directly

FastAPI auto-generates an interactive API explorer at **http://127.0.0.1:8000/docs** — useful for testing endpoints directly without the UI.

---

## Architecture notes

- **Sessions** are the shared "room" two people swipe within, identified by a short random code — no user accounts, no login
- **Matching logic** is a simple SQL query: a movie counts as matched once 2 *distinct* people have swiped right on it within the same session
- **Streaming data is cached per-session** at creation time rather than fetched live per-swipe, keeping the app within the API's free-tier rate limits
- The frontend **polls** for new matches every few seconds, so a match still surfaces even if it happens while you're mid-swipe on something else

---

## Roadmap

- [ ] Real deployment (currently runs locally / over local network)
- [ ] Genre and rating filters
- [ ] TV show support (currently movies only)
- [ ] Push notifications instead of polling

---

## License

MIT — see [LICENSE](LICENSE) for details.
