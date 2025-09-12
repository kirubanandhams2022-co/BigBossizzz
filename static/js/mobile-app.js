/**
 * BigBossizzz Mobile App Enhancements
 * Progressive Web App functionality with mobile-specific features
 */

class MobileAppManager {
    constructor() {
        this.isStandalone = window.matchMedia('(display-mode: standalone)').matches;
        this.isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
        this.isAndroid = /Android/.test(navigator.userAgent);
        this.isMobile = this.isIOS || this.isAndroid || window.innerWidth <= 768;
        
        // PWA Installation
        this.deferredPrompt = null;
        this.installPromptShown = false;
        
        // Mobile Navigation
        this.bottomNavActive = false;
        this.lastScrollPosition = 0;
        this.scrollDirection = 'up';
        
        // Touch Interactions
        this.touchStartY = 0;
        this.touchStartX = 0;
        this.pullToRefreshThreshold = 80;
        this.isRefreshing = false;
        
        // Mobile Performance
        this.isVisible = true;
        this.performanceObserver = null;
        
        // Notification Management
        this.notificationPermission = 'default';
        this.activeToasts = [];
        
        this.init();
    }
    
    async init() {
        console.log('[INFO] Initializing Mobile App Manager...');
        
        if (!this.isMobile && !this.isStandalone) {
            console.log('[INFO] Not on mobile device, skipping mobile enhancements');
            return;
        }
        
        try {
            await this.setupPWA();
            this.setupMobileNavigation();
            this.setupTouchInteractions();
            this.setupPerformanceOptimizations();
            this.setupNotifications();
            this.setupOfflineSupport();
            this.applyMobileStyles();
            this.initializeUIComponents();
            
            console.log('[INFO] Mobile App Manager initialized successfully');
        } catch (error) {
            console.error('[ERROR] Mobile App Manager initialization failed:', error);
        }
    }
    
    // ===== PWA Installation & Management =====
    async setupPWA() {
        // Check if PWA is already installed
        if (this.isStandalone) {
            console.log('[INFO] Running as installed PWA');
            document.body.classList.add('pwa-installed');
            this.hidePWAPrompt();
            return;
        }
        
        // Listen for beforeinstallprompt event
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('[INFO] PWA install prompt available');
            e.preventDefault();
            this.deferredPrompt = e;
            this.showPWAPrompt();
        });
        
        // Listen for app installed event
        window.addEventListener('appinstalled', () => {
            console.log('[INFO] PWA installed successfully');
            this.hidePWAPrompt();
            this.showToast('App installed successfully!', 'success');
        });
        
        // Register service worker
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/static/js/sw.js');
                console.log('[INFO] Service Worker registered:', registration);
                
                // Listen for updates
                registration.addEventListener('updatefound', () => {
                    console.log('[INFO] New version available');
                    this.showUpdatePrompt();
                });
            } catch (error) {
                console.error('[ERROR] Service Worker registration failed:', error);
            }
        }
    }
    
    showPWAPrompt() {
        if (this.installPromptShown) return;
        
        const promptHTML = `
            <div class="pwa-install-prompt" id="pwaPrompt">
                <div class="pwa-prompt-content">
                    <div class="pwa-prompt-icon">
                        <i class="fas fa-mobile-alt"></i>
                    </div>
                    <div class="pwa-prompt-text">
                        <h4>Install BigBossizzz</h4>
                        <p>Install our app for the best mobile experience with offline support and push notifications.</p>
                    </div>
                    <div class="pwa-prompt-actions">
                        <button class="btn btn-outline-secondary btn-sm" onclick="mobileApp.dismissPWAPrompt()">
                            Not now
                        </button>
                        <button class="btn btn-primary btn-sm" onclick="mobileApp.installPWA()">
                            Install
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', promptHTML);
        this.installPromptShown = true;
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            this.dismissPWAPrompt();
        }, 10000);
    }
    
    async installPWA() {
        if (!this.deferredPrompt) return;
        
        try {
            const result = await this.deferredPrompt.prompt();
            console.log('PWA install result:', result);
            
            if (result.outcome === 'accepted') {
                this.showToast('Installing app...', 'info');
            }
            
            this.deferredPrompt = null;
            this.hidePWAPrompt();
        } catch (error) {
            console.error('PWA installation error:', error);
        }
    }
    
    dismissPWAPrompt() {
        this.hidePWAPrompt();
        localStorage.setItem('pwa-prompt-dismissed', Date.now().toString());
    }
    
    hidePWAPrompt() {
        const prompt = document.getElementById('pwaPrompt');
        if (prompt) {
            prompt.remove();
        }
    }
    
    // ===== Mobile Navigation =====
    setupMobileNavigation() {
        // Create bottom navigation
        this.createBottomNavigation();
        
        // Handle scroll behavior
        this.setupScrollBehavior();
        
        // Setup mobile menu toggle
        this.setupMobileMenu();
        
        // Handle orientation changes
        this.setupOrientationHandling();
    }
    
    createBottomNavigation() {
        const currentUser = window.currentUser || {};
        const userRole = currentUser.role || 'participant';
        
        let navItems = [];
        
        if (userRole === 'admin') {
            navItems = [
                { icon: 'fas fa-tachometer-alt', label: 'Dashboard', href: '/admin/dashboard' },
                { icon: 'fas fa-users', label: 'Users', href: '/admin/users' },
                { icon: 'fas fa-clipboard-list', label: 'Quizzes', href: '/admin/quizzes' },
                { icon: 'fas fa-chart-bar', label: 'Reports', href: '/admin/proctoring-reports' },
                { icon: 'fas fa-cog', label: 'Settings', href: '/admin/settings' }
            ];
        } else if (userRole === 'host') {
            navItems = [
                { icon: 'fas fa-home', label: 'Dashboard', href: '/host_dashboard' },
                { icon: 'fas fa-book', label: 'Courses', href: '/host/courses' },
                { icon: 'fas fa-plus-circle', label: 'Create', href: '/create_quiz' },
                { icon: 'fas fa-chart-line', label: 'Analytics', href: '/host/analytics' },
                { icon: 'fas fa-user', label: 'Profile', href: '/profile' }
            ];
        } else {
            navItems = [
                { icon: 'fas fa-home', label: 'Dashboard', href: '/participant_dashboard' },
                { icon: 'fas fa-play-circle', label: 'Quizzes', href: '/available_quizzes' },
                { icon: 'fas fa-trophy', label: 'Results', href: '/quiz_results' },
                { icon: 'fas fa-graduation-cap', label: 'Courses', href: '/enrolled_courses' },
                { icon: 'fas fa-user', label: 'Profile', href: '/profile' }
            ];
        }
        
        const bottomNavHTML = `
            <nav class="mobile-bottom-nav" id="mobileBottomNav">
                ${navItems.map((item, index) => `
                    <a href="${item.href}" class="mobile-nav-item ${index === 0 ? 'active' : ''}" data-page="${item.href}">
                        <i class="${item.icon}"></i>
                        <span>${item.label}</span>
                        ${item.badge ? `<span class="badge">${item.badge}</span>` : ''}
                    </a>
                `).join('')}
            </nav>
        `;
        
        document.body.insertAdjacentHTML('beforeend', bottomNavHTML);
        document.body.classList.add('mobile-nav-enabled');
        
        // Add navigation click handlers
        this.setupBottomNavClickHandlers();
    }
    
    setupBottomNavClickHandlers() {
        const navItems = document.querySelectorAll('.mobile-nav-item');
        
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                // Update active state
                navItems.forEach(nav => nav.classList.remove('active'));
                item.classList.add('active');
                
                // Add click animation
                item.style.transform = 'scale(0.9)';
                setTimeout(() => {
                    item.style.transform = '';
                }, 150);
            });
        });
    }
    
    setupScrollBehavior() {
        let ticking = false;
        
        const updateNavigation = () => {
            const currentScroll = window.pageYOffset;
            const bottomNav = document.getElementById('mobileBottomNav');
            
            if (!bottomNav) return;
            
            // Determine scroll direction
            if (currentScroll > this.lastScrollPosition && currentScroll > 100) {
                // Scrolling down - hide navigation
                bottomNav.style.transform = 'translateY(100%)';
                this.scrollDirection = 'down';
            } else {
                // Scrolling up - show navigation
                bottomNav.style.transform = 'translateY(0)';
                this.scrollDirection = 'up';
            }
            
            this.lastScrollPosition = currentScroll;
            ticking = false;
        };
        
        const requestTick = () => {
            if (!ticking) {
                requestAnimationFrame(updateNavigation);
                ticking = true;
            }
        };
        
        window.addEventListener('scroll', requestTick, { passive: true });
    }
    
    setupMobileMenu() {
        const navbar = document.querySelector('.navbar');
        const navbarToggler = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');
        
        if (navbarToggler && navbarCollapse) {
            navbarToggler.addEventListener('click', () => {
                const isExpanded = navbarToggler.getAttribute('aria-expanded') === 'true';
                
                if (!isExpanded) {
                    // Opening menu
                    navbarCollapse.style.animation = 'slideInDown 0.3s ease';
                } else {
                    // Closing menu
                    navbarCollapse.style.animation = 'slideInUp 0.3s ease reverse';
                }
            });
        }
    }
    
    setupOrientationHandling() {
        const handleOrientationChange = () => {
            // Delay to allow for orientation change to complete
            setTimeout(() => {
                // Update viewport height for iOS
                if (this.isIOS) {
                    const vh = window.innerHeight * 0.01;
                    document.documentElement.style.setProperty('--vh', `${vh}px`);
                }
                
                // Refresh layout-dependent components
                this.refreshMobileLayout();
            }, 300);
        };
        
        window.addEventListener('orientationchange', handleOrientationChange);
        window.addEventListener('resize', handleOrientationChange);
        
        // Initial setup
        handleOrientationChange();
    }
    
    refreshMobileLayout() {
        // Trigger layout recalculation for mobile components
        const mobileComponents = document.querySelectorAll('.mobile-card, .quiz-container, .mobile-proctoring-panel');
        
        mobileComponents.forEach(component => {
            component.style.display = 'none';
            component.offsetHeight; // Force reflow
            component.style.display = '';
        });
    }
    
    // ===== Touch Interactions =====
    setupTouchInteractions() {
        this.setupPullToRefresh();
        this.setupSwipeGestures();
        this.setupTouchFeedback();
    }
    
    setupPullToRefresh() {
        let startY = 0;
        let pullDistance = 0;
        let isPulling = false;
        let refreshElement = null;
        
        // Create pull to refresh element
        const refreshHTML = `
            <div class="mobile-pull-refresh" id="pullToRefresh">
                <i class="fas fa-sync-alt refresh-icon"></i>
                <span class="refresh-text">Pull to refresh</span>
            </div>
        `;
        
        document.body.insertAdjacentHTML('afterbegin', refreshHTML);
        refreshElement = document.getElementById('pullToRefresh');
        
        const handleTouchStart = (e) => {
            if (window.pageYOffset === 0) {
                startY = e.touches[0].clientY;
                isPulling = true;
            }
        };
        
        const handleTouchMove = (e) => {
            if (!isPulling) return;
            
            const currentY = e.touches[0].clientY;
            pullDistance = Math.max(0, currentY - startY);
            
            if (pullDistance > 0) {
                e.preventDefault();
                
                // Update refresh element
                const progress = Math.min(pullDistance / this.pullToRefreshThreshold, 1);
                refreshElement.style.transform = `translateY(${pullDistance * 0.5}px)`;
                refreshElement.style.opacity = progress;
                
                if (pullDistance >= this.pullToRefreshThreshold) {
                    refreshElement.classList.add('active');
                    refreshElement.querySelector('.refresh-text').textContent = 'Release to refresh';
                } else {
                    refreshElement.classList.remove('active');
                    refreshElement.querySelector('.refresh-text').textContent = 'Pull to refresh';
                }
            }
        };
        
        const handleTouchEnd = () => {
            if (!isPulling) return;
            
            isPulling = false;
            
            if (pullDistance >= this.pullToRefreshThreshold && !this.isRefreshing) {
                this.triggerRefresh();
            } else {
                // Reset refresh element
                refreshElement.style.transform = '';
                refreshElement.style.opacity = '';
                refreshElement.classList.remove('active');
            }
            
            pullDistance = 0;
        };
        
        document.addEventListener('touchstart', handleTouchStart, { passive: false });
        document.addEventListener('touchmove', handleTouchMove, { passive: false });
        document.addEventListener('touchend', handleTouchEnd, { passive: true });
    }
    
    async triggerRefresh() {
        if (this.isRefreshing) return;
        
        this.isRefreshing = true;
        const refreshElement = document.getElementById('pullToRefresh');
        
        if (refreshElement) {
            refreshElement.classList.add('active');
            refreshElement.querySelector('.refresh-icon').style.animation = 'spin 1s linear infinite';
            refreshElement.querySelector('.refresh-text').textContent = 'Refreshing...';
        }
        
        try {
            // Refresh current page data
            await this.refreshPageData();
            
            // Show success feedback
            this.showToast('Page refreshed successfully!', 'success');
        } catch (error) {
            console.error('Refresh failed:', error);
            this.showToast('Failed to refresh page', 'error');
        } finally {
            // Reset refresh state
            setTimeout(() => {
                if (refreshElement) {
                    refreshElement.style.transform = '';
                    refreshElement.style.opacity = '';
                    refreshElement.classList.remove('active');
                    refreshElement.querySelector('.refresh-icon').style.animation = '';
                    refreshElement.querySelector('.refresh-text').textContent = 'Pull to refresh';
                }
                this.isRefreshing = false;
            }, 1000);
        }
    }
    
    async refreshPageData() {
        // Simulate data refresh
        return new Promise(resolve => {
            setTimeout(() => {
                // Reload current page
                window.location.reload();
                resolve();
            }, 1500);
        });
    }
    
    setupSwipeGestures() {
        let startX = 0;
        let startY = 0;
        let threshold = 100;
        
        const handleSwipeStart = (e) => {
            startX = e.touches[0].clientX;
            startY = e.touches[0].clientY;
        };
        
        const handleSwipeEnd = (e) => {
            const endX = e.changedTouches[0].clientX;
            const endY = e.changedTouches[0].clientY;
            
            const deltaX = endX - startX;
            const deltaY = endY - startY;
            
            // Check if it's a horizontal swipe
            if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > threshold) {
                if (deltaX > 0) {
                    // Swipe right
                    this.handleSwipeRight();
                } else {
                    // Swipe left
                    this.handleSwipeLeft();
                }
            }
        };
        
        document.addEventListener('touchstart', handleSwipeStart, { passive: true });
        document.addEventListener('touchend', handleSwipeEnd, { passive: true });
    }
    
    handleSwipeRight() {
        // Navigate back if possible
        if (window.history.length > 1) {
            window.history.back();
        }
    }
    
    handleSwipeLeft() {
        // Could be used for next page navigation or menu toggle
        console.log('Swipe left detected');
    }
    
    setupTouchFeedback() {
        // Add haptic feedback for supported devices
        const addHapticFeedback = (element, intensity = 'light') => {
            element.addEventListener('touchstart', () => {
                if (navigator.vibrate) {
                    const vibrationPattern = {
                        light: [10],
                        medium: [50],
                        heavy: [100]
                    };
                    navigator.vibrate(vibrationPattern[intensity] || vibrationPattern.light);
                }
            });
        };
        
        // Add feedback to buttons and interactive elements
        const interactiveElements = document.querySelectorAll('button, .btn, .card, .nav-link, .mobile-nav-item');
        interactiveElements.forEach(element => {
            addHapticFeedback(element);
        });
    }
    
    // ===== Mobile Notifications & Toasts =====
    setupNotifications() {
        this.requestNotificationPermission();
    }
    
    async requestNotificationPermission() {
        if (!('Notification' in window)) {
            console.log('This browser does not support notifications');
            return;
        }
        
        if (Notification.permission === 'default') {
            const permission = await Notification.requestPermission();
            this.notificationPermission = permission;
            
            if (permission === 'granted') {
                this.showToast('Notifications enabled!', 'success');
            }
        } else {
            this.notificationPermission = Notification.permission;
        }
    }
    
    showToast(message, type = 'info', duration = 4000) {
        const toastId = 'toast-' + Date.now();
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        const toastHTML = `
            <div class="mobile-toast ${type}" id="${toastId}">
                <div class="toast-header">
                    <i class="${icons[type] || icons.info}"></i>
                    <span class="toast-title">${type.charAt(0).toUpperCase() + type.slice(1)}</span>
                    <button class="toast-close" onclick="mobileApp.hideToast('${toastId}')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="toast-body">${message}</div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', toastHTML);
        
        const toast = document.getElementById(toastId);
        this.activeToasts.push(toastId);
        
        // Show toast
        setTimeout(() => {
            toast.classList.add('show');
        }, 100);
        
        // Auto-hide toast
        setTimeout(() => {
            this.hideToast(toastId);
        }, duration);
    }
    
    hideToast(toastId) {
        const toast = document.getElementById(toastId);
        if (toast) {
            toast.classList.remove('show');
            setTimeout(() => {
                toast.remove();
                this.activeToasts = this.activeToasts.filter(id => id !== toastId);
            }, 300);
        }
    }
    
    // ===== Performance Optimizations =====
    setupPerformanceOptimizations() {
        this.setupVisibilityAPI();
        this.setupIntersectionObserver();
        this.setupImageOptimization();
    }
    
    setupVisibilityAPI() {
        document.addEventListener('visibilitychange', () => {
            this.isVisible = !document.hidden;
            
            if (this.isVisible) {
                // Resume animations and updates
                console.log('App became visible - resuming operations');
            } else {
                // Pause non-essential operations
                console.log('App hidden - pausing operations');
            }
        });
    }
    
    setupIntersectionObserver() {
        if (!('IntersectionObserver' in window)) return;
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('mobile-content-loaded');
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '50px'
        });
        
        // Observe content elements
        const contentElements = document.querySelectorAll('.mobile-content, .card, .question-card');
        contentElements.forEach(element => {
            observer.observe(element);
        });
    }
    
    setupImageOptimization() {
        // Lazy load images
        const images = document.querySelectorAll('img[data-src]');
        
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            images.forEach(img => imageObserver.observe(img));
        } else {
            // Fallback for older browsers
            images.forEach(img => {
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
            });
        }
    }
    
    // ===== Offline Support =====
    setupOfflineSupport() {
        window.addEventListener('online', () => {
            this.showToast('Connection restored!', 'success');
            document.body.classList.remove('offline');
        });
        
        window.addEventListener('offline', () => {
            this.showToast('You are now offline', 'warning');
            document.body.classList.add('offline');
        });
        
        // Check initial connection state
        if (!navigator.onLine) {
            document.body.classList.add('offline');
        }
    }
    
    // ===== UI Component Initialization =====
    applyMobileStyles() {
        // Add mobile-specific CSS classes
        document.body.classList.add('mobile-enhanced');
        
        if (this.isIOS) {
            document.body.classList.add('ios-device');
        }
        
        if (this.isAndroid) {
            document.body.classList.add('android-device');
        }
        
        if (this.isStandalone) {
            document.body.classList.add('pwa-standalone');
        }
    }
    
    initializeUIComponents() {
        // Initialize mobile-specific UI components
        this.setupFloatingActionButton();
        this.setupCardStackInterface();
        this.enhanceFormInputs();
    }
    
    setupFloatingActionButton() {
        const currentPage = window.location.pathname;
        let fabAction = null;
        
        // Define FAB action based on current page
        if (currentPage.includes('quiz') || currentPage.includes('take_quiz')) {
            fabAction = {
                icon: 'fas fa-save',
                action: () => this.saveQuizProgress(),
                title: 'Save Progress'
            };
        } else if (currentPage.includes('dashboard')) {
            fabAction = {
                icon: 'fas fa-plus',
                action: () => window.location.href = '/create_quiz',
                title: 'Create Quiz'
            };
        }
        
        if (fabAction) {
            const fabHTML = `
                <button class="mobile-fab" title="${fabAction.title}" onclick="mobileApp.triggerFabAction()">
                    <i class="${fabAction.icon}"></i>
                </button>
            `;
            
            document.body.insertAdjacentHTML('beforeend', fabHTML);
            this.fabAction = fabAction.action;
        }
    }
    
    triggerFabAction() {
        if (this.fabAction) {
            this.fabAction();
        }
    }
    
    saveQuizProgress() {
        // Trigger quiz auto-save
        if (window.quizSystem && window.quizSystem.autoSave) {
            window.quizSystem.autoSave();
            this.showToast('Quiz progress saved!', 'success');
        }
    }
    
    setupCardStackInterface() {
        const cards = document.querySelectorAll('.question-card');
        
        if (cards.length > 1) {
            cards.forEach((card, index) => {
                card.classList.add('mobile-card');
                
                if (index === 0) {
                    card.classList.add('current');
                } else if (index === 1) {
                    card.classList.add('next');
                } else {
                    card.classList.add('hidden');
                }
            });
        }
    }
    
    enhanceFormInputs() {
        // Enhance form inputs for mobile
        const inputs = document.querySelectorAll('input, textarea, select');
        
        inputs.forEach(input => {
            input.classList.add('mobile-focus');
            
            // Add input labels animation
            const label = input.previousElementSibling;
            if (label && label.tagName === 'LABEL') {
                input.addEventListener('focus', () => {
                    label.style.transform = 'translateY(-20px) scale(0.8)';
                    label.style.color = 'var(--mobile-accent)';
                });
                
                input.addEventListener('blur', () => {
                    if (!input.value) {
                        label.style.transform = '';
                        label.style.color = '';
                    }
                });
            }
        });
    }
    
    // ===== Utility Methods =====
    showUpdatePrompt() {
        const updateHTML = `
            <div class="mobile-toast info" id="updateToast">
                <div class="toast-header">
                    <i class="fas fa-download"></i>
                    <span class="toast-title">Update Available</span>
                    <button class="toast-close" onclick="mobileApp.hideToast('updateToast')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="toast-body">
                    A new version is available. Refresh to update.
                    <button class="btn btn-sm btn-primary mt-2" onclick="window.location.reload()">
                        Update Now
                    </button>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', updateHTML);
        
        setTimeout(() => {
            document.getElementById('updateToast').classList.add('show');
        }, 100);
    }
}

// Initialize Mobile App Manager
let mobileApp;

document.addEventListener('DOMContentLoaded', () => {
    mobileApp = new MobileAppManager();
});

// Export for global access
window.mobileApp = mobileApp;