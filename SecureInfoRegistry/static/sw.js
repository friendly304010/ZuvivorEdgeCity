const CACHE_NAME = 'Zuvivor-v5';
const urlsToCache = [
  '/',
  '/static/css/custom.css',
  '/static/js/main.js',
  'https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
  '/static/icon-192x192.png',
  '/static/icon-512x512.png',
  '/static/offline.html'
];

self.addEventListener('install', (event) => {
  self.skipWaiting(); // Immediate skip waiting
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        if (response) {
          return response;
        }
        return fetch(event.request).then(
          (response) => {
            if (!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }
            const responseToCache = response.clone();
            caches.open(CACHE_NAME)
              .then((cache) => {
                cache.put(event.request, responseToCache);
              });
            return response;
          }
        );
      })
      .catch(() => {
        if (event.request.mode === 'navigate') {
          return caches.match('/static/offline.html');
        }
      })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    Promise.all([
      // Immediate cache clearing
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              return caches.delete(cacheName);
            }
          })
        );
      }),
      // Clear all caches immediately
      caches.delete(CACHE_NAME),
      // Tell clients to reload and take control
      self.clients.claim(),
      self.skipWaiting()
    ])
  );
});

self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
