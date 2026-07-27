/* ============================================
   Movie Match — swipe.js
   Handles: loading movies, drag-to-swipe gestures,
   talking to the backend, and showing match popups.
   ============================================ */

// --- Read session_id and user name out of the URL ---
// e.g. /swipe/a1b2c3d4?user=Alice
// Session codes are always lowercase — normalizing here means it doesn't
// matter how the code was typed, pasted, or displayed.
const sessionId = window.location.pathname.split('/').pop().toLowerCase();
const urlParams = new URLSearchParams(window.location.search);
const userName = urlParams.get('user') || 'Anonymous';

document.getElementById('session-label').textContent =
  `${userName} · session ${sessionId}`;

document.getElementById('matches-link').href =
  `/matches/${sessionId}?user=${encodeURIComponent(userName)}`;

const cardStack = document.getElementById('card-stack');
let currentMovie = null;      // the movie currently on top of the stack
let seenMatchIds = new Set(); // matches we've already shown a popup for

// ---------- Loading movies ----------

async function loadNextMovie() {
  const response = await fetch(
    `/session/${sessionId}/next-movie?user_name=${encodeURIComponent(userName)}`
  );

  if (!response.ok) {
    cardStack.innerHTML = `
      <div class="ticket empty-state" style="position: absolute; inset: 0;">
        <h2>Session not found</h2>
        <p>Double check the session code and try again.</p>
      </div>`;
    return;
  }

  const data = await response.json();

  if (!data.movie) {
    currentMovie = null;
    cardStack.innerHTML = `
      <div class="ticket empty-state" style="position: absolute; inset: 0; display: flex; flex-direction: column; justify-content: center;">
        <h2>That's everything!</h2>
        <p>You've swiped on every movie. Waiting to see if anything matched...</p>
      </div>`;
    return;
  }

  currentMovie = data.movie;
  renderCard(currentMovie);
}

function renderCard(movie) {
  const metaBits = [];
  if (movie.rating) metaBits.push(`★ ${movie.rating}/10`);
  if (movie.genres) metaBits.push(escapeHtml(movie.genres));
  const metaLine = metaBits.length
    ? `<div class="card-meta">${metaBits.join(' · ')}</div>`
    : '';

  // Not every movie has a poster (e.g. demo data) — fall back to a plain
  // gradient block with a film emoji instead of a broken image icon.
  const posterContent = movie.poster_url
    ? `<img src="${escapeHtml(movie.poster_url)}" alt="${escapeHtml(movie.title)} poster" />`
    : `<div class="poster-fallback">🎬</div>`;

  cardStack.innerHTML = `
    <div class="ticket ticket-perforation movie-card" id="active-card">
      <div class="card-poster">
        ${posterContent}
        <div class="service-badge">${escapeHtml(movie.streaming_service)}</div>
        <div class="stamp stamp-like" id="stamp-like">LIKE</div>
        <div class="stamp stamp-nope" id="stamp-nope">NOPE</div>
      </div>
      <div class="card-content">
        <h2>${escapeHtml(movie.title)}</h2>
        ${metaLine}
        <p>${escapeHtml(movie.overview || 'No description available.')}</p>
      </div>
    </div>`;

  attachDragHandlers(document.getElementById('active-card'));
}

// Basic protection against showing weird characters/HTML from movie data as raw markup.
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ---------- Drag-to-swipe ----------

function attachDragHandlers(card) {
  let startX = 0;
  let currentX = 0;
  let dragging = false;

  const stampLike = document.getElementById('stamp-like');
  const stampNope = document.getElementById('stamp-nope');

  function onPointerDown(e) {
    dragging = true;
    startX = e.clientX ?? e.touches[0].clientX;
    card.style.transition = 'none';
  }

  function onPointerMove(e) {
    if (!dragging) return;
    currentX = (e.clientX ?? e.touches[0].clientX) - startX;

    const rotation = currentX / 20; // subtle tilt as you drag
    card.style.transform = `translateX(${currentX}px) rotate(${rotation}deg)`;

    // Fade the LIKE/NOPE stamps in as you drag further
    const opacity = Math.min(Math.abs(currentX) / 100, 1);
    if (currentX > 0) {
      stampLike.style.opacity = opacity;
      stampNope.style.opacity = 0;
    } else {
      stampNope.style.opacity = opacity;
      stampLike.style.opacity = 0;
    }
  }

  function onPointerUp() {
    if (!dragging) return;
    dragging = false;

    const SWIPE_THRESHOLD = 100; // pixels you need to drag before it counts as a swipe

    if (currentX > SWIPE_THRESHOLD) {
      swipeCurrentCard('right');
    } else if (currentX < -SWIPE_THRESHOLD) {
      swipeCurrentCard('left');
    } else {
      // Not dragged far enough — snap back to center
      card.style.transition = 'transform 0.25s ease';
      card.style.transform = 'translateX(0) rotate(0)';
      stampLike.style.opacity = 0;
      stampNope.style.opacity = 0;
    }

    currentX = 0;
  }

  card.addEventListener('pointerdown', onPointerDown);
  card.addEventListener('pointermove', onPointerMove);
  card.addEventListener('pointerup', onPointerUp);
  card.addEventListener('pointerleave', onPointerUp);
}

// ---------- Sending the swipe to the backend ----------

async function swipeCurrentCard(direction) {
  if (!currentMovie) return;

  const card = document.getElementById('active-card');
  const movieToSwipe = currentMovie;
  currentMovie = null; // prevent double-swiping the same card

  // Animate the card flying off screen
  if (card) {
    card.style.transition = 'transform 0.3s ease, opacity 0.3s ease';
    card.style.transform = `translateX(${direction === 'right' ? 600 : -600}px) rotate(${direction === 'right' ? 20 : -20}deg)`;
    card.style.opacity = '0';
  }

  const response = await fetch(`/session/${sessionId}/swipe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_name: userName,
      movie_id: movieToSwipe.id,
      direction: direction,
    }),
  });

  const result = await response.json();

  if (result.match) {
    showMatch(movieToSwipe);
  }

  setTimeout(loadNextMovie, 300);
}

// ---------- Match popup ----------

let matchDismissTimer = null;

function showMatch(movie) {
  document.getElementById('match-movie-title').textContent = movie.title;
  document.getElementById('match-overlay').classList.add('visible');
  seenMatchIds.add(movie.id);

  // Auto-dismiss after a few seconds — no click needed. If another match
  // pops up while this one is showing, restart the timer for the new one.
  clearTimeout(matchDismissTimer);
  matchDismissTimer = setTimeout(dismissMatch, 4000);
}

function dismissMatch() {
  document.getElementById('match-overlay').classList.remove('visible');
  clearTimeout(matchDismissTimer);
}

// ---------- Poll for matches your partner might have triggered ----------
// (in case they swiped right on something after you already passed it)

async function pollForMatches() {
  try {
    const response = await fetch(`/session/${sessionId}/matches`);
    if (!response.ok) return;

    const data = await response.json();
    document.getElementById('matches-count').textContent = data.matches.length;

    for (const match of data.matches) {
      if (!seenMatchIds.has(match.id)) {
        showMatch(match);
        break; // show one at a time
      }
    }
  } catch (err) {
    // Silently ignore — we'll just try again on the next poll
  }
}

// On first load, quietly note any matches that already existed (e.g. you're
// re-opening the app) so we don't pop the "It's a match!" modal for old news.
async function primeSeenMatches() {
  try {
    const response = await fetch(`/session/${sessionId}/matches`);
    if (!response.ok) return;
    const data = await response.json();
    data.matches.forEach(match => seenMatchIds.add(match.id));
    document.getElementById('matches-count').textContent = data.matches.length;
  } catch (err) {
    // If this fails, worst case we show a popup for an old match — not a big deal.
  }
}

// ---------- Kick things off ----------
loadNextMovie();
primeSeenMatches().then(() => {
  setInterval(pollForMatches, 4000);
});
