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
        
        // Tab/App monitoring
        this.tabSwitchCount = 0;
        this.backgroundAppsDetected = [];
        this.isFullscreenLocked = false;
        this.preventStart = false;
        
        // Security configuration
        this.config = {
            maxLookAwayTime: 3000,        // 3 seconds
            maxMultiplePeople: 2,         // 2 detections
            maxCameraHidden: 2,           // 2 detections
            maxTabSwitches: 1,            // 1 switch = warning
            terminateOnViolations: 3,     // 3 violations = terminate
            realTimeAnalysis: true,       // Live analysis only
            noImageStorage: true,         // Never store images
            strictMode: true              // Enterprise mode
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
            
            // Get camera stream
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    frameRate: { ideal: 15 }  // Lower frame rate for performance
                },
                audio: false
            });
            
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
        
        // Real-time face detection (NO STORAGE)
        this.faceDetectionInterval = setInterval(() => {
            this.analyzeLiveFrame();
        }, 1000); // Analyze every second
        
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
        
        // Determine face count based on skin tone distribution
        let detectedFaces = 0;
        if (skinToneRatio > 0.02) detectedFaces = 1;  // Single person
        if (skinToneRatio > 0.08) detectedFaces = 2;  // Multiple people
        if (skinToneRatio < 0.005) detectedFaces = 0; // No face/camera covered
        
        this.processFaceDetection(detectedFaces);
    }
    
    processFaceDetection(faceCount) {
        const statusIndicator = document.getElementById('camera-status');
        
        if (faceCount === 0) {
            // No face detected or camera covered
            this.cameraHiddenCount++;
            this.updateCameraStatus('⚠️ NO FACE', '#ffc107');
            
            if (this.cameraHiddenCount > this.config.maxCameraHidden) {
                this.recordViolation('camera_hidden', 'high', 'Camera covered or no face detected');
            }
        } else if (faceCount === 1) {
            // Normal - single person
            this.cameraHiddenCount = 0;
            this.multiplePeopleCount = 0;
            this.updateCameraStatus('🔴 LIVE', '#28a745');
        } else if (faceCount >= 2) {
            // Multiple people detected
            this.multiplePeopleCount++;
            this.updateCameraStatus('⚠️ MULTIPLE', '#dc3545');
            
            if (this.multiplePeopleCount > this.config.maxMultiplePeople) {
                this.recordViolation('multiple_people', 'critical', 'Multiple people detected in camera');
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
        
        // If more brightness on edges than center, user might be looking away
        if (edgeBrightness > centralBrightness * 1.5) {
            this.lookAwayCount++;
            if (this.lookAwayCount > 3) {
                this.recordViolation('looking_away', 'medium', 'User appears to be looking away from screen');
                this.lookAwayCount = 0;
            }
        } else {
            this.lookAwayCount = Math.max(0, this.lookAwayCount - 1);
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
        
        // Window focus detection
        window.addEventListener('blur', () => {
            if (this.isActive) {
                this.recordViolation('window_blur', 'medium', 'Window lost focus');
            }
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
        switch (violation.severity) {
            case 'critical':
                this.showCriticalWarning(`🚨 CRITICAL VIOLATION: ${violation.description}`);
                break;
            case 'high':
                this.showWarning(`⚠️ WARNING: ${violation.description}`);
                break;
            case 'medium':
                this.showNotification(`⚠️ ${violation.description}`, 'warning');
                break;
            case 'low':
                console.log(`ℹ️ ${violation.description}`);
                break;
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
        this.isActive = false;
        
        if (this.faceDetectionInterval) {
            clearInterval(this.faceDetectionInterval);
        }
        
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
        }
        
        // Remove camera preview
        const preview = document.getElementById('live-camera-preview');
        if (preview) preview.remove();
        
        // Remove hidden elements
        if (this.videoElement) this.videoElement.remove();
        if (this.canvas) this.canvas.remove();
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
        alert(message); // For critical warnings, use alert to ensure user sees it
    }
    
    showCriticalError(message) {
        console.error(message);
        alert(message);
    }
}

// Global instance
window.EnhancedProctoringSystem = EnhancedProctoringSystem;