/**
 * BigBossizzz Theme Manager
 * Comprehensive theme management with user preferences and accessibility
 */

class ThemeManager {
    constructor() {
        this.currentTheme = 'auto';
        this.themes = {
            'auto': {
                name: 'Auto',
                icon: 'fas fa-adjust',
                description: 'Follow system preference'
            },
            'light': {
                name: 'Light',
                icon: 'fas fa-sun',
                description: 'Light theme'
            },
            'dark': {
                name: 'Dark',
                icon: 'fas fa-moon',
                description: 'Dark theme'
            }
        };
        
        this.init();
    }
    
    init() {
        console.log('? Initializing Theme Manager...');
        
        // Load saved theme preference
        this.loadThemePreference();
        
        // Apply initial theme
        this.applyTheme(this.currentTheme);
        
        // Create theme toggle UI
        this.createThemeToggle();
        
        // Listen for system theme changes
        this.listenForSystemThemeChanges();
        
        // Save preference to user profile if logged in
        this.saveThemeToProfile();
        
        console.log('? Theme Manager initialized successfully');
    }
    
    loadThemePreference() {
        // Try to load from user profile first
        const profileTheme = this.getUserProfileTheme();
        if (profileTheme) {
            this.currentTheme = profileTheme;
            return;
        }
        
        // Fall back to localStorage
        const savedTheme = localStorage.getItem('bigbossizzz-theme');
        if (savedTheme && this.themes[savedTheme]) {
            this.currentTheme = savedTheme;
            return;
        }
        
        // Default to auto (system preference)
        this.currentTheme = 'auto';
    }
    
    getUserProfileTheme() {
        // Check if user preference is available in the page
        const themeElement = document.querySelector('[data-user-theme]');
        return themeElement ? themeElement.dataset.userTheme : null;
    }
    
    applyTheme(theme) {
        console.log(`? Applying theme: ${theme}`);
        
        // Remove existing theme classes
        document.documentElement.removeAttribute('data-theme');
        
        // Apply new theme
        if (theme !== 'auto') {
            document.documentElement.setAttribute('data-theme', theme);
        }
        
        // Store current theme
        this.currentTheme = theme;
        
        // Save to localStorage
        localStorage.setItem('bigbossizzz-theme', theme);
        
        // Update theme toggle UI
        this.updateThemeToggleUI();
        
        // Announce theme change for screen readers
        this.announceThemeChange(theme);
        
        // Save to user profile
        this.saveThemeToProfile();
        
        // Dispatch theme change event
        window.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { theme: theme, effectiveTheme: this.getEffectiveTheme() }
        }));
    }
    
    getEffectiveTheme() {
        if (this.currentTheme === 'auto') {
            return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        return this.currentTheme;
    }
    
    createThemeToggle() {
        // Create theme toggle button
        const themeToggle = document.createElement('div');
        themeToggle.className = 'theme-toggle';
        themeToggle.setAttribute('role', 'button');
        themeToggle.setAttribute('tabindex', '0');
        themeToggle.setAttribute('aria-label', 'Theme selector');
        themeToggle.setAttribute('aria-expanded', 'false');
        themeToggle.innerHTML = `
            <i class="${this.themes[this.currentTheme].icon}" aria-hidden="true"></i>
            <div class="theme-toggle-dropdown" id="themeDropdown">
                ${Object.entries(this.themes).map(([key, theme]) => `
                    <div class="theme-option" data-theme="${key}" role="menuitem" tabindex="0"
                         aria-label="Switch to ${theme.name} theme">
                        <i class="${theme.icon}" aria-hidden="true"></i>
                        <span>${theme.name}</span>
                    </div>
                `).join('')}
            </div>
        `;
        
        // Add event listeners
        themeToggle.addEventListener('click', this.toggleThemeDropdown.bind(this));
        themeToggle.addEventListener('keydown', this.handleThemeToggleKeydown.bind(this));
        
        // Add option event listeners
        const dropdown = themeToggle.querySelector('.theme-toggle-dropdown');
        dropdown.addEventListener('click', this.handleThemeOptionClick.bind(this));
        dropdown.addEventListener('keydown', this.handleThemeOptionKeydown.bind(this));
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!themeToggle.contains(e.target)) {
                this.closeThemeDropdown();
            }
        });
        
        // Add to page
        document.body.appendChild(themeToggle);
        
        // Update initial UI state
        this.updateThemeToggleUI();
    }
    
    toggleThemeDropdown() {
        const dropdown = document.getElementById('themeDropdown');
        const isOpen = dropdown.classList.contains('show');
        
        if (isOpen) {
            this.closeThemeDropdown();
        } else {
            this.openThemeDropdown();
        }
    }
    
    openThemeDropdown() {
        const dropdown = document.getElementById('themeDropdown');
        const toggle = dropdown.parentElement;
        
        dropdown.classList.add('show');
        toggle.setAttribute('aria-expanded', 'true');
        
        // Focus first option
        const firstOption = dropdown.querySelector('.theme-option');
        if (firstOption) {
            firstOption.focus();
        }
    }
    
    closeThemeDropdown() {
        const dropdown = document.getElementById('themeDropdown');
        const toggle = dropdown.parentElement;
        
        dropdown.classList.remove('show');
        toggle.setAttribute('aria-expanded', 'false');
    }
    
    handleThemeToggleKeydown(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            this.toggleThemeDropdown();
        } else if (event.key === 'Escape') {
            this.closeThemeDropdown();
        }
    }
    
    handleThemeOptionClick(event) {
        const option = event.target.closest('.theme-option');
        if (option) {
            const theme = option.dataset.theme;
            this.applyTheme(theme);
            this.closeThemeDropdown();
        }
    }
    
    handleThemeOptionKeydown(event) {
        const options = Array.from(event.currentTarget.querySelectorAll('.theme-option'));
        const currentIndex = options.indexOf(event.target);
        
        switch (event.key) {
            case 'Enter':
            case ' ':
                event.preventDefault();
                const theme = event.target.dataset.theme;
                this.applyTheme(theme);
                this.closeThemeDropdown();
                break;
                
            case 'ArrowDown':
                event.preventDefault();
                const nextIndex = (currentIndex + 1) % options.length;
                options[nextIndex].focus();
                break;
                
            case 'ArrowUp':
                event.preventDefault();
                const prevIndex = (currentIndex - 1 + options.length) % options.length;
                options[prevIndex].focus();
                break;
                
            case 'Escape':
                event.preventDefault();
                this.closeThemeDropdown();
                document.querySelector('.theme-toggle').focus();
                break;
                
            case 'Home':
                event.preventDefault();
                options[0].focus();
                break;
                
            case 'End':
                event.preventDefault();
                options[options.length - 1].focus();
                break;
        }
    }
    
    updateThemeToggleUI() {
        const toggle = document.querySelector('.theme-toggle');
        if (!toggle) return;
        
        // Update main icon
        const mainIcon = toggle.querySelector('i');
        if (mainIcon) {
            mainIcon.className = this.themes[this.currentTheme].icon;
        }
        
        // Update active option
        const options = toggle.querySelectorAll('.theme-option');
        options.forEach(option => {
            option.classList.toggle('active', option.dataset.theme === this.currentTheme);
        });
        
        // Update aria-label
        toggle.setAttribute('aria-label', 
            `Current theme: ${this.themes[this.currentTheme].name}. Click to change theme.`);
    }
    
    listenForSystemThemeChanges() {
        // Listen for system theme changes when in auto mode
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            if (this.currentTheme === 'auto') {
                console.log('? System theme changed, updating...');
                this.announceThemeChange('auto');
                window.dispatchEvent(new CustomEvent('themeChanged', {
                    detail: { theme: 'auto', effectiveTheme: e.matches ? 'dark' : 'light' }
                }));
            }
        });
    }
    
    announceThemeChange(theme) {
        // Create announcement for screen readers
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        
        const effectiveTheme = this.getEffectiveTheme();
        announcement.textContent = `Theme changed to ${this.themes[theme].name}. 
            ${theme === 'auto' ? `Currently using ${effectiveTheme} mode.` : ''}`;
        
        document.body.appendChild(announcement);
        
        // Remove after announcement
        setTimeout(() => {
            if (announcement.parentNode) {
                announcement.parentNode.removeChild(announcement);
            }
        }, 1000);
    }
    
    async saveThemeToProfile() {
        // Save theme preference to user profile
        try {
            const response = await fetch('/api/user/theme-preference', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    theme: this.currentTheme
                })
            });
            
            if (response.ok) {
                console.log('? Theme preference saved to profile');
            }
        } catch (error) {
            console.log('?? Could not save theme preference:', error);
            // Silent fail - user not logged in or network issue
        }
    }
    
    getCSRFToken() {
        const tokenElement = document.querySelector('[name=csrf-token]');
        return tokenElement ? tokenElement.getAttribute('content') : '';
    }
    
    // Public API methods
    setTheme(theme) {
        if (this.themes[theme]) {
            this.applyTheme(theme);
        }
    }
    
    getCurrentTheme() {
        return this.currentTheme;
    }
    
    getEffectiveCurrentTheme() {
        return this.getEffectiveTheme();
    }
    
    getAvailableThemes() {
        return Object.keys(this.themes);
    }
    
    // Accessibility helpers
    getThemeForContrast() {
        // Return high contrast theme if user prefers high contrast
        if (window.matchMedia('(prefers-contrast: high)').matches) {
            return this.getEffectiveTheme() === 'dark' ? 'dark-high-contrast' : 'light-high-contrast';
        }
        return this.getEffectiveTheme();
    }
    
    supportsTheme(theme) {
        return this.themes.hasOwnProperty(theme);
    }
}

// Auto-initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}