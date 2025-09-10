/**
 * Enhanced Quiz Creation Interface
 * Provides smooth loading states and modern form experience
 */

class QuizCreationManager {
    constructor() {
        this.currentQuestionIndex = 0;
        this.questions = [];
        this.autoSaveEnabled = true;
        this.autoSaveInterval = null;
        this.isDirty = false;
        this.init();
    }

    init() {
        // Initialize auto-save
        this.startAutoSave();
        
        // Add loading states to forms
        this.enhanceFormSubmissions();
        
        // Add progress tracking
        this.initProgressTracking();
        
        // Add keyboard shortcuts
        this.addKeyboardShortcuts();
        
        // Initialize question creation flow
        this.initQuestionFlow();
    }

    enhanceFormSubmissions() {
        // Quiz settings form
        const quizForm = document.querySelector('form[method="POST"]');
        if (quizForm && !quizForm.hasAttribute('data-no-loading')) {
            quizForm.addEventListener('submit', (e) => {
                this.showLoadingState('Updating quiz settings...');
                const submitBtn = quizForm.querySelector('button[type="submit"]');
                if (submitBtn) {
                    const originalText = submitBtn.innerHTML;
                    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
                    submitBtn.disabled = true;
                    
                    // Re-enable after timeout as fallback
                    setTimeout(() => {
                        submitBtn.innerHTML = originalText;
                        submitBtn.disabled = false;
                    }, 5000);
                }
            });
        }

        // Question forms
        const questionForms = document.querySelectorAll('.question-form');
        questionForms.forEach(form => {
            form.addEventListener('submit', (e) => {
                this.showLoadingState('Adding question...');
                this.markClean(); // Question added, mark as clean
            });
        });
    }

    initProgressTracking() {
        // Create progress indicator
        const progressContainer = document.createElement('div');
        progressContainer.className = 'quiz-progress-container';
        progressContainer.innerHTML = `
            <div class="card border-primary mb-3">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h6 class="mb-0"><i class="fas fa-chart-line text-primary"></i> Creation Progress</h6>
                        <small class="text-muted" id="lastSaved">Auto-saved</small>
                    </div>
                    <div class="progress mb-2" style="height: 8px;">
                        <div class="progress-bar bg-primary" id="quizProgress" role="progressbar" style="width: 0%"></div>
                    </div>
                    <div class="row text-center">
                        <div class="col-4">
                            <small class="text-muted">Questions</small>
                            <div class="fw-bold text-primary" id="questionCount">0</div>
                        </div>
                        <div class="col-4">
                            <small class="text-muted">Points</small>
                            <div class="fw-bold text-success" id="totalPoints">0</div>
                        </div>
                        <div class="col-4">
                            <small class="text-muted">Status</small>
                            <div class="fw-bold text-info" id="quizStatus">Draft</div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Insert progress container
        const sidebar = document.querySelector('.col-lg-4');
        if (sidebar) {
            sidebar.insertBefore(progressContainer, sidebar.firstChild);
        }

        this.updateProgress();
    }

    updateProgress() {
        const questionCount = document.querySelectorAll('.accordion-item').length;
        const totalPoints = this.calculateTotalPoints();
        const completionPercentage = Math.min((questionCount / 5) * 100, 100); // Assume 5 questions for full progress

        const progressBar = document.getElementById('quizProgress');
        const questionCountEl = document.getElementById('questionCount');
        const totalPointsEl = document.getElementById('totalPoints');
        const statusEl = document.getElementById('quizStatus');

        if (progressBar) progressBar.style.width = `${completionPercentage}%`;
        if (questionCountEl) questionCountEl.textContent = questionCount;
        if (totalPointsEl) totalPointsEl.textContent = totalPoints;
        if (statusEl) {
            statusEl.textContent = questionCount === 0 ? 'Draft' : 
                                  questionCount < 3 ? 'In Progress' : 'Ready';
        }
    }

    calculateTotalPoints() {
        const pointsElements = document.querySelectorAll('.question-points');
        let total = 0;
        pointsElements.forEach(el => {
            const points = parseInt(el.textContent) || 0;
            total += points;
        });
        return total;
    }

    initQuestionFlow() {
        // Enhanced question modal
        const modal = document.getElementById('addQuestionModal');
        if (modal) {
            // Add step-by-step flow
            this.enhanceQuestionModal(modal);
        }

        // Add live preview
        this.addQuestionPreview();
    }

    enhanceQuestionModal(modal) {
        const modalBody = modal.querySelector('.modal-body');
        if (!modalBody) return;

        // Add question type selection step
        const originalContent = modalBody.innerHTML;
        modalBody.innerHTML = `
            <div class="question-creation-steps">
                <!-- Step 1: Question Type -->
                <div class="step-content" id="step1" style="display: block;">
                    <h5 class="mb-3"><i class="fas fa-list-ul"></i> Select Question Type</h5>
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <div class="card question-type-card" data-type="multiple_choice">
                                <div class="card-body text-center">
                                    <i class="fas fa-list-ul fa-2x text-primary mb-2"></i>
                                    <h6>Multiple Choice</h6>
                                    <small class="text-muted">Choose from multiple options</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6 mb-3">
                            <div class="card question-type-card" data-type="true_false">
                                <div class="card-body text-center">
                                    <i class="fas fa-check-double fa-2x text-success mb-2"></i>
                                    <h6>True/False</h6>
                                    <small class="text-muted">Simple true or false question</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6 mb-3">
                            <div class="card question-type-card" data-type="text">
                                <div class="card-body text-center">
                                    <i class="fas fa-pen fa-2x text-info mb-2"></i>
                                    <h6>Text Input</h6>
                                    <small class="text-muted">Open-ended text response</small>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-6 mb-3">
                            <div class="card question-type-card" data-type="essay">
                                <div class="card-body text-center">
                                    <i class="fas fa-file-text fa-2x text-warning mb-2"></i>
                                    <h6>Essay</h6>
                                    <small class="text-muted">Long-form response</small>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="d-flex justify-content-end">
                        <button type="button" class="btn btn-primary" id="nextToStep2" disabled>
                            Next <i class="fas fa-arrow-right"></i>
                        </button>
                    </div>
                </div>

                <!-- Step 2: Question Details -->
                <div class="step-content" id="step2" style="display: none;">
                    <h5 class="mb-3"><i class="fas fa-edit"></i> Question Details</h5>
                    ${originalContent}
                    <div class="d-flex justify-content-between">
                        <button type="button" class="btn btn-outline-secondary" id="backToStep1">
                            <i class="fas fa-arrow-left"></i> Back
                        </button>
                        <button type="button" class="btn btn-success" id="saveQuestion">
                            <i class="fas fa-save"></i> Save Question
                        </button>
                    </div>
                </div>
            </div>
        `;

        // Add step navigation logic
        this.addStepNavigation(modal);
    }

    addStepNavigation(modal) {
        let selectedType = null;

        // Question type selection
        modal.querySelectorAll('.question-type-card').forEach(card => {
            card.addEventListener('click', () => {
                // Remove selection from other cards
                modal.querySelectorAll('.question-type-card').forEach(c => 
                    c.classList.remove('border-primary', 'bg-light'));
                
                // Select this card
                card.classList.add('border-primary', 'bg-light');
                selectedType = card.dataset.type;
                
                // Enable next button
                document.getElementById('nextToStep2').disabled = false;
            });
        });

        // Step navigation
        document.getElementById('nextToStep2')?.addEventListener('click', () => {
            this.showStep(2);
            // Set the question type in the form
            const typeSelect = modal.querySelector('select[name="question_type"]');
            if (typeSelect && selectedType) {
                typeSelect.value = selectedType;
                typeSelect.dispatchEvent(new Event('change'));
            }
        });

        document.getElementById('backToStep1')?.addEventListener('click', () => {
            this.showStep(1);
        });
    }

    showStep(stepNumber) {
        document.querySelectorAll('.step-content').forEach(step => {
            step.style.display = 'none';
        });
        const targetStep = document.getElementById(`step${stepNumber}`);
        if (targetStep) {
            targetStep.style.display = 'block';
        }
    }

    addQuestionPreview() {
        // Add live preview panel
        const previewContainer = document.createElement('div');
        previewContainer.innerHTML = `
            <div class="card mt-3">
                <div class="card-header">
                    <h6><i class="fas fa-eye"></i> Live Preview</h6>
                </div>
                <div class="card-body" id="questionPreview">
                    <p class="text-muted text-center">Select question type to see preview</p>
                </div>
            </div>
        `;

        const modal = document.getElementById('addQuestionModal');
        if (modal) {
            const step2 = modal.querySelector('#step2');
            if (step2) {
                step2.appendChild(previewContainer);
            }
        }
    }

    startAutoSave() {
        if (!this.autoSaveEnabled) return;

        this.autoSaveInterval = setInterval(() => {
            if (this.isDirty) {
                this.performAutoSave();
            }
        }, 30000); // Auto-save every 30 seconds

        // Mark dirty when form changes
        document.addEventListener('input', (e) => {
            if (e.target.matches('input, textarea, select')) {
                this.markDirty();
            }
        });
    }

    markDirty() {
        this.isDirty = true;
        const lastSaved = document.getElementById('lastSaved');
        if (lastSaved) {
            lastSaved.textContent = 'Unsaved changes';
            lastSaved.classList.add('text-warning');
        }
    }

    markClean() {
        this.isDirty = false;
        const lastSaved = document.getElementById('lastSaved');
        if (lastSaved) {
            lastSaved.textContent = 'Auto-saved';
            lastSaved.classList.remove('text-warning');
        }
    }

    async performAutoSave() {
        try {
            // Get form data
            const quizForm = document.querySelector('form[method="POST"]');
            if (!quizForm) return;

            const formData = new FormData(quizForm);
            formData.append('auto_save', '1');

            const response = await fetch(window.location.href, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                this.markClean();
                this.showToast('Quiz auto-saved', 'success');
            }
        } catch (error) {
            console.error('Auto-save failed:', error);
        }
    }

    showLoadingState(message = 'Loading...') {
        if (window.loadingManager) {
            window.loadingManager.show(message);
        }
    }

    hideLoadingState() {
        if (window.loadingManager) {
            window.loadingManager.hide();
        }
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        // Add to toast container or create one
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(container);
        }

        container.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();

        // Remove after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    addKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+S to save
            if (e.ctrlKey && e.key === 's') {
                e.preventDefault();
                this.performAutoSave();
            }
            
            // Ctrl+Q to add question
            if (e.ctrlKey && e.key === 'q') {
                e.preventDefault();
                const addBtn = document.querySelector('[data-bs-target="#addQuestionModal"]');
                if (addBtn) addBtn.click();
            }
        });
    }
}

// Global functions for backwards compatibility
window.autoSaveProgress = function() {
    if (window.quizManager) {
        window.quizManager.performAutoSave();
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.quizManager = new QuizCreationManager();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function(e) {
    if (window.quizManager && window.quizManager.isDirty) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
    }
});