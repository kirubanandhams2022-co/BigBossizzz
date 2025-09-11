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
            <div style="text-align: center; color: #333;">
                <div style="position: relative; margin: 0 auto 2rem; width: 80px; height: 80px;">
                    <div class="professional-spinner" style="
                        position: relative;
                        width: 80px;
                        height: 80px;
                        border-radius: 50%;
                        border: 4px solid #f0f0f0;
                        border-top: 4px solid #4f46e5;
                        animation: professionalSpin 1s linear infinite;
                    "></div>
                    <div style="
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        width: 24px;
                        height: 24px;
                        background: #4f46e5;
                        border-radius: 50%;
                        opacity: 0.8;
                    "></div>
                </div>
                
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem; color: #1f2937; font-weight: 600;">
                    Assessment Platform
                </div>
                
                <div style="font-size: 0.9rem; color: #6b7280; margin-bottom: 1.5rem;">
                    <span class="loading-text">Loading your workspace...</span>
                </div>
                
                <div style="width: 240px; height: 4px; background: rgba(103, 102, 241, 0.2); border-radius: 3px; margin: 0 auto; overflow: hidden;">
                    <div style="height: 100%; background: linear-gradient(90deg, #6366f1, #8b5cf6, #a855f7); border-radius: 3px; animation: techProgress 2.5s ease-in-out infinite;"></div>
                </div>
            </div>
        `;
        
        // Add CSS animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes techEyePulse {
                0%, 100% { 
                    transform: scale(1);
                    box-shadow: 0 0 30px rgba(103, 102, 241, 0.8);
                }
                50% { 
                    transform: scale(1.05);
                    box-shadow: 0 0 40px rgba(103, 102, 241, 1);
                }
            }
            
            @keyframes techEyeRotate {
                0% { transform: rotate(0deg) scale(1.1); }
                100% { transform: rotate(360deg) scale(1.1); }
            }
            
            @keyframes techEyeScan {
                0%, 100% { transform: translateX(-100%); }
                50% { transform: translateX(100%); }
            }
            
            @keyframes loadingFade {
                0%, 100% { opacity: 0.8; }
                50% { opacity: 1; }
            }
            
            @keyframes techTypeWriter {
                0%, 100% { opacity: 0.7; }
                50% { opacity: 1; }
            }
            
            @keyframes techProgress {
                0% { width: 0%; margin-left: 0%; }
                50% { width: 70%; margin-left: 15%; }
                100% { width: 0%; margin-left: 100%; }
            }
        `;
        document.head.appendChild(style);
        
        document.body.appendChild(this.overlay);
    }

    show(message = 'Processing your request...') {
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
                this.show('Processing your request...');
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
                this.show('Loading data...');
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
                    window.loadingManager?.show('Loading data...');
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

    showForPromise(promise, message = 'Loading...') {
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

// ===== ENHANCED LOADING SCREEN FOR LIGHT THEME =====
document.addEventListener('DOMContentLoaded', function() {
    // Add light theme class to body
    document.body.classList.add('light-theme');
    
    // Enhanced typing animation for loading screen
    const typedTextElement = document.querySelector('.typed-text');
    if (typedTextElement) {
        const texts = [
            '🔍 Scanning participant identity...',
            '🛡️ Initializing security protocols...',
            '📡 Activating monitoring systems...',
            '🤖 AI surveillance online...',
            '🔬 Technology integration active...',
            '🎯 Advanced recognition system ready...',
            '⚡ Neural network analyzing...',
            '✅ Tech-Eye monitoring engaged!'
        ];
        
        let textIndex = 0;
        let charIndex = 0;
        
        function typeText() {
            if (charIndex < texts[textIndex].length) {
                typedTextElement.textContent += texts[textIndex].charAt(charIndex);
                charIndex++;
                setTimeout(typeText, 50);
            } else {
                setTimeout(() => {
                    typedTextElement.textContent = '';
                    charIndex = 0;
                    textIndex = (textIndex + 1) % texts.length;
                    typeText();
                }, 1000);
            }
        }
        
        typeText();
    }
    
    // Hide initial loading screen after content loads
    setTimeout(() => {
        const loadingScreen = document.getElementById('loading-screen');
        if (loadingScreen) {
            loadingScreen.classList.add('loading-hidden');
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 500);
        }
    }, 3000);
    
    // Enhanced UI interactions
    document.documentElement.style.scrollBehavior = 'smooth';
    
    // Enhanced form validation and feedback
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