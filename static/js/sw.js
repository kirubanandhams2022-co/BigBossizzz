/**
 * BigBossizzz Service Worker
 * Provides offline functionality and caching for PWA
 */

const CACHE_NAME = 'bigbossizzz-v1.2.0';
const OFFLINE_URL = '/offline';

// Assets to cache immediately
const STATIC_CACHE_URLS = [
    '/',
    '/offline',
    '/static/css/bootstrap.min.css',
    '/static/css/custom.css', 
    '/static/css/mobile-enhancements.css',
    '/static/js/bootstrap.bundle.min.js',
    '/static/js/mobile-app.js',
    '/static/js/proctoring.js',
    '/static/images/icon-192x192.png',
    '/static/images/icon-512x512.png',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
];

// Assets to cache on first request
const DYNAMIC_CACHE_URLS = [
    '/participant_dashboard',
    '/host_dashboard', 
    '/admin/dashboard',
    '/available_quizzes',
    '/profile',
    '/quiz_results'
];

// Network-first resources (always try network first)
const NETWORK_FIRST_URLS = [
    '/api/',
    '/take_quiz/',
    '/submit_quiz'
];

self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('📦 Caching static assets...');
                return cache.addAll(STATIC_CACHE_URLS);
            })
            .then(() => {
                console.log('✅ Static assets cached successfully');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('❌ Cache installation failed:', error);
            })
    );
});

self.addEventListener('activate', (event) => {
    console.log('🚀 Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME) {
                            console.log('🗑️ Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('✅ Service Worker activated');
                return self.clients.claim();
            })
    );
});

self.addEventListener('fetch', (event) => {
    const requestUrl = new URL(event.request.url);
    
    // Skip cross-origin requests
    if (requestUrl.origin !== location.origin) {
        return;
    }
    
    // Handle different request types
    if (event.request.method === 'GET') {
        if (isNetworkFirst(requestUrl.pathname)) {
            event.respondWith(networkFirst(event.request));
        } else if (isStaticAsset(requestUrl.pathname)) {
            event.respondWith(cacheFirst(event.request));
        } else {
            event.respondWith(staleWhileRevalidate(event.request));
        }
    }
});

// Cache strategies
async function networkFirst(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('🌐 Network failed, trying cache:', request.url);
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page for navigation requests
        if (request.mode === 'navigate') {
            return caches.match(OFFLINE_URL);
        }
        
        throw error;
    }
}

async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('📱 Failed to fetch:', request.url, error);
        throw error;
    }
}

async function staleWhileRevalidate(request) {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    const fetchPromise = fetch(request).then((networkResponse) => {
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    }).catch((error) => {
        console.log('🌐 Network failed for:', request.url);
        return cachedResponse;
    });
    
    return cachedResponse || fetchPromise;
}

// Helper functions
function isNetworkFirst(pathname) {
    return NETWORK_FIRST_URLS.some(url => pathname.startsWith(url));
}

function isStaticAsset(pathname) {
    return pathname.startsWith('/static/') || 
           pathname.endsWith('.css') || 
           pathname.endsWith('.js') || 
           pathname.endsWith('.png') || 
           pathname.endsWith('.jpg') || 
           pathname.endsWith('.svg');
}

// Background sync for offline quiz submissions
self.addEventListener('sync', (event) => {
    if (event.tag === 'quiz-submission') {
        event.waitUntil(syncQuizSubmissions());
    }
});

async function syncQuizSubmissions() {
    try {
        const cache = await caches.open('quiz-submissions');
        const requests = await cache.keys();
        
        for (const request of requests) {
            try {
                const response = await fetch(request);
                if (response.ok) {
                    await cache.delete(request);
                    console.log('✅ Quiz submission synced:', request.url);
                }
            } catch (error) {
                console.log('❌ Failed to sync quiz submission:', error);
            }
        }
    } catch (error) {
        console.error('❌ Background sync failed:', error);
    }
}

// Push notifications
self.addEventListener('push', (event) => {
    if (!event.data) return;
    
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/images/icon-192x192.png',
        badge: '/static/images/icon-72x72.png',
        data: data.url,
        actions: [
            {
                action: 'open',
                title: 'Open',
                icon: '/static/images/icon-72x72.png'
            },
            {
                action: 'close',
                title: 'Close'
            }
        ],
        requireInteraction: true,
        renotify: true,
        tag: data.tag || 'bigbossizzz-notification'
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'open' || !event.action) {
        const urlToOpen = event.notification.data || '/';
        
        event.waitUntil(
            clients.matchAll({ type: 'window' }).then((clientsArr) => {
                const hadWindowToFocus = clientsArr.some((windowClient) => {
                    if (windowClient.url === urlToOpen) {
                        windowClient.focus();
                        return true;
                    }
                    return false;
                });
                
                if (!hadWindowToFocus) {
                    clients.openWindow(urlToOpen);
                }
            })
        );
    }
});

// Share target handling
self.addEventListener('fetch', (event) => {
    if (event.request.method === 'POST' && event.request.url.endsWith('/share-target')) {
        event.respondWith(handleShareTarget(event.request));
    }
});

async function handleShareTarget(request) {
    const formData = await request.formData();
    const title = formData.get('title') || '';
    const text = formData.get('text') || '';
    const url = formData.get('url') || '';
    
    // Store shared content for the app to process
    const shareData = { title, text, url, timestamp: Date.now() };
    
    const cache = await caches.open('shared-content');
    await cache.put('/shared-content', new Response(JSON.stringify(shareData)));
    
    return Response.redirect('/?shared=1', 303);
}

// Periodic background sync
self.addEventListener('periodicsync', (event) => {
    if (event.tag === 'quiz-data-sync') {
        event.waitUntil(syncQuizData());
    }
});

async function syncQuizData() {
    try {
        // Sync quiz data, results, and user progress
        console.log('🔄 Syncing quiz data...');
        
        const response = await fetch('/api/sync-quiz-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            console.log('✅ Quiz data synced successfully');
        }
    } catch (error) {
        console.error('❌ Quiz data sync failed:', error);
    }
}

// Error handling
self.addEventListener('error', (event) => {
    console.error('❌ Service Worker error:', event.error);
});

self.addEventListener('unhandledrejection', (event) => {
    console.error('❌ Service Worker unhandled rejection:', event.reason);
});

console.log('🚀 BigBossizzz Service Worker loaded successfully');