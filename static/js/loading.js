/**
 * Assessment Platform Loading System
 * Provides professional loading animations and user feedback
 */

class LoadingManager {
    constructor() {
        this.isLoading = false;
        this.overlay = null;
        this.init();
    }

    init() {
        // Create loading overlay element
        this.createOverlay();
        
        // Add event listeners for form submissions
        this.attachFormListeners();
        
        // Add event listeners for AJAX requests
        this.attachAjaxListeners();
    }

    createOverlay() {
        this.overlay = document.createElement('div');
        this.overlay.id = 'loadingOverlay';
        this.overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            z-index: 10000;
            display: none;
            align-items: center;
            justify-content: center;
        `;
        
        this.overlay.innerHTML = `
            <div style="text-align: center; color: #333; max-width: 320px; margin: 0 auto;">
                <div style="margin: 0 auto 2rem; width: 60px; height: 60px;">
                    <div class="professional-spinner" style="
                        width: 60px;
                        height: 60px;
                        border-radius: 50%;
                        border: 3px solid #e5e7eb;
                        border-top: 3px solid #374151;
                        animation: professionalSpin 0.8s linear infinite;
                    "></div>
                </div>
                
                <div style="font-size: 1.1rem; margin-bottom: 0.75rem; color: #374151; font-weight: 500; letter-spacing: 0.025em;">
                    <span class="loading-text">Loading...</span>
                </div>
                
                <div style="width: 200px; height: 2px; background: #e5e7eb; border-radius: 1px; margin: 0 auto; overflow: hidden;">
                    <div style="height: 100%; background: #374151; border-radius: 1px; animation: professionalProgress 1.5s ease-in-out infinite;"></div>
                </div>
            </div>
        `;
        
        // Add CSS animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes professionalSpin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            @keyframes professionalProgress {
                0% { width: 0%; margin-left: 0%; }
                50% { width: 60%; margin-left: 20%; }
                100% { width: 0%; margin-left: 100%; }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(this.overlay);
    }

    show(message = 'Loading...') {
        if (this.isLoading) return;
        
        this.isLoading = true;
        
        // Update message if provided
        const messageElement = this.overlay.querySelector('.loading-text');
        if (messageElement) {
            messageElement.textContent = message;
        }
        
        this.overlay.style.display = 'flex';
        
        // Animate in
        setTimeout(() => {
            this.overlay.style.opacity = '1';
        }, 10);
    }

    hide() {
        if (!this.isLoading) return;
        
        this.isLoading = false;
        
        // Animate out
        this.overlay.style.opacity = '0';
        setTimeout(() => {
            this.overlay.style.display = 'none';
        }, 300);
    }

    attachFormListeners() {
        document.addEventListener('submit', (event) => {
            const form = event.target;
            
            // Only show loading for specific forms that need it
            const needsLoading = form.classList.contains('needs-loading') ||
                               form.hasAttribute('data-loading') ||
                               form.action?.includes('/quiz/') ||
                               form.action?.includes('/create') ||
                               form.action?.includes('/upload');
            
            // Skip if form explicitly doesn't need loading or doesn't need it
            if (form.hasAttribute('data-no-loading') || !needsLoading) {
                return;
            }
            
            // Skip for simple forms like login, search, and navigation
            if (form.classList.contains('search-form') || 
                form.classList.contains('quick-action') ||
                form.classList.contains('simple-form')) {
                return;
            }
            
            if (form.tagName === 'FORM') {
                this.show('Processing...');
            }
        });
    }

    attachAjaxListeners() {
        // Intercept fetch requests only for specific endpoints
        const originalFetch = window.fetch;
        window.fetch = (...args) => {
            const url = args[0];
            
            // Only show loading for data-heavy or complex requests
            const needsLoading = url?.includes('/api/') ||
                               url?.includes('/upload') ||
                               url?.includes('/quiz/') ||
                               url?.includes('/create') ||
                               url?.includes('/generate');
            
            if (needsLoading) {
                this.show('Processing...');
            }
            
            return originalFetch(...args).finally(() => {
                if (needsLoading) {
                    setTimeout(() => this.hide(), 500);
                }
            });
        };

        // Intercept XMLHttpRequest with selective loading
        const originalOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(...args) {
            const method = args[0];
            const url = args[1];
            
            // Only show loading for specific XMLHttpRequests
            const needsLoading = (method === 'POST' || method === 'PUT' || method === 'DELETE') &&
                               (url?.includes('/api/') ||
                                url?.includes('/upload') ||
                                url?.includes('/quiz/') ||
                                url?.includes('/create') ||
                                url?.includes('/generate'));
            
            if (needsLoading) {
                this.addEventListener('loadstart', () => {
                    window.loadingManager?.show('Processing...');
                });
                this.addEventListener('loadend', () => {
                    setTimeout(() => window.loadingManager?.hide(), 500);
                });
            }
            
            return originalOpen.apply(this, args);
        };
    }

    // Utility methods for specific loading scenarios
    showWithRedirect(message, redirectUrl, delay = 2000) {
        this.show(message);
        setTimeout(() => {
            window.location.href = redirectUrl;
        }, delay);
    }

    showForPromise(promise, message = 'Processing...') {
        this.show(message);
        return promise.finally(() => {
            setTimeout(() => this.hide(), 300);
        });
    }
}

// Initialize loading manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.loadingManager = new LoadingManager();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoadingManager;
}

// ===== PROFESSIONAL LOADING ENHANCEMENTS =====
document.addEventListener('DOMContentLoaded', function() {
    // Hide initial loading screen after content loads
    setTimeout(() => {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.classList.add('loading-hidden');
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 500);
        }
    }, 2000);
    
    // Smooth scrolling for better UX
    document.documentElement.style.scrollBehavior = 'smooth';
    
    // Enhanced form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                    field.classList.add('is-valid');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
});