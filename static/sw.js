/**
 * sw.js — Service Worker
 *
 * Caches only the static "app shell" (CSS, JS, icons) so the app loads
 * instantly and works offline for its visual shell. Everything else
 * (session data, swipes, matches) always goes straight to the network —
 * this app's whole point is live shared data between two people, so
 * caching that would show stale/wrong information.
 *
 * IMPORTANT: whenever style.css or swipe.js change and you bump their
 * ?v= cache-busting number elsewhere, update SHELL_ASSETS below to match,
 * AND bump CACHE_NAME — otherwise this service worker will keep serving
 * an old cached version of those files even after you update them.
 */

const CACHE_NAME = "movie-match-shell-v1";

const SHELL_ASSETS = [
  "/static/style.css?v=4",
  "/static/swipe.js?v=4",
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  // Clean up old cache versions from previous deployments
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const isShellAsset = SHELL_ASSETS.some((asset) => event.request.url.endsWith(asset));

  if (isShellAsset) {
    // Cache-first for the shell — fast loading, works offline
    event.respondWith(
      caches.match(event.request).then((cached) => cached || fetch(event.request))
    );
  }
  // Everything else (HTML pages, /session/*, /matches/* API calls) is left
  // completely alone — the browser handles it as a normal network request.
});
