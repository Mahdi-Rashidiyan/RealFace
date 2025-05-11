// Service Worker for RealFace application
const CACHE_NAME = 'realface-cache-v1';
const urlsToCache = [
    '/',
    '/static/detector/css/style.css',
    '/static/detector/js/main.js',
    '/static/detector/manifest.json',
];

// Install service worker and cache static assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
    );
});

// Activate and clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.filter(cacheName => {
                    return cacheName !== CACHE_NAME;
                }).map(cacheName => {
                    return caches.delete(cacheName);
                })
            );
        })
    );
});

// Intercept fetch requests and serve from cache if possible
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // Return the cached response if available
                if (response) {
                    return response;
                }
                
                // Clone the request to avoid using it twice
                const fetchRequest = event.request.clone();
                
                // Make the network request and cache new responses for non-API calls
                return fetch(fetchRequest).then(response => {
                    // Check if response is valid
                    if (!response || response.status !== 200 || response.type !== 'basic') {
                        return response;
                    }
                    
                    // Check if the URL is an API call
                    if (event.request.url.includes('/analyze/')) {
                        return response;
                    }
                    
                    // Clone the response to avoid using it twice
                    const responseToCache = response.clone();
                    
                    // Add the response to cache
                    caches.open(CACHE_NAME)
                        .then(cache => {
                            cache.put(event.request, responseToCache);
                        });
                        
                    return response;
                });
            })
            .catch(error => {
                console.log('Fetch failed:', error);
                // Show offline page or return cached home page as fallback
                return caches.match('/');
            })
    );
}); 