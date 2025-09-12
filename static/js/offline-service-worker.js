/**
 * BigBossizzz Offline Service Worker
 * Handles caching and offline functionality for quiz platform
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
    '/static/manifest.json',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// Install event - cache static assets
self.addEventListener('install', event => {
    console.log('Service Worker installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('Static assets cached successfully');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('Failed to cache static assets:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker activated');
                return self.clients.claim();
            })
    );
});

// Fetch event - handle requests with caching strategy
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests and chrome-extension requests
    if (request.method !== 'GET' || url.protocol === 'chrome-extension:') {
        return;
    }
    
    // Handle different types of requests
    if (isStaticAsset(request)) {
        event.respondWith(handleStaticAsset(request));
    } else if (isQuizRequest(request)) {
        event.respondWith(handleQuizRequest(request));
    } else if (isAPIRequest(request)) {
        event.respondWith(handleAPIRequest(request));
    } else {
        event.respondWith(handleOtherRequests(request));
    }
});

// Check if request is for static assets
function isStaticAsset(request) {
    const url = new URL(request.url);
    return url.pathname.startsWith('/static/') || 
           url.hostname.includes('cdn.jsdelivr.net') ||
           url.hostname.includes('cdnjs.cloudflare.com');
}

// Check if request is quiz-related
function isQuizRequest(request) {
    const url = new URL(request.url);
    return url.pathname.includes('/quiz/') || 
           url.pathname.includes('/take-quiz/');
}

// Check if request is API call
function isAPIRequest(request) {
    const url = new URL(request.url);
    return url.pathname.startsWith('/api/');
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
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
        
    } catch (error) {
        console.error('? Failed to handle static asset:', error);
        
        // Return cached version if available
        const cache = await caches.open(STATIC_CACHE);
        const cachedResponse = await cache.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline fallback
        return new Response('Offline - Asset not available', {
            status: 503,
            statusText: 'Service Unavailable'
        });
    }
}

// Handle quiz requests - Network First strategy with offline support
async function handleQuizRequest(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache successful quiz responses
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
            return networkResponse;
        }
        
        // If network fails, try cache
        const cache = await caches.open(DYNAMIC_CACHE);
        const cachedResponse = await cache.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline quiz page
        return getOfflineQuizPage();
        
    } catch (error) {
        console.error('? Network error for quiz request:', error);
        
        // Try to serve from cache
        const cache = await caches.open(DYNAMIC_CACHE);
        const cachedResponse = await cache.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline quiz page
        return getOfflineQuizPage();
    }
}

// Handle API requests - special offline handling
async function handleAPIRequest(request) {
    const url = new URL(request.url);
    
    // Connectivity check endpoint
    if (url.pathname === '/api/connectivity-check') {
        return new Response('OK', { status: 200 });
    }
    
    try {
        const networkResponse = await fetch(request);
        return networkResponse;
        
    } catch (error) {
        console.error('? API request failed:', error);
        
        // For quiz-related APIs in offline mode
        if (url.pathname.includes('/quiz/') || url.pathname.includes('/api/quiz/')) {
            return handleOfflineQuizAPI(request);
        }
        
        // Return offline API response
        return new Response(JSON.stringify({
            error: 'Offline - API not available',
            offline: true,
            timestamp: new Date().toISOString()
        }), {
            status: 503,
            statusText: 'Service Unavailable',
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Handle other requests - Cache First with Network Fallback
async function handleOtherRequests(request) {
    try {
        const cache = await caches.open(DYNAMIC_CACHE);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            // Serve from cache and try to update in background
            fetch(request)
                .then(networkResponse => {
                    if (networkResponse.ok) {
                        cache.put(request, networkResponse.clone());
                    }
                })
                .catch(() => {
                    // Network failed, but we already have cached version
                });
            
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
        
    } catch (error) {
        console.error('? Request failed:', error);
        
        // Try cache one more time
        const cache = await caches.open(DYNAMIC_CACHE);
        const cachedResponse = await cache.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page
        return getOfflinePage();
    }
}

// Generate offline quiz page
function getOfflineQuizPage() {
    const html = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Offline Quiz - BigBossizzz</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f8f9fa;
                color: #333;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .offline-icon {
                font-size: 4rem;
                text-align: center;
                margin-bottom: 20px;
                color: #ffc107;
            }
            h1 {
                text-align: center;
                color: #495057;
                margin-bottom: 20px;
            }
            .message {
                text-align: center;
                margin-bottom: 30px;
                line-height: 1.6;
            }
            .btn {
                display: inline-block;
                padding: 12px 24px;
                background: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                margin: 0 10px;
            }
            .btn:hover {
                background: #0056b3;
            }
            .features {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
            }
            .feature {
                margin-bottom: 15px;
                padding: 10px;
                background: #e9ecef;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="offline-icon">?</div>
            <h1>Offline Mode Active</h1>
            <div class="message">
                <p>You're currently offline, but don't worry! BigBossizzz has you covered.</p>
                <p>Your quiz progress is being saved locally and will sync automatically when your connection is restored.</p>
            </div>
            
            <div style="text-align: center;">
                <a href="javascript:location.reload()" class="btn">Try Again</a>
                <a href="/" class="btn">Go Home</a>
            </div>
            
            <div class="features">
                <h3>Offline Features Available:</h3>
                <div class="feature">
                    ? Continue taking your current quiz
                </div>
                <div class="feature">
                    ? All answers are saved locally
                </div>
                <div class="feature">
                    ? Automatic sync when connection returns
                </div>
                <div class="feature">
                    ? Theme and accessibility preferences maintained
                </div>
            </div>
        </div>
        
        <script>
            // Check for connection every 5 seconds
            setInterval(() => {
                if (navigator.onLine) {
                    location.reload();
                }
            }, 5000);
            
            // Listen for online event
            window.addEventListener('online', () => {
                location.reload();
            });
        </script>
    </body>
    </html>
    `;
    
    return new Response(html, {
        headers: { 'Content-Type': 'text/html' }
    });
}

// Generate offline page for other content
function getOfflinePage() {
    const html = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Offline - BigBossizzz</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f8f9fa;
                color: #333;
                text-align: center;
            }
            .container {
                max-width: 600px;
                margin: 100px auto;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .offline-icon {
                font-size: 5rem;
                margin-bottom: 20px;
                color: #ffc107;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="offline-icon">?</div>
            <h1>You're Offline</h1>
            <p>This page isn't available offline. Please check your connection and try again.</p>
            <button onclick="location.reload()" style="padding: 10px 20px; margin-top: 20px;">Try Again</button>
        </div>
        
        <script>
            window.addEventListener('online', () => {
                location.reload();
            });
        </script>
    </body>
    </html>
    `;
    
    return new Response(html, {
        headers: { 'Content-Type': 'text/html' }
    });
}

// Handle offline quiz API requests
function handleOfflineQuizAPI(request) {
    const url = new URL(request.url);
    
    // Quiz sync endpoint
    if (url.pathname === '/api/quiz/sync-progress') {
        return new Response(JSON.stringify({
            success: true,
            message: 'Progress will be synced when online',
            offline: true
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
    }
    
    // Default offline API response
    return new Response(JSON.stringify({
        error: 'API temporarily unavailable offline',
        offline: true,
        retry: true
    }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
    });
}

// Message handling from main thread
self.addEventListener('message', event => {
    const { type, data } = event.data;
    
    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
            
        case 'CACHE_QUIZ_DATA':
            cacheQuizData(data);
            break;
            
        case 'GET_CACHE_INFO':
            getCacheInfo().then(info => {
                event.ports[0].postMessage(info);
            });
            break;
    }
});

// Cache quiz data for offline use
async function cacheQuizData(quizData) {
    try {
        const cache = await caches.open(DYNAMIC_CACHE);
        const response = new Response(JSON.stringify(quizData), {
            headers: { 'Content-Type': 'application/json' }
        });
        
        await cache.put(`/api/quiz/${quizData.id}/offline`, response);
        console.log('[INFO] Quiz data cached for offline use:', quizData.id);
        
    } catch (error) {
        console.error('? Failed to cache quiz data:', error);
    }
}

// Get cache information
async function getCacheInfo() {
    try {
        const cacheNames = await caches.keys();
        const info = {
            caches: cacheNames.length,
            static_assets: 0,
            dynamic_content: 0
        };
        
        for (const cacheName of cacheNames) {
            const cache = await caches.open(cacheName);
            const keys = await cache.keys();
            
            if (cacheName === STATIC_CACHE) {
                info.static_assets = keys.length;
            } else if (cacheName === DYNAMIC_CACHE) {
                info.dynamic_content = keys.length;
            }
        }
        
        return info;
        
    } catch (error) {
        console.error('? Failed to get cache info:', error);
        return { error: 'Failed to get cache info' };
    }
}

console.log('[INFO] BigBossizzz Service Worker loaded');