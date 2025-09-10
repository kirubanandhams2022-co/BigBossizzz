/**
 * BigBossizzz Loading System
 * Provides smooth loading animations with eye-based theme
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
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            z-index: 10000;
            display: none;
            align-items: center;
            justify-content: center;
        `;
        
        this.overlay.innerHTML = `
            <div style="text-align: center; color: #fff;">
                <div style="position: relative; margin: 0 auto 2rem; width: 80px; height: 80px;">
                    <div class="loading-eye" style="
                        position: absolute;
                        width: 80px;
                        height: 40px;
                        background: linear-gradient(45deg, #007bff, #0056b3);
                        border-radius: 40px 40px 0 0;
                        animation: loadingEyeBlink 1.5s ease-in-out infinite;
                        box-shadow: 0 0 20px rgba(0, 123, 255, 0.5);
                    ">
                        <div style="
                            position: absolute;
                            top: 50%;
                            left: 50%;
                            transform: translate(-50%, -50%);
                            width: 16px;
                            height: 16px;
                            background: #fff;
                            border-radius: 50%;
                        ">
                            <div style="
                                position: absolute;
                                top: 60%;
                                left: 55%;
                                transform: translate(-50%, -50%);
                                width: 6px;
                                height: 6px;
                                background: #333;
                                border-radius: 50%;
                            "></div>
                        </div>
                    </div>
                    <div style="
                        position: absolute;
                        top: 0;
                        left: 0;
                        width: 80px;
                        height: 40px;
                        background: linear-gradient(135deg, #1a1a1a, #2d2d2d);
                        border-radius: 40px 40px 0 0;
                        animation: loadingLidBlink 1.5s ease-in-out infinite;
                        z-index: 2;
                    "></div>
                </div>
                
                <div style="font-size: 1.2rem; margin-bottom: 1rem; animation: loadingFade 1.5s ease-in-out infinite;">
                    <i class="fas fa-eye"></i> BigBossizzz
                </div>
                
                <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 1.5rem;">
                    Processing your request...
                </div>
                
                <div style="width: 200px; height: 3px; background: rgba(255, 255, 255, 0.1); border-radius: 2px; margin: 0 auto; overflow: hidden;">
                    <div style="height: 100%; background: linear-gradient(90deg, #007bff, #0056b3); border-radius: 2px; animation: loadingProgress 1.5s ease-in-out infinite;"></div>
                </div>
            </div>
        `;
        
        // Add CSS animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes loadingEyeBlink {
                0%, 85%, 100% { transform: scaleY(1); }
                90% { transform: scaleY(0.1); }
            }
            
            @keyframes loadingLidBlink {
                0%, 85%, 100% { transform: scaleY(0.3); }
                90% { transform: scaleY(1); }
            }
            
            @keyframes loadingFade {
                0%, 100% { opacity: 0.7; }
                50% { opacity: 1; }
            }
            
            @keyframes loadingProgress {
                0% { width: 0%; margin-left: 0%; }
                50% { width: 60%; margin-left: 20%; }
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
        const messageElement = this.overlay.querySelector('div[style*="color: #6c757d"]');
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
            if (form.tagName === 'FORM' && !form.hasAttribute('data-no-loading')) {
                this.show('Submitting form...');
            }
        });
    }

    attachAjaxListeners() {
        // Intercept fetch requests
        const originalFetch = window.fetch;
        window.fetch = (...args) => {
            this.show('Loading data...');
            return originalFetch(...args).finally(() => {
                setTimeout(() => this.hide(), 500);
            });
        };

        // Intercept XMLHttpRequest
        const originalOpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(...args) {
            this.addEventListener('loadstart', () => {
                window.loadingManager?.show('Loading data...');
            });
            this.addEventListener('loadend', () => {
                setTimeout(() => window.loadingManager?.hide(), 500);
            });
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
            'Initializing security protocols...',
            'Loading proctoring modules...',
            'Connecting to database...',
            'Setting up user interface...',
            'Ready to secure your exams!'
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