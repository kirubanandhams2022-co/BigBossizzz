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
        
        // Audio Environment Analysis
        this.audioStream = null;
        this.audioContext = null;
        this.analyser = null;
        this.dataArray = null;
        this.audioMonitoringActive = false;
        this.baselineNoiseLevel = null;
        this.voiceDetectionCount = 0;
        this.suspiciousSoundCount = 0;
        this.environmentAnalysis = {
            isQuiet: true,
            hasConversation: false,
            noiseLevelHistory: [],
            lastVoiceActivity: 0
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
        
        // Mobile/Desktop detection
        this.isMobile = /Mobi|Android/i.test(navigator.userAgent);
        this.isTablet = /Tablet|iPad/i.test(navigator.userAgent);
        
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
        
        // Disable page refresh attempts (silent prevention)
        window.addEventListener('beforeunload', (e) => {
            if (this.isActive && !this.isTerminated) {
                // Only prevent accidental refresh, don't record violation
                e.preventDefault();
                e.returnValue = '';
                return '';
            }
        });
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
            
            // Get camera and audio streams
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    frameRate: { ideal: 15 }  // Lower frame rate for performance
                },
                audio: {
                    echoCancellation: false,  // We want to hear background noise
                    noiseSuppression: false,  // We want to analyze all sounds
                    autoGainControl: false    // Maintain original audio levels
                }
            });
            
            // Start audio monitoring
            await this.startAudioEnvironmentAnalysis();
            
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
    
    sendViolationToServer(violation) {
        // Send violation to server for logging
        fetch('/api/proctoring/violation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify(violation)
        }).catch(error => {
            console.error('Failed to send violation to server:', error);
        });
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
        
        // Stop audio monitoring
        this.audioMonitoringActive = false;
        if (this.audioAnalysisInterval) {
            clearInterval(this.audioAnalysisInterval);
            this.audioAnalysisInterval = null;
        }
        
        // Properly dispose of audio context
        if (this.audioContext) {
            try {
                if (this.audioContext.state !== 'closed') {
                    this.audioContext.close().then(() => {
                        console.log('✅ Audio context closed successfully');
                    }).catch(err => {
                        console.warn('Audio context close warning:', err);
                    });
                }
            } catch (error) {
                console.warn('Failed to close audio context:', error);
            }
            this.audioContext = null;
        }
        
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
        
        // Remove audio indicator
        const audioIndicator = document.getElementById('audio-monitoring-indicator');
        if (audioIndicator) {
            audioIndicator.remove();
            console.log('Removed audio monitoring indicator');
        }
        
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
        try {
            console.log('🎤 Starting background noise and environment analysis');
            
            // Check browser compatibility for AudioContext
            const AudioContextClass = window.AudioContext || window.webkitAudioContext || window.mozAudioContext;
            if (!AudioContextClass) {
                throw new Error('AudioContext not supported in this browser');
            }
            
            // Create audio context with better error handling
            try {
                this.audioContext = new AudioContextClass();
            } catch (contextError) {
                console.error('Failed to create audio context:', contextError);
                throw new Error('Audio context creation failed - microphone may be in use');
            }
            
            // Check if audio context is running
            if (this.audioContext.state === 'suspended') {
                try {
                    await this.audioContext.resume();
                } catch (resumeError) {
                    console.warn('Failed to resume audio context:', resumeError);
                }
            }
            
            // Get audio track from media stream with validation
            const audioTrack = this.mediaStream.getAudioTracks()[0];
            if (!audioTrack) {
                throw new Error('No audio track available - microphone access may be denied');
            }
            
            // Check if audio track is enabled and active
            if (!audioTrack.enabled) {
                throw new Error('Audio track is disabled');
            }
            
            if (audioTrack.readyState !== 'live') {
                throw new Error('Audio track is not active');
            }
            
            // Create audio source with error handling
            let source;
            try {
                source = this.audioContext.createMediaStreamSource(new MediaStream([audioTrack]));
            } catch (sourceError) {
                console.error('Failed to create media stream source:', sourceError);
                throw new Error('Audio source creation failed');
            }
            
            // Create analyser with optimized settings
            this.analyser = this.audioContext.createAnalyser();
            this.analyser.fftSize = 1024; // Reduced for better performance
            this.analyser.smoothingTimeConstant = 0.8;
            this.analyser.minDecibels = -90;
            this.analyser.maxDecibels = -10;
            
            // Connect source to analyser
            source.connect(this.analyser);
            
            // Create data array for frequency analysis
            this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
            
            // Show audio monitoring indicator
            this.showAudioMonitoringIndicator();
            
            // Show privacy notice for audio monitoring
            this.showAudioPrivacyNotice();
            
            // Start baseline noise calibration
            await this.calibrateBaselineNoise();
            
            // Start continuous audio monitoring with error handling
            this.audioMonitoringActive = true;
            this.startContinuousAudioAnalysis();
            
            console.log('✅ Audio environment analysis active');
            
        } catch (error) {
            console.error('Audio monitoring failed:', error);
            this.handleAudioSetupFailure(error);
        }
    }
    
    showAudioMonitoringIndicator() {
        // Create audio monitoring indicator
        const indicator = document.createElement('div');
        indicator.id = 'audio-monitoring-indicator';
        indicator.style.cssText = `
            position: fixed;
            top: 20px;
            left: 20px;
            width: 120px;
            height: 60px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border-radius: 8px;
            padding: 8px;
            z-index: 1001;
            font-size: 12px;
            text-align: center;
            border: 2px solid #17a2b8;
        `;
        
        indicator.innerHTML = `
            <div style="margin-bottom: 4px;">🎤 AUDIO MONITOR</div>
            <div id="noise-level-bar" style="width: 100%; height: 8px; background: #333; border-radius: 4px; overflow: hidden;">
                <div id="noise-level-fill" style="width: 0%; height: 100%; background: linear-gradient(90deg, #28a745, #ffc107, #dc3545); transition: width 0.1s;"></div>
            </div>
            <div id="environment-status" style="font-size: 10px; margin-top: 4px;">Calibrating...</div>
        `;
        
        document.body.appendChild(indicator);
    }
    
    async calibrateBaselineNoise() {
        console.log('🔧 Calibrating baseline noise level...');
        
        return new Promise(resolve => {
            const samples = [];
            const sampleDuration = 3000; // 3 seconds
            const sampleInterval = 100; // Every 100ms
            
            const sampleNoise = () => {
                this.analyser.getByteFrequencyData(this.dataArray);
                const averageVolume = this.dataArray.reduce((sum, value) => sum + value, 0) / this.dataArray.length;
                samples.push(averageVolume);
                
                if (samples.length < sampleDuration / sampleInterval) {
                    setTimeout(sampleNoise, sampleInterval);
                } else {
                    // Calculate baseline as average of samples
                    this.baselineNoiseLevel = samples.reduce((sum, sample) => sum + sample, 0) / samples.length;
                    console.log(`📊 Baseline noise level: ${this.baselineNoiseLevel.toFixed(2)}`);
                    
                    // Update status
                    const statusElement = document.getElementById('environment-status');
                    if (statusElement) {
                        statusElement.textContent = 'Active';
                    }
                    
                    resolve();
                }
            };
            
            sampleNoise();
        });
    }
    
    startContinuousAudioAnalysis() {
        if (!this.audioMonitoringActive) return;
        
        // Analyze audio every 500ms (optimized from 200ms for better performance)
        this.audioAnalysisInterval = setInterval(() => {
            if (!this.audioMonitoringActive) {
                clearInterval(this.audioAnalysisInterval);
                return;
            }
            
            try {
                this.analyzeAudioEnvironment();
            } catch (error) {
                console.error('Audio analysis error:', error);
                // Don't stop monitoring for minor errors
            }
        }, 500);
    }
    
    analyzeAudioEnvironment() {
        if (!this.analyser || !this.dataArray) return;
        
        // Get current audio data
        this.analyser.getByteFrequencyData(this.dataArray);
        
        // Calculate current noise level
        const currentNoiseLevel = this.dataArray.reduce((sum, value) => sum + value, 0) / this.dataArray.length;
        
        // Update noise level history
        this.environmentAnalysis.noiseLevelHistory.push(currentNoiseLevel);
        if (this.environmentAnalysis.noiseLevelHistory.length > 50) {
            this.environmentAnalysis.noiseLevelHistory.shift(); // Keep last 50 samples (10 seconds)
        }
        
        // Update visual indicator
        this.updateAudioIndicator(currentNoiseLevel);
        
        // Analyze for different types of audio events
        this.detectBackgroundNoise(currentNoiseLevel);
        this.detectVoiceActivity();
        this.detectSuspiciousSounds();
        this.analyzeEnvironmentQuality();
    }
    
    updateAudioIndicator(currentLevel) {
        const fillElement = document.getElementById('noise-level-fill');
        const statusElement = document.getElementById('environment-status');
        
        if (fillElement && this.baselineNoiseLevel) {
            // Calculate percentage based on baseline (0-200% range)
            const percentage = Math.min((currentLevel / this.baselineNoiseLevel) * 50, 100);
            fillElement.style.width = `${percentage}%`;
        }
        
        if (statusElement) {
            if (this.environmentAnalysis.hasConversation) {
                statusElement.textContent = '⚠️ Conversation';
                statusElement.style.color = '#ffc107';
            } else if (!this.environmentAnalysis.isQuiet) {
                statusElement.textContent = '🔊 Noisy';
                statusElement.style.color = '#dc3545';
            } else {
                statusElement.textContent = '✅ Quiet';
                statusElement.style.color = '#28a745';
            }
        }
    }
    
    detectBackgroundNoise(currentLevel) {
        if (!this.baselineNoiseLevel) return;
        
        // Consider environment noisy if consistently above 150% of baseline
        const noiseThreshold = this.baselineNoiseLevel * 1.5;
        
        if (currentLevel > noiseThreshold) {
            this.suspiciousSoundCount++;
            
            // Trigger violation if noisy for extended period
            if (this.suspiciousSoundCount > 25) { // 5 seconds of noise
                this.environmentAnalysis.isQuiet = false;
                
                if (!this.warningShown) {
                    this.recordViolation('noisy_environment', 'medium', 'Environment is too noisy for testing');
                    this.showSingleWarning('⚠️ Please ensure a quiet environment for testing');
                    this.warningShown = true;
                }
                
                this.suspiciousSoundCount = 0; // Reset to prevent spam
            }
        } else {
            // Reset if noise level returns to normal
            if (this.suspiciousSoundCount > 0) {
                this.suspiciousSoundCount = Math.max(0, this.suspiciousSoundCount - 2);
            }
            if (currentLevel < noiseThreshold * 0.8) {
                this.environmentAnalysis.isQuiet = true;
                this.warningShown = false; // Allow new warnings
            }
        }
    }
    
    detectVoiceActivity() {
        if (!this.dataArray) return;
        
        // Voice typically appears in 300-3000 Hz range
        // FFT bins: bin = frequency * fftSize / sampleRate
        const sampleRate = this.audioContext.sampleRate;
        const binSize = sampleRate / this.analyser.fftSize;
        
        const voiceStartBin = Math.floor(300 / binSize);
        const voiceEndBin = Math.floor(3000 / binSize);
        
        // Calculate voice band energy
        let voiceEnergy = 0;
        for (let i = voiceStartBin; i < voiceEndBin && i < this.dataArray.length; i++) {
            voiceEnergy += this.dataArray[i];
        }
        voiceEnergy /= (voiceEndBin - voiceStartBin);
        
        // Detect voice if energy in voice band is significantly higher than baseline
        const voiceThreshold = this.baselineNoiseLevel ? this.baselineNoiseLevel * 2 : 50;
        
        if (voiceEnergy > voiceThreshold) {
            this.voiceDetectionCount++;
            this.environmentAnalysis.lastVoiceActivity = Date.now();
            
            // Detect conversation if voice activity persists
            if (this.voiceDetectionCount > 15) { // 3 seconds of voice
                this.environmentAnalysis.hasConversation = true;
                
                if (!this.warningShown) {
                    this.recordViolation('voice_detected', 'high', 'Voice or conversation detected in background');
                    this.showSingleWarning('⚠️ Voice activity detected. Please ensure you are alone.');
                    this.warningShown = true;
                }
                
                this.voiceDetectionCount = 0; // Reset counter
            }
        } else {
            // Reset if no voice detected
            if (this.voiceDetectionCount > 0) {
                this.voiceDetectionCount = Math.max(0, this.voiceDetectionCount - 1);
            }
            
            // Consider conversation ended if no voice for 5 seconds
            if (Date.now() - this.environmentAnalysis.lastVoiceActivity > 5000) {
                this.environmentAnalysis.hasConversation = false;
                this.warningShown = false; // Allow new warnings
            }
        }
    }
    
    detectSuspiciousSounds() {
        if (!this.dataArray) return;
        
        // High frequency sounds (phone rings, notifications, typing)
        const highFreqStart = Math.floor(2000 / (this.audioContext.sampleRate / this.analyser.fftSize));
        const highFreqEnd = Math.floor(8000 / (this.audioContext.sampleRate / this.analyser.fftSize));
        
        let highFreqEnergy = 0;
        for (let i = highFreqStart; i < highFreqEnd && i < this.dataArray.length; i++) {
            highFreqEnergy += this.dataArray[i];
        }
        highFreqEnergy /= (highFreqEnd - highFreqStart);
        
        // Sudden spikes in high frequency could indicate phone rings, notifications
        const spikeThreshold = this.baselineNoiseLevel ? this.baselineNoiseLevel * 3 : 80;
        
        if (highFreqEnergy > spikeThreshold) {
            console.log('🔊 Suspicious high-frequency sound detected');
            this.recordViolation('suspicious_sound', 'low', 'Suspicious high-frequency sound detected (phone, notification, etc.)');
        }
        
        // Repetitive sounds (typing, paper rustling)
        // This is a simplified version - in practice, you'd use more sophisticated pattern recognition
        this.detectRepetitiveSounds();
    }
    
    detectRepetitiveSounds() {
        // Simplified repetitive sound detection
        const history = this.environmentAnalysis.noiseLevelHistory;
        if (history.length < 20) return;
        
        // Check for repetitive patterns in the last 4 seconds
        const recentSamples = history.slice(-20);
        let patterns = 0;
        
        for (let i = 0; i < recentSamples.length - 5; i++) {
            const pattern = recentSamples.slice(i, i + 3);
            const nextPattern = recentSamples.slice(i + 3, i + 6);
            
            // Check if patterns are similar (indicating repetitive sounds like typing)
            if (this.arraysAreSimilar(pattern, nextPattern)) {
                patterns++;
            }
        }
        
        if (patterns > 3) {
            console.log('🔄 Repetitive sound pattern detected (possible typing/paper rustling)');
            this.recordViolation('repetitive_sound', 'low', 'Repetitive sound pattern detected');
        }
    }
    
    arraysAreSimilar(arr1, arr2, tolerance = 10) {
        if (arr1.length !== arr2.length) return false;
        
        for (let i = 0; i < arr1.length; i++) {
            if (Math.abs(arr1[i] - arr2[i]) > tolerance) {
                return false;
            }
        }
        return true;
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
    
    // ============== STRONG SECURITY ENFORCEMENT ==============
    
    activateStrongEnforcement() {
        console.log('🔐 Activating aggressive security enforcement');
        this.enforcementActive = true;
        
        // Force immediate fullscreen and lock it
        this.enforceAggressiveFullscreen();
        
        // Block all tab switching attempts
        this.blockTabSwitching();
        
        // Block screenshot attempts
        this.blockScreenshots();
        
        // Detect and prevent window minimization
        this.preventWindowMinimization();
        
        // Block background app access
        this.blockBackgroundApps();
        
        // Enhanced keyboard blocking
        this.enhancedKeyboardBlocking();
        
        // Continuous focus monitoring
        this.startAggressiveFocusMonitoring();
        
        console.log('✅ Aggressive security enforcement activated');
    }
    
    deactivateStrongEnforcement() {
        if (!this.enforcementActive) return;
        
        console.log('🔓 Deactivating security enforcement');
        this.enforcementActive = false;
        this.blockingActive = false;
        
        // Remove event listeners
        this.blockedEvents.forEach(({ element, event, handler }) => {
            element.removeEventListener(event, handler);
        });
        this.blockedEvents = [];
        
        // Remove keyboard blocker
        if (this.keyboardBlocker) {
            document.removeEventListener('keydown', this.keyboardBlocker);
            this.keyboardBlocker = null;
        }
        
        // Exit fullscreen
        if (document.fullscreenElement) {
            document.exitFullscreen().catch(() => {});
        }
        
        console.log('✅ Security enforcement deactivated');
    }
    
    enforceAggressiveFullscreen() {
        // Force fullscreen immediately and lock it
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.warn('Failed to enter fullscreen:', err);
                this.recordViolation('fullscreen_failed', 'high', 'Failed to enter fullscreen mode');
            });
        }
        
        // Continuously monitor and re-enforce fullscreen
        const fullscreenEnforcer = () => {
            if (this.enforcementActive && !document.fullscreenElement) {
                console.warn('🚨 Fullscreen exit detected - re-enforcing');
                document.documentElement.requestFullscreen().catch(() => {
                    this.recordViolation('fullscreen_violation', 'critical', 'Repeatedly exited fullscreen mode');
                });
            }
        };
        
        // Check every 100ms for fullscreen violations
        setInterval(fullscreenEnforcer, 100);
        
        // Block escape key
        const escapeBlocker = (e) => {
            if (e.key === 'Escape' && this.enforcementActive) {
                e.preventDefault();
                e.stopPropagation();
                this.recordViolation('escape_blocked', 'medium', 'Attempted to exit fullscreen with Escape key');
                return false;
            }
        };
        
        document.addEventListener('keydown', escapeBlocker);
        this.blockedEvents.push({ element: document, event: 'keydown', handler: escapeBlocker });
    }
    
    blockTabSwitching() {
        // Aggressive tab switch prevention
        const blockTabSwitch = (e) => {
            if (!this.enforcementActive) return;
            
            // Block Alt+Tab, Ctrl+Tab, Windows key, etc.
            if (e.altKey || e.metaKey || e.key === 'Tab') {
                e.preventDefault();
                e.stopPropagation();
                this.tabSwitchCount++;
                this.recordViolation('tab_switch_blocked', 'high', 'Attempted to switch tabs/applications');
                this.showSingleWarning('⚠️ Tab switching is blocked during the quiz!');
                return false;
            }
        };
        
        // Enhanced visibility change detection
        const visibilityHandler = () => {
            if (document.hidden && this.enforcementActive) {
                this.tabSwitchCount++;
                this.recordViolation('tab_switch_detected', 'critical', `Tab switched away (${this.tabSwitchCount} times)`);
                
                // Immediately try to regain focus
                window.focus();
                
                if (this.tabSwitchCount >= 2) {
                    this.showCriticalWarning('🚨 QUIZ TERMINATION WARNING: Return to quiz immediately!');
                }
                
                if (this.tabSwitchCount >= 3) {
                    this.terminateQuiz();
                }
            }
        };
        
        // Focus loss detection
        const focusHandler = () => {
            if (this.enforcementActive) {
                this.lastFocusTime = Date.now();
                // Try to regain focus immediately
                setTimeout(() => window.focus(), 10);
            }
        };
        
        document.addEventListener('keydown', blockTabSwitch);
        document.addEventListener('visibilitychange', visibilityHandler);
        window.addEventListener('blur', focusHandler);
        
        this.blockedEvents.push(
            { element: document, event: 'keydown', handler: blockTabSwitch },
            { element: document, event: 'visibilitychange', handler: visibilityHandler },
            { element: window, event: 'blur', handler: focusHandler }
        );
    }
    
    blockScreenshots() {
        const screenshotBlocker = (e) => {
            if (!this.enforcementActive) return;
            
            // Block Print Screen, Windows+S, etc.
            const screenshotKeys = [
                'PrintScreen',
                'F12', // Dev tools
                'F10', // Context menu
                'F11'  // Fullscreen toggle
            ];
            
            if (screenshotKeys.includes(e.key) || 
                (e.metaKey && e.key === 's') || // Windows+S
                (e.altKey && e.key === 'PrintScreen') || // Alt+PrintScreen
                (e.ctrlKey && e.shiftKey && e.key === 'S')) { // Ctrl+Shift+S
                
                e.preventDefault();
                e.stopPropagation();
                this.screenshotAttempts++;
                
                this.recordViolation('screenshot_blocked', 'high', `Screenshot attempt blocked (${this.screenshotAttempts} times)`);
                this.showSingleWarning('⚠️ Screenshots are strictly prohibited!');
                
                if (this.screenshotAttempts >= 3) {
                    this.recordViolation('multiple_screenshot_attempts', 'critical', 'Multiple screenshot attempts detected');
                    this.showCriticalWarning('🚨 Multiple screenshot attempts detected! Quiz may be terminated.');
                }
                
                return false;
            }
        };
        
        // Block context menu (right-click)
        const contextBlocker = (e) => {
            if (this.enforcementActive) {
                e.preventDefault();
                this.recordViolation('context_menu_blocked', 'low', 'Right-click menu blocked');
                return false;
            }
        };
        
        document.addEventListener('keydown', screenshotBlocker);
        document.addEventListener('contextmenu', contextBlocker);
        
        this.blockedEvents.push(
            { element: document, event: 'keydown', handler: screenshotBlocker },
            { element: document, event: 'contextmenu', handler: contextBlocker }
        );
    }
    
    preventWindowMinimization() {
        // Detect minimize attempts through window state changes
        const minimizeDetector = () => {
            if (this.enforcementActive && 
                (window.outerHeight <= 100 || window.outerWidth <= 100 || 
                 document.visibilityState === 'hidden')) {
                
                this.minimizeAttempts++;
                this.recordViolation('window_minimize', 'high', `Window minimization detected (${this.minimizeAttempts} times)`);
                
                // Try to restore window
                window.focus();
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen().catch(() => {});
                }
                
                if (this.minimizeAttempts >= 2) {
                    this.showCriticalWarning('🚨 Window minimization detected! Keep quiz window active.');
                }
            }
        };
        
        // Monitor window state every 200ms
        setInterval(minimizeDetector, 200);
        
        // Block minimize shortcuts
        const minimizeBlocker = (e) => {
            if (!this.enforcementActive) return;
            
            // Block Windows+D (show desktop), Windows+M (minimize all)
            if (e.metaKey && (e.key === 'd' || e.key === 'm')) {
                e.preventDefault();
                e.stopPropagation();
                this.recordViolation('minimize_shortcut_blocked', 'medium', 'Minimize shortcut blocked');
                return false;
            }
        };
        
        document.addEventListener('keydown', minimizeBlocker);
        this.blockedEvents.push({ element: document, event: 'keydown', handler: minimizeBlocker });
    }
    
    blockBackgroundApps() {
        // Enhanced background app detection
        const appSwitchBlocker = (e) => {
            if (!this.enforcementActive) return;
            
            // Block common app switching shortcuts
            const blockedCombos = [
                { alt: true, key: 'Tab' },        // Alt+Tab
                { ctrl: true, alt: true, key: 'Tab' }, // Ctrl+Alt+Tab
                { meta: true, key: 'Tab' },       // Cmd+Tab (Mac)
                { ctrl: true, shift: true, key: 'Escape' }, // Task Manager
                { ctrl: true, alt: true, key: 'Delete' }, // Ctrl+Alt+Del
                { meta: true, key: ' ' },         // Windows key + Space
                { meta: true, key: 'r' },         // Windows + R (Run)
            ];
            
            for (const combo of blockedCombos) {
                if (this.matchesKeyCombo(e, combo)) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.recordViolation('app_switch_blocked', 'high', `Blocked app switching: ${this.getKeyCombo(e)}`);
                    this.showSingleWarning('⚠️ Application switching is blocked during the quiz!');
                    return false;
                }
            }
        };
        
        document.addEventListener('keydown', appSwitchBlocker);
        this.blockedEvents.push({ element: document, event: 'keydown', handler: appSwitchBlocker });
    }
    
    enhancedKeyboardBlocking() {
        this.keyboardBlocker = (e) => {
            if (!this.enforcementActive) return;
            
            // Comprehensive keyboard shortcut blocking
            const strictlyBlocked = [
                // Developer tools
                { ctrl: true, shift: true, key: 'I' },
                { ctrl: true, shift: true, key: 'J' },
                { ctrl: true, shift: true, key: 'C' },
                { ctrl: true, key: 'U' },
                { key: 'F12' },
                
                // Navigation and browsing
                { ctrl: true, key: 'T' },         // New tab
                { ctrl: true, key: 'N' },         // New window
                { ctrl: true, key: 'W' },         // Close tab
                { ctrl: true, shift: true, key: 'T' }, // Reopen tab
                { ctrl: true, key: 'H' },         // History
                { ctrl: true, key: 'L' },         // Address bar
                { ctrl: true, key: 'K' },         // Search
                { ctrl: true, key: 'D' },         // Bookmark
                
                // Copy/paste/printing
                { ctrl: true, key: 'A' },         // Select all
                { ctrl: true, key: 'C' },         // Copy
                { ctrl: true, key: 'V' },         // Paste
                { ctrl: true, key: 'X' },         // Cut
                { ctrl: true, key: 'P' },         // Print
                { ctrl: true, key: 'S' },         // Save
                
                // Zoom and refresh
                { ctrl: true, key: '0' },         // Reset zoom
                { ctrl: true, key: '+' },         // Zoom in
                { ctrl: true, key: '-' },         // Zoom out
                { ctrl: true, key: 'R' },         // Refresh
                { key: 'F5' },                    // Refresh
                
                // Function keys
                { key: 'F1' }, { key: 'F2' }, { key: 'F3' }, 
                { key: 'F4' }, { key: 'F6' }, { key: 'F7' }, 
                { key: 'F8' }, { key: 'F9' }, { key: 'F10' }, 
                { key: 'F11' }
            ];
            
            for (const combo of strictlyBlocked) {
                if (this.matchesKeyCombo(e, combo)) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.recordViolation('keyboard_shortcut_blocked', 'medium', `Blocked: ${this.getKeyCombo(e)}`);
                    return false;
                }
            }
        };
        
        document.addEventListener('keydown', this.keyboardBlocker);
    }
    
    startAggressiveFocusMonitoring() {
        // Continuous focus monitoring
        setInterval(() => {
            if (this.enforcementActive) {
                const timeSinceLastFocus = Date.now() - this.lastFocusTime;
                
                // If window has been out of focus for more than 2 seconds
                if (timeSinceLastFocus > 2000 && document.hidden) {
                    this.recordViolation('prolonged_focus_loss', 'high', 'Window out of focus for extended period');
                    
                    // Try to regain focus
                    window.focus();
                    
                    // Show warning if focus lost too long
                    if (timeSinceLastFocus > 5000) {
                        this.showCriticalWarning('🚨 Return focus to quiz window immediately!');
                    }
                }
            }
        }, 1000);
        
        // Update focus time on any user interaction
        const updateFocus = () => {
            if (this.enforcementActive) {
                this.lastFocusTime = Date.now();
            }
        };
        
        ['mousedown', 'keydown', 'focus', 'click'].forEach(event => {
            document.addEventListener(event, updateFocus);
            this.blockedEvents.push({ element: document, event, handler: updateFocus });
        });
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
}

// Global instance
window.EnhancedProctoringSystem = EnhancedProctoringSystem;