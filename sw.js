const CACHE_NAME = "raintrack-cache-v1";

// These are the URLs we want to save to the device
const ASSETS_TO_CACHE = [
  "/",
  "/chart",
  "/static/index.html",
  "/static/chart.html",
  "/static/entry.js",
  "/static/chart.js",
  "/static/manifest.webmanifest"
];

// 1. Install Event: Save the files to the device
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log("Caching app assets...");
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
});

// 2. Fetch Event: Use saved files if the internet is down
self.addEventListener("fetch", (event) => {
  // Only intercept GET requests
  if (event.request.method !== 'GET') return;

  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});