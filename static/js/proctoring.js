// Proctoring.js - Advanced proctoring functionality for quiz monitoring

class ProctoringManager {
    constructor(attemptId) {
        this.attemptId = attemptId;
        this.isActive = false;
        this.violations = [];
        this.mediaStream = null;
        this.videoElement = null;
        this.canvas = null;
        this.context = null;
        this.detectionInterval = null;
        
        // WebSocket connection for real-time monitoring
        this.socket = null;
        this.socketReconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        
        // Enhanced face detection
        this.faceDetectionModel = null;
        this.lastDetectedFaces = 0;
        this.noFaceDetectedCount = 0;
        this.multipleFaceDetectedCount = 0;
        this.suspiciousMovementCount = 0;
        this.previousImageData = null;
        
        // Enhanced violation tracking
        this.violationCount = 0;
        this.highSeverityCount = 0;
        this.isTerminated = false;
        this.maxViolations = 3;
        this.lastViolationTime = null;
        this.violationBuffer = [];
        
        // Configuration - Enhanced like Moodle Proctoring Pro
        this.config = {
            // Core proctoring features
            faceDetection: true,
            tabSwitchDetection: true,
            fullscreenEnforcement: true,
            screenshotDetection: true,
            audioMonitoring: true,
            mouseMoveTracking: true,
            keyboardMonitoring: true,
            windowBlurDetection: true,
            multipleTabDetection: true,
            rightClickDisabled: true,
            copyPasteDisabled: true,
            devToolsDetection: true,
            printScreenBlocked: true,
            selectTextDisabled: true,
            
            // NEW: Moodle Proctoring Pro-like features
            intervalCapture: true,
            captureIntervalMs: 30000, // 30 seconds like Moodle Proctoring Pro
            imageQuality: 0.8,
            preExamFaceVerification: true,
            faceVerificationRequired: true,
            screenResizeDetection: true,
            windowResizeDetection: true,
            browserChangeDetection: true,
            bulkImageAnalysis: true,
            autoTerminateOnViolations: true,
            violationThreshold: 5
        };
        
        // NEW: Interval capture system
        this.intervalCaptureTimer = null;
        this.capturedImages = [];
        this.faceVerificationStatus = 'pending';
        this.preExamVerificationComplete = false;
        
        this.init();
    }

    async init() {
        console.log('Initializing Enhanced Proctoring System (Moodle Proctoring Pro style)...');
        
        try {
            // NEW: Pre-exam face verification like Moodle Proctoring Pro
            if (this.config.preExamFaceVerification) {
                await this.performPreExamVerification();
            }
            
            await this.requestPermissions();
            this.setupEventListeners();
            this.setupEnhancedDetection(); // NEW: Enhanced detection methods
            this.initWebSocket();
            this.startMonitoring();
            this.startAdvancedFaceDetection();
            
            // NEW: Start interval-based captures like Moodle Proctoring Pro
            if (this.config.intervalCapture) {
                this.startIntervalCapture();
            }
            
            this.showProctoringStatus('active');
        } catch (error) {
            console.error('Proctoring initialization failed:', error);
            this.showProctoringStatus('error', error.message);
            // If pre-verification fails, block quiz access
            if (error.type === 'face_verification_failed') {
                this.blockQuizAccess(error.message);
            }
        }
    }

    async requestPermissions() {
        // Enhanced browser compatibility check
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            // Try older browser APIs as fallback
            if (navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia) {
                console.warn('Using legacy getUserMedia API');
                return this.requestPermissionsLegacy();
            } else {
                throw new Error('Camera access not supported by this browser. Please use a modern browser like Chrome, Firefox, or Safari.');
            }
        }

        // Check for HTTPS requirement
        if (location.protocol !== 'https:' && !['localhost', '127.0.0.1'].includes(location.hostname)) {
            throw new Error('Camera access requires a secure connection (HTTPS). Please access this page via HTTPS.');
        }

        try {
            // Request camera and microphone access with enhanced error handling
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640, min: 320 },
                    height: { ideal: 480, min: 240 },
                    frameRate: { ideal: 15, min: 10 },
                    facingMode: 'user'
                },
                audio: this.config.audioMonitoring
            });

            // Setup video element for face detection
            this.setupVideoElement();
            console.log('Camera access granted successfully');
            
        } catch (error) {
            console.error('Camera access error:', error);
            
            if (error.name === 'NotAllowedError') {
                throw new Error('Camera permission denied. Please click "Allow" when prompted and refresh the page.');
            } else if (error.name === 'NotFoundError') {
                throw new Error('No camera found. Please connect a camera and refresh the page.');
            } else if (error.name === 'OverconstrainedError') {
                console.warn('Camera constraints too strict, trying with basic settings');
                return this.requestBasicPermissions();
            } else if (error.name === 'SecurityError') {
                throw new Error('Security error accessing camera. Please ensure you are on a secure connection.');
            } else {
                throw new Error(`Camera access error: ${error.message}`);
            }
        }
    }
    
    async requestBasicPermissions() {
        try {
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                video: true,
                audio: false
            });
            this.setupVideoElement();
            console.log('Basic camera access granted');
        } catch (error) {
            throw new Error(`Even basic camera access failed: ${error.message}`);
        }
    }
    
    requestPermissionsLegacy() {
        return new Promise((resolve, reject) => {
            const getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia;
            
            getUserMedia.call(navigator, {
                video: true,
                audio: false
            }, (stream) => {
                this.mediaStream = stream;
                this.setupVideoElement();
                resolve();
            }, (error) => {
                reject(new Error(`Legacy camera access failed: ${error.message}`));
            });
        });
    }

    setupVideoElement() {
        try {
            // Create video element for face detection with enhanced error handling
            this.videoElement = document.createElement('video');
            this.videoElement.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                width: 200px;
                height: 150px;
                z-index: 9999;
                border: 2px solid #28a745;
                border-radius: 8px;
                background: #000;
                box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            `;
            this.videoElement.autoplay = true;
            this.videoElement.muted = true;
            this.videoElement.playsInline = true; // Important for iOS
            
            // Add error handling for video element
            this.videoElement.onerror = (e) => {
                console.error('Video element error:', e);
                this.recordViolation('video_error', 'Video playback error', 'medium');
            };
            
            this.videoElement.onloadedmetadata = () => {
                console.log('Video metadata loaded successfully');
            };
            
            // Set video source
            if (this.mediaStream) {
                this.videoElement.srcObject = this.mediaStream;
            } else {
                throw new Error('No media stream available');
            }
            
            document.body.appendChild(this.videoElement);
            
            // Add status indicator
            this.createStatusIndicator();
            
        } catch (error) {
            console.error('Error setting up video element:', error);
            throw new Error(`Video setup failed: ${error.message}`);
        }

        // Setup canvas for face detection
        this.canvas = document.createElement('canvas');
        this.context = this.canvas.getContext('2d');
        this.canvas.width = 640;
        this.canvas.height = 480;
    }
    
    initWebSocket() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/proctoring/${this.attemptId}`;
            
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                console.log('WebSocket connected for real-time monitoring');
                this.socketReconnectAttempts = 0;
                this.sendWebSocketMessage('connection_established', {
                    timestamp: new Date().toISOString(),
                    userAgent: navigator.userAgent,
                    screenResolution: `${screen.width}x${screen.height}`
                });
            };
            
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(data);
            };
            
            this.socket.onclose = () => {
                console.log('WebSocket connection closed');
                this.reconnectWebSocket();
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
            
        } catch (error) {
            console.warn('WebSocket not available, falling back to HTTP polling');
            this.startPollingFallback();
        }
    }
    
    reconnectWebSocket() {
        if (this.socketReconnectAttempts < this.maxReconnectAttempts && !this.isTerminated) {
            this.socketReconnectAttempts++;
            setTimeout(() => {
                console.log(`Attempting WebSocket reconnection (${this.socketReconnectAttempts}/${this.maxReconnectAttempts})`);
                this.initWebSocket();
            }, 3000 * this.socketReconnectAttempts);
        }
    }
    
    sendWebSocketMessage(type, data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({
                type: type,
                attemptId: this.attemptId,
                timestamp: new Date().toISOString(),
                data: data
            }));
        }
    }
    
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'warning':
                this.showWarningMessage(message.data.message);
                break;
            case 'terminate_quiz':
                this.terminateQuiz(message.data.reason);
                break;
            case 'host_message':
                this.showHostMessage(message.data.message);
                break;
        }
    }
    
    startPollingFallback() {
        // Fallback to HTTP polling if WebSocket is not available
        setInterval(() => {
            this.sendViolationUpdate();
        }, 10000);
    }
    
    async startAdvancedFaceDetection() {
        // Load face detection model if available
        try {
            if (typeof cv !== 'undefined') {
                console.log('OpenCV.js detected, using advanced face detection');
                this.faceDetectionModel = new cv.CascadeClassifier();
                this.faceDetectionModel.load('haarcascade_frontalface_default.xml');
            }
        } catch (error) {
            console.log('Advanced face detection not available, using basic detection');
        }
        
        // Start face detection loop
        this.faceDetectionLoop();
    }
    
    faceDetectionLoop() {
        if (this.isTerminated) return;
        
        if (this.videoElement && this.videoElement.readyState === 4) {
            this.context.drawImage(this.videoElement, 0, 0, 640, 480);
            
            // Get current image data
            const currentImageData = this.context.getImageData(0, 0, 640, 480);
            
            // Detect faces
            const faceCount = this.detectFaces(currentImageData);
            
            // Check for violations
            this.checkFaceViolations(faceCount);
            
            // Detect suspicious movement
            if (this.previousImageData) {
                this.detectSuspiciousMovement(currentImageData, this.previousImageData);
            }
            
            this.previousImageData = currentImageData;
            this.lastDetectedFaces = faceCount;
            
            // Send real-time update
            this.sendWebSocketMessage('face_detection_update', {
                faceCount: faceCount,
                timestamp: new Date().toISOString()
            });
        }
        
        // Continue detection loop
        setTimeout(() => this.faceDetectionLoop(), 2000);
    }

    // NEW: Pre-exam face verification like Moodle Proctoring Pro
    async performPreExamVerification() {
        return new Promise((resolve, reject) => {
            console.log('Starting pre-exam face verification...');
            
            // Show verification modal
            this.showVerificationModal();
            
            // Wait for user to capture verification image
            document.getElementById('capture-verification-btn').addEventListener('click', async () => {
                try {
                    const verificationImage = await this.captureVerificationImage();
                    const verified = await this.verifyUserIdentity(verificationImage);
                    
                    if (verified) {
                        this.preExamVerificationComplete = true;
                        this.faceVerificationStatus = 'verified';
                        this.hideVerificationModal();
                        resolve();
                    } else {
                        const error = new Error('Face verification failed. Please ensure good lighting and look directly at the camera.');
                        error.type = 'face_verification_failed';
                        reject(error);
                    }
                } catch (error) {
                    error.type = 'face_verification_failed';
                    reject(error);
                }
            });
        });
    }

    // NEW: Enhanced detection setup like Moodle Proctoring Pro
    setupEnhancedDetection() {
        // Screen resize detection
        if (this.config.screenResizeDetection) {
            let originalWidth = window.screen.width;
            let originalHeight = window.screen.height;
            
            setInterval(() => {
                if (window.screen.width !== originalWidth || window.screen.height !== originalHeight) {
                    this.logViolation('screen_resize', 
                        `Screen resolution changed from ${originalWidth}x${originalHeight} to ${window.screen.width}x${window.screen.height}`, 
                        'medium');
                    originalWidth = window.screen.width;
                    originalHeight = window.screen.height;
                }
            }, 5000);
        }

        // Window resize detection
        if (this.config.windowResizeDetection) {
            let originalWindowWidth = window.innerWidth;
            let originalWindowHeight = window.innerHeight;
            
            window.addEventListener('resize', () => {
                const newWidth = window.innerWidth;
                const newHeight = window.innerHeight;
                
                if (Math.abs(newWidth - originalWindowWidth) > 50 || Math.abs(newHeight - originalWindowHeight) > 50) {
                    this.logViolation('window_resize', 
                        `Browser window resized significantly from ${originalWindowWidth}x${originalWindowHeight} to ${newWidth}x${newHeight}`, 
                        'medium');
                }
                
                originalWindowWidth = newWidth;
                originalWindowHeight = newHeight;
            });
        }

        // Enhanced developer tools detection
        if (this.config.devToolsDetection) {
            this.detectDevTools();
        }
    }

    // NEW: Interval-based image capture like Moodle Proctoring Pro
    startIntervalCapture() {
        console.log(`Starting interval capture every ${this.config.captureIntervalMs / 1000} seconds`);
        
        this.intervalCaptureTimer = setInterval(async () => {
            if (this.isActive && !this.isTerminated) {
                try {
                    const capturedImage = await this.captureCurrentFrame();
                    await this.sendCapturedImage(capturedImage);
                    this.capturedImages.push({
                        timestamp: new Date().toISOString(),
                        image: capturedImage,
                        analyzed: false
                    });
                    
                    // Keep only last 100 images
                    if (this.capturedImages.length > 100) {
                        this.capturedImages.shift();
                    }
                } catch (error) {
                    console.error('Interval capture failed:', error);
                    this.logViolation('capture_failed', 'Failed to capture webcam image', 'low');
                }
            }
        }, this.config.captureIntervalMs);
    }

    // NEW: Enhanced developer tools detection
    detectDevTools() {
        let devtools = {
            open: false,
            orientation: null
        };
        
        setInterval(() => {
            const threshold = 160;
            let orientation = window.outerHeight - window.innerHeight > threshold ? 'vertical' : 'horizontal';
            
            if (!(window.outerHeight - window.innerHeight > threshold) && 
                !(window.outerWidth - window.innerWidth > threshold)) {
                devtools.open = false;
            } else {
                if (!devtools.open || devtools.orientation !== orientation) {
                    devtools.open = true;
                    devtools.orientation = orientation;
                    this.logViolation('devtools_opened', 
                        `Developer tools detected (${orientation} orientation)`, 
                        'high');
                }
            }
        }, 1000);
        
        // Additional F12 key detection
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F12' || 
                (e.ctrlKey && e.shiftKey && e.key === 'I') ||
                (e.ctrlKey && e.shiftKey && e.key === 'C') ||
                (e.ctrlKey && e.shiftKey && e.key === 'J')) {
                e.preventDefault();
                this.logViolation('devtools_shortcut', 
                    `Developer tools shortcut blocked: ${e.key}`, 
                    'high');
                return false;
            }
        });
    }
    
    detectFaces(imageData) {
        // Enhanced biometric-style face detection with multi-person detection
        const data = imageData.data;
        const width = 640;
        const height = 480;
        
        // Check if camera is blocked first
        if (this.isCameraBlocked(data)) {
            this.logViolation('camera_blocked', 'Camera appears to be blocked or covered', 'high');
            return 0;
        }
        
        // Detect face regions using enhanced algorithm
        const faceRegions = this.detectFaceRegions(data, width, height);
        const faceCount = faceRegions.length;
        
        // Enhanced lighting check
        const avgBrightness = this.calculateAverageBrightness(data);
        if (avgBrightness < 25) {
            this.logViolation('poor_lighting', 'Environment too dark for proper face detection', 'medium');
        }
        
        return faceCount;
    }
    
    detectFaceRegions(data, width, height) {
        const faces = [];
        const blockSize = 40; // Larger blocks for better accuracy
        
        for (let y = 0; y < height - blockSize; y += 20) {
            for (let x = 0; x < width - blockSize; x += 20) {
                const faceScore = this.calculateFaceScore(data, x, y, blockSize, width);
                
                if (faceScore > 0.4) {
                    // Check if this region overlaps with existing faces
                    const overlaps = faces.some(face => 
                        Math.abs(face.x - x) < blockSize && Math.abs(face.y - y) < blockSize
                    );
                    
                    if (!overlaps) {
                        faces.push({ x, y, score: faceScore, width: blockSize, height: blockSize });
                    }
                }
            }
        }
        
        // Filter out weak detections and merge nearby regions
        return this.refineFaceDetections(faces);
    }
    
    calculateFaceScore(data, startX, startY, blockSize, width) {
        let skinPixels = 0;
        let totalPixels = 0;
        let edgePixels = 0;
        
        for (let y = startY; y < startY + blockSize; y++) {
            for (let x = startX; x < startX + blockSize; x++) {
                if (y >= 0 && y < 480 && x >= 0 && x < width) {
                    const i = (y * width + x) * 4;
                    if (i < data.length - 3) {
                        const r = data[i];
                        const g = data[i + 1];
                        const b = data[i + 2];
                        
                        totalPixels++;
                        
                        // Enhanced skin tone detection
                        if (this.isEnhancedSkinTone(r, g, b)) {
                            skinPixels++;
                        }
                        
                        // Edge detection for facial features
                        if (this.isEdgePixel(data, x, y, width)) {
                            edgePixels++;
                        }
                    }
                }
            }
        }
        
        if (totalPixels === 0) return 0;
        
        const skinRatio = skinPixels / totalPixels;
        const edgeRatio = edgePixels / totalPixels;
        
        // Combined score considering skin tone and facial features
        return (skinRatio * 0.6) + (edgeRatio * 0.4);
    }
    
    isEnhancedSkinTone(r, g, b) {
        // More sophisticated skin tone detection
        const max = Math.max(r, g, b);
        const min = Math.min(r, g, b);
        
        return r > 95 && g > 40 && b > 20 && 
               max - min > 15 && 
               Math.abs(r - g) > 15 && 
               r > g && r > b &&
               r < 255 && g < 200 && b < 170 &&
               (r + g + b) > 200; // Ensure sufficient brightness
    }
    
    isEdgePixel(data, x, y, width) {
        const i = (y * width + x) * 4;
        const rightI = (y * width + x + 1) * 4;
        const downI = ((y + 1) * width + x) * 4;
        
        if (rightI >= data.length || downI >= data.length) return false;
        
        const grayCenter = (data[i] + data[i + 1] + data[i + 2]) / 3;
        const grayRight = (data[rightI] + data[rightI + 1] + data[rightI + 2]) / 3;
        const grayDown = (data[downI] + data[downI + 1] + data[downI + 2]) / 3;
        
        return Math.abs(grayCenter - grayRight) > 25 || Math.abs(grayCenter - grayDown) > 25;
    }
    
    refineFaceDetections(faces) {
        // Sort by score and filter out weak detections
        faces.sort((a, b) => b.score - a.score);
        
        if (faces.length <= 1) return faces;
        
        // Remove overlapping detections (keep the stronger ones)
        const refined = [];
        for (let i = 0; i < faces.length; i++) {
            const current = faces[i];
            let isOverlapped = false;
            
            for (let j = 0; j < refined.length; j++) {
                const existing = refined[j];
                const distance = Math.sqrt(
                    Math.pow(current.x - existing.x, 2) + 
                    Math.pow(current.y - existing.y, 2)
                );
                
                if (distance < 60) { // Faces closer than 60 pixels are considered same person
                    isOverlapped = true;
                    break;
                }
            }
            
            if (!isOverlapped && current.score > 0.5) {
                refined.push(current);
            }
        }
        
        return refined;
    }
    
    isCameraBlocked(data) {
        let darkPixels = 0;
        const totalPixels = data.length / 4;
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            const brightness = (r + g + b) / 3;
            
            if (brightness < 15) {
                darkPixels++;
            }
        }
        
        // If more than 85% of pixels are very dark, camera is likely blocked
        return (darkPixels / totalPixels) > 0.85;
    }
    
    calculateAverageBrightness(data) {
        let totalBrightness = 0;
        const totalPixels = data.length / 4;
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            totalBrightness += (r + g + b) / 3;
        }
        
        return totalPixels > 0 ? totalBrightness / totalPixels : 0;
    }
    
    checkFaceViolations(faceCount) {
        if (faceCount === 0) {
            this.noFaceDetectedCount++;
            if (this.noFaceDetectedCount > 5) { // 10 seconds of no face
                this.logViolation('no_face_detected', 'Participant not visible in camera', 'high');
                this.noFaceDetectedCount = 0;
            }
        } else if (faceCount > 1) {
            this.multipleFaceDetectedCount++;
            if (this.multipleFaceDetectedCount > 3) { // 6 seconds of multiple faces
                this.logViolation('multiple_faces', `${faceCount} faces detected in camera`, 'high');
                this.multipleFaceDetectedCount = 0;
            }
        } else {
            // Reset counters when normal
            this.noFaceDetectedCount = 0;
            this.multipleFaceDetectedCount = 0;
        }
    }
    
    detectSuspiciousMovement(currentData, previousData) {
        let totalDiff = 0;
        const data1 = currentData.data;
        const data2 = previousData.data;
        
        // Calculate pixel differences
        for (let i = 0; i < data1.length; i += 16) { // Sample every 4th pixel for performance
            const diff = Math.abs(data1[i] - data2[i]) + 
                        Math.abs(data1[i + 1] - data2[i + 1]) + 
                        Math.abs(data1[i + 2] - data2[i + 2]);
            totalDiff += diff;
        }
        
        const avgDiff = totalDiff / (data1.length / 16);
        
        // Detect suspicious rapid movement
        if (avgDiff > 50) {
            this.suspiciousMovementCount++;
            if (this.suspiciousMovementCount > 10) {
                this.logViolation('suspicious_movement', 'Rapid or suspicious movement detected', 'medium');
                this.suspiciousMovementCount = 0;
            }
        } else {
            this.suspiciousMovementCount = Math.max(0, this.suspiciousMovementCount - 1);
        }
    }

    setupEventListeners() {
        // Tab switch detection
        if (this.config.tabSwitchDetection) {
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    this.logViolation('tab_switch', 'User switched away from quiz tab', 'high');
                    this.notifyHostAdmin('Student switched away from quiz tab', 'high');
                }
            });
        }

        // Window blur detection
        if (this.config.windowBlurDetection) {
            window.addEventListener('blur', () => {
                this.logViolation('window_blur', 'Quiz window lost focus', 'medium');
                this.notifyHostAdmin('Student left quiz window', 'medium');
            });
        }

        // Right-click prevention
        if (this.config.rightClickDisabled) {
            document.addEventListener('contextmenu', (e) => {
                e.preventDefault();
                this.logViolation('right_click_attempt', 'Right-click attempted', 'low');
                return false;
            });
        }

        // Enhanced copy/paste and security prevention
        if (this.config.copyPasteDisabled) {
            // Block text selection
            document.body.style.userSelect = 'none';
            document.body.style.webkitUserSelect = 'none';
            document.body.style.mozUserSelect = 'none';
            document.body.style.msUserSelect = 'none';
            
            // Disable drag and drop
            document.addEventListener('dragstart', (e) => {
                e.preventDefault();
                return false;
            });
            
            document.addEventListener('selectstart', (e) => {
                e.preventDefault();
                this.logViolation('text_selection', 'Text selection attempted', 'low');
                return false;
            });

            // Block copy/paste events directly
            document.addEventListener('copy', (e) => {
                e.preventDefault();
                this.logViolation('copy_attempt', 'Copy operation blocked', 'medium');
                return false;
            });

            document.addEventListener('paste', (e) => {
                e.preventDefault();
                this.logViolation('paste_attempt', 'Paste operation blocked', 'medium');
                return false;
            });

            document.addEventListener('cut', (e) => {
                e.preventDefault();
                this.logViolation('cut_attempt', 'Cut operation blocked', 'medium');
                return false;
            });

            document.addEventListener('keydown', (e) => {
                // Block comprehensive list of shortcuts
                const blockedCombos = [
                    // Copy/Paste operations
                    { ctrl: true, key: 'c' },
                    { ctrl: true, key: 'v' },
                    { ctrl: true, key: 'a' },
                    { ctrl: true, key: 'x' },
                    { ctrl: true, key: 'z' },
                    { ctrl: true, key: 's' },
                    // Developer tools
                    { key: 'F12' },
                    { ctrl: true, shift: true, key: 'i' },
                    { ctrl: true, shift: true, key: 'c' },
                    { ctrl: true, shift: true, key: 'j' },
                    { ctrl: true, shift: true, key: 'k' },
                    { ctrl: true, key: 'u' },
                    // Navigation
                    { ctrl: true, key: 'r' },
                    { key: 'F5' },
                    { ctrl: true, key: 'h' },
                    { ctrl: true, key: 'l' },
                    { ctrl: true, key: 't' },
                    { ctrl: true, key: 'n' },
                    { ctrl: true, key: 'w' },
                    { alt: true, key: 'F4' },
                    // Print
                    { ctrl: true, key: 'p' },
                    { key: 'PrintScreen' }
                ];

                for (let combo of blockedCombos) {
                    if ((!combo.ctrl || e.ctrlKey) && 
                        (!combo.shift || e.shiftKey) && 
                        (!combo.alt || e.altKey) && 
                        e.key.toLowerCase() === combo.key.toLowerCase()) {
                        
                        e.preventDefault();
                        e.stopPropagation();
                        this.logViolation('blocked_shortcut', `Blocked shortcut: ${combo.key}`, 'medium');
                        this.notifyHostAdmin(`Student attempted blocked shortcut: ${combo.key}`, 'medium');
                        return false;
                    }
                }
            });
        }

        // Enhanced screenshot detection
        this.setupScreenshotDetection();
        
        // Enhanced browser focus monitoring
        this.setupBrowserFocusMonitoring();

        // Enhanced screenshot detection and prevention
        if (this.config.screenshotDetection) {
            // Print Screen key detection
            document.addEventListener('keydown', (e) => {
                if (e.key === 'PrintScreen') {
                    e.preventDefault();
                    this.logViolation('screenshot_attempt', 'Screenshot attempt blocked', 'high');
                    return false;
                }
            });
            
            document.addEventListener('keyup', (e) => {
                if (e.key === 'PrintScreen') {
                    e.preventDefault();
                    this.logViolation('screenshot_attempt', 'Screenshot key detected', 'high');
                    return false;
                }
            });
            
            // Detect screenshot via clipboard API
            document.addEventListener('paste', (e) => {
                if (e.clipboardData && e.clipboardData.files.length > 0) {
                    this.logViolation('screenshot_detected', 'Screenshot pasted from clipboard', 'high');
                }
            });
            
            // Block Windows snipping tool shortcuts
            document.addEventListener('keydown', (e) => {
                // Windows + Shift + S (Snipping Tool)
                if (e.metaKey && e.shiftKey && e.key === 'S') {
                    e.preventDefault();
                    this.logViolation('snipping_tool_blocked', 'Snipping tool shortcut blocked', 'high');
                    return false;
                }
            });
            
            // Detect screen recording software shortcuts
            const screenRecordShortcuts = [
                { alt: true, key: 'r' }, // Common screen record
                { ctrl: true, shift: true, key: 'r' }, // Various screen recorders
                { meta: true, shift: true, key: 'r' }, // Mac screen record
            ];
            
            document.addEventListener('keydown', (e) => {
                for (let combo of screenRecordShortcuts) {
                    if ((!combo.ctrl || e.ctrlKey) && 
                        (!combo.shift || e.shiftKey) && 
                        (!combo.alt || e.altKey) && 
                        (!combo.meta || e.metaKey) && 
                        e.key.toLowerCase() === combo.key.toLowerCase()) {
                        
                        e.preventDefault();
                        e.stopPropagation();
                        this.logViolation('screen_record_blocked', 'Screen recording shortcut blocked', 'high');
                        return false;
                    }
                }
            });
        }

        // Multiple tab detection
        if (this.config.multipleTabDetection) {
            window.addEventListener('storage', (e) => {
                if (e.key === 'quiz_active_tab') {
                    this.logViolation('multiple_tabs', 'Multiple quiz tabs detected', 'high');
                }
            });
            localStorage.setItem('quiz_active_tab', this.attemptId);
        }

        // Fullscreen change detection
        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement && this.config.fullscreenEnforcement) {
                this.logViolation('fullscreen_exit', 'Exited fullscreen mode', 'medium');
                this.enforceFullscreen();
            }
        });

        // Mouse movement tracking (for unusual patterns)
        if (this.config.mouseMoveTracking) {
            let mouseMovements = [];
            document.addEventListener('mousemove', (e) => {
                mouseMovements.push({
                    x: e.clientX,
                    y: e.clientY,
                    timestamp: Date.now()
                });
                
                // Keep only recent movements (last 10 seconds)
                const cutoff = Date.now() - 10000;
                mouseMovements = mouseMovements.filter(m => m.timestamp > cutoff);
                
                // Detect unusual patterns (e.g., too regular/automated movement)
                if (mouseMovements.length > 100) {
                    this.analyzeMouseMovements(mouseMovements);
                }
            });
        }

        // Face detection setup
        if (this.config.faceDetection && this.videoElement) {
            this.videoElement.addEventListener('loadedmetadata', () => {
                this.startFaceDetection();
            });
        }

        // DevTools detection
        if (this.config.devToolsDetection) {
            this.detectDevTools();
        }
    }

    startMonitoring() {
        this.isActive = true;
        
        // Start periodic checks
        this.detectionInterval = setInterval(() => {
            this.performPeriodicChecks();
        }, 5000); // Check every 5 seconds

        console.log('Proctoring monitoring started');
    }

    stopMonitoring() {
        this.isActive = false;
        
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
        }
        
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
        }
        
        if (this.videoElement && this.videoElement.parentNode) {
            this.videoElement.parentNode.removeChild(this.videoElement);
        }

        localStorage.removeItem('quiz_active_tab');
        
        console.log('Proctoring monitoring stopped');
    }

    startFaceDetection() {
        if (!this.videoElement || !this.canvas) return;

        const detectFaces = () => {
            if (!this.isActive) return;

            this.context.drawImage(this.videoElement, 0, 0, this.canvas.width, this.canvas.height);
            
            // Basic face detection using image analysis
            // In a real implementation, you would use a proper face detection library
            const imageData = this.context.getImageData(0, 0, this.canvas.width, this.canvas.height);
            const faceCount = this.analyzeImageForFaces(imageData);
            
            if (faceCount === 0) {
                this.logViolation('no_face_detected', 'No face detected in camera', 'high');
            } else if (faceCount > 1) {
                this.logViolation('multiple_faces', `${faceCount} faces detected`, 'high');
            }
            
            // Continue detection
            setTimeout(detectFaces, 2000); // Check every 2 seconds
        };

        detectFaces();
    }

    analyzeImageForFaces(imageData) {
        // Simplified face detection - in production, use proper libraries like face-api.js
        // This is a placeholder that returns a random number for demonstration
        
        // Check for basic skin color detection
        const data = imageData.data;
        let skinPixels = 0;
        const totalPixels = data.length / 4;
        
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];
            
            // Simple skin color detection
            if (r > 95 && g > 40 && b > 20 && 
                Math.max(r, g, b) - Math.min(r, g, b) > 15 &&
                Math.abs(r - g) > 15 && r > g && r > b) {
                skinPixels++;
            }
        }
        
        const skinRatio = skinPixels / totalPixels;
        
        // Estimate face count based on skin ratio
        if (skinRatio > 0.1) return 1; // Assume one face
        if (skinRatio > 0.2) return 2; // Might be multiple faces
        return 0; // No face detected
    }

    analyzeMouseMovements(movements) {
        // Detect if movements are too regular (possible automation)
        if (movements.length < 10) return;
        
        const distances = [];
        const intervals = [];
        
        for (let i = 1; i < movements.length; i++) {
            const prev = movements[i - 1];
            const curr = movements[i];
            
            const distance = Math.sqrt(
                Math.pow(curr.x - prev.x, 2) + Math.pow(curr.y - prev.y, 2)
            );
            const interval = curr.timestamp - prev.timestamp;
            
            distances.push(distance);
            intervals.push(interval);
        }
        
        // Calculate variance in distances and intervals
        const avgDistance = distances.reduce((a, b) => a + b, 0) / distances.length;
        const avgInterval = intervals.reduce((a, b) => a + b, 0) / intervals.length;
        
        const distanceVariance = distances.reduce((sum, d) => sum + Math.pow(d - avgDistance, 2), 0) / distances.length;
        const intervalVariance = intervals.reduce((sum, i) => sum + Math.pow(i - avgInterval, 2), 0) / intervals.length;
        
        // If movements are too regular, it might be automated
        if (distanceVariance < 5 && intervalVariance < 100) {
            this.logViolation('suspicious_mouse_pattern', 'Detected potentially automated mouse movements', 'medium');
        }
    }

    detectDevTools() {
        // Multiple methods to detect developer tools
        let devtools = {open: false, orientation: null};
        
        setInterval(() => {
            if (window.outerHeight - window.innerHeight > 200 || 
                window.outerWidth - window.innerWidth > 200) {
                if (!devtools.open) {
                    devtools.open = true;
                    this.logViolation('devtools_opened', 'Developer tools opened', 'high');
                }
            } else {
                devtools.open = false;
            }
        }, 500);

        // Detect console access
        let consoleOpened = false;
        Object.defineProperty(console, '_commandLineAPI', {
            get: function() {
                if (!consoleOpened) {
                    consoleOpened = true;
                    proctoringManager.logViolation('console_access', 'Console accessed', 'high');
                }
                return undefined;
            }
        });
    }

    performPeriodicChecks() {
        // Check window dimensions for unusual changes
        if (window.innerWidth < 800 || window.innerHeight < 600) {
            this.logViolation('window_resize', 'Window resized to unusually small dimensions', 'medium');
        }
        
        // Check if page is in focus
        if (document.hasFocus && !document.hasFocus()) {
            this.logViolation('focus_lost', 'Page lost focus', 'medium');
        }
        
        // Check for multiple instances
        const tabCount = localStorage.getItem('quiz_tab_count') || '0';
        if (parseInt(tabCount) > 1) {
            this.logViolation('multiple_instances', 'Multiple quiz instances detected', 'high');
        }
    }

    enforceFullscreen() {
        if (document.documentElement.requestFullscreen) {
            document.documentElement.requestFullscreen();
        }
    }

    logViolation(type, description, severity = 'medium') {
        if (this.isTerminated) {
            return; // No more violations after termination
        }
        
        const violation = {
            type: type,
            description: description,
            severity: severity,
            timestamp: new Date().toISOString(),
            attemptId: this.attemptId,
            userAgent: navigator.userAgent,
            url: window.location.href
        };
        
        this.violations.push(violation);
        
        // Enhanced violation tracking
        this.violationCount++;
        if (severity === 'high') {
            this.highSeverityCount++;
        }
        
        // Store in violation buffer for pattern analysis
        this.violationBuffer.push({
            ...violation,
            timestamp: Date.now()
        });
        
        // Clean old violations (last 5 minutes)
        const fiveMinutesAgo = Date.now() - (5 * 60 * 1000);
        this.violationBuffer = this.violationBuffer.filter(v => v.timestamp > fiveMinutesAgo);
        
        console.warn('Proctoring violation:', violation);
        console.warn(`Total violations: ${this.violationCount}, High severity: ${this.highSeverityCount}`);
        
        // Check for immediate termination conditions
        if (this.shouldTerminateQuiz(violation)) {
            this.terminateQuiz(violation);
            return;
        }
        
        // Send to server
        this.sendViolationToServer(violation);
        
        // Show warning to user
        this.showViolationWarning(violation);
        
        // Update security status display
        this.updateSecurityStatus();
    }

    async sendViolationToServer(violation) {
        try {
            const response = await fetch('/api/proctoring/event', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(violation)
            });
            
            if (!response.ok) {
                console.error('Failed to send violation to server');
                return;
            }
            
            const result = await response.json();
            
            // If quiz is terminated due to violation, trigger local termination
            if (result.status === 'terminated') {
                this.isTerminated = true;
                this.showTerminationMessage({
                    type: 'server_terminated',
                    description: result.message || 'Quiz terminated by security system',
                    severity: 'critical'
                });
                return;
            }
        } catch (error) {
            console.error('Error sending violation to server:', error);
        }
    }

    showViolationWarning(violation) {
        const warningDiv = document.createElement('div');
        warningDiv.className = 'alert alert-warning alert-dismissible fade show position-fixed';
        warningDiv.style.cssText = `
            top: 120px;
            right: 20px;
            z-index: 1051;
            max-width: 350px;
        `;
        
        let message = 'Proctoring Alert: ';
        switch (violation.severity) {
            case 'high':
                message = '?? Security Violation: ';
                warningDiv.className = warningDiv.className.replace('alert-warning', 'alert-danger');
                break;
            case 'medium':
                message = '? Proctoring Warning: ';
                break;
            case 'low':
                message = '?? Proctoring Notice: ';
                warningDiv.className = warningDiv.className.replace('alert-warning', 'alert-info');
                break;
        }
        
        warningDiv.innerHTML = `
            <strong>${message}</strong>${violation.description}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(warningDiv);
        
        // Auto-remove after 8 seconds
        setTimeout(() => {
            if (warningDiv.parentNode) {
                warningDiv.remove();
            }
        }, 8000);
        
        // Play warning sound
        this.playWarningSound();
    }
    
    shouldTerminateQuiz(violation) {
        if (this.isTerminated) {
            return false;
        }
        
        // Immediate termination violations (zero tolerance)
        const immediateTerminationTypes = [
            'console_access',
            'multiple_instances',
            'devtools_opened'
        ];
        
        if (immediateTerminationTypes.includes(violation.type)) {
            return true;
        }
        
        // Terminate after maximum violations reached
        if (this.violationCount >= this.maxViolations) {
            return true;
        }
        
        // Terminate after 2 high severity violations
        if (this.highSeverityCount >= 2) {
            return true;
        }
        
        // Terminate if too many violations in short time (4 violations in 2 minutes)
        const twoMinutesAgo = Date.now() - (2 * 60 * 1000);
        const recentViolations = this.violationBuffer.filter(v => v.timestamp > twoMinutesAgo);
        if (recentViolations.length >= 4) {
            return true;
        }
        
        return false;
    }
    
    terminateQuiz(triggerViolation) {
        this.isTerminated = true;
        this.isActive = false;
        
        // Stop all monitoring
        this.stopMonitoring();
        
        // Log the termination
        const terminationViolation = {
            type: 'quiz_terminated',
            description: `Quiz terminated due to: ${triggerViolation.description}`,
            severity: 'critical',
            timestamp: new Date().toISOString(),
            attemptId: this.attemptId,
            userAgent: navigator.userAgent,
            url: window.location.href,
            triggerViolation: triggerViolation
        };
        
        // Send termination event to server
        fetch('/api/proctoring/event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(terminationViolation)
        }).catch(error => {
            console.error('Failed to send termination event:', error);
        });
        
        // Show termination message
        this.showTerminationMessage(triggerViolation);
        
        // Disable all form inputs
        this.disableQuizInterface();
        
        // Auto-redirect after 10 seconds
        setTimeout(() => {
            window.location.href = '/dashboard';
        }, 10000);
    }
    
    showTerminationMessage(violation) {
        // Remove all existing alerts
        document.querySelectorAll('.alert').forEach(alert => alert.remove());
        
        // Create termination overlay
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(220, 53, 69, 0.95);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-family: Arial, sans-serif;
        `;
        
        overlay.innerHTML = `
            <div style="text-align: center; max-width: 600px; padding: 40px;">
                <i class="fas fa-exclamation-triangle" style="font-size: 80px; margin-bottom: 20px; color: #fff;"></i>
                <h1 style="font-size: 2.5rem; margin-bottom: 20px; color: #fff;">QUIZ TERMINATED</h1>
                <h3 style="margin-bottom: 30px; color: #fff;">? SECURITY VIOLATION DETECTED ?</h3>
                <div style="background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px; margin-bottom: 30px;">
                    <p style="font-size: 1.2rem; margin-bottom: 10px; color: #fff;"><strong>Violation Type:</strong> ${violation.type.replace('_', ' ').toUpperCase()}</p>
                    <p style="font-size: 1.1rem; margin-bottom: 10px; color: #fff;"><strong>Description:</strong> ${violation.description}</p>
                    <p style="font-size: 1rem; color: #fff;"><strong>Total Violations:</strong> ${this.violationCount}</p>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <p style="margin: 0; font-size: 1rem; color: #fff;">?? Your exam session has been flagged for review</p>
                    <p style="margin: 5px 0 0 0; font-size: 0.9rem; color: #fff;">Contact your administrator for retake permissions</p>
                </div>
                <p style="font-size: 1rem; margin-bottom: 0; color: #fff;">Redirecting to dashboard in <span id="countdown">10</span> seconds...</p>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        // Countdown timer
        let countdown = 10;
        const countdownElement = document.getElementById('countdown');
        const timer = setInterval(() => {
            countdown--;
            if (countdownElement) {
                countdownElement.textContent = countdown;
            }
            if (countdown <= 0) {
                clearInterval(timer);
            }
        }, 1000);
        
        // Play termination sound
        this.playTerminationSound();
    }
    
    updateSecurityStatus() {
        let status = 'secure';
        let message = `? Secure - ${this.violationCount} violations detected`;
        
        if (this.violationCount >= 1) {
            status = 'warning';
            message = `? Warning - ${this.violationCount} violations (${this.maxViolations - this.violationCount} remaining)`;
        }
        
        if (this.violationCount >= this.maxViolations - 1) {
            status = 'danger';
            message = `? Critical - ${this.violationCount} violations (1 more will terminate quiz)`;
        }
        
        if (this.highSeverityCount >= 1) {
            status = 'danger';
            message = `? High Risk - ${this.highSeverityCount} high-severity violations detected`;
        }
        
        this.showProctoringStatus(status, message);
    }
    
    disableQuizInterface() {
        // Disable all form inputs
        const form = document.getElementById('quiz-form');
        if (form) {
            const inputs = form.querySelectorAll('input, textarea, button, select');
            inputs.forEach(input => {
                input.disabled = true;
                input.style.opacity = '0.5';
            });
        }
        
        // Add overlay to prevent interaction
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.3);
            z-index: 999;
            pointer-events: none;
        `;
        document.body.appendChild(overlay);
    }
    
    playTerminationSound() {
        try {
            // Create termination sound sequence
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            
            // Create dramatic sound sequence
            const frequencies = [880, 659, 523, 440];  // A5, E5, C5, A4
            
            frequencies.forEach((freq, index) => {
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                oscillator.frequency.setValueAtTime(freq, audioContext.currentTime + index * 0.3);
                oscillator.type = 'square';
                
                gainNode.gain.setValueAtTime(0.1, audioContext.currentTime + index * 0.3);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + index * 0.3 + 0.2);
                
                oscillator.start(audioContext.currentTime + index * 0.3);
                oscillator.stop(audioContext.currentTime + index * 0.3 + 0.2);
            });
        } catch (error) {
            console.error('Failed to play termination sound:', error);
        }
    }
    
    stopMonitoring() {
        // Stop all monitoring activities
        if (this.mediaStream) {
            const tracks = this.mediaStream.getTracks();
            tracks.forEach(track => track.stop());
        }
        
        // Clear intervals
        if (this.detectionInterval) {
            clearInterval(this.detectionInterval);
        }
        
        // Hide camera view
        if (this.videoElement) {
            this.videoElement.style.display = 'none';
        }
        
        this.isActive = false;
    }

    showProctoringStatus(status, message = '') {
        let existingIndicator = document.getElementById('proctoring-indicator');
        
        if (existingIndicator) {
            existingIndicator.remove();
        }
        
        const indicator = document.createElement('div');
        indicator.id = 'proctoring-indicator';
        indicator.className = 'proctoring-indicator';
        
        switch (status) {
            case 'active':
                indicator.className += ' proctoring-active';
                indicator.innerHTML = '<i class="fas fa-eye"></i> Proctoring Active';
                break;
            case 'error':
                indicator.className += ' proctoring-violation';
                indicator.innerHTML = `<i class="fas fa-exclamation-triangle"></i> Error: ${message}`;
                break;
            case 'inactive':
                indicator.className += ' bg-secondary text-white';
                indicator.innerHTML = '<i class="fas fa-eye-slash"></i> Proctoring Inactive';
                break;
        }
        
        document.body.appendChild(indicator);
    }

    playWarningSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            // Create warning sound pattern
            oscillator.frequency.setValueAtTime(400, audioContext.currentTime);
            oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
            oscillator.frequency.setValueAtTime(400, audioContext.currentTime + 0.2);
            
            oscillator.type = 'square';
            gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
            
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.3);
        } catch (e) {
            console.log('Audio warning not available');
        }
    }

    getViolationSummary() {
        const summary = {
            total: this.violations.length,
            high: this.violations.filter(v => v.severity === 'high').length,
            medium: this.violations.filter(v => v.severity === 'medium').length,
            low: this.violations.filter(v => v.severity === 'low').length,
            types: {}
        };
        
        this.violations.forEach(v => {
            summary.types[v.type] = (summary.types[v.type] || 0) + 1;
        });
        
        return summary;
    }
    
    // Enhanced auto-termination functionality
    terminateQuizImmediately(reason) {
        if (this.isTerminated) return;
        
        this.isTerminated = true;
        console.error('Auto-terminating quiz:', reason);
        
        // Send termination request to server
        fetch(`/api/monitoring/auto-terminate/${this.attemptId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ reason: reason })
        }).then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showTerminationScreen(reason);
            }
        }).catch(error => {
            console.error('Failed to terminate quiz:', error);
            // Force termination anyway
            this.showTerminationScreen(reason);
        });
    }
    
    showTerminationScreen(reason) {
        // Create full-screen termination overlay
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: #dc3545;
            z-index: 10000;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            font-family: Arial, sans-serif;
        `;
        
        const messageBox = document.createElement('div');
        messageBox.style.cssText = `
            text-align: center;
            padding: 40px;
            max-width: 600px;
        `;
        
        messageBox.innerHTML = `
            <h1 style="margin-bottom: 30px; font-size: 3em;">? QUIZ TERMINATED</h1>
            <h2 style="margin-bottom: 20px;">Security Violation Detected</h2>
            <p style="font-size: 1.2em; margin-bottom: 30px;">${reason}</p>
            <p style="font-size: 1em;">Contact your instructor if you believe this is an error.</p>
            <p style="font-size: 0.9em; margin-top: 30px;">This session has been recorded for review.</p>
        `;
        
        overlay.appendChild(messageBox);
        document.body.appendChild(overlay);
        
        // Completely lock down the page
        this.lockdownPage();
        
        // Auto-redirect after 10 seconds
        setTimeout(() => {
            window.location.href = '/participant/dashboard';
        }, 10000);
    }
    
    lockdownPage() {
        // Block all keyboard events
        document.addEventListener('keydown', function(e) {
            e.preventDefault();
            e.stopPropagation();
            return false;
        }, true);
        
        // Block right-click
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            return false;
        }, true);
        
        // Block text selection
        document.addEventListener('selectstart', function(e) {
            e.preventDefault();
            return false;
        }, true);
    }
    
    // Enhanced device logging for security tracking
    logDeviceInfo() {
        const deviceInfo = {
            userAgent: navigator.userAgent,
            screenResolution: `${screen.width}x${screen.height}`,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language,
            platform: navigator.platform,
            cookieEnabled: navigator.cookieEnabled,
            onLine: navigator.onLine,
            quizId: this.quizId || null
        };
        
        deviceInfo.deviceType = this.detectDeviceType();
        deviceInfo.browserInfo = this.getBrowserInfo();
        
        // Send to server for logging
        fetch('/api/device-log', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(deviceInfo)
        }).catch(error => {
            console.error('Failed to log device info:', error);
        });
    }
    
    detectDeviceType() {
        const userAgent = navigator.userAgent;
        if (/tablet/i.test(userAgent)) return 'tablet';
        if (/mobile/i.test(userAgent)) return 'mobile';
        return 'desktop';
    }
    
    getBrowserInfo() {
        const userAgent = navigator.userAgent;
        let browser = 'Unknown';
        
        if (userAgent.indexOf('Chrome') > -1) browser = 'Chrome';
        else if (userAgent.indexOf('Firefox') > -1) browser = 'Firefox';
        else if (userAgent.indexOf('Safari') > -1) browser = 'Safari';
        else if (userAgent.indexOf('Edge') > -1) browser = 'Edge';
        
        return `${browser} ${navigator.appVersion}`;
    }

    // NEW: Helper methods for Moodle Proctoring Pro-style features
    showVerificationModal() {
        const modal = document.createElement('div');
        modal.id = 'face-verification-modal';
        modal.style.cssText = `
            position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.8); z-index: 10000; display: flex;
            align-items: center; justify-content: center; color: white;
        `;
        
        modal.innerHTML = `
            <div style="background: #343a40; padding: 30px; border-radius: 10px; text-align: center; max-width: 500px;">
                <h2 style="margin-bottom: 20px;">? Identity Verification Required</h2>
                <p style="margin-bottom: 20px;">Please verify your identity before starting the exam.</p>
                <p style="margin-bottom: 30px; font-size: 0.9em; color: #adb5bd;">
                    Look directly at the camera and ensure good lighting for best results.
                </p>
                <div id="verification-preview" style="margin-bottom: 20px; width: 320px; height: 240px; background: #000; border-radius: 8px; margin: 0 auto 20px;"></div>
                <button id="capture-verification-btn" class="btn btn-primary" style="margin-right: 10px;">
                    ? Capture & Verify
                </button>
                <button id="cancel-verification-btn" class="btn btn-secondary">Cancel</button>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Handle cancel
        document.getElementById('cancel-verification-btn').addEventListener('click', () => {
            this.hideVerificationModal();
            window.location.href = '/dashboard';
        });
    }

    async captureVerificationImage() {
        if (!this.videoElement || !this.canvas) {
            throw new Error('Camera not available for verification');
        }
        
        // Capture current frame
        this.context.drawImage(this.videoElement, 0, 0, 640, 480);
        return this.canvas.toDataURL('image/jpeg', this.config.imageQuality);
    }

    async verifyUserIdentity(imageData) {
        try {
            const response = await fetch('/api/proctoring/verify-identity', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image: imageData,
                    attemptId: this.attemptId
                })
            });
            
            const result = await response.json();
            return result.verified === true;
        } catch (error) {
            console.error('Identity verification failed:', error);
            return false; // Fail safe
        }
    }

    // ===== REAL-TIME NOTIFICATION SYSTEM =====
    notifyHostAdmin(message, severity = 'medium') {
        // Send immediate notification to hosts and admins
        const notification = {
            message,
            severity,
            student: this.getStudentInfo(),
            timestamp: new Date().toISOString(),
            attemptId: this.attemptId
        };

        // Send via real-time WebSocket if available
        if (window.realTimeSocket && window.realTimeSocket.connected) {
            window.realTimeSocket.emit('violation_alert', {
                student: this.getStudentInfo(),
                violationType: 'proctoring_violation',
                message: message,
                severity: severity,
                timestamp: new Date().toISOString(),
                attemptId: this.attemptId
            });
        }

        // Also send via HTTP API as backup
        fetch('/api/proctoring/notify-violation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(notification)
        }).catch(err => console.error('Failed to send violation notification:', err));
    }

    getStudentInfo() {
        // Get student identification info for notifications
        return {
            id: window.currentUserId || 'unknown',
            name: window.currentUserName || 'Unknown Student',
            email: window.currentUserEmail || 'unknown@example.com'
        };
    }

    setupScreenshotDetection() {
        // Enhanced screenshot detection beyond just PrintScreen key
        
        // Detect print screen attempts
        document.addEventListener('keyup', (e) => {
            if (e.key === 'PrintScreen') {
                this.logViolation('screenshot_attempt', 'Screenshot attempt detected (PrintScreen)', 'high');
                this.notifyHostAdmin('Student attempted to take screenshot', 'high');
            }
        });

        // Monitor clipboard for screenshot pastes
        document.addEventListener('paste', (e) => {
            const items = e.clipboardData?.items;
            if (items) {
                for (let item of items) {
                    if (item.type.indexOf('image') !== -1) {
                        this.logViolation('image_paste', 'Image pasted from clipboard (possible screenshot)', 'high');
                        this.notifyHostAdmin('Student pasted image from clipboard', 'high');
                        break;
                    }
                }
            }
        });
    }

    setupBrowserFocusMonitoring() {
        // Enhanced focus monitoring with multiple detection methods
        let focusLostTime = 0;

        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                focusLostTime = Date.now();
            } else if (focusLostTime > 0) {
                const timeAway = Date.now() - focusLostTime;
                if (timeAway > 3000) { // More than 3 seconds away
                    this.logViolation('extended_focus_loss', 
                        `Student was away for ${Math.round(timeAway/1000)} seconds`, 'high');
                    this.notifyHostAdmin(`Student was away from quiz for ${Math.round(timeAway/1000)} seconds`, 'high');
                }
                focusLostTime = 0;
            }
        });

        // Mouse leave detection (student left quiz area)
        document.addEventListener('mouseleave', () => {
            this.logViolation('mouse_left_window', 'Mouse cursor left the quiz window', 'low');
        });
    }

    hideVerificationModal() {
        const modal = document.getElementById('face-verification-modal');
        if (modal) modal.remove();
    }

    blockQuizAccess(message) {
        document.body.innerHTML = `
            <div style="display: flex; align-items: center; justify-content: center; height: 100vh; background: #dc3545; color: white; font-family: Arial;">
                <div style="text-align: center; max-width: 600px; padding: 40px;">
                    <h1 style="margin-bottom: 30px;">? Access Denied</h1>
                    <h3 style="margin-bottom: 20px;">Face Verification Failed</h3>
                    <p style="margin-bottom: 30px; font-size: 1.1em;">${message}</p>
                    <p>Please contact your instructor for assistance.</p>
                    <button onclick="window.location.href='/dashboard'" style="margin-top: 20px; padding: 10px 20px; background: white; color: #dc3545; border: none; border-radius: 5px; cursor: pointer;">
                        Return to Dashboard
                    </button>
                </div>
            </div>
        `;
    }

    async captureCurrentFrame() {
        if (!this.videoElement || !this.canvas) {
            throw new Error('Camera not available for capture');
        }
        
        this.context.drawImage(this.videoElement, 0, 0, 640, 480);
        return this.canvas.toDataURL('image/jpeg', this.config.imageQuality);
    }

    async sendCapturedImage(imageData) {
        try {
            await fetch('/api/proctoring/image-capture', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    image: imageData,
                    attemptId: this.attemptId,
                    timestamp: new Date().toISOString()
                })
            });
        } catch (error) {
            console.error('Failed to send captured image:', error);
        }
    }
}

// Global initialization function
function initializeProctoring(attemptId) {
    if (window.proctoringManager) {
        window.proctoringManager.stopMonitoring();
    }
    
    window.proctoringManager = new ProctoringManager(attemptId);
}

// Auto-cleanup when page unloads
window.addEventListener('beforeunload', () => {
    if (window.proctoringManager) {
        window.proctoringManager.stopMonitoring();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ProctoringManager;
}
