/**
 * Drag and Drop Interface for Course and Quiz Management
 * Provides intuitive drag-and-drop functionality for reordering courses and quizzes
 */

class DragDropManager {
    constructor() {
        this.draggedElement = null;
        this.draggedIndex = null;
        this.container = null;
        this.onDropCallback = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.addDragDropStyles();
    }

    /**
     * Initialize drag-and-drop for a container
     * @param {string} containerSelector - CSS selector for the container
     * @param {string} itemSelector - CSS selector for draggable items
     * @param {function} onDropCallback - Callback function when item is dropped
     */
    initializeDragDrop(containerSelector, itemSelector, onDropCallback) {
        const container = document.querySelector(containerSelector);
        if (!container) return;

        // For table rows, use tbody as the actual drag container
        this.container = container.querySelector('tbody') || container;
        this.onDropCallback = onDropCallback;

        // Make items draggable
        const items = container.querySelectorAll(itemSelector);
        items.forEach((item, index) => {
            this.makeDraggable(item, index);
        });

        // Setup container drop zones
        this.setupDropZones(this.container);
    }

    makeDraggable(element, index) {
        element.draggable = true;
        element.dataset.originalIndex = index;
        
        // Add drag handle if not present
        if (!element.querySelector('.drag-handle')) {
            const dragHandle = document.createElement('div');
            dragHandle.className = 'drag-handle';
            dragHandle.innerHTML = '<i class="fas fa-grip-vertical"></i>';
            dragHandle.title = 'Drag to reorder';
            element.insertBefore(dragHandle, element.firstChild);
        }

        // Drag events
        element.addEventListener('dragstart', (e) => this.handleDragStart(e));
        element.addEventListener('dragend', (e) => this.handleDragEnd(e));
    }

    setupDropZones(container) {
        container.addEventListener('dragover', (e) => this.handleDragOver(e));
        container.addEventListener('drop', (e) => this.handleDrop(e));
    }

    handleDragStart(e) {
        this.draggedElement = e.target;
        this.draggedIndex = parseInt(e.target.dataset.originalIndex);
        
        e.target.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.target.outerHTML);

        // Add visual feedback
        setTimeout(() => {
            e.target.style.opacity = '0.5';
        }, 0);

        this.showDropIndicators();
    }

    handleDragEnd(e) {
        e.target.classList.remove('dragging');
        e.target.style.opacity = '';
        this.hideDropIndicators();
        
        // Clean up
        this.draggedElement = null;
        this.draggedIndex = null;
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';

        const afterElement = this.getDragAfterElement(e.clientY);
        const draggingElement = document.querySelector('.dragging');
        
        if (afterElement == null) {
            this.container.appendChild(draggingElement);
        } else {
            this.container.insertBefore(draggingElement, afterElement);
        }
    }

    handleDrop(e) {
        e.preventDefault();
        
        if (!this.draggedElement) return;

        const newOrder = this.getNewOrder();
        
        if (this.onDropCallback) {
            this.onDropCallback(newOrder);
        }

        this.updateVisualOrder();
        this.showSuccessAnimation();
    }

    getDragAfterElement(y) {
        const draggableElements = [...this.container.querySelectorAll('[draggable="true"]:not(.dragging)')];
        
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    getNewOrder() {
        const items = this.container.querySelectorAll('[draggable="true"]');
        return Array.from(items).map(item => {
            return {
                id: item.dataset.itemId,
                element: item
            };
        });
    }

    updateVisualOrder() {
        const items = this.container.querySelectorAll('[draggable="true"]');
        items.forEach((item, index) => {
            item.dataset.originalIndex = index;
        });
    }

    showDropIndicators() {
        const items = this.container.querySelectorAll('[draggable="true"]:not(.dragging)');
        items.forEach(item => {
            item.classList.add('drop-target');
        });
    }

    hideDropIndicators() {
        const items = this.container.querySelectorAll('[draggable="true"]');
        items.forEach(item => {
            item.classList.remove('drop-target');
        });
    }

    showSuccessAnimation() {
        // Create success indicator
        const indicator = document.createElement('div');
        indicator.className = 'reorder-success';
        indicator.innerHTML = '<i class="fas fa-check"></i> Order updated!';
        
        document.body.appendChild(indicator);
        
        setTimeout(() => {
            indicator.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            indicator.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(indicator);
            }, 300);
        }, 2000);
    }

    addDragDropStyles() {
        if (document.getElementById('drag-drop-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'drag-drop-styles';
        styles.textContent = `
            /* Drag Handle Styles */
            .drag-handle {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 20px;
                height: 20px;
                margin-right: 10px;
                cursor: grab;
                color: #6c757d;
                border-radius: 3px;
                transition: all 0.2s ease;
            }

            .drag-handle:hover {
                background-color: #e9ecef;
                color: #495057;
            }

            .drag-handle:active {
                cursor: grabbing;
            }

            /* Dragging States */
            [draggable="true"].dragging {
                opacity: 0.5 !important;
                transform: rotate(2deg);
                box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                z-index: 1000;
                position: relative;
            }

            [draggable="true"].drop-target {
                border: 2px dashed #007bff;
                background-color: rgba(0,123,255,0.1);
                transition: all 0.2s ease;
            }

            [draggable="true"] {
                transition: all 0.2s ease;
                position: relative;
            }

            [draggable="true"]:hover .drag-handle {
                background-color: #007bff;
                color: white;
            }

            /* Success Animation */
            .reorder-success {
                position: fixed;
                top: 20px;
                right: 20px;
                background: #28a745;
                color: white;
                padding: 12px 20px;
                border-radius: 6px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                font-weight: 500;
                z-index: 9999;
                transform: translateX(100%);
                opacity: 0;
                transition: all 0.3s ease;
            }

            .reorder-success.show {
                transform: translateX(0);
                opacity: 1;
            }

            .reorder-success i {
                margin-right: 8px;
            }

            /* Loading states */
            .reordering {
                pointer-events: none;
                opacity: 0.6;
            }

            .reordering::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(255,255,255,0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10;
            }

            /* Responsive adjustments */
            @media (max-width: 768px) {
                .drag-handle {
                    width: 24px;
                    height: 24px;
                }
                
                .reorder-success {
                    top: 10px;
                    right: 10px;
                    left: 10px;
                    text-align: center;
                }
            }
        `;
        
        document.head.appendChild(styles);
    }

    setupEventListeners() {
        // Prevent default drag behavior on images
        document.addEventListener('dragstart', (e) => {
            if (e.target.tagName === 'IMG') {
                e.preventDefault();
            }
        });
    }
}

// Course Management Drag-and-Drop
class CourseDragDrop extends DragDropManager {
    constructor() {
        super();
        this.initializeCoursesDragDrop();
    }

    initializeCoursesDragDrop() {
        this.initializeDragDrop(
            '.courses-container, .course-list', 
            '.course-item, .course-card', 
            (newOrder) => this.updateCourseOrder(newOrder)
        );
    }

    async updateCourseOrder(newOrder) {
        const courseIds = newOrder.map(item => item.id);
        
        try {
            this.showLoadingState();
            
            const response = await fetch('/api/reorder-courses', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    course_ids: courseIds
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showSuccessAnimation();
            } else {
                this.showErrorMessage(result.message);
                this.revertOrder();
            }
        } catch (error) {
            console.error('Error updating course order:', error);
            this.showErrorMessage('Failed to update course order');
            this.revertOrder();
        } finally {
            this.hideLoadingState();
        }
    }

    showLoadingState() {
        if (this.container) {
            this.container.classList.add('reordering');
        }
    }

    hideLoadingState() {
        if (this.container) {
            this.container.classList.remove('reordering');
        }
    }

    showErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.textContent = message;
        
        if (this.container) {
            this.container.insertBefore(errorDiv, this.container.firstChild);
            setTimeout(() => {
                errorDiv.remove();
            }, 5000);
        }
    }

    revertOrder() {
        // Reload the page to revert changes
        window.location.reload();
    }
}

// Quiz Management Drag-and-Drop
class QuizDragDrop extends DragDropManager {
    constructor(courseId = null) {
        super();
        this.courseId = courseId;
        this.initializeQuizzesDragDrop();
    }

    initializeQuizzesDragDrop() {
        this.initializeDragDrop(
            '.quizzes-container, .quiz-list', 
            '.quiz-item, .quiz-card', 
            (newOrder) => this.updateQuizOrder(newOrder)
        );
    }

    async updateQuizOrder(newOrder) {
        const quizIds = newOrder.map(item => item.id);
        
        try {
            this.showLoadingState();
            
            const response = await fetch('/api/reorder-quizzes', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    quiz_ids: quizIds,
                    course_id: this.courseId
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showSuccessAnimation();
            } else {
                this.showErrorMessage(result.message);
                this.revertOrder();
            }
        } catch (error) {
            console.error('Error updating quiz order:', error);
            this.showErrorMessage('Failed to update quiz order');
            this.revertOrder();
        } finally {
            this.hideLoadingState();
        }
    }

    showLoadingState() {
        if (this.container) {
            this.container.classList.add('reordering');
        }
    }

    hideLoadingState() {
        if (this.container) {
            this.container.classList.remove('reordering');
        }
    }

    showErrorMessage(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger';
        errorDiv.textContent = message;
        
        if (this.container) {
            this.container.insertBefore(errorDiv, this.container.firstChild);
            setTimeout(() => {
                errorDiv.remove();
            }, 5000);
        }
    }

    revertOrder() {
        // Reload the page to revert changes
        window.location.reload();
    }
}

// Auto-initialize based on page context
document.addEventListener('DOMContentLoaded', function() {
    // Initialize course drag-and-drop if course elements are present
    if (document.querySelector('.courses-container, .course-list')) {
        new CourseDragDrop();
    }
    
    // Initialize quiz drag-and-drop if quiz elements are present
    if (document.querySelector('.quizzes-container, .quiz-list')) {
        const courseId = document.querySelector('[data-course-id]')?.dataset.courseId;
        new QuizDragDrop(courseId);
    }
});

// Export for external use
window.DragDropManager = DragDropManager;
window.CourseDragDrop = CourseDragDrop;
window.QuizDragDrop = QuizDragDrop;