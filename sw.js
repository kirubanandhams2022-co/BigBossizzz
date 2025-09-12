/**
 * BigBossizzz Root Service Worker
 * Handles caching and offline functionality for the entire application
 */

const CACHE_NAME = 'bigbossizzz-offline-v1';
const STATIC_CACHE = 'bigbossizzz-static-v1';
const DYNAMIC_CACHE = 'bigbossizzz-dynamic-v1';

// Resources to cache for offline use
const STATIC_ASSETS = [
    '/',
    '/static/css/theme-system.css',
    '/static/css/accessibility-features.css',
    '/static/css/mobile-enhancements.css',
    '/static/js/theme-manager.js',
    '/static/js/accessibility-manager.js',
    '/static/js/offline-manager.js',
    '/static/js/mobile-app.js',
    '/static/js/voice-commands.js'
];

// Install event - cache static assets
self.addEventListener('install', event => {
    console.log('🔧 Root Service Worker installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('📦 Caching static assets');
                return cache.addAll(STATIC_ASSETS.filter(url => !url.includes('cdn')));
            })
            .then(() => {
                console.log('✅ Static assets cached successfully');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('❌ Failed to cache static assets:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('🚀 Root Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('🗑️ Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('✅ Root Service Worker activated');
                return self.clients.claim();
            })
    );
});

// Fetch event - handle requests with secure caching strategy
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests and chrome-extension requests
    if (request.method !== 'GET' || url.protocol === 'chrome-extension:') {
        return;
    }
    
    // Skip authenticated API routes and quiz content for security
    if (url.pathname.startsWith('/api/') && 
        !url.pathname.includes('/connectivity-check')) {
        return;
    }
    
    // Handle different types of requests
    if (isStaticAsset(request)) {
        event.respondWith(handleStaticAsset(request));
    } else if (isPublicRoute(request)) {
        event.respondWith(handlePublicRoute(request));
    }
});

// Check if request is for static assets
function isStaticAsset(request) {
    const url = new URL(request.url);
    return url.pathname.startsWith('/static/') && 
           !url.pathname.includes('.js.map') &&
           !url.pathname.includes('.css.map');
}

// Check if request is for public routes
function isPublicRoute(request) {
    const url = new URL(request.url);
    const publicRoutes = ['/', '/login', '/register', '/api/connectivity-check'];
    return publicRoutes.includes(url.pathname);
}

// Handle static assets - Cache First strategy
async function handleStaticAsset(request) {
    try {
        const cache = await caches.open(STATIC_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        if (networkResponse.ok && !networkResponse.redirected) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
        
    } catch (error) {
        console.error('❌ Failed to handle static asset:', error);
        
        // Return cached version if available
        const cache = await caches.open(STATIC_CACHE);
        const cachedResponse = await cache.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return minimal offline response
        return new Response('Offline - Asset not available', {
            status: 503,
            statusText: 'Service Unavailable'
        });
    }
}

// Handle public routes - Network First with limited caching
async function handlePublicRoute(request) {
    try {
        const networkResponse = await fetch(request);
        return networkResponse;
        
    } catch (error) {
        console.error('❌ Network error for public route:', error);
        
        // Only cache non-sensitive public pages
        const url = new URL(request.url);
        if (url.pathname === '/' || url.pathname === '/login') {
            const cache = await caches.open(DYNAMIC_CACHE);
            const cachedResponse = await cache.match(request);
            if (cachedResponse) {
                return cachedResponse;
            }
        }
        
        // Return offline page
        return getOfflinePage();
    }
}

// Generate minimal offline page
function getOfflinePage() {
    const html = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Offline - BigBossizzz</title>
        <style>
            body { font-family: system-ui, sans-serif; margin: 0; padding: 20px; text-align: center; }
            .container { max-width: 400px; margin: 100px auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌐 You're Offline</h1>
            <p>Please check your connection and try again.</p>
            <button onclick="location.reload()">Try Again</button>
        </div>
        <script>
            window.addEventListener('online', () => location.reload());
        </script>
    </body>
    </html>
    `;
    
    return new Response(html, {
        headers: { 'Content-Type': 'text/html' }
    });
}

console.log('🔧 BigBossizzz Root Service Worker loaded');