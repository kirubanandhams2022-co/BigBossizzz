/**
 * BigBossizzz Accessibility Manager
 * Comprehensive accessibility features including screen reader support, keyboard navigation, and inclusive UX
 */

class AccessibilityManager {
    constructor() {
        this.isKeyboardNavActive = false;
        this.currentRegion = null;
        this.announcements = [];
        this.focusHistory = [];
        this.skipLinks = [];
        
        this.init();
    }
    
    init() {
        console.log('? Initializing Accessibility Manager...');
        
        // Create skip links
        this.createSkipLinks();
        
        // Setup keyboard navigation detection
        this.setupKeyboardNavigation();
        
        // Setup focus management
        this.setupFocusManagement();
        
        // Setup ARIA live regions
        this.setupLiveRegions();
        
        // Setup form accessibility
        this.setupFormAccessibility();
        
        // Setup modal accessibility
        this.setupModalAccessibility();
        
        // Setup table accessibility
        this.setupTableAccessibility();
        
        // Setup quiz accessibility
        this.setupQuizAccessibility();
        
        // Setup landmark navigation
        this.setupLandmarkNavigation();
        
        console.log('? Accessibility Manager initialized successfully');
    }
    
    createSkipLinks() {
        const skipLinksContainer = document.createElement('div');
        skipLinksContainer.className = 'skip-links';
        skipLinksContainer.setAttribute('role', 'navigation');
        skipLinksContainer.setAttribute('aria-label', 'Skip links');
        
        this.skipLinks = [
            { href: '#main-content', text: 'Skip to main content' },
            { href: '#navigation', text: 'Skip to navigation' },
            { href: '#quiz-content', text: 'Skip to quiz' },
            { href: '#footer', text: 'Skip to footer' }
        ];
        
        this.skipLinks.forEach(link => {
            const skipLink = document.createElement('a');
            skipLink.href = link.href;
            skipLink.className = 'skip-link sr-only-focusable';
            skipLink.textContent = link.text;
            skipLink.addEventListener('click', this.handleSkipLinkClick.bind(this));
            skipLinksContainer.appendChild(skipLink);
        });
        
        document.body.insertBefore(skipLinksContainer, document.body.firstChild);
    }
    
    handleSkipLinkClick(event) {
        event.preventDefault();
        const targetId = event.target.getAttribute('href').substring(1);
        const targetElement = document.getElementById(targetId);
        
        if (targetElement) {
            targetElement.focus();
            targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
            this.announce(`Skipped to ${event.target.textContent.toLowerCase()}`);
        }
    }
    
    setupKeyboardNavigation() {
        // Detect keyboard vs mouse navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                this.isKeyboardNavActive = true;
                document.body.classList.add('keyboard-nav-active');
                document.body.classList.remove('mouse-nav-active');
            }
        });
        
        document.addEventListener('mousedown', () => {
            this.isKeyboardNavActive = false;
            document.body.classList.add('mouse-nav-active');
            document.body.classList.remove('keyboard-nav-active');
        });
        
        // Enhanced keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Alt + M: Go to main content
            if (e.altKey && e.key === 'm') {
                e.preventDefault();
                this.focusMainContent();
            }
            
            // Alt + N: Go to navigation
            if (e.altKey && e.key === 'n') {
                e.preventDefault();
                this.focusNavigation();
            }
            
            // Alt + S: Go to search
            if (e.altKey && e.key === 's') {
                e.preventDefault();
                this.focusSearch();
            }
            
            // Alt + H: Go to help
            if (e.altKey && e.key === 'h') {
                e.preventDefault();
                this.showKeyboardShortcuts();
            }
            
            // Escape: Close modals, dropdowns, etc.
            if (e.key === 'Escape') {
                this.handleEscapeKey();
            }
        });
    }
    
    setupFocusManagement() {
        // Track focus history for better navigation
        document.addEventListener('focusin', (e) => {
            this.focusHistory.push(e.target);
            if (this.focusHistory.length > 10) {
                this.focusHistory.shift();
            }
        });
        
        // Ensure focus is visible
        document.addEventListener('focusin', (e) => {
            if (this.isKeyboardNavActive) {
                e.target.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'nearest',
                    inline: 'nearest'
                });
            }
        });
        
        // Focus trapping for modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const modal = document.querySelector('.modal.show');
                if (modal) {
                    this.trapFocusInModal(e, modal);
                }
            }
        });
    }
    
    setupLiveRegions() {
        // Create live regions for announcements
        const liveRegionPolite = document.createElement('div');
        liveRegionPolite.id = 'live-region-polite';
        liveRegionPolite.setAttribute('aria-live', 'polite');
        liveRegionPolite.setAttribute('aria-atomic', 'true');
        liveRegionPolite.className = 'sr-only';
        
        const liveRegionAssertive = document.createElement('div');
        liveRegionAssertive.id = 'live-region-assertive';
        liveRegionAssertive.setAttribute('aria-live', 'assertive');
        liveRegionAssertive.setAttribute('aria-atomic', 'true');
        liveRegionAssertive.className = 'sr-only';
        
        document.body.appendChild(liveRegionPolite);
        document.body.appendChild(liveRegionAssertive);
    }
    
    setupFormAccessibility() {
        // Enhanced form labeling and descriptions
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            // Add form submission announcements
            form.addEventListener('submit', (e) => {
                this.announce('Form submitted. Please wait...', 'assertive');
            });
            
            // Enhanced error handling
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('invalid', (e) => {
                    const label = this.getAssociatedLabel(input);
                    const labelText = label ? label.textContent : 'Field';
                    this.announce(`${labelText} has an error: ${input.validationMessage}`, 'assertive');
                });
                
                // Describe form controls
                this.enhanceFormControl(input);
            });
        });
    }
    
    enhanceFormControl(input) {
        // Add aria-describedby for help text
        const helpText = input.parentElement.querySelector('.form-help, .form-text');
        if (helpText && !helpText.id) {
            helpText.id = `help-${Date.now()}-${Math.random()}`;
            input.setAttribute('aria-describedby', helpText.id);
        }
        
        // Mark required fields
        if (input.required) {
            const label = this.getAssociatedLabel(input);
            if (label) {
                label.classList.add('required');
                input.setAttribute('aria-required', 'true');
            }
        }
        
        // Add change announcements for important fields
        if (input.type === 'checkbox' || input.type === 'radio') {
            input.addEventListener('change', () => {
                const label = this.getAssociatedLabel(input);
                const labelText = label ? label.textContent : 'Option';
                const status = input.checked ? 'checked' : 'unchecked';
                this.announce(`${labelText} ${status}`);
            });
        }
    }
    
    getAssociatedLabel(input) {
        // Find associated label
        if (input.id) {
            return document.querySelector(`label[for="${input.id}"]`);
        }
        return input.closest('label') || input.parentElement.querySelector('label');
    }
    
    setupModalAccessibility() {
        // Handle modal opening
        document.addEventListener('show.bs.modal', (e) => {
            const modal = e.target;
            this.setupModalFocus(modal);
            this.announce('Dialog opened');
        });
        
        // Handle modal closing
        document.addEventListener('hide.bs.modal', (e) => {
            this.announce('Dialog closed');
            this.restoreFocus();
        });
    }
    
    setupModalFocus(modal) {
        // Store the element that opened the modal
        this.modalTrigger = document.activeElement;
        
        // Focus the first focusable element in modal
        setTimeout(() => {
            const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');\n            if (firstFocusable) {\n                firstFocusable.focus();\n            }\n        }, 100);\n    }\n    \n    trapFocusInModal(event, modal) {\n        const focusableElements = modal.querySelectorAll(\n            'button, [href], input, select, textarea, [tabindex]:not([tabindex=\"-1\"])'\n        );\n        \n        const firstFocusable = focusableElements[0];\n        const lastFocusable = focusableElements[focusableElements.length - 1];\n        \n        if (event.shiftKey) {\n            if (document.activeElement === firstFocusable) {\n                event.preventDefault();\n                lastFocusable.focus();\n            }\n        } else {\n            if (document.activeElement === lastFocusable) {\n                event.preventDefault();\n                firstFocusable.focus();\n            }\n        }\n    }\n    \n    setupTableAccessibility() {\n        const tables = document.querySelectorAll('table');\n        tables.forEach(table => {\n            // Add table caption if missing\n            if (!table.caption) {\n                const caption = document.createElement('caption');\n                caption.textContent = 'Data table';\n                caption.className = 'sr-only';\n                table.appendChild(caption);\n            }\n            \n            // Add scope attributes to headers\n            const headers = table.querySelectorAll('th');\n            headers.forEach(header => {\n                if (!header.getAttribute('scope')) {\n                    // Determine if it's a column or row header\n                    const isColumnHeader = header.parentElement.parentElement.tagName === 'THEAD';\n                    header.setAttribute('scope', isColumnHeader ? 'col' : 'row');\n                }\n            });\n            \n            // Add table navigation instructions\n            this.addTableInstructions(table);\n        });\n    }\n    \n    addTableInstructions(table) {\n        const instructions = document.createElement('div');\n        instructions.className = 'sr-only';\n        instructions.textContent = 'Use arrow keys to navigate table cells when focused';\n        table.parentElement.insertBefore(instructions, table);\n        \n        // Add arrow key navigation\n        table.addEventListener('keydown', (e) => {\n            if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {\n                this.navigateTable(e, table);\n            }\n        });\n    }\n    \n    navigateTable(event, table) {\n        const cell = event.target.closest('td, th');\n        if (!cell) return;\n        \n        const row = cell.parentElement;\n        const rowIndex = Array.from(row.parentElement.children).indexOf(row);\n        const cellIndex = Array.from(row.children).indexOf(cell);\n        \n        let targetRow, targetCell;\n        \n        switch (event.key) {\n            case 'ArrowUp':\n                targetRow = row.parentElement.children[rowIndex - 1];\n                break;\n            case 'ArrowDown':\n                targetRow = row.parentElement.children[rowIndex + 1];\n                break;\n            case 'ArrowLeft':\n                targetCell = row.children[cellIndex - 1];\n                break;\n            case 'ArrowRight':\n                targetCell = row.children[cellIndex + 1];\n                break;\n        }\n        \n        if (targetRow && (event.key === 'ArrowUp' || event.key === 'ArrowDown')) {\n            targetCell = targetRow.children[cellIndex];\n        }\n        \n        if (targetCell) {\n            event.preventDefault();\n            targetCell.focus();\n            targetCell.setAttribute('tabindex', '0');\n            cell.setAttribute('tabindex', '-1');\n        }\n    }\n    \n    setupQuizAccessibility() {\n        // Enhanced quiz option accessibility\n        const quizOptions = document.querySelectorAll('.quiz-option');\n        quizOptions.forEach((option, index) => {\n            // Add proper ARIA attributes\n            option.setAttribute('role', 'radio');\n            option.setAttribute('aria-checked', 'false');\n            option.setAttribute('tabindex', index === 0 ? '0' : '-1');\n            \n            // Add keyboard navigation\n            option.addEventListener('keydown', (e) => {\n                this.handleQuizOptionKeydown(e, option);\n            });\n            \n            // Add selection announcements\n            option.addEventListener('click', () => {\n                this.announceQuizSelection(option);\n            });\n        });\n        \n        // Add quiz instructions\n        const quizContainer = document.querySelector('.quiz-container');\n        if (quizContainer) {\n            this.addQuizInstructions(quizContainer);\n        }\n    }\n    \n    handleQuizOptionKeydown(event, option) {\n        const options = Array.from(option.parentElement.querySelectorAll('.quiz-option'));\n        const currentIndex = options.indexOf(option);\n        \n        switch (event.key) {\n            case 'ArrowUp':\n            case 'ArrowLeft':\n                event.preventDefault();\n                const prevIndex = (currentIndex - 1 + options.length) % options.length;\n                this.focusQuizOption(options[prevIndex]);\n                break;\n                \n            case 'ArrowDown':\n            case 'ArrowRight':\n                event.preventDefault();\n                const nextIndex = (currentIndex + 1) % options.length;\n                this.focusQuizOption(options[nextIndex]);\n                break;\n                \n            case 'Enter':\n            case ' ':\n                event.preventDefault();\n                option.click();\n                break;\n        }\n    }\n    \n    focusQuizOption(option) {\n        // Update tabindex\n        option.parentElement.querySelectorAll('.quiz-option').forEach(opt => {\n            opt.setAttribute('tabindex', '-1');\n        });\n        option.setAttribute('tabindex', '0');\n        option.focus();\n    }\n    \n    announceQuizSelection(option) {\n        const optionText = option.textContent.trim();\n        const questionElement = option.closest('.question-card');\n        const questionNumber = questionElement ? \n            questionElement.querySelector('.question-number')?.textContent || '' : '';\n        \n        this.announce(`${questionNumber} Selected: ${optionText}`);\n    }\n    \n    addQuizInstructions(container) {\n        const instructions = document.createElement('div');\n        instructions.className = 'sr-only';\n        instructions.setAttribute('aria-live', 'polite');\n        instructions.innerHTML = `\n            <p>Quiz instructions: Use Tab to navigate between questions and options. \n            Use arrow keys to move between options within a question. \n            Press Enter or Space to select an option.</p>\n        `;\n        container.insertBefore(instructions, container.firstChild);\n    }\n    \n    setupLandmarkNavigation() {\n        // Add landmark roles if missing\n        const landmarks = [\n            { selector: 'nav', role: 'navigation' },\n            { selector: 'main', role: 'main' },\n            { selector: 'header', role: 'banner' },\n            { selector: 'footer', role: 'contentinfo' },\n            { selector: 'aside', role: 'complementary' }\n        ];\n        \n        landmarks.forEach(({ selector, role }) => {\n            const elements = document.querySelectorAll(selector);\n            elements.forEach(element => {\n                if (!element.getAttribute('role')) {\n                    element.setAttribute('role', role);\n                }\n            });\n        });\n        \n        // Add landmark navigation\n        document.addEventListener('keydown', (e) => {\n            // Alt + R: Navigate through regions\n            if (e.altKey && e.key === 'r') {\n                e.preventDefault();\n                this.navigateToNextLandmark();\n            }\n        });\n    }\n    \n    navigateToNextLandmark() {\n        const landmarks = document.querySelectorAll('[role=\"banner\"], [role=\"navigation\"], [role=\"main\"], [role=\"complementary\"], [role=\"contentinfo\"]');\n        const currentIndex = Array.from(landmarks).findIndex(landmark => \n            landmark.contains(document.activeElement));\n        \n        const nextIndex = (currentIndex + 1) % landmarks.length;\n        const nextLandmark = landmarks[nextIndex];\n        \n        if (nextLandmark) {\n            nextLandmark.focus();\n            const role = nextLandmark.getAttribute('role');\n            this.announce(`Navigated to ${role} landmark`);\n        }\n    }\n    \n    // Utility methods\n    announce(message, priority = 'polite') {\n        const liveRegion = document.getElementById(`live-region-${priority}`);\n        if (liveRegion) {\n            liveRegion.textContent = '';\n            setTimeout(() => {\n                liveRegion.textContent = message;\n            }, 100);\n        }\n        \n        // Store announcement for history\n        this.announcements.push({\n            message,\n            priority,\n            timestamp: new Date()\n        });\n        \n        // Keep only last 50 announcements\n        if (this.announcements.length > 50) {\n            this.announcements.shift();\n        }\n    }\n    \n    focusMainContent() {\n        const mainContent = document.getElementById('main-content') || \n                          document.querySelector('main') || \n                          document.querySelector('.main-content');\n        if (mainContent) {\n            mainContent.focus();\n            this.announce('Focused main content');\n        }\n    }\n    \n    focusNavigation() {\n        const navigation = document.getElementById('navigation') || \n                         document.querySelector('nav') || \n                         document.querySelector('.navbar');\n        if (navigation) {\n            const firstLink = navigation.querySelector('a, button');\n            if (firstLink) {\n                firstLink.focus();\n                this.announce('Focused navigation');\n            }\n        }\n    }\n    \n    focusSearch() {\n        const searchInput = document.querySelector('input[type=\"search\"], .search-input, #search');\n        if (searchInput) {\n            searchInput.focus();\n            this.announce('Focused search');\n        }\n    }\n    \n    showKeyboardShortcuts() {\n        const shortcuts = [\n            'Alt + M: Go to main content',\n            'Alt + N: Go to navigation',\n            'Alt + S: Go to search',\n            'Alt + R: Navigate landmarks',\n            'Alt + H: Show this help',\n            'Tab: Navigate forward',\n            'Shift + Tab: Navigate backward',\n            'Escape: Close dialogs'\n        ];\n        \n        this.announce(`Keyboard shortcuts available: ${shortcuts.join('. ')}`, 'polite');\n    }\n    \n    handleEscapeKey() {\n        // Close modals\n        const openModal = document.querySelector('.modal.show');\n        if (openModal) {\n            const closeButton = openModal.querySelector('.btn-close, [data-bs-dismiss=\"modal\"]');\n            if (closeButton) {\n                closeButton.click();\n            }\n            return;\n        }\n        \n        // Close dropdowns\n        const openDropdown = document.querySelector('.dropdown-menu.show');\n        if (openDropdown) {\n            openDropdown.classList.remove('show');\n            return;\n        }\n        \n        // Close any other overlays\n        const overlay = document.querySelector('.overlay, .popup, .tooltip');\n        if (overlay) {\n            overlay.remove();\n        }\n    }\n    \n    restoreFocus() {\n        if (this.modalTrigger) {\n            this.modalTrigger.focus();\n            this.modalTrigger = null;\n        }\n    }\n    \n    // Public API methods\n    makeAnnouncement(message, priority = 'polite') {\n        this.announce(message, priority);\n    }\n    \n    addSkipLink(href, text) {\n        this.skipLinks.push({ href, text });\n        // Recreate skip links\n        const existingSkipLinks = document.querySelector('.skip-links');\n        if (existingSkipLinks) {\n            existingSkipLinks.remove();\n        }\n        this.createSkipLinks();\n    }\n    \n    getAnnouncementHistory() {\n        return this.announcements;\n    }\n    \n    isKeyboardNavigationActive() {\n        return this.isKeyboardNavActive;\n    }\n}\n\n// Auto-initialize accessibility manager\ndocument.addEventListener('DOMContentLoaded', () => {\n    window.accessibilityManager = new AccessibilityManager();\n});\n\n// Export for use in other modules\nif (typeof module !== 'undefined' && module.exports) {\n    module.exports = AccessibilityManager;\n}