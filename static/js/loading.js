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
                <div style="position: relative; margin: 0 auto 2rem; width: 120px; height: 120px;">
                    <div class="tech-eye-container" style="
                        position: relative;
                        width: 120px;
                        height: 120px;
                        border-radius: 50%;
                        overflow: hidden;
                        animation: techEyePulse 2s ease-in-out infinite;
                        box-shadow: 0 0 30px rgba(103, 102, 241, 0.8);
                    ">
                        <img src="/static/images/tech-eye-loading.jpg" style="
                            width: 100%;
                            height: 100%;
                            object-fit: cover;
                            animation: techEyeRotate 3s linear infinite;
                        " alt="Tech Eye">
                        <div style="
                            position: absolute;
                            top: 0;
                            left: 0;
                            width: 100%;
                            height: 100%;
                            background: linear-gradient(45deg, transparent 30%, rgba(103, 102, 241, 0.3) 50%, transparent 70%);
                            animation: techEyeScan 2s ease-in-out infinite;
                        "></div>
                    </div>
                </div>
                
                <div style="font-size: 1.3rem; margin-bottom: 1rem; animation: loadingFade 2s ease-in-out infinite; font-weight: 600;">
                    🤖 BigBossizzz
                </div>
                
                <div style="font-size: 0.95rem; color: #a0a0a0; margin-bottom: 1.5rem; animation: techTypeWriter 3s ease-in-out infinite;">
                    <span class="loading-text">Initializing AI surveillance systems...</span>
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