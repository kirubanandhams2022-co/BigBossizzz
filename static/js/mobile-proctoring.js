// Mobile Proctoring.js - Enhanced mobile-specific proctoring for secure quiz taking
// Features: Camera enforcement, screenshot prevention, do-not-disturb mode, background app monitoring

class MobileProctoringManager {
    constructor(attemptId, deviceType) {
        this.attemptId = attemptId;
        this.deviceType = deviceType; // 'mobile' or 'tablet'
        this.isActive = false;
        this.violations = [];
        this.mediaStream = null;
        this.videoElement = null;
        this.canvas = null;
        this.context = null;
        this.detectionInterval = null;
        
        // Mobile-specific features
        this.isScreenBlocked = false;
        this.screenshotAttempts = 0;
        this.backgroundDetectionCount = 0;
        this.phoneCallDetected = false;
        this.doNotDisturbActive = false;
        this.visibilityChangeCount = 0;
        this.lastVisibilityTime = null;
        
        // Configuration for mobile devices
        this.config = {
            // Core mobile proctoring features
            enforceCamera: true,
            blockScreenshots: true,
            preventBackground: true,
            detectPhoneCalls: true,
            doNotDisturbMode: true,
            fullscreenRequired: true,
            orientationLock: true,
            
            // Detection thresholds
            maxScreenshotAttempts: 3,
            maxBackgroundSwitches: 5,
            maxVisibilityChanges: 10,
            
            // Monitoring intervals
            cameraCheckInterval: 5000,  // 5 seconds
            backgroundCheckInterval: 2000,  // 2 seconds
            phoneCallCheckInterval: 3000  // 3 seconds
        };
        
        this.init();
    }
    
    async init() {
        console.log(`Initializing Mobile Proctoring for ${this.deviceType} device`);
        
        // Initialize mobile-specific proctoring features
        await this.initializeMobileSecurityFeatures();
        
        // Start monitoring systems
        if (this.config.enforceCamera) {
            await this.initializeCamera();
        }
        
        if (this.config.blockScreenshots) {
            this.setupScreenshotPrevention();
        }
        
        if (this.config.preventBackground) {
            this.setupBackgroundAppMonitoring();
        }
        
        if (this.config.detectPhoneCalls) {
            this.setupPhoneCallDetection();
        }
        
        if (this.config.doNotDisturbMode) {
            this.activateDoNotDisturbMode();
        }
        
        if (this.config.fullscreenRequired) {
            this.enforceFullscreen();
        }
        
        if (this.config.orientationLock) {
            this.lockOrientation();
        }
        
        this.startMonitoring();
        
        console.log('Mobile proctoring initialized successfully');
    }
    
    async initializeMobileSecurityFeatures() {
        // Create mobile-specific UI elements
        this.createMobileSecurityOverlay();
        
        // Set up mobile-specific event listeners
        this.setupMobileEventListeners();
        
        // Configure mobile browser settings
        this.configureMobileBrowser();
    }
    
    createMobileSecurityOverlay() {
        // Create security overlay for mobile devices
        const overlay = document.createElement('div');
        overlay.id = 'mobile-security-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            z-index: 9999;
            display: none;
            color: white;
            text-align: center;
            padding: 20px;
            box-sizing: border-box;
        `;
        
        overlay.innerHTML = `
            <div style="margin-top: 20%;">
                <i class="fas fa-shield-alt" style="font-size: 4rem; color: #dc3545; margin-bottom: 20px;"></i>
                <h2>Security Violation Detected</h2>
                <p id="violation-message">Please return to the quiz immediately</p>
                <button onclick="mobileProctoringManager.returnToQuiz()" style="
                    background: #007bff; 
                    color: white; 
                    border: none; 
                    padding: 15px 30px; 
                    font-size: 1.2rem; 
                    border-radius: 5px; 
                    cursor: pointer;
                    margin-top: 20px;
                ">Return to Quiz</button>
            </div>
        `;
        
        document.body.appendChild(overlay);
        this.securityOverlay = overlay;
    }
    
    setupMobileEventListeners() {
        // Page visibility API for background app detection
        document.addEventListener('visibilitychange', () => {
            this.handleVisibilityChange();
        });
        
        // Page focus/blur for additional security
        window.addEventListener('focus', () => {
            this.handleWindowFocus();
        });
        
        window.addEventListener('blur', () => {
            this.handleWindowBlur();
        });
        
        // Screen orientation changes
        if (screen.orientation) {
            screen.orientation.addEventListener('change', () => {
                this.handleOrientationChange();
            });
        }
        
        // Touch events for interaction monitoring
        document.addEventListener('touchstart', (e) => {
            this.handleTouchStart(e);
        });
        
        // Prevent context menu (right-click equivalent on mobile)
        document.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.logViolation('context_menu_blocked', 'Context menu access blocked', 'medium');
        });
        
        // Prevent text selection
        document.addEventListener('selectstart', (e) => {
            e.preventDefault();
        });
        
        // Detect screenshot attempts (volume down + power button on many devices)
        this.setupScreenshotDetection();
    }
    
    configureMobileBrowser() {
        // Prevent zoom
        const viewport = document.querySelector('meta[name="viewport"]');
        if (viewport) {
            viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no');
        }
        
        // Disable text selection
        document.body.style.webkitUserSelect = 'none';
        document.body.style.mozUserSelect = 'none';
        document.body.style.msUserSelect = 'none';
        document.body.style.userSelect = 'none';
        
        // Disable drag
        document.body.style.webkitUserDrag = 'none';
        document.body.style.mozUserDrag = 'none';
        document.body.style.userDrag = 'none';
        
        // Prevent copy/paste
        document.addEventListener('copy', (e) => {
            e.preventDefault();
            this.logViolation('copy_attempt', 'Copy attempt blocked', 'medium');
        });
        
        document.addEventListener('paste', (e) => {
            e.preventDefault();
            this.logViolation('paste_attempt', 'Paste attempt blocked', 'medium');
        });
    }
    
    async initializeCamera() {
        try {
            console.log('Requesting camera access for mobile proctoring...');
            
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'user', // Front-facing camera
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                },
                audio: false // No audio recording for mobile
            });
            
            // Create video element for mobile
            this.videoElement = document.createElement('video');
            this.videoElement.srcObject = this.mediaStream;
            this.videoElement.autoplay = true;
            this.videoElement.muted = true;
            this.videoElement.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                width: 120px;
                height: 90px;
                border: 2px solid #007bff;
                border-radius: 8px;
                z-index: 1000;
                background: black;
            `;
            
            document.body.appendChild(this.videoElement);
            
            console.log('Mobile camera initialized successfully');
            this.logViolation('camera_initialized', 'Mobile camera access granted', 'info');
            
        } catch (error) {
            console.error('Failed to initialize camera:', error);
            this.handleCameraError();
        }
    }
    
    handleCameraError() {
        this.showSecurityOverlay('Camera access is required for this quiz. Please grant camera permission and refresh the page.');
        this.logViolation('camera_access_denied', 'Camera access denied on mobile device', 'critical');
    }
    
    setupScreenshotPrevention() {
        // Multiple layers of screenshot prevention for mobile devices
        
        // Method 1: Detect keyboard shortcuts (though limited on mobile)
        document.addEventListener('keydown', (e) => {
            // Common screenshot key combinations
            if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'p')) {
                e.preventDefault();
                this.handleScreenshotAttempt();
            }
        });
        
        // Method 2: Detect volume button combinations (Android)
        let volumeDownPressed = false;
        let powerButtonPressed = false;
        
        // This is limited due to browser security, but we try to detect patterns
        document.addEventListener('keydown', (e) => {
            if (e.code === 'VolumeDown') {
                volumeDownPressed = true;
                setTimeout(() => { volumeDownPressed = false; }, 500);
            }
        });
        
        // Method 3: Page visibility changes that might indicate screenshot apps
        this.setupVisibilityScreenshotDetection();
        
        // Method 4: Disable print screen and similar
        document.addEventListener('keyup', (e) => {
            if (e.keyCode === 44) { // Print Screen key
                this.handleScreenshotAttempt();
            }
        });
    }
    
    setupVisibilityScreenshotDetection() {
        let rapidVisibilityChanges = 0;
        let lastVisibilityChange = Date.now();
        
        document.addEventListener('visibilitychange', () => {
            const now = Date.now();
            if (now - lastVisibilityChange < 1000) { // Less than 1 second
                rapidVisibilityChanges++;
                if (rapidVisibilityChanges > 3) {
                    this.handleScreenshotAttempt();
                    rapidVisibilityChanges = 0;
                }
            } else {
                rapidVisibilityChanges = 0;
            }
            lastVisibilityChange = now;
        });
    }
    
    handleScreenshotAttempt() {
        this.screenshotAttempts++;
        console.warn(`Screenshot attempt detected (${this.screenshotAttempts})`);
        
        this.logViolation('screenshot_attempt', `Screenshot attempt detected on ${this.deviceType} device (attempt ${this.screenshotAttempts})`, 'high');
        
        if (this.screenshotAttempts >= this.config.maxScreenshotAttempts) {
            this.terminateQuizForViolation('Multiple screenshot attempts detected');
        } else {
            this.showWarning(`Screenshot attempt detected! ${this.config.maxScreenshotAttempts - this.screenshotAttempts} attempts remaining before quiz termination.`);
        }
    }
    
    setupBackgroundAppMonitoring() {
        // Monitor for background apps and multitasking
        setInterval(() => {
            this.checkBackgroundApps();
        }, this.config.backgroundCheckInterval);
    }
    
    checkBackgroundApps() {
        // Check if the page is in background
        if (document.hidden) {
            this.backgroundDetectionCount++;
            
            if (this.backgroundDetectionCount === 1) {
                this.showSecurityOverlay('Please return to the quiz. Background apps are not allowed during the exam.');
            }
            
            this.logViolation('background_app_detected', 
                `Page moved to background on ${this.deviceType} device (count: ${this.backgroundDetectionCount})`, 
                'high');
            
            if (this.backgroundDetectionCount >= this.config.maxBackgroundSwitches) {
                this.terminateQuizForViolation('Too many background app switches detected');
            }
        } else if (this.backgroundDetectionCount > 0 && !document.hidden) {
            // User returned to the quiz
            this.hideSecurityOverlay();
        }
    }
    
    setupPhoneCallDetection() {
        // Detect phone calls and other interruptions
        setInterval(() => {
            this.checkForPhoneCalls();
        }, this.config.phoneCallCheckInterval);
    }
    
    checkForPhoneCalls() {
        // Check if audio context is suspended (might indicate phone call)
        if (typeof AudioContext !== 'undefined' || typeof webkitAudioContext !== 'undefined') {
            const AudioContextClass = window.AudioContext || window.webkitAudioContext;
            
            if (!this.audioContext) {
                this.audioContext = new AudioContextClass();
            }
            
            if (this.audioContext.state === 'suspended') {
                if (!this.phoneCallDetected) {
                    this.phoneCallDetected = true;
                    this.handlePhoneCallDetected();
                }
            } else {
                if (this.phoneCallDetected) {
                    this.phoneCallDetected = false;
                    this.handlePhoneCallEnded();
                }
            }
        }
        
        // Additional method: Check for connection type changes
        if (navigator.connection) {
            if (navigator.connection.type === 'cellular' && this.lastConnectionType !== 'cellular') {
                this.logViolation('connection_change', 'Connection changed to cellular during quiz', 'medium');
            }
            this.lastConnectionType = navigator.connection.type;
        }
    }
    
    handlePhoneCallDetected() {
        console.warn('Phone call detected during quiz');
        this.showSecurityOverlay('Phone call detected. Please end the call and return to the quiz.');
        this.logViolation('phone_call_detected', 'Phone call detected during quiz on mobile device', 'critical');
    }
    
    handlePhoneCallEnded() {
        console.log('Phone call ended, returning to quiz');
        this.hideSecurityOverlay();
        this.logViolation('phone_call_ended', 'Phone call ended, user returned to quiz', 'info');
    }
    
    activateDoNotDisturbMode() {
        // Request notification permissions to prevent interruptions
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
        
        // Try to prevent wake lock interruptions
        if ('wakeLock' in navigator) {
            this.requestWakeLock();
        }
        
        // Hide system UI on supported browsers
        this.hideSystemUI();
        
        this.doNotDisturbActive = true;
        this.logViolation('do_not_disturb_activated', 'Do not disturb mode activated for mobile quiz', 'info');
    }
    
    async requestWakeLock() {
        try {
            this.wakeLock = await navigator.wakeLock.request('screen');
            console.log('Wake lock acquired');
        } catch (err) {
            console.warn('Could not acquire wake lock:', err);
        }
    }
    
    hideSystemUI() {
        // Request fullscreen with system UI hidden
        if (document.documentElement.requestFullscreen) {
            document.documentElement.requestFullscreen({ navigationUI: 'hide' });
        }
    }
    
    enforceFullscreen() {
        // Force fullscreen mode for mobile devices
        if (!document.fullscreenElement) {
            this.enterFullscreen();
        }
        
        // Monitor fullscreen changes
        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement) {
                this.handleFullscreenExit();
            }
        });
    }
    
    enterFullscreen() {
        const element = document.documentElement;
        if (element.requestFullscreen) {
            element.requestFullscreen();
        } else if (element.mozRequestFullScreen) {
            element.mozRequestFullScreen();
        } else if (element.webkitRequestFullscreen) {
            element.webkitRequestFullscreen();
        } else if (element.msRequestFullscreen) {
            element.msRequestFullscreen();
        }
    }
    
    handleFullscreenExit() {
        console.warn('Fullscreen mode exited');
        this.showWarning('Please return to fullscreen mode');
        this.logViolation('fullscreen_exit', 'User exited fullscreen mode on mobile device', 'high');
        
        // Try to re-enter fullscreen after a short delay
        setTimeout(() => {
            this.enterFullscreen();
        }, 2000);
    }
    
    lockOrientation() {
        // Lock orientation to portrait or landscape as appropriate
        if (screen.orientation && screen.orientation.lock) {
            const orientation = window.innerHeight > window.innerWidth ? 'portrait' : 'landscape';
            screen.orientation.lock(orientation).catch(err => {
                console.warn('Could not lock orientation:', err);
            });
        }
    }
    
    handleOrientationChange() {
        this.logViolation('orientation_change', 'Device orientation changed during quiz', 'medium');
        
        // Warn user about orientation changes
        this.showWarning('Please maintain consistent device orientation during the quiz');
    }
    
    handleVisibilityChange() {
        if (document.hidden) {
            this.visibilityChangeCount++;
            this.lastVisibilityTime = Date.now();
            
            this.logViolation('visibility_hidden', 
                `Quiz hidden on ${this.deviceType} device (count: ${this.visibilityChangeCount})`, 
                'medium');
            
            if (this.visibilityChangeCount >= this.config.maxVisibilityChanges) {
                this.terminateQuizForViolation('Too many app switches detected');
            }
        } else {
            // User returned to quiz
            if (this.lastVisibilityTime) {
                const hiddenDuration = Date.now() - this.lastVisibilityTime;
                this.logViolation('visibility_restored', 
                    `Quiz restored after ${hiddenDuration}ms on ${this.deviceType} device`, 
                    'info');
            }
        }
    }
    
    handleWindowFocus() {
        // Quiz regained focus
        this.hideSecurityOverlay();
    }
    
    handleWindowBlur() {
        // Quiz lost focus
        this.showWarning('Please keep the quiz in focus');
    }
    
    handleTouchStart(e) {
        // Monitor touch patterns for suspicious behavior
        if (e.touches.length > 2) {
            this.logViolation('multi_touch', 'Multiple touch points detected', 'low');
        }
    }
    
    setupScreenshotDetection() {
        // Advanced screenshot detection methods for mobile
        
        // Method 1: Monitor for rapid screen captures via media queries
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(orientation: portrait)');
            mediaQuery.addListener(() => {
                // Rapid orientation changes might indicate screenshot tools
                this.checkForRapidScreenChanges();
            });
        }
        
        // Method 2: Monitor for specific key combinations
        document.addEventListener('keydown', (e) => {
            // iOS screenshot: Power + Home or Power + Volume Up
            // Android screenshot: Power + Volume Down
            if (e.key === 'PrintScreen' || 
                (e.key === 'Power' && (e.key === 'VolumeDown' || e.key === 'Home'))) {
                this.handleScreenshotAttempt();
            }
        });
    }
    
    checkForRapidScreenChanges() {
        // Implementation for detecting rapid screen changes
        const now = Date.now();
        if (this.lastScreenChange && (now - this.lastScreenChange) < 500) {
            this.handleScreenshotAttempt();
        }
        this.lastScreenChange = now;
    }
    
    startMonitoring() {
        // Start all monitoring systems
        this.detectionInterval = setInterval(() => {
            this.performSecurityChecks();
        }, 5000); // Check every 5 seconds
        
        this.isActive = true;
        console.log('Mobile proctoring monitoring started');
    }
    
    performSecurityChecks() {
        // Perform comprehensive security checks
        this.checkCameraStatus();
        this.checkConnectionStatus();
        this.checkDeviceStatus();
    }
    
    checkCameraStatus() {
        if (this.mediaStream && this.config.enforceCamera) {
            const videoTrack = this.mediaStream.getVideoTracks()[0];
            if (!videoTrack || !videoTrack.enabled) {
                this.handleCameraDisabled();
            }
        }
    }
    
    handleCameraDisabled() {
        console.warn('Camera disabled during quiz');
        this.showSecurityOverlay('Camera must remain enabled during the quiz');
        this.logViolation('camera_disabled', 'Camera disabled during mobile quiz', 'critical');
    }
    
    checkConnectionStatus() {
        if (!navigator.onLine) {
            this.handleConnectionLost();
        }
    }
    
    handleConnectionLost() {
        this.showSecurityOverlay('Internet connection lost. Please restore connection to continue.');
        this.logViolation('connection_lost', 'Internet connection lost during quiz', 'high');
    }
    
    checkDeviceStatus() {
        // Check battery level if available
        if (navigator.getBattery) {
            navigator.getBattery().then(battery => {
                if (battery.level < 0.1) { // Less than 10%
                    this.showWarning('Low battery detected. Please charge your device.');
                    this.logViolation('low_battery', `Low battery level: ${Math.round(battery.level * 100)}%`, 'medium');
                }
            });
        }
    }
    
    showSecurityOverlay(message) {
        if (this.securityOverlay) {
            const messageElement = this.securityOverlay.querySelector('#violation-message');
            if (messageElement) {
                messageElement.textContent = message;
            }
            this.securityOverlay.style.display = 'block';
            this.isScreenBlocked = true;
        }
    }
    
    hideSecurityOverlay() {
        if (this.securityOverlay) {
            this.securityOverlay.style.display = 'none';
            this.isScreenBlocked = false;
        }
    }
    
    returnToQuiz() {
        this.hideSecurityOverlay();
        this.enterFullscreen();
        
        // Reset some counters with a warning
        if (this.backgroundDetectionCount > 0) {
            this.backgroundDetectionCount = Math.max(0, this.backgroundDetectionCount - 1);
        }
    }
    
    showWarning(message) {
        // Show temporary warning message
        const warning = document.createElement('div');
        warning.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #ff6b6b;
            color: white;
            padding: 20px;
            border-radius: 10px;
            z-index: 9998;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        `;
        warning.innerHTML = `
            <i class="fas fa-exclamation-triangle" style="margin-right: 10px;"></i>
            ${message}
        `;
        
        document.body.appendChild(warning);
        
        setTimeout(() => {
            if (warning.parentNode) {
                warning.parentNode.removeChild(warning);
            }
        }, 5000);
    }
    
    logViolation(type, message, severity = 'medium') {
        const violation = {
            type,
            message,
            severity,
            timestamp: new Date().toISOString(),
            deviceType: this.deviceType,
            userAgent: navigator.userAgent
        };
        
        this.violations.push(violation);
        console.log(`Mobile Proctoring Violation [${severity}]:`, violation);
        
        // Send to server
        this.sendViolationToServer(violation);
    }
    
    sendViolationToServer(violation) {
        fetch('/api/log_violation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                attempt_id: this.attemptId,
                ...violation
            })
        }).catch(err => {
            console.error('Failed to send violation to server:', err);
        });
    }
    
    terminateQuizForViolation(reason) {
        console.error('Terminating quiz due to violation:', reason);
        
        this.showSecurityOverlay(`Quiz terminated due to security violations: ${reason}`);
        
        this.logViolation('quiz_terminated', `Quiz terminated: ${reason}`, 'critical');
        
        // Disable all form inputs
        const inputs = document.querySelectorAll('input, textarea, select, button');
        inputs.forEach(input => {
            input.disabled = true;
        });
        
        // Auto-submit the quiz
        setTimeout(() => {
            if (typeof quizManager !== 'undefined' && quizManager.autoSubmitQuiz) {
                quizManager.autoSubmitQuiz();
            }
        }, 5000);
    }
    
    cleanup() {
        // Clean up all resources
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
        }
        
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
        }
        
        if (this.videoElement && this.videoElement.parentNode) {
            this.videoElement.parentNode.removeChild(this.videoElement);
        }
        
        if (this.securityOverlay && this.securityOverlay.parentNode) {
            this.securityOverlay.parentNode.removeChild(this.securityOverlay);
        }
        
        if (this.wakeLock) {
            this.wakeLock.release();
        }
        
        this.isActive = false;
        console.log('Mobile proctoring cleanup completed');
    }
}

// Global instance
let mobileProctoringManager;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // This will be initialized from the template with device type
    console.log('Mobile proctoring script loaded');
});