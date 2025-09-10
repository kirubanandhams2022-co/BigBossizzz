/**
 * Real-time Monitoring with WebSocket Support
 * Handles live violation alerts and system monitoring
 */

class RealTimeMonitoring {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.violationCount = { high: 0, medium: 0, low: 0 };
        
        this.init();
    }
    
    init() {
        // Initialize Socket.IO connection
        if (typeof io !== 'undefined') {
            this.socket = io({
                transports: ['websocket', 'polling'],
                upgrade: true,
                rememberUpgrade: true
            });
            
            this.setupSocketEvents();
        } else {
            console.warn('Socket.IO not loaded, falling back to polling');
            this.fallbackToPolling();
        }
    }
    
    setupSocketEvents() {
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.reconnectAttempts = 0;
            console.log('Connected to real-time monitoring');
            
            // Join monitoring room for hosts/admins
            if (window.userRole === 'host' || window.userRole === 'admin') {
                this.socket.emit('join_monitoring', {});
            }
            
            this.updateConnectionStatus(true);
        });
        
        this.socket.on('disconnect', () => {
            this.isConnected = false;
            console.log('Disconnected from real-time monitoring');
            this.updateConnectionStatus(false);
            this.attemptReconnect();
        });
        
        this.socket.on('new_violation', (data) => {
            this.handleNewViolation(data);
        });
        
        this.socket.on('status', (data) => {
            console.log('Status update:', data.msg);
        });
        
        this.socket.on('connect_error', (error) => {
            console.error('Connection error:', error);
            this.updateConnectionStatus(false);
            this.attemptReconnect();
        });
    }
    
    handleNewViolation(data) {
        console.log('New violation received:', data);
        
        // Update violation counts
        this.violationCount[data.severity]++;
        this.updateViolationStats();
        
        // Show real-time notification
        this.showViolationAlert(data);
        
        // Add to violation feed
        this.addViolationToFeed(data);
        
        // Play sound alert for high severity
        if (data.severity === 'high') {
            this.playAlertSound();
        }
    }
    
    showViolationAlert(data) {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `alert alert-${this.getSeverityClass(data.severity)} alert-dismissible fade show position-fixed`;
        toast.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            animation: slideIn 0.5s ease-out;
        `;
        
        toast.innerHTML = `
            <div class="d-flex align-items-center">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <div>
                    <strong>${data.student.name || 'Student'}</strong><br>
                    <small>${data.violation}</small>
                </div>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 10000);
    }
    
    addViolationToFeed(data) {
        const container = document.getElementById('violationsContainer');
        if (!container) return;
        
        const violationCard = this.createViolationCard(data);
        container.insertAdjacentHTML('afterbegin', violationCard);
        
        // Keep only latest 50 violations
        const cards = container.querySelectorAll('.violation-card');
        if (cards.length > 50) {
            for (let i = 50; i < cards.length; i++) {
                cards[i].remove();
            }
        }
    }
    
    createViolationCard(data) {
        const timestamp = new Date(data.timestamp).toLocaleTimeString();
        const severityClass = this.getSeverityClass(data.severity);
        
        return `
            <div class="violation-card severity-${data.severity} p-3 mb-2" style="animation: slideInLeft 0.5s ease-out;">
                <div class="d-flex align-items-start">
                    <div class="violation-type-icon bg-${severityClass} text-white me-3">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <div class="flex-grow-1">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="mb-0 fw-bold">${data.student.name || 'Unknown Student'}</h6>
                            <small class="text-muted">${timestamp}</small>
                        </div>
                        <p class="mb-1 text-dark">${data.violation}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">
                                <i class="fas fa-clock"></i> Real-time alert
                            </small>
                            <span class="badge bg-${severityClass}">
                                ${data.severity.toUpperCase()}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    updateViolationStats() {
        // Update dashboard counters
        const highElement = document.getElementById('highViolations');
        const mediumElement = document.getElementById('mediumViolations');
        const lowElement = document.getElementById('lowViolations');
        
        if (highElement) highElement.textContent = this.violationCount.high;
        if (mediumElement) mediumElement.textContent = this.violationCount.medium;
        if (lowElement) lowElement.textContent = this.violationCount.low;
    }
    
    updateConnectionStatus(connected) {
        const indicator = document.querySelector('.live-indicator');
        if (indicator) {
            indicator.style.background = connected ? '#28a745' : '#dc3545';
        }
        
        const statusText = document.getElementById('connectionStatus');
        if (statusText) {
            statusText.textContent = connected ? 'Connected' : 'Disconnected';
            statusText.className = connected ? 'text-success' : 'text-danger';
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts && !this.isConnected) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
            
            setTimeout(() => {
                if (this.socket) {
                    this.socket.connect();
                }
            }, Math.pow(2, this.reconnectAttempts) * 1000); // Exponential backoff
        }
    }
    
    fallbackToPolling() {
        console.log('Using polling fallback for real-time updates');
        setInterval(() => {
            this.pollForUpdates();
        }, 3000);
    }
    
    async pollForUpdates() {
        try {
            const response = await fetch('/api/monitoring/live-data');
            const data = await response.json();
            
            if (data.participants) {
                this.updateParticipantData(data.participants);
            }
        } catch (error) {
            console.error('Polling error:', error);
        }
    }
    
    updateParticipantData(participants) {
        const activeStudents = document.getElementById('activeStudents');
        if (activeStudents) {
            activeStudents.textContent = participants.length;
        }
    }
    
    getSeverityClass(severity) {
        switch (severity) {
            case 'high': return 'danger';
            case 'medium': return 'warning';
            case 'low': return 'success';
            default: return 'info';
        }
    }
    
    playAlertSound() {
        const audio = document.getElementById('alertSound');
        if (audio) {
            audio.play().catch(() => {
                // Ignore audio play errors (browser restrictions)
            });
        }
    }
    
    // Public methods for manual testing
    testViolation(severity = 'high') {
        if (this.socket && this.isConnected) {
            this.socket.emit('violation_alert', {
                student: { name: 'Test Student', id: 'test' },
                violation: 'Test violation for debugging',
                severity: severity,
                timestamp: new Date().toISOString(),
                attemptId: 'test-123'
            });
        }
    }
    
    getConnectionStatus() {
        return {
            connected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            violationCount: this.violationCount
        };
    }
}

// Initialize real-time monitoring when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize on monitoring pages
    if (document.getElementById('violationsContainer') || 
        document.querySelector('.live-indicator')) {
        
        window.realTimeMonitoring = new RealTimeMonitoring();
    }
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideInLeft {
        from { transform: translateX(-100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .violation-card {
        transition: all 0.3s ease;
        border-radius: 8px;
        border-left: 4px solid;
    }
    
    .violation-card.severity-high {
        border-left-color: #dc3545;
        background: linear-gradient(135deg, #ffeaea, #ffebee);
    }
    
    .violation-card.severity-medium {
        border-left-color: #ffc107;
        background: linear-gradient(135deg, #fffbf0, #fff8e1);
    }
    
    .violation-card.severity-low {
        border-left-color: #28a745;
        background: linear-gradient(135deg, #f0fdf4, #f7fff7);
    }
`;
document.head.appendChild(style);