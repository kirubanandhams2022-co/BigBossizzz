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
        
        // Configuration
        this.config = {
            faceDetection: true,
            tabSwitchDetection: true,
            fullscreenEnforcement: false,
            screenshotDetection: true,
            audioMonitoring: false,
            mouseMoveTracking: true,
            keyboardMonitoring: true,
            windowBlurDetection: true,
            multipleTabDetection: true,
            rightClickDisabled: true,
            copyPasteDisabled: true,
            devToolsDetection: true
        };
        
        this.init();
    }

    async init() {
        console.log('Initializing proctoring system...');
        
        try {
            await this.requestPermissions();
            this.setupEventListeners();
            this.startMonitoring();
            this.showProctoringStatus('active');
        } catch (error) {
            console.error('Proctoring initialization failed:', error);
            this.showProctoringStatus('error', error.message);
        }
    }

    async requestPermissions() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Camera access not supported by this browser');
        }

        try {
            // Request camera and microphone access
            this.mediaStream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    frameRate: { ideal: 15 }
                },
                audio: this.config.audioMonitoring
            });

            // Setup video element for face detection
            this.setupVideoElement();
            
        } catch (error) {
            if (error.name === 'NotAllowedError') {
                throw new Error('Camera permission denied. Please allow camera access to continue.');
            } else if (error.name === 'NotFoundError') {
                throw new Error('No camera found. Please connect a camera to continue.');
            } else {
                throw new Error(`Camera access error: ${error.message}`);
            }
        }
    }

    setupVideoElement() {
        // Create hidden video element for face detection
        this.videoElement = document.createElement('video');
        this.videoElement.style.cssText = `
            position: fixed;
            top: 10px;
            right: 10px;
            width: 200px;
            height: 150px;
            z-index: 9999;
            border: 2px solid #ffc107;
            border-radius: 8px;
            background: #000;
        `;
        this.videoElement.autoplay = true;
        this.videoElement.muted = true;
        this.videoElement.srcObject = this.mediaStream;
        
        document.body.appendChild(this.videoElement);

        // Setup canvas for face detection
        this.canvas = document.createElement('canvas');
        this.context = this.canvas.getContext('2d');
        this.canvas.width = 640;
        this.canvas.height = 480;
    }

    setupEventListeners() {
        // Tab switch detection
        if (this.config.tabSwitchDetection) {
            document.addEventListener('visibilitychange', () => {
                if (document.hidden) {
                    this.logViolation('tab_switch', 'User switched away from quiz tab', 'high');
                }
            });
        }

        // Window blur detection
        if (this.config.windowBlurDetection) {
            window.addEventListener('blur', () => {
                this.logViolation('window_blur', 'Quiz window lost focus', 'medium');
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

        // Copy/paste prevention
        if (this.config.copyPasteDisabled) {
            document.addEventListener('keydown', (e) => {
                // Prevent Ctrl+C, Ctrl+V, Ctrl+A, Ctrl+X
                if (e.ctrlKey && ['c', 'v', 'a', 'x'].includes(e.key.toLowerCase())) {
                    e.preventDefault();
                    this.logViolation('copy_paste_attempt', `Attempted ${e.key.toUpperCase()} operation`, 'medium');
                    return false;
                }
                
                // Prevent F12, Ctrl+Shift+I (DevTools)
                if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I')) {
                    e.preventDefault();
                    this.logViolation('devtools_attempt', 'Attempted to open developer tools', 'high');
                    return false;
                }
            });
        }

        // Screenshot detection (print screen)
        if (this.config.screenshotDetection) {
            document.addEventListener('keyup', (e) => {
                if (e.key === 'PrintScreen') {
                    this.logViolation('screenshot_attempt', 'Print Screen key pressed', 'high');
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
        
        // Send to server
        this.sendViolationToServer(violation);
        
        // Show warning to user
        this.showViolationWarning(violation);
        
        console.warn('Proctoring violation:', violation);
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
                message = '⚠️ Security Violation: ';
                warningDiv.className = warningDiv.className.replace('alert-warning', 'alert-danger');
                break;
            case 'medium':
                message = '⚡ Proctoring Warning: ';
                break;
            case 'low':
                message = 'ℹ️ Proctoring Notice: ';
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
