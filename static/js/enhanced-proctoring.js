/**
 * Enhanced Enterprise Proctoring System - Live Monitoring Only
 * No image storage - Real-time behavioral analysis
 * Institutional-grade security for BigBossizzz Platform
 */

class EnhancedProctoringSystem {
    constructor(attemptId, quizId) {
        this.attemptId = attemptId;
        this.quizId = quizId;
        this.isActive = false;
        this.violations = [];
        this.mediaStream = null;
        this.videoElement = null;
        this.canvas = null;
        this.context = null;
        
        // Real-time detection (NO IMAGE STORAGE)
        this.faceDetectionInterval = null;
        this.lastFaceCount = 0;
        this.lookAwayCount = 0;
        this.multiplePeopleCount = 0;
        this.cameraHiddenCount = 0;
        this.warningShown = false;  // Prevent repeated warnings
        
        // Enhanced Audio Environment Analysis with Speech Detection
        this.audioStream = null;
        this.audioContext = null;
        this.analyser = null;
        this.dataArray = null;
        this.audioMonitoringActive = false;
        this.baselineNoiseLevel = null;
        this.voiceDetectionCount = 0;
        this.suspiciousSoundCount = 0;
        this.conversationDetected = false;
        this.sustainedSpeechCount = 0;
        this.environmentAnalysis = {
            isQuiet: true,
            hasConversation: false,
            noiseLevelHistory: [],
            lastVoiceActivity: 0,
            speechSegments: [],
            conversationStartTime: null,
            baselineCalibrated: false
        };
        
        // Tab/App monitoring
        this.tabSwitchCount = 0;
        this.backgroundAppsDetected = [];
        this.isFullscreenLocked = false;
        this.preventStart = false;
        
        // Strong Security Enforcement
        this.enforcementActive = false;
        this.blockingActive = false;
        this.blockedEvents = [];
        this.keyboardBlocker = null;
        this.screenshotAttempts = 0;
        this.minimizeAttempts = 0;
        this.lastFocusTime = Date.now();
        
        // Security configuration - Balanced for better user experience
        this.config = {
            maxLookAwayTime: 10000,       // 10 seconds (as requested)
            maxMultiplePeople: 8,         // 8 detections (very lenient)
            maxCameraHidden: 8,           // 8 detections (very forgiving) 
            maxTabSwitches: 3,            // 3 switches = warning
            terminateOnViolations: 7,     // 7 violations = terminate (more lenient)
            realTimeAnalysis: true,       // Live analysis only
            noImageStorage: true,         // Never store images
            strictMode: false,            // Balanced for UX
            lookAwayThreshold: 0.6        // Less sensitive look-away detection
        };
        
        // Violation tracking
        this.violationLog = [];
        this.warningCount = 0;
        this.criticalViolations = 0;
        this.isTerminated = false;
        
        // Enhanced Mobile/Desktop detection with blocking
        this.isMobile = this.detectMobileDevice();
        this.isTablet = this.detectTabletDevice();
        this.deviceInfo = this.getDeviceInfo();
        
        this.init();
    }
    
    preventCheating() {
        // Enhanced cheating prevention setup
        console.log('🔒 Setting up enhanced cheating prevention');
        
        // Activate strong security enforcement
        this.activateStrongEnforcement();
        
        // Disable text selection
        document.body.style.userSelect = 'none';
        document.body.style.webkitUserSelect = 'none';
        document.body.style.mozUserSelect = 'none';
        document.body.style.msUserSelect = 'none';
        
        // Disable drag and drop
        document.addEventListener('dragstart', (e) => e.preventDefault());
        document.addEventListener('drop', (e) => e.preventDefault());
        
        // Disable image saving
        document.addEventListener('contextmenu', (e) => {
            if (e.target.tagName === 'IMG') {
                e.preventDefault();
                this.recordViolation('image_save_attempt', 'medium', 'Attempted to save image');
            }
        });
        
        // Block screenshot attempts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'PrintScreen') {
                e.preventDefault();
                this.recordViolation('screenshot_attempt', 'high', 'Screenshot attempt detected');
                this.showSingleWarning('⚠️ Screenshots are not allowed during the quiz');
            }
        });
        
        // Detect zoom changes
        let lastZoom = window.devicePixelRatio;
        setInterval(() => {
            if (this.isActive && Math.abs(window.devicePixelRatio - lastZoom) > 0.1) {
                this.recordViolation('zoom_change', 'low', 'Browser zoom level changed');
                lastZoom = window.devicePixelRatio;
            }
        }, 2000);
        
        // DISABLED: Mouse movement monitoring (was causing too many false positives)
        // Only log for debugging, no violations recorded
        let mouseEvents = [];
        document.addEventListener('mousemove', (e) => {
            if (this.isActive) {
                mouseEvents.push({x: e.clientX, y: e.clientY, time: Date.now()});
                if (mouseEvents.length > 20) mouseEvents.shift(); // Keep more history
                
                // Only check for extremely obvious bot patterns (much less sensitive)
                if (mouseEvents.length >= 15) {
                    const isLinear = this.checkLinearMovement(mouseEvents.slice(-10));
                    if (isLinear) {
                        // Just log, don't record violation
                        console.log('ℹ️ Unusual mouse pattern detected (logged only)');
                    }
                }
            }
        });
        
        // Disable common cheating shortcuts
        document.addEventListener('keydown', (e) => {
            if (this.isActive) {
                const blockedCombos = [
                    {ctrl: true, shift: true, key: 'i'},  // Dev tools
                    {ctrl: true, shift: true, key: 'j'},  // Console
                    {ctrl: true, shift: true, key: 'c'},  // Inspect
                    {ctrl: true, key: 'u'},               // View source
                    {ctrl: true, key: 'p'},               // Print
                    {ctrl: true, key: 'h'},               // History
                    {f12: true},                          // Dev tools
                ];
                
                for (const combo of blockedCombos) {
                    if (this.matchesCombo(e, combo)) {
                        e.preventDefault();
                        this.recordViolation('blocked_shortcut', 'medium', `Blocked shortcut: ${this.getKeyCombo(e)}`);
                        return false;
                    }
                }
            }
        });
        
        // Smart page refresh prevention (no auto-reload)
        this.preventAutoRefresh();
        
        // Mobile device blocking
        if (this.isMobile || this.isTablet) {
            this.blockMobileAccess();
            return;
        }
    }
    
    checkLinearMovement(points) {
        if (points.length < 3) return false;
        
        // Calculate if points form a straight line (bot-like behavior)
        const tolerance = 5; // pixels
        const first = points[0];
        const last = points[points.length - 1];
        
        for (let i = 1; i < points.length - 1; i++) {
            const point = points[i];
            const expected = {
                x: first.x + (last.x - first.x) * (i / (points.length - 1)),
                y: first.y + (last.y - first.y) * (i / (points.length - 1))
            };
            
            const distance = Math.sqrt(
                Math.pow(point.x - expected.x, 2) + Math.pow(point.y - expected.y, 2)
            );
            
            if (distance > tolerance) return false;
        }
        
        return true;
    }
    
    matchesCombo(event, combo) {
        if (combo.f12 && event.key === 'F12') return true;
        if (combo.ctrl && !event.ctrlKey) return false;
        if (combo.shift && !event.shiftKey) return false;
        if (combo.alt && !event.altKey) return false;
        if (combo.key && event.key.toLowerCase() !== combo.key.toLowerCase()) return false;
        return true;
    }
    
    getKeyCombo(event) {
        let combo = '';
        if (event.ctrlKey) combo += 'Ctrl+';
        if (event.shiftKey) combo += 'Shift+';
        if (event.altKey) combo += 'Alt+';
        combo += event.key;
        return combo;
    }
    
    async init() {
        console.log('🔒 Initializing Enhanced Proctoring System');
        await this.checkSystemRequirements();
        this.setupEventListeners();
        this.preventCheating();
    }
    
    async checkSystemRequirements() {
        // Check if HTTPS (required for camera)
        if (location.protocol !== 'https:' && location.hostname !== 'localhost') {
            this.showCriticalError('⚠️ HTTPS required for camera access. Please use the secure URL.');
            return false;
        }
        
        // Check for other tabs/apps before starting
        await this.scanForBackgroundActivities();
        
        // Check camera availability
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const cameras = devices.filter(device => device.kind === 'videoinput');
            if (cameras.length === 0) {
                this.showCriticalError('📷 No camera detected. Camera is required for this quiz.');
                return false;
            }
        } catch (error) {
            this.showCriticalError('📷 Camera access denied. Please allow camera access.');
            return false;
        }
        
        return true;
    }
    
    async scanForBackgroundActivities() {
        // Check for multiple tabs (Chrome API when available)
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.getRegistration();
                if (registration) {
                    // Send message to service worker to check tabs
                    registration.active?.postMessage({action: 'checkTabs'});
                }
            } catch (error) {
                console.warn('Could not check for multiple tabs');
            }
        }
        
        // Check window focus
        if (!document.hasFocus()) {
            this.preventStart = true;
            this.showWarning('⚠️ Please focus on this window and close all other applications before starting.');
        }
        
        // Check for developer tools
        if (this.isDevToolsOpen()) {
            this.preventStart = true;
            this.showCriticalError('⚠️ Developer tools detected. Please close developer tools.');
        }
    }
    
    async startLiveCameraMonitoring() {
        if (this.isActive) return;
        
        try {
            console.log('📷 Starting live camera monitoring (no storage)');
            
            // Get camera stream only (audio monitoring removed per user request)
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    frameRate: { ideal: 15 }  // Lower frame rate for performance
                }
            });
            
            // Audio monitoring removed per user request
            
            // Create video element for live analysis
            this.videoElement = document.createElement('video');
            this.videoElement.srcObject = this.mediaStream;
            this.videoElement.autoplay = true;
            this.videoElement.muted = true;
            this.videoElement.style.display = 'none'; // Hidden - for analysis only
            document.body.appendChild(this.videoElement);
            
            // Create canvas for real-time analysis (NO STORAGE)
            this.canvas = document.createElement('canvas');
            this.context = this.canvas.getContext('2d');
            this.canvas.style.display = 'none'; // Hidden
            document.body.appendChild(this.canvas);
            
            // Show live camera preview to user
            this.showLiveCameraPreview();
            
            // Start real-time analysis
            this.videoElement.onloadedmetadata = () => {
                this.canvas.width = this.videoElement.videoWidth;
                this.canvas.height = this.videoElement.videoHeight;
                this.startRealTimeAnalysis();
            };
            
            this.isActive = true;
            this.showNotification('✅ Live camera monitoring active', 'success');
            
        } catch (error) {
            console.error('Camera initialization failed:', error);
            this.showCriticalError('📷 Camera access failed. Please allow camera access and refresh.');
            throw error;
        }
    }
    
    showLiveCameraPreview() {
        // Create live camera preview for user
        const previewContainer = document.createElement('div');
        previewContainer.id = 'live-camera-preview';
        previewContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 200px;
            height: 150px;
            border: 2px solid #28a745;
            border-radius: 8px;
            background: #000;
            z-index: 1000;
            overflow: hidden;
        `;
        
        const previewVideo = document.createElement('video');
        previewVideo.srcObject = this.mediaStream;
        previewVideo.autoplay = true;
        previewVideo.muted = true;
        previewVideo.style.cssText = `
            width: 100%;
            height: 100%;
            object-fit: cover;
        `;
        
        const statusIndicator = document.createElement('div');
        statusIndicator.id = 'camera-status';
        statusIndicator.style.cssText = `
            position: absolute;
            bottom: 5px;
            left: 5px;
            background: rgba(40, 167, 69, 0.9);
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        `;
        statusIndicator.textContent = '🔴 LIVE';
        
        previewContainer.appendChild(previewVideo);
        previewContainer.appendChild(statusIndicator);
        document.body.appendChild(previewContainer);
    }
    
    startRealTimeAnalysis() {
        console.log('🔍 Starting real-time behavioral analysis');
        
        // Real-time face detection (NO STORAGE) - Less frequent
        this.faceDetectionInterval = setInterval(() => {
            this.analyzeLiveFrame();
        }, 3000); // Analyze every 3 seconds (reduced frequency)
        
        // Monitor camera stream status
        setInterval(() => {
            this.checkCameraStatus();
        }, 500);
    }
    
    analyzeLiveFrame() {
        if (!this.videoElement || this.videoElement.videoWidth === 0) return;
        
        try {
            // Draw current frame to canvas for analysis ONLY
            this.context.drawImage(this.videoElement, 0, 0, this.canvas.width, this.canvas.height);
            
            // Get image data for analysis (NOT STORED)
            const imageData = this.context.getImageData(0, 0, this.canvas.width, this.canvas.height);
            
            // Perform real-time analysis
            this.detectFacesInFrame(imageData);
            this.detectMovementPatterns(imageData);
            this.detectLookDirection(imageData);
            
            // Clear canvas immediately (NO STORAGE)
            this.context.clearRect(0, 0, this.canvas.width, this.canvas.height);
            
        } catch (error) {
            console.error('Frame analysis failed:', error);
        }
    }
    
    detectFacesInFrame(imageData) {
        // Simple face detection using brightness and color analysis
        const data = imageData.data;
        let facePixelCount = 0;
        let skinTonePixels = 0;
        
        // Scan for skin-tone colored pixels (simple face detection)
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            
            // Detect skin tones (rough approximation)
            if (r > 95 && g > 40 && b > 20 && 
                r > g && r > b && 
                Math.abs(r - g) > 15) {
                skinTonePixels++;
            }
        }
        
        const skinToneRatio = skinTonePixels / (data.length / 4);
        
        // Determine face count based on skin tone distribution (LESS SENSITIVE)
        let detectedFaces = 1; // Default: assume single person present
        if (skinToneRatio > 0.15) detectedFaces = 2;  // Multiple people (much higher threshold)
        if (skinToneRatio < 0.001) detectedFaces = 0; // No face/camera covered (very low threshold)
        
        this.processFaceDetection(detectedFaces);
    }
    
    processFaceDetection(faceCount) {
        const statusIndicator = document.getElementById('camera-status');
        
        if (faceCount === 0) {
            // No face detected or camera covered
            this.cameraHiddenCount++;
            this.updateCameraStatus('⚠️ CHECK CAMERA', '#ffc107');
            
            if (this.cameraHiddenCount > this.config.maxCameraHidden && !this.warningShown) {
                this.warningShown = true;
                this.showSingleWarning('⚠️ Please ensure your camera shows your face clearly');
                // Reset counter to give user time to adjust
                this.cameraHiddenCount = 0;
            }
        } else if (faceCount === 1) {
            // Normal - single person (reset all counters)
            this.cameraHiddenCount = 0;
            this.multiplePeopleCount = 0;
            this.warningShown = false; // Allow new warnings after normal detection
            this.updateCameraStatus('🔴 LIVE', '#28a745');
        } else if (faceCount >= 2) {
            // Multiple people detected
            this.multiplePeopleCount++;
            this.updateCameraStatus('⚠️ MULTIPLE PEOPLE', '#dc3545');
            
            if (this.multiplePeopleCount > this.config.maxMultiplePeople && !this.warningShown) {
                this.warningShown = true;
                this.showSingleWarning('⚠️ Multiple people detected. Please ensure you are alone during the quiz.');
                // Give user time to address the issue
                this.multiplePeopleCount = 0;
            }
        }
        
        this.lastFaceCount = faceCount;
    }
    
    updateCameraStatus(text, color) {
        const statusIndicator = document.getElementById('camera-status');
        if (statusIndicator) {
            statusIndicator.textContent = text;
            statusIndicator.style.backgroundColor = color;
        }
    }
    
    detectMovementPatterns(imageData) {
        // Detect if user is looking away from screen
        // This is a simplified version - in practice you'd use more sophisticated eye tracking
        const data = imageData.data;
        let centralBrightness = 0;
        let edgeBrightness = 0;
        
        const centerX = imageData.width / 2;
        const centerY = imageData.height / 2;
        const centerRegion = imageData.width / 6;
        
        // Sample center region and edge regions
        for (let y = 0; y < imageData.height; y++) {
            for (let x = 0; x < imageData.width; x++) {
                const index = (y * imageData.width + x) * 4;
                const brightness = (data[index] + data[index + 1] + data[index + 2]) / 3;
                
                const distFromCenter = Math.sqrt((x - centerX) ** 2 + (y - centerY) ** 2);
                
                if (distFromCenter < centerRegion) {
                    centralBrightness += brightness;
                } else if (distFromCenter > centerRegion * 2) {
                    edgeBrightness += brightness;
                }
            }
        }
        
        // Less sensitive look-away detection
        const lookAwayThreshold = this.config.lookAwayThreshold || 0.6;
        if (edgeBrightness > centralBrightness * (1 + lookAwayThreshold)) {
            this.lookAwayCount++;
            if (this.lookAwayCount > 10) { // More forgiving - need 10 consecutive detections
                this.recordViolation('looking_away', 'low', 'Extended time looking away from screen');
                this.lookAwayCount = 0;
            }
        } else {
            this.lookAwayCount = Math.max(0, this.lookAwayCount - 2); // Faster reset
        }
    }
    
    detectLookDirection(imageData) {
        // Additional look direction analysis
        // This would typically use more advanced computer vision
        // For now, we'll use motion detection
        
        if (this.previousFrameData) {
            const currentData = imageData.data;
            const prevData = this.previousFrameData;
            let motionScore = 0;
            
            for (let i = 0; i < currentData.length; i += 16) { // Sample every 4th pixel
                const diff = Math.abs(currentData[i] - prevData[i]);
                if (diff > 30) motionScore++;
            }
            
            // Too much motion might indicate looking around
            if (motionScore > 1000) {
                this.recordViolation('excessive_movement', 'low', 'Excessive movement detected');
            }
        }
        
        // Store current frame data for next comparison (NOT SAVED TO DISK)
        this.previousFrameData = new Uint8ClampedArray(imageData.data);
    }
    
    checkCameraStatus() {
        if (!this.mediaStream) return;
        
        const videoTrack = this.mediaStream.getVideoTracks()[0];
        if (videoTrack && !videoTrack.enabled) {
            this.recordViolation('camera_disabled', 'critical', 'Camera was disabled');
        }
        
        if (videoTrack && videoTrack.readyState === 'ended') {
            this.recordViolation('camera_disconnected', 'critical', 'Camera was disconnected');
        }
    }
    
    setupEventListeners() {
        // Tab switch detection
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.isActive) {
                this.tabSwitchCount++;
                this.recordViolation('tab_switch', 'high', `Tab switched away (${this.tabSwitchCount} times)`);
                
                if (this.tabSwitchCount >= this.config.maxTabSwitches) {
                    this.showCriticalWarning('⚠️ TAB SWITCHING DETECTED! Return to quiz immediately or it will be terminated.');
                }
            }
        });
        
        // REDUCED: Window focus detection (less sensitive)
        let focusLossCount = 0;
        window.addEventListener('blur', () => {
            if (this.isActive) {
                focusLossCount++;
                // Only record if user loses focus multiple times quickly
                if (focusLossCount > 3) {
                    this.recordViolation('frequent_focus_loss', 'low', 'Frequent window focus changes');
                    focusLossCount = 0; // Reset counter
                }
            }
        });
        
        // Reset focus loss count when user returns
        window.addEventListener('focus', () => {
            setTimeout(() => {
                focusLossCount = Math.max(0, focusLossCount - 1);
            }, 2000);
        });
        
        // Fullscreen exit detection
        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement && this.isActive && this.isFullscreenLocked) {
                this.recordViolation('fullscreen_exit', 'high', 'Exited fullscreen mode');
                this.enforceFullscreen();
            }
        });
        
        // Keyboard shortcuts blocking
        document.addEventListener('keydown', (e) => {
            if (this.isActive) {
                this.blockKeyboardShortcuts(e);
            }
        });
        
        // Right-click blocking
        document.addEventListener('contextmenu', (e) => {
            if (this.isActive) {
                e.preventDefault();
                this.recordViolation('right_click', 'low', 'Right-click attempted');
                return false;
            }
        });
        
        // Copy/paste blocking
        document.addEventListener('copy', (e) => {
            if (this.isActive) {
                e.preventDefault();
                this.recordViolation('copy_attempt', 'medium', 'Copy operation attempted');
            }
        });
        
        document.addEventListener('paste', (e) => {
            if (this.isActive) {
                e.preventDefault();
                this.recordViolation('paste_attempt', 'medium', 'Paste operation attempted');
            }
        });
        
        // Mobile specific - prevent home button
        if (this.isMobile || this.isTablet) {
            this.setupMobileLockdown();
        }
    }
    
    blockKeyboardShortcuts(event) {
        const blockedKeys = [
            'F12',           // Developer tools
            'F11',           // Fullscreen toggle
            'PrintScreen',   // Screenshot
            'Meta',          // Windows/Cmd key
        ];
        
        const blockedCombinations = [
            {ctrl: true, key: 'c'},          // Copy
            {ctrl: true, key: 'v'},          // Paste
            {ctrl: true, key: 'x'},          // Cut
            {ctrl: true, key: 'a'},          // Select all
            {ctrl: true, key: 's'},          // Save
            {ctrl: true, key: 'r'},          // Refresh
            {ctrl: true, key: 'w'},          // Close tab
            {ctrl: true, key: 't'},          // New tab
            {ctrl: true, key: 'n'},          // New window
            {ctrl: true, shift: true, key: 'i'}, // Dev tools
            {ctrl: true, shift: true, key: 'j'}, // Console
            {ctrl: true, shift: true, key: 'c'}, // Inspect
            {alt: true, key: 'Tab'},         // Alt+Tab
            {alt: true, key: 'F4'},          // Alt+F4
            {meta: true, key: 'Tab'},        // Cmd+Tab (Mac)
        ];
        
        // Check single keys
        if (blockedKeys.includes(event.key)) {
            event.preventDefault();
            this.recordViolation('blocked_shortcut', 'medium', `Blocked shortcut: ${event.key}`);
            return false;
        }
        
        // Check key combinations
        for (const combo of blockedCombinations) {
            let match = true;
            if (combo.ctrl && !event.ctrlKey) match = false;
            if (combo.alt && !event.altKey) match = false;
            if (combo.shift && !event.shiftKey) match = false;
            if (combo.meta && !event.metaKey) match = false;
            if (combo.key && event.key.toLowerCase() !== combo.key.toLowerCase()) match = false;
            
            if (match) {
                event.preventDefault();
                this.recordViolation('blocked_shortcut', 'medium', `Blocked combination: ${JSON.stringify(combo)}`);
                return false;
            }
        }
    }
    
    setupMobileLockdown() {
        // Prevent mobile app switching
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.isActive) {
                setTimeout(() => {
                    if (document.hidden) {
                        this.recordViolation('mobile_app_switch', 'critical', 'Switched to another app on mobile');
                    }
                }, 1000);
            }
        });
        
        // Prevent pinch zoom
        document.addEventListener('touchstart', (e) => {
            if (e.touches.length > 1) {
                e.preventDefault();
                this.recordViolation('pinch_zoom', 'low', 'Pinch zoom attempted');
            }
        }, {passive: false});
        
        // Prevent pull-to-refresh
        document.addEventListener('touchmove', (e) => {
            if (e.touches.length === 1 && window.scrollY === 0) {
                e.preventDefault();
            }
        }, {passive: false});
    }
    
    enforceFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.warn('Cannot enforce fullscreen:', err);
            });
        }
        this.isFullscreenLocked = true;
    }
    
    activateDoNotDisturbMode() {
        console.log('🔒 Activating Do Not Disturb Mode');
        
        // Hide all other UI elements
        const elementsToHide = ['nav', 'header', 'footer', '.sidebar', '.notification'];
        elementsToHide.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                el.style.display = 'none';
            });
        });
        
        // Create lockdown overlay
        const lockdownOverlay = document.createElement('div');
        lockdownOverlay.id = 'proctoring-lockdown';
        lockdownOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.95);
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-family: Arial, sans-serif;
        `;
        
        lockdownOverlay.innerHTML = `
            <div style="text-align: center;">
                <h2>🔒 PROCTORED QUIZ MODE</h2>
                <p>Quiz is locked in secure mode</p>
                <p>Do not attempt to exit or switch applications</p>
                <div id="lockdown-status">Waiting for quiz to start...</div>
            </div>
        `;
        
        document.body.appendChild(lockdownOverlay);
        
        // Enforce fullscreen
        this.enforceFullscreen();
        
        // Disable browser notifications
        if ('Notification' in window) {
            Notification.requestPermission().then(permission => {
                if (permission === 'granted') {
                    // Block notifications during quiz
                    this.originalNotification = window.Notification;
                    window.Notification = function() { return null; };
                }
            });
        }
    }
    
    recordViolation(type, severity, description) {
        const violation = {
            timestamp: new Date().toISOString(),
            type: type,
            severity: severity,
            description: description,
            attemptId: this.attemptId
        };
        
        this.violations.push(violation);
        this.violationLog.push(violation);
        
        console.warn(`🚨 VIOLATION [${severity.toUpperCase()}]: ${description}`);
        
        // Count violations by severity
        if (severity === 'critical') {
            this.criticalViolations++;
        } else if (severity === 'high') {
            this.warningCount++;
        }
        
        // Send to server in real-time
        this.sendViolationToServer(violation);
        
        // Show appropriate response
        this.handleViolationResponse(violation);
        
        // Check for termination
        if (this.shouldTerminateQuiz()) {
            this.terminateQuiz();
        }
    }
    
    handleViolationResponse(violation) {
        // Only show one warning per violation type
        if (this.warningShown) return;
        
        switch (violation.severity) {
            case 'critical':
                this.showCriticalWarning(`🚨 CRITICAL: ${violation.description}`);
                break;
            case 'high':
                this.showSingleWarning(`⚠️ WARNING: ${violation.description}`);
                break;
            case 'medium':
                this.showNotification(`⚠️ ${violation.description}`, 'warning');
                break;
            case 'low':
                console.log(`ℹ️ ${violation.description}`);
                break;
        }
    }
    
    showSingleWarning(message) {
        // REDUCED: Only show warning for important issues, no spam
        console.warn(message);
        
        // Only show visual warning for critical issues
        if (message.includes('CRITICAL') || message.includes('multiple people')) {
            const toast = document.createElement('div');
            toast.style.cssText = `
                position: fixed;
                top: 100px;
                right: 20px;
                background: #ffc107;
                color: #000;
                padding: 8px 15px;
                border-radius: 6px;
                z-index: 10000;
                font-weight: bold;
                max-width: 250px;
                border: 1px solid #ff9800;
                font-size: 14px;
            `;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            // Remove toast after 3 seconds (shorter)
            setTimeout(() => {
                if (toast.parentNode) toast.remove();
            }, 3000);
        }
    }
    
    shouldTerminateQuiz() {
        return this.criticalViolations >= 1 || 
               (this.warningCount + this.criticalViolations) >= this.config.terminateOnViolations ||
               this.tabSwitchCount >= 3 ||
               this.multiplePeopleCount >= 3;
    }
    
    terminateQuiz() {
        if (this.isTerminated) return;
        
        this.isTerminated = true;
        console.error('🚨 QUIZ TERMINATED DUE TO VIOLATIONS');
        
        // Stop all monitoring
        this.stopMonitoring();
        
        // Show termination screen
        this.showTerminationScreen();
        
        // Submit quiz automatically
        if (typeof submitQuizAutomatically === 'function') {
            submitQuizAutomatically('terminated_violations');
        }
        
        // Redirect after delay
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 5000);
    }
    
    showTerminationScreen() {
        const terminationScreen = document.createElement('div');
        terminationScreen.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #dc3545, #6f1319);
            color: white;
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: Arial, sans-serif;
            text-align: center;
        `;
        
        terminationScreen.innerHTML = `
            <div>
                <h1>🚨 QUIZ TERMINATED</h1>
                <h3>Multiple violations detected</h3>
                <p>Your quiz session has been terminated due to:</p>
                <ul style="text-align: left; margin: 20px 0;">
                    ${this.violationLog.map(v => `<li>${v.description}</li>`).join('')}
                </ul>
                <p>This incident has been reported to your instructor.</p>
                <p>Redirecting in 5 seconds...</p>
            </div>
        `;
        
        document.body.appendChild(terminationScreen);
    }
    
    async sendViolationToServer(violation) {
        // Enhanced violation server communication with immediate malpractice handling
        try {
            const violationData = {
                attemptId: this.attemptId,
                type: violation.type,
                severity: violation.severity,
                description: violation.description,
                timestamp: new Date().toISOString(),
                details: {
                    ...violation.details,
                    userAgent: navigator.userAgent,
                    isMobile: this.isMobile,
                    isTablet: this.isTablet
                }
            };

            const response = await fetch('/api/proctoring/violation', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(violationData)
            });

            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}`);
            }

            const result = await response.json();
            
            // Handle immediate malpractice termination
            if (result.should_terminate || this.shouldTriggerImmediateMalpractice(violation)) {
                await this.handleImmediateMalpractice(violation, result);
            }

            return result;
        } catch (error) {
            console.error('Failed to send violation to server:', error);
            
            // Store violation locally if server fails (for recovery)
            this.storeViolationLocally(violation);
            
            // Still trigger immediate malpractice for critical violations
            if (this.shouldTriggerImmediateMalpractice(violation)) {
                await this.handleImmediateMalpractice(violation, null);
            }
        }
    }
    
    stopMonitoring() {
        console.log('🚫 Stopping all monitoring systems');
        this.isActive = false;
        
        // Deactivate strong enforcement
        this.deactivateStrongEnforcement();
        
        // Stop video monitoring
        if (this.faceDetectionInterval) {
            clearInterval(this.faceDetectionInterval);
            this.faceDetectionInterval = null;
        }
        
        // Audio monitoring removed per user request
        
        // Stop all media tracks
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => {
                try {
                    track.stop();
                    console.log(`✅ Stopped ${track.kind} track`);
                } catch (error) {
                    console.warn(`Failed to stop ${track.kind} track:`, error);
                }
            });
            this.mediaStream = null;
        }
        
        // Clear audio analysis data
        this.analyser = null;
        this.dataArray = null;
        this.baselineNoiseLevel = null;
        this.environmentAnalysis = {
            isQuiet: true,
            hasConversation: false,
            noiseLevelHistory: [],
            lastVoiceActivity: 0
        };
        
        // Remove UI elements
        this.removeMonitoringUI();
        
        // Remove hidden elements
        if (this.videoElement) {
            this.videoElement.remove();
            this.videoElement = null;
        }
        if (this.canvas) {
            this.canvas.remove();
            this.canvas = null;
        }
        
        console.log('✅ All monitoring systems stopped and cleaned up');
    }
    
    removeMonitoringUI() {
        // Remove camera preview
        const preview = document.getElementById('live-camera-preview');
        if (preview) {
            preview.remove();
            console.log('Removed camera preview');
        }
        
        // Audio monitoring removed per user request
        
        // Remove privacy notice if still visible
        const privacyNotice = document.getElementById('audio-privacy-notice');
        if (privacyNotice) {
            privacyNotice.remove();
            console.log('Removed privacy notice');
        }
        
        // Reset proctoring status
        const statusAlert = document.getElementById('proctoring-status-alert');
        if (statusAlert) {
            statusAlert.className = 'alert alert-secondary';
            statusAlert.innerHTML = '<i class="fas fa-shield"></i> <strong>MONITORING STOPPED</strong><br><small>All monitoring systems have been disabled</small>';
        }
    }
    
    async startAudioEnvironmentAnalysis() {
        // Audio monitoring removed per user request
        console.log('Audio monitoring has been disabled');
        return;
    }
    
    
    
    
    
    
    
    
    
    
    
    analyzeEnvironmentQuality() {
        // Overall environment quality assessment
        const history = this.environmentAnalysis.noiseLevelHistory;
        if (history.length < 10) return;
        
        const recentSamples = history.slice(-10);
        const averageRecent = recentSamples.reduce((sum, val) => sum + val, 0) / recentSamples.length;
        const variability = this.calculateVariability(recentSamples);
        
        // Environment is considered good if:
        // 1. Noise level is consistent (low variability)
        // 2. Average level is close to baseline
        // 3. No recent voice activity
        
        const isEnvironmentGood = (
            variability < 15 && // Low variability
            this.baselineNoiseLevel && 
            averageRecent < this.baselineNoiseLevel * 1.3 && // Close to baseline
            !this.environmentAnalysis.hasConversation
        );
        
        // Update proctoring status based on environment quality
        const statusAlert = document.getElementById('proctoring-status-alert');
        if (statusAlert && this.audioMonitoringActive) {
            if (isEnvironmentGood) {
                statusAlert.className = 'alert alert-success';
                statusAlert.innerHTML = '<i class="fas fa-shield-check"></i> <strong>SECURE ENVIRONMENT</strong><br><small>Camera • Audio • Quiet environment detected</small>';
            } else if (this.environmentAnalysis.hasConversation) {
                statusAlert.className = 'alert alert-warning';
                statusAlert.innerHTML = '<i class="fas fa-exclamation-triangle"></i> <strong>VOICE DETECTED</strong><br><small>Conversation or voice activity in background</small>';
            } else if (!this.environmentAnalysis.isQuiet) {
                statusAlert.className = 'alert alert-warning';
                statusAlert.innerHTML = '<i class="fas fa-volume-up"></i> <strong>NOISY ENVIRONMENT</strong><br><small>Background noise above acceptable levels</small>';
            }
        }
    }
    
    calculateVariability(samples) {
        if (samples.length < 2) return 0;
        
        const mean = samples.reduce((sum, val) => sum + val, 0) / samples.length;
        const variance = samples.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / samples.length;
        return Math.sqrt(variance);
    }
    
    showAudioPrivacyNotice() {
        // Show privacy notice for audio monitoring
        const notice = document.createElement('div');
        notice.id = 'audio-privacy-notice';
        notice.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            max-width: 280px;
            background: rgba(23, 162, 184, 0.95);
            color: white;
            padding: 12px;
            border-radius: 8px;
            font-size: 11px;
            z-index: 1002;
            border: 1px solid #17a2b8;
        `;
        
        notice.innerHTML = `
            <div style="font-weight: bold; margin-bottom: 6px;">🔒 Audio Privacy Notice</div>
            <div style="margin-bottom: 8px;">Audio is being analyzed in real-time for:</div>
            <ul style="margin: 0; padding-left: 16px; font-size: 10px;">
                <li>Background noise levels</li>
                <li>Voice activity detection</li>
                <li>Environment quality</li>
            </ul>
            <div style="margin-top: 8px; font-weight: bold; font-size: 10px;">NO AUDIO IS RECORDED OR STORED</div>
            <button onclick="this.parentElement.remove()" style="
                background: #fff;
                border: none;
                color: #17a2b8;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 10px;
                cursor: pointer;
                margin-top: 8px;
            ">Got it</button>
        `;
        
        document.body.appendChild(notice);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (notice.parentElement) notice.remove();
        }, 10000);
    }
    
    handleAudioSetupFailure(error) {
        console.error('Audio monitoring setup failed:', error);
        
        // Determine error type and provide appropriate feedback
        let userMessage = '⚠️ Audio monitoring setup failed.';
        let severity = 'medium';
        
        if (error.message.includes('denied') || error.message.includes('not supported')) {
            userMessage = '🎤 Microphone access denied. Audio monitoring disabled.';
            severity = 'high';
        } else if (error.message.includes('in use')) {
            userMessage = '🎤 Microphone is in use by another application.';
            severity = 'high';
        } else if (error.message.includes('context')) {
            userMessage = '🎤 Audio context failed. Please refresh and try again.';
            severity = 'medium';
        }
        
        // Record violation with appropriate severity
        this.recordViolation('audio_setup_failed', severity, error.message);
        
        // Show user-friendly message
        this.showSingleWarning(userMessage);
        
        // Set audio monitoring as failed but don't block the quiz
        this.audioMonitoringActive = false;
        this.audioSetupFailed = true;
        
        // Show fallback indicator
        this.showAudioFailureIndicator();
        
        // Continue with visual monitoring only
        console.warn('Continuing with visual monitoring only');
    }
    
    showAudioFailureIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'audio-monitoring-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            left: 20px;
            width: 120px;
            height: 40px;
            background: rgba(220, 53, 69, 0.9);
            color: white;
            border-radius: 8px;
            padding: 8px;
            z-index: 1001;
            font-size: 11px;
            text-align: center;
            border: 2px solid #dc3545;
        `;
        
        indicator.innerHTML = `
            <div>🎤 AUDIO DISABLED</div>
            <div style="font-size: 9px; margin-top: 4px;">Visual only</div>
        `;
        
        document.body.appendChild(indicator);
    }
    
    // Utility methods
    isDevToolsOpen() {
        const threshold = 160;
        return window.outerHeight - window.innerHeight > threshold ||
               window.outerWidth - window.innerWidth > threshold;
    }
    
    getCSRFToken() {
        const token = document.querySelector('meta[name="csrf-token"]');
        return token ? token.getAttribute('content') : '';
    }

    // ============== MOBILE DETECTION & BLOCKING ==============
    
    detectMobileDevice() {
        // Comprehensive mobile detection
        const userAgent = navigator.userAgent.toLowerCase();
        const mobileKeywords = ['mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone'];
        
        // Check user agent
        const isMobileUA = mobileKeywords.some(keyword => userAgent.includes(keyword));
        
        // Check touch capabilities
        const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        
        // Check screen size
        const smallScreen = window.screen.width <= 768 || window.screen.height <= 768;
        
        // Check CSS media queries
        const isMobileMedia = window.matchMedia('(pointer: coarse)').matches;
        
        return isMobileUA || (hasTouch && smallScreen) || isMobileMedia;
    }

    detectTabletDevice() {
        const userAgent = navigator.userAgent.toLowerCase();
        const tabletKeywords = ['tablet', 'ipad'];
        
        const isTabletUA = tabletKeywords.some(keyword => userAgent.includes(keyword));
        const largeTouch = 'ontouchstart' in window && window.screen.width > 768;
        
        return isTabletUA || largeTouch;
    }

    getDeviceInfo() {
        return {
            userAgent: navigator.userAgent,
            screenWidth: window.screen.width,
            screenHeight: window.screen.height,
            maxTouchPoints: navigator.maxTouchPoints || 0,
            orientation: screen.orientation?.type || 'unknown',
            pixelRatio: window.devicePixelRatio || 1
        };
    }

    blockMobileAccess() {
        console.error('🚫 Mobile device detected - Quiz access blocked');
        
        // Create blocking overlay
        const blockingOverlay = document.createElement('div');
        blockingOverlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #dc3545, #6f1319);
            color: white;
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: Arial, sans-serif;
            text-align: center;
        `;
        
        blockingOverlay.innerHTML = `
            <div style="max-width: 400px; padding: 20px;">
                <h1>📱 Mobile Access Blocked</h1>
                <h3>Quiz access restricted to desktop computers only</h3>
                <p>For security and proctoring requirements, this quiz must be taken on a desktop or laptop computer.</p>
                <p><strong>Device detected:</strong> ${this.isMobile ? 'Mobile Phone' : 'Tablet'}</p>
                <hr style="margin: 20px 0; opacity: 0.3;">
                <p style="font-size: 14px;">Please use a desktop computer and try again.</p>
                <p style="font-size: 12px; opacity: 0.7;">This restriction ensures exam integrity and proper proctoring.</p>
            </div>
        `;
        
        document.body.appendChild(blockingOverlay);
        
        // Record device violation
        this.recordViolation('mobile_device_blocked', 'critical', 
            `Mobile device access blocked: ${this.deviceInfo.userAgent}`);
        
        // Prevent any further initialization
        this.preventStart = true;
        return;
    }

    // ============== AUTO-REFRESH PREVENTION ==============
    
    preventAutoRefresh() {
        // Add reload-loop protection
        const reloadAttempts = parseInt(sessionStorage.getItem('quiz_reload_attempts') || '0');
        
        if (reloadAttempts >= 3) {
            console.error('🚫 Multiple reload attempts detected - blocking further reloads');
            this.showCriticalError('Too many page reload attempts detected. Please contact your instructor.');
            return;
        }
        
        // Increment reload counter
        sessionStorage.setItem('quiz_reload_attempts', (reloadAttempts + 1).toString());
        
        // Smart beforeunload handling
        window.addEventListener('beforeunload', (e) => {
            if (this.isActive && !this.isTerminated) {
                // Record the attempt but don't auto-refresh
                this.recordViolation('page_unload_attempt', 'medium', 'User attempted to leave quiz page');
                
                // Show warning but allow user choice
                const message = 'Are you sure you want to leave the quiz? This may be recorded as a violation.';
                e.returnValue = message;
                return message;
            }
        });
        
        // Clear reload counter on successful quiz completion
        window.addEventListener('quiz:completed', () => {
            sessionStorage.removeItem('quiz_reload_attempts');
        });
    }

    // ============== IMMEDIATE MALPRACTICE HANDLING ==============
    
    shouldTriggerImmediateMalpractice(violation) {
        // Define immediate malpractice triggers
        const criticalViolations = [
            'mobile_device_blocked',
            'multiple_people_detected',
            'camera_disabled',
            'sustained_conversation',
            'cheating_software_detected',
            'identity_verification_failed'
        ];
        
        // Immediate triggers
        if (criticalViolations.includes(violation.type)) {
            return true;
        }
        
        // Count-based triggers
        const highSeverityCount = this.violationLog.filter(v => v.severity === 'high' || v.severity === 'critical').length;
        const tabSwitchCount = this.violationLog.filter(v => v.type.includes('tab_switch')).length;
        const lookAwayCount = this.violationLog.filter(v => v.type.includes('look_away')).length;
        
        return (
            highSeverityCount >= 2 ||          // 2 high/critical violations
            tabSwitchCount >= 3 ||             // 3 tab switches
            lookAwayCount >= 5 ||              // 5 look-away instances
            this.violationLog.length >= 8      // 8 total violations
        );
    }

    async handleImmediateMalpractice(violation, serverResponse) {
        console.error('🚨 IMMEDIATE MALPRACTICE DETECTED:', violation);
        
        this.isTerminated = true;
        this.criticalViolations++;
        
        // Mark user as malpractice immediately
        try {
            await this.markAsMalpractice(violation);
            await this.notifyHostAndParticipants(violation);
        } catch (error) {
            console.error('Failed to send immediate malpractice notifications:', error);
        }
        
        // Show immediate termination screen
        this.showMalpracticeTerminationScreen(violation);
        
        // Auto-submit quiz if possible
        setTimeout(() => {
            this.forceQuizSubmission();
        }, 3000);
    }

    async markAsMalpractice(violation) {
        const malpracticeData = {
            attemptId: this.attemptId,
            quizId: this.quizId,
            violation: violation,
            timestamp: new Date().toISOString(),
            action: 'immediate_termination',
            severity: 'critical'
        };

        await fetch('/api/proctoring/mark-malpractice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(malpracticeData)
        });
    }

    async notifyHostAndParticipants(violation) {
        // Notify host immediately
        const hostNotification = {
            type: 'immediate_malpractice',
            attemptId: this.attemptId,
            quizId: this.quizId,
            violation: violation,
            message: `🚨 IMMEDIATE MALPRACTICE: ${violation.description}`,
            severity: 'critical',
            student: {
                name: document.querySelector('[data-username]')?.dataset.username || 'Unknown',
                email: document.querySelector('[data-email]')?.dataset.email || 'Unknown'
            }
        };

        await fetch('/api/proctoring/notify-violation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(hostNotification)
        });

        // Notify other participants if required
        const participantNotification = {
            type: 'malpractice_alert',
            quizId: this.quizId,
            message: '⚠️ A participant has been terminated for malpractice during this quiz session.'
        };

        await fetch('/api/proctoring/notify-participants', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(participantNotification)
        });
    }

    showMalpracticeTerminationScreen(violation) {
        const terminationScreen = document.createElement('div');
        terminationScreen.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #dc3545, #6f1319);
            color: white;
            z-index: 999999;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: Arial, sans-serif;
            text-align: center;
        `;
        
        terminationScreen.innerHTML = `
            <div style="max-width: 500px; padding: 30px;">
                <h1>🚨 MALPRACTICE DETECTED</h1>
                <h2>Quiz Terminated Immediately</h2>
                <div style="background: rgba(255,255,255,0.1); padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3>Violation: ${violation.description}</h3>
                    <p><strong>Severity:</strong> ${violation.severity.toUpperCase()}</p>
                    <p><strong>Time:</strong> ${new Date().toLocaleString()}</p>
                </div>
                <p><strong>Actions Taken:</strong></p>
                <ul style="text-align: left; margin: 20px 0;">
                    <li>✅ Host notified immediately</li>
                    <li>✅ Incident logged in system</li>
                    <li>✅ Quiz attempt marked as malpractice</li>
                    <li>✅ Academic integrity office alerted</li>
                </ul>
                <p style="color: #ffcccc;"><strong>This incident will be reviewed by your instructor and academic integrity committee.</strong></p>
                <p>Redirecting to dashboard in <span id="countdown">10</span> seconds...</p>
            </div>
        `;
        
        document.body.appendChild(terminationScreen);
        
        // Countdown timer
        let seconds = 10;
        const countdownElement = terminationScreen.querySelector('#countdown');
        const timer = setInterval(() => {
            seconds--;
            countdownElement.textContent = seconds;
            if (seconds <= 0) {
                clearInterval(timer);
                window.location.href = '/dashboard';
            }
        }, 1000);
    }

    forceQuizSubmission() {
        // Force submit the quiz with malpractice flag
        const submitData = {
            action: 'force_submit',
            reason: 'malpractice_detected',
            timestamp: new Date().toISOString()
        };

        fetch('/api/quiz/force-submit', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(submitData)
        }).catch(error => {
            console.error('Failed to force submit quiz:', error);
        });
    }

    storeViolationLocally(violation) {
        // Store violation locally for recovery if server fails
        const localViolations = JSON.parse(localStorage.getItem('quiz_violations') || '[]');
        localViolations.push({
            ...violation,
            timestamp: new Date().toISOString(),
            attemptId: this.attemptId,
            stored_locally: true
        });
        localStorage.setItem('quiz_violations', JSON.stringify(localViolations));
    }

    // ============== ENHANCED BACKGROUND NOISE & SPEECH DETECTION ==============
    
    async setupEnhancedAudioMonitoring() {
        console.log('🎤 Setting up enhanced audio monitoring with speech detection');
        
        try {
            // Request enhanced audio permissions
            this.audioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: false,      // Disable to detect background voices
                    noiseSuppression: false,      // Disable to catch all sounds
                    autoGainControl: false,       // Disable to get raw levels
                    sampleRate: 44100,           // High quality for speech analysis
                    channelCount: 1              // Mono for processing efficiency
                }
            });

            // Create enhanced audio context for analysis
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
                sampleRate: 44100
            });

            const source = this.audioContext.createMediaStreamSource(this.audioStream);
            this.analyser = this.audioContext.createAnalyser();
            
            // Enhanced analyzer settings for speech detection
            this.analyser.fftSize = 2048;
            this.analyser.smoothingTimeConstant = 0.3;
            this.analyser.minDecibels = -90;
            this.analyser.maxDecibels = -10;
            
            source.connect(this.analyser);

            this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
            this.audioMonitoringActive = true;

            // Calibrate baseline environment for 8 seconds
            await this.calibrateEnvironmentBaseline();
            
            // Start continuous enhanced audio analysis
            this.startEnhancedAudioAnalysis();
            
            console.log('✅ Enhanced audio monitoring with speech detection activated');
            this.showAudioMonitoringIndicator();

        } catch (error) {
            console.error('Enhanced audio monitoring setup failed:', error);
            this.handleAudioSetupFailure(error);
        }
    }

    async calibrateEnvironmentBaseline() {
        console.log('📊 Calibrating environment baseline for speech detection...');
        
        const calibrationSamples = [];
        const calibrationDuration = 8000; // 8 seconds
        const sampleInterval = 100; // Sample every 100ms
        
        return new Promise((resolve) => {
            const startTime = Date.now();
            
            const calibrationInterval = setInterval(() => {
                if (!this.audioMonitoringActive) {
                    clearInterval(calibrationInterval);
                    resolve();
                    return;
                }
                
                this.analyser.getByteFrequencyData(this.dataArray);
                
                // Calculate multiple audio metrics for baseline
                const rms = this.calculateRMS(this.dataArray);
                const spectralCentroid = this.calculateSpectralCentroid(this.dataArray);
                const spectralRolloff = this.calculateSpectralRolloff(this.dataArray);
                
                calibrationSamples.push({
                    rms,
                    spectralCentroid,
                    spectralRolloff,
                    timestamp: Date.now()
                });
                
                if (Date.now() - startTime >= calibrationDuration) {
                    clearInterval(calibrationInterval);
                    
                    // Calculate baseline metrics
                    this.baselineNoiseLevel = this.calculateBaselineMetrics(calibrationSamples);
                    this.environmentAnalysis.baselineCalibrated = true;
                    
                    console.log('✅ Environment baseline calibrated:', this.baselineNoiseLevel);
                    resolve();
                }
            }, sampleInterval);
        });
    }

    calculateBaselineMetrics(samples) {
        const rmsValues = samples.map(s => s.rms);
        const centroidValues = samples.map(s => s.spectralCentroid);
        const rolloffValues = samples.map(s => s.spectralRolloff);
        
        return {
            avgRMS: rmsValues.reduce((a, b) => a + b, 0) / rmsValues.length,
            maxRMS: Math.max(...rmsValues),
            avgSpectralCentroid: centroidValues.reduce((a, b) => a + b, 0) / centroidValues.length,
            avgSpectralRolloff: rolloffValues.reduce((a, b) => a + b, 0) / rolloffValues.length,
            variabilityRMS: this.calculateVariance(rmsValues)
        };
    }

    calculateVariance(values) {
        const mean = values.reduce((a, b) => a + b, 0) / values.length;
        return values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / values.length;
    }

    startEnhancedAudioAnalysis() {
        const analysisInterval = 250; // Analyze every 250ms for speech detection
        
        this.audioAnalysisInterval = setInterval(() => {
            if (!this.audioMonitoringActive || !this.environmentAnalysis.baselineCalibrated) return;
            
            this.analyser.getByteFrequencyData(this.dataArray);
            
            // Calculate current audio metrics
            const currentMetrics = {
                rms: this.calculateRMS(this.dataArray),
                spectralCentroid: this.calculateSpectralCentroid(this.dataArray),
                spectralRolloff: this.calculateSpectralRolloff(this.dataArray),
                timestamp: Date.now()
            };
            
            // Analyze for speech patterns
            this.analyzeForSpeechPatterns(currentMetrics);
            
            // Check for conversation detection
            this.checkForConversation(currentMetrics);
            
            // Update environment analysis
            this.updateEnvironmentAnalysis(currentMetrics);
            
        }, analysisInterval);
    }

    calculateRMS(dataArray) {
        let sum = 0;
        for (let i = 0; i < dataArray.length; i++) {
            sum += dataArray[i] * dataArray[i];
        }
        return Math.sqrt(sum / dataArray.length);
    }

    calculateSpectralCentroid(dataArray) {
        let numerator = 0;
        let denominator = 0;
        
        for (let i = 0; i < dataArray.length; i++) {
            numerator += i * dataArray[i];
            denominator += dataArray[i];
        }
        
        return denominator > 0 ? numerator / denominator : 0;
    }

    calculateSpectralRolloff(dataArray) {
        const totalEnergy = dataArray.reduce((sum, val) => sum + val, 0);
        const threshold = totalEnergy * 0.85; // 85% energy threshold
        
        let cumulativeEnergy = 0;
        for (let i = 0; i < dataArray.length; i++) {
            cumulativeEnergy += dataArray[i];
            if (cumulativeEnergy >= threshold) {
                return i;
            }
        }
        return dataArray.length - 1;
    }

    analyzeForSpeechPatterns(currentMetrics) {
        if (!this.baselineNoiseLevel) return;
        
        const baseline = this.baselineNoiseLevel;
        
        // Speech detection criteria
        const rmsThreshold = baseline.avgRMS + (baseline.variabilityRMS * 2.5);
        const centroidThreshold = baseline.avgSpectralCentroid * 1.3; // Human speech increases centroid
        
        const isSpeechLikely = 
            currentMetrics.rms > rmsThreshold &&
            currentMetrics.spectralCentroid > centroidThreshold &&
            currentMetrics.spectralRolloff > baseline.avgSpectralRolloff * 1.2;
        
        if (isSpeechLikely) {
            this.detectSpeechActivity(currentMetrics);
        } else {
            this.resetSpeechDetection();
        }
    }

    detectSpeechActivity(metrics) {
        const now = Date.now();
        
        // Add to speech segments
        this.environmentAnalysis.speechSegments.push({
            timestamp: now,
            rms: metrics.rms,
            spectralCentroid: metrics.spectralCentroid,
            confidence: this.calculateSpeechConfidence(metrics)
        });
        
        // Keep only recent speech segments (last 10 seconds)
        this.environmentAnalysis.speechSegments = this.environmentAnalysis.speechSegments
            .filter(segment => now - segment.timestamp < 10000);
        
        this.voiceDetectionCount++;
        this.environmentAnalysis.lastVoiceActivity = now;
        
        // Check for sustained speech (potential conversation)
        const recentSpeech = this.environmentAnalysis.speechSegments
            .filter(segment => now - segment.timestamp < 3000); // Last 3 seconds
        
        if (recentSpeech.length >= 8) { // 8 detections in 3 seconds = sustained speech
            this.sustainedSpeechCount++;
            
            if (this.sustainedSpeechCount >= 3) { // 3 sustained periods = conversation
                this.handleConversationDetection();
            }
            
            console.log('🔄 Sustained speech pattern detected');
            this.recordViolation('sustained_speech', 'medium', 
                `Sustained speech detected (${recentSpeech.length} segments in 3s)`);
        }
        
        // Log regular voice activity
        if (this.voiceDetectionCount % 5 === 0) {
            console.log(`ℹ️ Voice activity detected (${this.voiceDetectionCount} times)`);
            this.recordViolation('voice_activity', 'low', 
                `Voice activity detected (count: ${this.voiceDetectionCount})`);
        }
    }

    calculateSpeechConfidence(metrics) {
        if (!this.baselineNoiseLevel) return 0;
        
        const baseline = this.baselineNoiseLevel;
        
        // Calculate confidence based on how much the signal deviates from baseline
        const rmsScore = Math.min((metrics.rms / (baseline.avgRMS + baseline.variabilityRMS)) - 1, 1);
        const centroidScore = Math.min((metrics.spectralCentroid / baseline.avgSpectralCentroid) - 1, 1);
        const rolloffScore = Math.min((metrics.spectralRolloff / baseline.avgSpectralRolloff) - 1, 1);
        
        return (rmsScore + centroidScore + rolloffScore) / 3;
    }

    handleConversationDetection() {
        if (this.conversationDetected) return; // Already detected
        
        this.conversationDetected = true;
        this.environmentAnalysis.hasConversation = true;
        this.environmentAnalysis.conversationStartTime = Date.now();
        
        console.error('🚨 CONVERSATION DETECTED - Potential malpractice');
        
        // Record as critical violation for immediate malpractice handling
        this.recordViolation('sustained_conversation', 'critical', 
            'Sustained conversation detected - multiple speech patterns identified');
        
        // Show immediate warning
        this.showCriticalWarning('⚠️ CONVERSATION DETECTED: Sustained speech patterns indicate possible conversation during the quiz');
    }

    resetSpeechDetection() {
        // Reset speech detection if no activity for 2 seconds
        const now = Date.now();
        if (now - this.environmentAnalysis.lastVoiceActivity > 2000) {
            this.sustainedSpeechCount = 0;
        }
    }

    checkForConversation(currentMetrics) {
        // Additional conversation detection logic
        const recentSegments = this.environmentAnalysis.speechSegments
            .filter(segment => Date.now() - segment.timestamp < 5000);
        
        if (recentSegments.length >= 15) { // Many speech segments in 5 seconds
            const avgConfidence = recentSegments.reduce((sum, seg) => sum + seg.confidence, 0) / recentSegments.length;
            
            if (avgConfidence > 0.6) { // High confidence speech
                this.handleConversationDetection();
            }
        }
    }

    updateEnvironmentAnalysis(currentMetrics) {
        // Update noise level history
        this.environmentAnalysis.noiseLevelHistory.push({
            level: currentMetrics.rms,
            timestamp: Date.now()
        });
        
        // Keep only recent history (last 30 seconds)
        this.environmentAnalysis.noiseLevelHistory = this.environmentAnalysis.noiseLevelHistory
            .filter(entry => Date.now() - entry.timestamp < 30000);
        
        // Update quiet status
        const recentLevels = this.environmentAnalysis.noiseLevelHistory.slice(-10);
        const avgRecentLevel = recentLevels.reduce((sum, entry) => sum + entry.level, 0) / recentLevels.length;
        
        this.environmentAnalysis.isQuiet = avgRecentLevel <= (this.baselineNoiseLevel?.avgRMS * 1.5 || 20);
    }

    showAudioMonitoringIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'enhanced-audio-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            width: 140px;
            height: 50px;
            background: rgba(40, 167, 69, 0.9);
            color: white;
            border-radius: 8px;
            padding: 8px;
            z-index: 1001;
            font-size: 11px;
            text-align: center;
            border: 2px solid #28a745;
        `;
        
        indicator.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100%;">
                <div>
                    <div>🎤 ENHANCED AUDIO</div>
                    <div style="font-size: 9px; margin-top: 2px;">Speech Detection Active</div>
                </div>
            </div>
        `;
        
        document.body.appendChild(indicator);
        
        // Update indicator based on audio activity
        setInterval(() => {
            if (this.conversationDetected) {
                indicator.style.background = 'rgba(220, 53, 69, 0.9)';
                indicator.style.borderColor = '#dc3545';
                indicator.innerHTML = `
                    <div style="display: flex; align-items: center; justify-content: center; height: 100%;">
                        <div>
                            <div>🚨 CONVERSATION</div>
                            <div style="font-size: 9px; margin-top: 2px;">Multiple Voices</div>
                        </div>
                    </div>
                `;
            } else if (this.voiceDetectionCount > 0) {
                indicator.style.background = 'rgba(255, 193, 7, 0.9)';
                indicator.style.borderColor = '#ffc107';
                indicator.innerHTML = `
                    <div style="display: flex; align-items: center; justify-content: center; height: 100%;">
                        <div>
                            <div>🔊 VOICE DETECTED</div>
                            <div style="font-size: 9px; margin-top: 2px;">Count: ${this.voiceDetectionCount}</div>
                        </div>
                    </div>
                `;
            }
        }, 1000);
    }
    
    showNotification(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);
        // You can implement toast notifications here
    }
    
    showWarning(message) {
        console.warn(message);
        // You can implement warning modals here
    }
    
    showCriticalWarning(message) {
        console.error(message);
        // REMOVED: No alert popups, only console logging
        this.showSingleWarning(message);
    }
    
    showCriticalError(message) {
        console.error(message);
        // REMOVED: No alert popups, only console logging
        this.showSingleWarning(message);
    }
    
    // ============== SMART SECURITY MONITORING ==============
    
    activateStrongEnforcement() {
        console.log('🔐 Activating smart security monitoring');
        this.enforcementActive = true;
        
        try {
            // Request fullscreen with graceful fallback
            this.requestFullscreenGracefully();
            
            // Monitor tab switching and focus changes
            this.monitorTabSwitching();
            
            // Detect screenshot attempts (what's detectable)
            this.detectScreenshotAttempts();
            
            // Monitor window state changes
            this.monitorWindowState();
            
            // Monitor system shortcuts
            this.monitorSystemShortcuts();
            
            // Essential keyboard monitoring (not blocking normal use)
            this.setupEssentialKeyboardMonitoring();
            
            // Smart focus monitoring
            this.startSmartFocusMonitoring();
            
            console.log('✅ Smart security monitoring activated');
        } catch (error) {
            console.error('Security monitoring setup failed:', error);
            this.handleSecuritySetupFailure(error);
        }
    }
    
    deactivateStrongEnforcement() {
        if (!this.enforcementActive) return;
        
        console.log('🔓 Deactivating security monitoring');
        this.enforcementActive = false;
        this.blockingActive = false;
        
        try {
            // Remove event listeners with error handling
            this.blockedEvents.forEach(({ element, event, handler }) => {
                try {
                    element.removeEventListener(event, handler);
                } catch (error) {
                    console.warn('Failed to remove event listener:', error);
                }
            });
            this.blockedEvents = [];
            
            // Remove keyboard monitor
            if (this.keyboardBlocker) {
                try {
                    document.removeEventListener('keydown', this.keyboardBlocker);
                    this.keyboardBlocker = null;
                } catch (error) {
                    console.warn('Failed to remove keyboard monitor:', error);
                }
            }
            
            // Exit fullscreen gracefully
            if (document.fullscreenElement) {
                document.exitFullscreen().catch(error => {
                    console.warn('Failed to exit fullscreen:', error);
                });
            }
            
            console.log('✅ Security monitoring deactivated');
        } catch (error) {
            console.error('Error during security monitoring deactivation:', error);
        }
    }
    
    requestFullscreenGracefully() {
        // Request fullscreen with proper error handling
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.warn('Fullscreen request failed:', err);
                this.showSingleWarning('⚠️ Fullscreen mode recommended for enhanced security');
                // Don't record as violation - user may have legitimate reasons
            });
        }
        
        // Monitor fullscreen changes (detection only)
        const fullscreenMonitor = () => {
            if (this.enforcementActive && !document.fullscreenElement) {
                console.log('📊 Fullscreen exited - monitoring only');
                this.recordViolation('fullscreen_exited', 'medium', 'Exited fullscreen mode');
                // Don't try to force back - just detect and record
            }
        };
        
        document.addEventListener('fullscreenchange', fullscreenMonitor);
        this.blockedEvents.push({ element: document, event: 'fullscreenchange', handler: fullscreenMonitor });
        
        // Monitor escape key usage (for awareness, not blocking)
        const escapeMonitor = (e) => {
            if (e.key === 'Escape' && this.enforcementActive && document.fullscreenElement) {
                // Just record the attempt, don't block it
                this.recordViolation('escape_pressed', 'low', 'Escape key pressed in fullscreen mode');
                console.log('📊 Escape key usage detected');
            }
        };
        
        document.addEventListener('keydown', escapeMonitor);
        this.blockedEvents.push({ element: document, event: 'keydown', handler: escapeMonitor });
    }
    
    monitorTabSwitching() {
        // Monitor tab switching (detection, not blocking)
        const tabSwitchMonitor = (e) => {
            if (!this.enforcementActive) return;
            
            // Monitor certain key combinations (but don't block normal browser use)
            if (e.altKey && e.key === 'Tab') {
                this.tabSwitchCount++;
                this.recordViolation('alt_tab_detected', 'medium', 'Alt+Tab key combination detected');
                console.log('📊 Alt+Tab detected');
                // Don't prevent - OS handles this, we just detect
            }
        };
        
        // Smart visibility change detection
        const visibilityHandler = () => {
            if (document.hidden && this.enforcementActive) {
                this.tabSwitchCount++;
                this.recordViolation('tab_switch_detected', 'high', `Tab/window switched away (${this.tabSwitchCount} times)`);
                
                // Show warning but don't try to force focus (can be annoying)
                if (this.tabSwitchCount === 1) {
                    this.showSingleWarning('⚠️ Please stay focused on the quiz window');
                } else if (this.tabSwitchCount === 5) {
                    this.showSingleWarning('⚠️ Multiple tab switches detected - please remain focused');
                } else if (this.tabSwitchCount >= 10) {
                    this.showCriticalWarning('⚠️ Excessive tab switching detected - quiz integrity at risk');
                }
            }
        };
        
        // Focus monitoring (less aggressive)
        const focusHandler = () => {
            if (this.enforcementActive) {
                this.lastFocusTime = Date.now();
                // Don't automatically try to regain focus - let user control their browser
            }
        };
        
        document.addEventListener('keydown', tabSwitchMonitor);
        document.addEventListener('visibilitychange', visibilityHandler);
        window.addEventListener('blur', focusHandler);
        
        this.blockedEvents.push(
            { element: document, event: 'keydown', handler: tabSwitchMonitor },
            { element: document, event: 'visibilitychange', handler: visibilityHandler },
            { element: window, event: 'blur', handler: focusHandler }
        );
    }
    
    detectScreenshotAttempts() {
        const screenshotDetector = (e) => {
            if (!this.enforcementActive) return;
            
            // Detect screenshot-related key presses (what we can reasonably detect)
            const suspiciousKeys = [
                'PrintScreen',
                'F12', // Dev tools (can interfere with screenshots)
            ];
            
            // Detect some browser-level screenshot shortcuts
            if (suspiciousKeys.includes(e.key) || 
                (e.ctrlKey && e.shiftKey && e.key === 'S')) { // Browser screenshot tools
                
                this.screenshotAttempts++;
                
                this.recordViolation('screenshot_attempt_detected', 'medium', `Screenshot key detected: ${e.key}`);
                console.log('📊 Screenshot-related key detected:', e.key);
                
                if (this.screenshotAttempts === 1) {
                    this.showSingleWarning('⚠️ Screenshot attempts are monitored and logged');
                } else if (this.screenshotAttempts >= 5) {
                    this.showSingleWarning('⚠️ Multiple screenshot attempts detected');
                }
                
                // Note: We don't preventDefault() because browsers can't actually block OS-level screenshots
                // We just detect and log for policy enforcement
            }
        };
        
        // Monitor right-click (but allow it - just log for awareness)
        const contextMonitor = (e) => {
            if (this.enforcementActive) {
                this.recordViolation('right_click_detected', 'low', 'Right-click menu accessed');
                console.log('📊 Right-click detected');
                // Don't block - just monitor
            }
        };
        
        document.addEventListener('keydown', screenshotDetector);
        document.addEventListener('contextmenu', contextMonitor);
        
        this.blockedEvents.push(
            { element: document, event: 'keydown', handler: screenshotDetector },
            { element: document, event: 'contextmenu', handler: contextMonitor }
        );
    }
    
    monitorWindowState() {
        // Monitor window state changes (detection only)
        const windowStateMonitor = () => {
            if (this.enforcementActive) {
                // Detect very small windows (might indicate minimization or hiding)
                if (window.outerHeight <= 100 || window.outerWidth <= 100) {
                    this.minimizeAttempts++;
                    this.recordViolation('window_resized_small', 'medium', `Window resized very small (${this.minimizeAttempts} times)`);
                    console.log('📊 Small window size detected');
                }
                
                // Detect if window is hidden (visibility API)
                if (document.visibilityState === 'hidden') {
                    this.recordViolation('window_hidden', 'medium', 'Window became hidden');
                    console.log('📊 Window hidden detected');
                }
            }
        };
        
        // Monitor window state periodically
        setInterval(windowStateMonitor, 1000); // Less frequent monitoring
        
        // Monitor minimize-related shortcuts (detect, not block)
        const minimizeShortcutMonitor = (e) => {
            if (!this.enforcementActive) return;
            
            // Monitor Windows+D (show desktop), Windows+M (minimize all)
            if (e.metaKey && (e.key === 'd' || e.key === 'm')) {
                this.recordViolation('minimize_shortcut_detected', 'low', `Minimize shortcut detected: ${this.getKeyCombo(e)}`);
                console.log('📊 Minimize shortcut detected:', this.getKeyCombo(e));
                // Don't block - just detect and log
            }
        };
        
        document.addEventListener('keydown', minimizeShortcutMonitor);
        this.blockedEvents.push({ element: document, event: 'keydown', handler: minimizeShortcutMonitor });
    }
    
    monitorSystemShortcuts() {
        // Monitor system-level shortcuts (realistic detection)
        const systemShortcutMonitor = (e) => {
            if (!this.enforcementActive) return;
            
            // Monitor common system shortcuts (we can detect the key press, but can't block OS handling)
            const systemShortcuts = [
                { ctrl: true, shift: true, key: 'Escape' }, // Task Manager
                { ctrl: true, alt: true, key: 'Delete' }, // Ctrl+Alt+Del
                { meta: true, key: 'r' },         // Windows + R (Run)
                { meta: true, key: 'l' },         // Windows + L (Lock)
            ];
            
            for (const combo of systemShortcuts) {
                if (this.matchesKeyCombo(e, combo)) {
                    this.recordViolation('system_shortcut_detected', 'high', `System shortcut detected: ${this.getKeyCombo(e)}`);
                    console.log('📊 System shortcut detected:', this.getKeyCombo(e));
                    
                    // Note: We can't actually block these at OS level, just detect and log
                    this.showSingleWarning('⚠️ System shortcut detected and logged');
                }
            }
        };
        
        document.addEventListener('keydown', systemShortcutMonitor);
        this.blockedEvents.push({ element: document, event: 'keydown', handler: systemShortcutMonitor });
    }
    
    setupEssentialKeyboardMonitoring() {
        this.keyboardBlocker = (e) => {
            if (!this.enforcementActive) return;
            
            // Only block truly suspicious shortcuts that clearly indicate cheating attempts
            const suspiciousShortcuts = [
                // Developer tools (these can enable cheating)
                { ctrl: true, shift: true, key: 'I' },
                { ctrl: true, shift: true, key: 'J' },
                { ctrl: true, shift: true, key: 'C' },
                { ctrl: true, key: 'U' },
                { key: 'F12' },
                
                // Navigation that clearly violates quiz rules
                { ctrl: true, key: 'T' },         // New tab
                { ctrl: true, key: 'N' },         // New window
                { ctrl: true, key: 'W' },         // Close tab
                { ctrl: true, shift: true, key: 'T' }, // Reopen tab
                
                // Print (to prevent printing questions)
                { ctrl: true, key: 'P' },
            ];
            
            // Monitor but don't block normal usage shortcuts
            const monitoredShortcuts = [
                { ctrl: true, key: 'A' },         // Select all
                { ctrl: true, key: 'C' },         // Copy
                { ctrl: true, key: 'V' },         // Paste
                { ctrl: true, key: 'X' },         // Cut
                { ctrl: true, key: 'S' },         // Save
                { ctrl: true, key: 'R' },         // Refresh
                { key: 'F5' },                    // Refresh
            ];
            
            // Block only the truly suspicious ones
            for (const combo of suspiciousShortcuts) {
                if (this.matchesKeyCombo(e, combo)) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.recordViolation('suspicious_shortcut_blocked', 'high', `Blocked: ${this.getKeyCombo(e)}`);
                    console.log('🚫 Blocked suspicious shortcut:', this.getKeyCombo(e));
                    return false;
                }
            }
            
            // Just monitor normal shortcuts (don't block them)
            for (const combo of monitoredShortcuts) {
                if (this.matchesKeyCombo(e, combo)) {
                    this.recordViolation('shortcut_used', 'low', `Used: ${this.getKeyCombo(e)}`);
                    console.log('📊 Monitored shortcut used:', this.getKeyCombo(e));
                    // Don't prevent - just log for awareness
                }
            }
        };
        
        document.addEventListener('keydown', this.keyboardBlocker);
    }
    
    startSmartFocusMonitoring() {
        // Smart focus monitoring (less aggressive)
        setInterval(() => {
            if (this.enforcementActive) {
                const timeSinceLastFocus = Date.now() - this.lastFocusTime;
                
                // More reasonable focus loss detection
                if (timeSinceLastFocus > 30000 && document.hidden) { // 30 seconds instead of 2
                    this.recordViolation('extended_focus_loss', 'medium', 'Window out of focus for extended period');
                    console.log('📊 Extended focus loss detected');
                    
                    // Don't automatically try to regain focus - let user control their browser
                    
                    // Show gentle reminder instead of aggressive warning
                    if (timeSinceLastFocus > 60000) { // 1 minute
                        this.showSingleWarning('⚠️ Please return to the quiz window when ready');
                    }
                }
            }
        }, 5000); // Check every 5 seconds instead of every second
        
        // Update focus time on user interaction
        const updateFocus = () => {
            if (this.enforcementActive) {
                this.lastFocusTime = Date.now();
            }
        };
        
        // Monitor focus-related events
        ['focus', 'click', 'keydown'].forEach(event => {
            document.addEventListener(event, updateFocus);
            this.blockedEvents.push({ element: document, event, handler: updateFocus });
        });
        
        // Monitor visibility changes
        const visibilityFocusMonitor = () => {
            if (this.enforcementActive && !document.hidden) {
                this.lastFocusTime = Date.now(); // Reset timer when window becomes visible
            }
        };
        
        document.addEventListener('visibilitychange', visibilityFocusMonitor);
        this.blockedEvents.push({ element: document, event: 'visibilitychange', handler: visibilityFocusMonitor });
    }
    
    matchesKeyCombo(event, combo) {
        return (
            (combo.ctrl === undefined || event.ctrlKey === combo.ctrl) &&
            (combo.alt === undefined || event.altKey === combo.alt) &&
            (combo.shift === undefined || event.shiftKey === combo.shift) &&
            (combo.meta === undefined || event.metaKey === combo.meta) &&
            (combo.key === undefined || event.key.toLowerCase() === combo.key.toLowerCase())
        );
    }
    
    getKeyCombo(event) {
        const parts = [];
        if (event.ctrlKey) parts.push('Ctrl');
        if (event.altKey) parts.push('Alt');
        if (event.shiftKey) parts.push('Shift');
        if (event.metaKey) parts.push('Meta');
        if (event.key) parts.push(event.key);
        return parts.join('+');
    }
    
    handleSecuritySetupFailure(error) {
        console.error('Security monitoring setup failed:', error);
        
        // Determine appropriate user feedback based on error type
        let userMessage = '⚠️ Some security monitoring features could not be enabled.';
        
        if (error.message && error.message.includes('fullscreen')) {
            userMessage = '⚠️ Fullscreen mode could not be activated. Please enable manually if needed.';
        } else if (error.message && error.message.includes('permission')) {
            userMessage = '⚠️ Some monitoring features require additional permissions.';
        } else if (error.message && error.message.includes('not supported')) {
            userMessage = '⚠️ Your browser has limited security monitoring support.';
        }
        
        // Show user-friendly message
        this.showSingleWarning(userMessage);
        
        // Record the failure for administrative review
        this.recordViolation('security_setup_failed', 'medium', `Security setup error: ${error.message}`);
        
        // Continue with basic monitoring even if some features fail
        console.log('Continuing with available security monitoring features...');
    }
}

// Global instance
window.EnhancedProctoringSystem = EnhancedProctoringSystem;