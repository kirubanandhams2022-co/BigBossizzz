// Quiz.js - Enhanced quiz functionality with proctoring integration and heatmap tracking

class HeatmapTracker {
    constructor(attemptId) {
        this.attemptId = attemptId;
        this.questionStartTimes = new Map();
        this.interactionQueue = [];
        this.isTracking = true;
        this.flushInterval = null;
        this.currentQuestionId = null;
        
        this.initializeTracking();
    }
    
    initializeTracking() {
        if (!this.isTracking) return;
        
        // Store event listeners for cleanup
        this.eventListeners = [];
        
        // Start periodic data flushing
        this.flushInterval = setInterval(() => {
            this.flushInteractions();
        }, 5000); // Flush every 5 seconds
        
        // Track mouse clicks
        this.clickHandler = (e) => this.trackInteraction('click', e);
        document.addEventListener('click', this.clickHandler);
        this.eventListeners.push(['document', 'click', this.clickHandler]);
        
        // Track mouse movement (throttled)
        this.setupMouseMovementTracking();
        
        // Track mouse hovers on question elements
        document.querySelectorAll('.question-card, .question-input, .form-check').forEach(element => {
            const enterHandler = (e) => this.trackInteraction('hover_start', e);
            const leaveHandler = (e) => this.trackInteraction('hover_end', e);
            
            element.addEventListener('mouseenter', enterHandler);
            element.addEventListener('mouseleave', leaveHandler);
            
            this.eventListeners.push(['element', element, 'mouseenter', enterHandler]);
            this.eventListeners.push(['element', element, 'mouseleave', leaveHandler]);
        });
        
        // Track question focus/visibility changes
        this.setupQuestionVisibilityTracking();
        
        // Track scroll behavior
        this.setupScrollTracking();
        
        // Track window focus/blur
        this.focusHandler = () => this.trackInteraction('window_focus');
        this.blurHandler = () => this.trackInteraction('window_blur');
        
        window.addEventListener('focus', this.focusHandler);
        window.addEventListener('blur', this.blurHandler);
        
        this.eventListeners.push(['window', 'focus', this.focusHandler]);
        this.eventListeners.push(['window', 'blur', this.blurHandler]);
        
        // Setup final data delivery on page unload
        this.setupFinalDelivery();
    }
    
    setupMouseMovementTracking() {
        let lastMouseTime = 0;
        let lastX = -1, lastY = -1;
        const MOUSE_THROTTLE = 100; // Limit to ~10 Hz
        
        this.mouseMoveHandler = (e) => {
            const now = Date.now();
            
            // Throttle mouse movement events
            if (now - lastMouseTime < MOUSE_THROTTLE) return;
            
            // Skip if mouse hasn't moved significantly
            const deltaX = Math.abs(e.clientX - lastX);
            const deltaY = Math.abs(e.clientY - lastY);
            if (deltaX < 5 && deltaY < 5) return;
            
            lastMouseTime = now;
            lastX = e.clientX;
            lastY = e.clientY;
            
            this.trackInteraction('mouse_move', e);
        };
        
        document.addEventListener('mousemove', this.mouseMoveHandler);
        this.eventListeners.push(['document', 'mousemove', this.mouseMoveHandler]);
    }
    
    setupScrollTracking() {
        let scrollTimeout;
        this.scrollHandler = () => {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(() => {
                this.trackInteraction('scroll', null, {
                    scrollTop: window.pageYOffset,
                    scrollLeft: window.pageXOffset
                });
            }, 150); // Debounce scroll events
        };
        
        document.addEventListener('scroll', this.scrollHandler);
        this.eventListeners.push(['document', 'scroll', this.scrollHandler]);
    }
    
    setupFinalDelivery() {
        // Use beforeunload and visibilitychange for final data delivery
        this.beforeUnloadHandler = (e) => {
            this.sendFinalBatch();
        };
        
        this.visibilityChangeHandler = () => {
            if (document.visibilityState === 'hidden') {
                this.sendFinalBatch();
            }
        };
        
        window.addEventListener('beforeunload', this.beforeUnloadHandler);
        document.addEventListener('visibilitychange', this.visibilityChangeHandler);
        
        this.eventListeners.push(['window', 'beforeunload', this.beforeUnloadHandler]);
        this.eventListeners.push(['document', 'visibilitychange', this.visibilityChangeHandler]);
    }
    
    setupQuestionVisibilityTracking() {
        // Use Intersection Observer to track which questions are visible
        this.visibilityObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const questionCard = entry.target;
                const questionId = this.getQuestionIdFromElement(questionCard);
                
                if (entry.isIntersecting) {
                    // Question came into view - only start timing if not already tracking
                    if (!this.questionStartTimes.has(questionId)) {
                        this.startQuestionTiming(questionId);
                        this.trackInteraction('question_view_start', null, {
                            questionId: questionId,
                            visibility: entry.intersectionRatio
                        });
                    }
                } else {
                    // Question left view - only end timing if we were tracking
                    if (this.questionStartTimes.has(questionId)) {
                        this.endQuestionTiming(questionId);
                        this.trackInteraction('question_view_end', null, {
                            questionId: questionId
                        });
                    }
                }
            });
        }, {
            threshold: [0.1, 0.5, 0.9] // Track partial visibility
        });
        
        // Observe all question cards
        document.querySelectorAll('.question-card').forEach(card => {
            this.visibilityObserver.observe(card);
        });
    }
    
    getQuestionIdFromElement(element) {
        // Extract question ID from element attributes or content
        const questionIdAttr = element.getAttribute('data-question-id');
        if (questionIdAttr) return parseInt(questionIdAttr);
        
        // Try to find from input names
        const inputs = element.querySelectorAll('.question-input');
        if (inputs.length > 0) {
            const name = inputs[0].name;
            const match = name.match(/question_(\d+)/);
            if (match) return parseInt(match[1]);
        }
        
        // Fallback: use element position
        const allQuestions = document.querySelectorAll('.question-card');
        const index = Array.from(allQuestions).indexOf(element);
        return index >= 0 ? index + 1 : null;
    }
    
    startQuestionTiming(questionId) {
        if (questionId && !this.questionStartTimes.has(questionId)) {
            this.questionStartTimes.set(questionId, Date.now());
        }
    }
    
    endQuestionTiming(questionId) {
        if (questionId && this.questionStartTimes.has(questionId)) {
            const startTime = this.questionStartTimes.get(questionId);
            const timeSpent = Date.now() - startTime;
            
            this.trackInteraction('question_time', null, {
                questionId: questionId,
                timeSpent: timeSpent
            });
            
            this.questionStartTimes.delete(questionId);
        }
    }
    
    trackInteraction(type, event = null, additionalData = {}) {
        if (!this.isTracking) return;
        
        const interaction = {
            type: type,
            timestamp: Date.now(),
            attemptId: this.attemptId,
            ...additionalData
        };
        
        // Add event-specific data
        if (event) {
            interaction.x = event.clientX;
            interaction.y = event.clientY;
            interaction.target = this.getElementInfo(event.target);
            
            // Get question context
            const questionElement = event.target.closest('.question-card');
            if (questionElement) {
                interaction.questionId = this.getQuestionIdFromElement(questionElement);
            }
        }
        
        // Add to queue
        this.interactionQueue.push(interaction);
        
        // If queue is getting large, flush immediately
        if (this.interactionQueue.length >= 50) {
            this.flushInteractions();
        }
    }
    
    getElementInfo(element) {
        if (!element) return null;
        
        return {
            tagName: element.tagName,
            className: element.className,
            id: element.id,
            type: element.type || null,
            name: element.name || null,
            value: element.type === 'radio' ? element.value : null
        };
    }
    
    async flushInteractions() {
        if (this.interactionQueue.length === 0) return;
        
        const batch = [...this.interactionQueue];
        this.interactionQueue = [];
        
        try {
            // Send as single batched request
            await this.sendInteractionBatch(batch);
        } catch (error) {
            console.warn('Failed to send interaction batch:', error);
            // Re-queue failed interactions (up to a limit) 
            if (this.interactionQueue.length < 100) {
                this.interactionQueue.unshift(...batch);
            }
        }
    }
    
    async sendInteractionBatch(interactions) {
        if (interactions.length === 0) return;
        
        try {
            const response = await fetch('/api/heatmap/interaction/batch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    interactions: interactions,
                    attemptId: this.attemptId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.warn('Failed to send interaction batch:', error);
            throw error;
        }
    }
    
    sendFinalBatch() {
        // Use sendBeacon for guaranteed delivery on page unload
        if (this.interactionQueue.length === 0) return;
        
        const batch = [...this.interactionQueue];
        this.interactionQueue = [];
        
        try {
            if (navigator.sendBeacon) {
                const data = JSON.stringify({
                    interactions: batch,
                    attemptId: this.attemptId,
                    final: true
                });
                
                navigator.sendBeacon('/api/heatmap/interaction/batch', data);
            } else {
                // Fallback for browsers without sendBeacon
                this.sendInteractionBatch(batch).catch(() => {
                    // Silent failure on unload
                });
            }
        } catch (error) {
            console.warn('Failed to send final batch:', error);
        }
    }
    
    trackAnswerChange(questionId, answerValue, answerType) {
        this.trackInteraction('answer_change', null, {
            questionId: questionId,
            answerValue: answerValue,
            answerType: answerType,
            timestamp: Date.now()
        });
    }
    
    trackQuestionFocus(questionId) {
        this.currentQuestionId = questionId;
        this.startQuestionTiming(questionId);
        this.trackInteraction('question_focus', null, {
            questionId: questionId
        });
    }
    
    trackQuestionBlur(questionId) {
        if (this.currentQuestionId === questionId) {
            this.endQuestionTiming(questionId);
            this.currentQuestionId = null;
        }
        this.trackInteraction('question_blur', null, {
            questionId: questionId
        });
    }
    
    destroy() {
        this.isTracking = false;
        
        // Send final batch
        this.sendFinalBatch();
        
        // Clear intervals
        if (this.flushInterval) {
            clearInterval(this.flushInterval);
            this.flushInterval = null;
        }
        
        // Remove all event listeners
        this.eventListeners.forEach(([target, eventOrElement, typeOrHandler, handler]) => {
            if (target === 'document') {
                document.removeEventListener(eventOrElement, typeOrHandler);
            } else if (target === 'window') {
                window.removeEventListener(eventOrElement, typeOrHandler);
            } else if (target === 'element') {
                eventOrElement.removeEventListener(typeOrHandler, handler);
            }
        });
        this.eventListeners = [];
        
        // Disconnect intersection observer
        if (this.visibilityObserver) {
            this.visibilityObserver.disconnect();
            this.visibilityObserver = null;
        }
        
        // Clear question timing
        this.questionStartTimes.clear();
    }
}

class QuizManager {
    constructor(timeLimit, attemptId) {
        this.timeLimit = timeLimit * 60; // Convert to seconds
        this.timeRemaining = this.timeLimit;
        this.attemptId = attemptId;
        this.timerInterval = null;
        this.autoSaveInterval = null;
        this.answers = new Map();
        this.isSubmitted = false;
        
        // Initialize heatmap tracking
        this.heatmapTracker = new HeatmapTracker(attemptId);
        
        this.init();
    }

    init() {
        this.startTimer();
        this.setupEventListeners();
        this.startAutoSave();
        this.loadExistingAnswers();
        this.updateProgress();
        this.preventUnload();
    }

    startTimer() {
        const timerElement = document.getElementById('timer');
        if (!timerElement) return;

        this.timerInterval = setInterval(() => {
            this.timeRemaining--;
            this.updateTimerDisplay();
            
            // Warning notifications
            if (this.timeRemaining === 300) { // 5 minutes
                this.showTimeWarning('5 minutes remaining!');
                timerElement.classList.add('time-warning');
            }
            
            if (this.timeRemaining === 60) { // 1 minute
                this.showTimeWarning('1 minute remaining!', 'danger');
                timerElement.classList.remove('time-warning');
                timerElement.classList.add('time-critical');
            }
            
            // Auto-submit when time runs out
            if (this.timeRemaining <= 0) {
                this.autoSubmitQuiz();
            }
        }, 1000);
    }

    updateTimerDisplay() {
        const timerElement = document.getElementById('timer');
        if (!timerElement) return;

        const minutes = Math.floor(this.timeRemaining / 60);
        const seconds = this.timeRemaining % 60;
        const display = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        
        timerElement.textContent = display;
        
        // Update page title with remaining time
        document.title = `[${display}] Quiz in Progress`;
    }

    setupEventListeners() {
        // Answer change listeners with enhanced tracking
        document.querySelectorAll('.question-input').forEach(input => {
            if (input.type === 'radio') {
                input.addEventListener('change', (e) => {
                    this.handleAnswerChange(e.target.name, e.target.value, 'radio');
                });
                
                // Track focus events for questions
                input.addEventListener('focus', (e) => {
                    const questionId = this.extractQuestionId(e.target.name);
                    if (questionId && this.heatmapTracker) {
                        this.heatmapTracker.trackQuestionFocus(questionId);
                    }
                });
                
                input.addEventListener('blur', (e) => {
                    const questionId = this.extractQuestionId(e.target.name);
                    if (questionId && this.heatmapTracker) {
                        this.heatmapTracker.trackQuestionBlur(questionId);
                    }
                });
                
            } else if (input.tagName === 'TEXTAREA') {
                input.addEventListener('input', (e) => {
                    this.handleAnswerChange(e.target.name, e.target.value, 'text');
                });
                
                // Enhanced tracking for text inputs
                input.addEventListener('focus', (e) => {
                    const questionId = this.extractQuestionId(e.target.name);
                    if (questionId && this.heatmapTracker) {
                        this.heatmapTracker.trackQuestionFocus(questionId);
                    }
                });
                
                input.addEventListener('blur', (e) => {
                    const questionId = this.extractQuestionId(e.target.name);
                    if (questionId && this.heatmapTracker) {
                        this.heatmapTracker.trackQuestionBlur(questionId);
                    }
                });
                
                // Track typing patterns
                let typingTimer;
                input.addEventListener('keydown', (e) => {
                    clearTimeout(typingTimer);
                    typingTimer = setTimeout(() => {
                        if (this.heatmapTracker) {
                            this.heatmapTracker.trackInteraction('typing_pause', null, {
                                questionId: this.extractQuestionId(e.target.name),
                                textLength: e.target.value.length
                            });
                        }
                    }, 1000); // 1 second pause indicates end of typing burst
                });
            }
        });

        // Form submission
        const quizForm = document.getElementById('quizForm');
        if (quizForm) {
            quizForm.addEventListener('submit', (e) => {
                if (!this.isSubmitted) {
                    e.preventDefault();
                    this.showSubmissionConfirmation();
                }
            });
        }

        // Save draft button
        const saveDraftBtn = document.querySelector('[onclick="saveDraft()"]');
        if (saveDraftBtn) {
            saveDraftBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.saveDraft();
            });
        }

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+S to save draft
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.saveDraft();
            }
            // Ctrl+Enter to submit (if confirmed)
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.showSubmissionConfirmation();
            }
        });
    }

    handleAnswerChange(questionName, value, type) {
        this.answers.set(questionName, { value, type, timestamp: new Date() });
        this.updateProgress();
        
        // Track answer change for heatmap
        const questionId = this.extractQuestionId(questionName);
        if (questionId && this.heatmapTracker) {
            this.heatmapTracker.trackAnswerChange(questionId, value, type);
        }
        
        // Auto-save after answer change (debounced)
        clearTimeout(this.autoSaveTimeout);
        this.autoSaveTimeout = setTimeout(() => {
            this.saveDraft(false); // Silent save
        }, 2000);
    }
    
    extractQuestionId(questionName) {
        // Extract question ID from question name (e.g., "question_5" -> 5)
        const match = questionName.match(/question_(\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    updateProgress() {
        const totalQuestions = document.querySelectorAll('.question-card').length;
        let answeredQuestions = 0;
        
        // Count answered questions
        const questionNames = new Set();
        document.querySelectorAll('.question-input').forEach(input => {
            if (input.type === 'radio' && input.checked) {
                questionNames.add(input.name);
            } else if (input.tagName === 'TEXTAREA' && input.value.trim()) {
                questionNames.add(input.name);
            }
        });
        
        answeredQuestions = questionNames.size;
        const percentage = totalQuestions > 0 ? (answeredQuestions / totalQuestions) * 100 : 0;
        
        // Update progress bar
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', percentage);
            
            if (percentage === 100) {
                progressBar.classList.add('bg-success');
                progressBar.classList.remove('bg-primary');
            } else {
                progressBar.classList.remove('bg-success');
                progressBar.classList.add('bg-primary');
            }
        }
        
        if (progressText) {
            progressText.textContent = `${answeredQuestions} of ${totalQuestions} answered`;
        }

        return { answered: answeredQuestions, total: totalQuestions, percentage };
    }

    showSubmissionConfirmation() {
        const progress = this.updateProgress();
        const unanswered = progress.total - progress.answered;
        
        // Update modal content
        const summaryElement = document.getElementById('submissionSummary');
        if (summaryElement) {
            let message = `You have answered ${progress.answered} out of ${progress.total} questions.`;
            if (unanswered > 0) {
                message += ` ${unanswered} questions remain unanswered and will be marked as incorrect.`;
            }
            summaryElement.textContent = message;
        }
        
        // Show confirmation modal
        const submitModal = document.getElementById('submitModal');
        if (submitModal) {
            const modal = new bootstrap.Modal(submitModal);
            modal.show();
            
            // Setup confirm button
            const confirmBtn = submitModal.querySelector('.btn-success');
            if (confirmBtn) {
                confirmBtn.onclick = () => {
                    modal.hide();
                    this.submitQuiz();
                };
            }
        } else {
            // Fallback to simple confirm dialog
            const confirmed = confirm(`Are you sure you want to submit your quiz?\n\nAnswered: ${progress.answered}/${progress.total} questions\n\nThis action cannot be undone.`);
            if (confirmed) {
                this.submitQuiz();
            }
        }
    }

    submitQuiz() {
        if (this.isSubmitted) return;
        
        this.isSubmitted = true;
        this.clearTimers();
        
        // Show loading state
        this.showLoadingState('Submitting quiz...');
        
        // Submit the form
        const quizForm = document.getElementById('quizForm');
        if (quizForm) {
            // Add submission timestamp
            const timestampInput = document.createElement('input');
            timestampInput.type = 'hidden';
            timestampInput.name = 'submission_timestamp';
            timestampInput.value = new Date().toISOString();
            quizForm.appendChild(timestampInput);
            
            quizForm.submit();
        }
    }

    autoSubmitQuiz() {
        if (this.isSubmitted) return;
        
        this.showAlert('Time\'s up! Submitting quiz automatically...', 'warning');
        
        setTimeout(() => {
            this.submitQuiz();
        }, 2000);
    }

    saveDraft(showNotification = true) {
        if (this.isSubmitted) return;

        const formData = new FormData();
        formData.append('attempt_id', this.attemptId);
        formData.append('action', 'save_draft');
        
        // Collect current answers
        document.querySelectorAll('.question-input').forEach(input => {
            if (input.type === 'radio' && input.checked) {
                formData.append(input.name, input.value);
            } else if (input.tagName === 'TEXTAREA') {
                formData.append(input.name, input.value);
            }
        });

        // Save to localStorage as backup
        const draftData = {
            attemptId: this.attemptId,
            answers: Object.fromEntries(formData.entries()),
            timestamp: new Date().toISOString(),
            timeRemaining: this.timeRemaining
        };
        localStorage.setItem(`quiz_draft_${this.attemptId}`, JSON.stringify(draftData));
        
        if (showNotification) {
            this.showAlert('Draft saved successfully!', 'success', 3000);
        }
        
        // In a real implementation, you would also send this to the server
        // fetch('/api/save-draft', { method: 'POST', body: formData })
    }

    loadExistingAnswers() {
        // Try to load from localStorage first
        const draftData = localStorage.getItem(`quiz_draft_${this.attemptId}`);
        if (draftData) {
            try {
                const data = JSON.parse(draftData);
                // You could restore the draft here if needed
                console.log('Draft data found:', data);
            } catch (e) {
                console.error('Error parsing draft data:', e);
            }
        }
    }

    startAutoSave() {
        // Auto-save every 30 seconds
        this.autoSaveInterval = setInterval(() => {
            if (!this.isSubmitted) {
                this.saveDraft(false);
            }
        }, 30000);
    }

    clearTimers() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = null;
        }
        if (this.autoSaveTimeout) {
            clearTimeout(this.autoSaveTimeout);
            this.autoSaveTimeout = null;
        }
        
        // Clean up heatmap tracking
        if (this.heatmapTracker) {
            this.heatmapTracker.destroy();
            this.heatmapTracker = null;
        }
    }

    preventUnload() {
        window.addEventListener('beforeunload', (e) => {
            if (!this.isSubmitted) {
                const message = 'Are you sure you want to leave? Your quiz progress may be lost.';
                e.preventDefault();
                e.returnValue = message;
                return message;
            }
        });

        // Handle visibility change (tab switching)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && !this.isSubmitted) {
                // Log potential proctoring violation
                if (window.proctoringManager) {
                    window.proctoringManager.logEvent('tab_switch', 'User switched away from quiz tab');
                }
                
                // Track tab switch in heatmap
                if (this.heatmapTracker) {
                    this.heatmapTracker.trackInteraction('tab_hidden');
                }
            } else if (!this.isSubmitted) {
                // Track return to tab
                if (this.heatmapTracker) {
                    this.heatmapTracker.trackInteraction('tab_visible');
                }
            }
        });
    }

    showTimeWarning(message, type = 'warning') {
        this.showAlert(message, type, 5000);
        
        // Play notification sound if available
        this.playNotificationSound();
    }

    showAlert(message, type = 'info', duration = 5000) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = `
            top: 100px;
            right: 20px;
            z-index: 1050;
            max-width: 300px;
        `;
        
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, duration);
        }
    }

    showLoadingState(message) {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'quiz-loading';
        loadingDiv.className = 'position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center';
        loadingDiv.style.cssText = `
            background: rgba(0, 0, 0, 0.8);
            z-index: 9999;
        `;
        
        loadingDiv.innerHTML = `
            <div class="text-center text-white">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <h4>${message}</h4>
            </div>
        `;
        
        document.body.appendChild(loadingDiv);
    }

    playNotificationSound() {
        // Create and play a simple notification sound
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.5);
        } catch (e) {
            // Silently fail if audio context is not available
            console.log('Audio notification not available');
        }
    }

    // Utility methods
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }

    getQuestionProgress() {
        const questions = document.querySelectorAll('.question-card');
        const answered = [];
        const unanswered = [];
        
        questions.forEach((questionCard, index) => {
            const inputs = questionCard.querySelectorAll('.question-input');
            let hasAnswer = false;
            
            inputs.forEach(input => {
                if (input.type === 'radio' && input.checked) {
                    hasAnswer = true;
                } else if (input.tagName === 'TEXTAREA' && input.value.trim()) {
                    hasAnswer = true;
                }
            });
            
            if (hasAnswer) {
                answered.push(index + 1);
            } else {
                unanswered.push(index + 1);
            }
        });
        
        return { answered, unanswered };
    }
}

// Initialize quiz manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a quiz-taking page
    const quizForm = document.getElementById('quizForm');
    if (quizForm) {
        // Extract quiz parameters from the page
        const timeLimitElement = document.querySelector('[data-time-limit]');
        const attemptIdElement = document.querySelector('[data-attempt-id]');
        
        if (timeLimitElement && attemptIdElement) {
            const timeLimit = parseInt(timeLimitElement.dataset.timeLimit);
            const attemptId = parseInt(attemptIdElement.dataset.attemptId);
            
            // Initialize quiz manager
            window.quizManager = new QuizManager(timeLimit, attemptId);
        }
    }
});

// Global functions for backward compatibility
function updateProgress() {
    if (window.quizManager) {
        return window.quizManager.updateProgress();
    }
}

function saveDraft() {
    if (window.quizManager) {
        window.quizManager.saveDraft(true);
    }
}

function confirmSubmit() {
    if (window.quizManager) {
        window.quizManager.showSubmissionConfirmation();
    }
    return false; // Prevent default form submission
}

function submitQuiz() {
    if (window.quizManager) {
        window.quizManager.submitQuiz();
    }
}
