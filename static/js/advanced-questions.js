/**
 * Advanced Question Types JavaScript Module
 * Handles Code Submission, File Upload, and Drawing question types
 */

class AdvancedQuestionHandler {
    constructor() {
        this.codeEditors = new Map();
        this.canvases = new Map();
        this.uploadedFiles = new Map();
        this.init();
    }

    init() {
        this.setupQuestionTypeHandlers();
        this.setupCodeEditors();
        this.setupDrawingCanvases();
        this.setupFileUploads();
    }

    setupQuestionTypeHandlers() {
        // Handle question type changes in forms
        const questionTypeSelects = document.querySelectorAll('select[name*="question_type"]');
        
        questionTypeSelects.forEach(select => {
            select.addEventListener('change', (e) => {
                this.toggleAdvancedFields(e.target);
            });
            
            // Initialize on page load
            this.toggleAdvancedFields(select);
        });
    }

    toggleAdvancedFields(selectElement) {
        const questionType = selectElement.value;
        const container = selectElement.closest('.question-container') || selectElement.closest('form');
        
        if (!container) return;

        // Hide all advanced fields first
        this.hideAllAdvancedFields(container);

        // Show relevant fields based on question type
        switch (questionType) {
            case 'code_submission':
                this.showCodeSubmissionFields(container);
                break;
            case 'file_upload':
                this.showFileUploadFields(container);
                break;
            case 'drawing':
                this.showDrawingFields(container);
                break;
        }
    }

    hideAllAdvancedFields(container) {
        const advancedFields = [
            '.code-submission-fields',
            '.file-upload-fields', 
            '.drawing-fields',
            '.multiple-choice-fields'
        ];

        advancedFields.forEach(selector => {
            const field = container.querySelector(selector);
            if (field) {
                field.style.display = 'none';
            }
        });
    }

    showCodeSubmissionFields(container) {
        const codeFields = container.querySelector('.code-submission-fields');
        if (codeFields) {
            codeFields.style.display = 'block';
            this.initializeCodeEditor(container);
        }
    }

    showFileUploadFields(container) {
        const fileFields = container.querySelector('.file-upload-fields');
        if (fileFields) {
            fileFields.style.display = 'block';
        }
    }

    showDrawingFields(container) {
        const drawingFields = container.querySelector('.drawing-fields');
        if (drawingFields) {
            drawingFields.style.display = 'block';
            this.initializeDrawingCanvas(container);
        }
    }

    initializeCodeEditor(container) {
        const codeTextarea = container.querySelector('textarea[name*="starter_code"]');
        if (!codeTextarea || this.codeEditors.has(codeTextarea.id)) return;

        // Create a simple code editor with syntax highlighting
        const editorWrapper = document.createElement('div');
        editorWrapper.className = 'code-editor-wrapper';
        editorWrapper.innerHTML = `
            <div class="editor-toolbar">
                <select class="language-selector form-select form-select-sm">
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="java">Java</option>
                    <option value="cpp">C++</option>
                    <option value="sql">SQL</option>
                </select>
                <span class="editor-label">Starter Code:</span>
            </div>
            <div class="code-editor" contenteditable="true" style="
                font-family: 'Courier New', monospace;
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 10px;
                min-height: 200px;
                white-space: pre;
                overflow-x: auto;
            "></div>
        `;

        codeTextarea.style.display = 'none';
        codeTextarea.parentNode.insertBefore(editorWrapper, codeTextarea.nextSibling);

        const editor = editorWrapper.querySelector('.code-editor');
        const languageSelect = editorWrapper.querySelector('.language-selector');

        // Sync content between editor and textarea
        editor.addEventListener('input', () => {
            codeTextarea.value = editor.textContent;
        });

        // Update language selection
        languageSelect.addEventListener('change', () => {
            const programmingLanguageSelect = container.querySelector('select[name*="programming_language"]');
            if (programmingLanguageSelect) {
                programmingLanguageSelect.value = languageSelect.value;
            }
        });

        // Store editor reference
        this.codeEditors.set(codeTextarea.id, {
            editor: editor,
            textarea: codeTextarea,
            languageSelect: languageSelect
        });
    }

    initializeDrawingCanvas(container) {
        const canvasContainer = container.querySelector('.drawing-canvas-container');
        if (!canvasContainer) return;

        const canvas = document.createElement('canvas');
        canvas.width = 800;
        canvas.height = 600;
        canvas.style.border = '2px solid #dee2e6';
        canvas.style.borderRadius = '4px';
        canvas.style.backgroundColor = 'white';
        canvas.style.cursor = 'crosshair';

        const toolbar = document.createElement('div');
        toolbar.className = 'drawing-toolbar mb-2';
        toolbar.innerHTML = `
            <div class="btn-group" role="group">
                <button type="button" class="btn btn-outline-primary tool-btn active" data-tool="pen">
                    <i class="fas fa-pen"></i> Pen
                </button>
                <button type="button" class="btn btn-outline-primary tool-btn" data-tool="eraser">
                    <i class="fas fa-eraser"></i> Eraser
                </button>
                <button type="button" class="btn btn-outline-primary tool-btn" data-tool="line">
                    <i class="fas fa-minus"></i> Line
                </button>
                <button type="button" class="btn btn-outline-primary tool-btn" data-tool="rectangle">
                    <i class="fas fa-square"></i> Rectangle
                </button>
                <button type="button" class="btn btn-outline-primary tool-btn" data-tool="circle">
                    <i class="fas fa-circle"></i> Circle
                </button>
            </div>
            <div class="ms-3">
                <label>Color:</label>
                <input type="color" class="color-picker ms-1" value="#000000">
                <label class="ms-2">Size:</label>
                <input type="range" class="brush-size ms-1" min="1" max="20" value="3">
            </div>
            <button type="button" class="btn btn-warning ms-3 clear-canvas">
                <i class="fas fa-trash"></i> Clear
            </button>
        `;

        canvasContainer.innerHTML = '';
        canvasContainer.appendChild(toolbar);
        canvasContainer.appendChild(canvas);

        // Initialize drawing functionality
        this.setupDrawingEvents(canvas, toolbar, container);
        
        // Store canvas reference
        const questionId = container.dataset.questionId || 'new';
        this.canvases.set(questionId, canvas);
    }

    setupDrawingEvents(canvas, toolbar, container) {
        const ctx = canvas.getContext('2d');
        let isDrawing = false;
        let currentTool = 'pen';
        let currentColor = '#000000';
        let currentSize = 3;
        let startX, startY;

        // Tool selection
        toolbar.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                toolbar.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentTool = btn.dataset.tool;
            });
        });

        // Color and size controls
        const colorPicker = toolbar.querySelector('.color-picker');
        const brushSize = toolbar.querySelector('.brush-size');
        
        colorPicker.addEventListener('change', (e) => {
            currentColor = e.target.value;
        });

        brushSize.addEventListener('input', (e) => {
            currentSize = parseInt(e.target.value);
        });

        // Clear canvas
        toolbar.querySelector('.clear-canvas').addEventListener('click', () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            this.saveCanvasData(canvas, container);
        });

        // Drawing events
        canvas.addEventListener('mousedown', (e) => {
            isDrawing = true;
            const rect = canvas.getBoundingClientRect();
            startX = e.clientX - rect.left;
            startY = e.clientY - rect.top;

            ctx.beginPath();
            ctx.strokeStyle = currentColor;
            ctx.lineWidth = currentSize;
            ctx.lineCap = 'round';
        });

        canvas.addEventListener('mousemove', (e) => {
            if (!isDrawing) return;

            const rect = canvas.getBoundingClientRect();
            const currentX = e.clientX - rect.left;
            const currentY = e.clientY - rect.top;

            switch (currentTool) {
                case 'pen':
                    ctx.lineTo(currentX, currentY);
                    ctx.stroke();
                    break;
                case 'eraser':
                    ctx.globalCompositeOperation = 'destination-out';
                    ctx.arc(currentX, currentY, currentSize, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.globalCompositeOperation = 'source-over';
                    break;
            }
        });

        canvas.addEventListener('mouseup', (e) => {
            if (!isDrawing) return;
            isDrawing = false;

            const rect = canvas.getBoundingClientRect();
            const endX = e.clientX - rect.left;
            const endY = e.clientY - rect.top;

            switch (currentTool) {
                case 'line':
                    ctx.beginPath();
                    ctx.moveTo(startX, startY);
                    ctx.lineTo(endX, endY);
                    ctx.stroke();
                    break;
                case 'rectangle':
                    ctx.beginPath();
                    ctx.rect(startX, startY, endX - startX, endY - startY);
                    ctx.stroke();
                    break;
                case 'circle':
                    const radius = Math.sqrt(Math.pow(endX - startX, 2) + Math.pow(endY - startY, 2));
                    ctx.beginPath();
                    ctx.arc(startX, startY, radius, 0, Math.PI * 2);
                    ctx.stroke();
                    break;
            }

            // Save canvas data after drawing
            this.saveCanvasData(canvas, container);
        });
    }

    saveCanvasData(canvas, container) {
        const imageData = canvas.toDataURL('image/png');
        const hiddenInput = container.querySelector('input[name*="drawing_data"]') || 
                           this.createHiddenInput(container, 'drawing_data', '');
        hiddenInput.value = imageData;
    }

    setupFileUploads() {
        const fileInputs = document.querySelectorAll('input[type="file"][data-question-type="file_upload"]');
        
        fileInputs.forEach(input => {
            input.addEventListener('change', (e) => {
                this.handleFileUpload(e.target);
            });
        });
    }

    handleFileUpload(input) {
        const file = input.files[0];
        if (!file) return;

        const container = input.closest('.question-container') || input.closest('form');
        const preview = container.querySelector('.file-upload-preview') || 
                       this.createFilePreview(container, input);

        // Validate file type and size
        const allowedTypes = input.dataset.allowedTypes ? 
                           input.dataset.allowedTypes.split(',') : 
                           ['pdf', 'docx', 'jpg', 'png', 'txt'];
        
        const maxSize = parseInt(input.dataset.maxSize || '10') * 1024 * 1024; // Convert MB to bytes
        const fileExt = file.name.split('.').pop().toLowerCase();

        if (!allowedTypes.includes(fileExt)) {
            preview.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    Invalid file type. Allowed: ${allowedTypes.join(', ')}
                </div>
            `;
            input.value = '';
            return;
        }

        if (file.size > maxSize) {
            preview.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    File too large. Maximum size: ${input.dataset.maxSize || '10'}MB
                </div>
            `;
            input.value = '';
            return;
        }

        // Show file preview
        preview.innerHTML = `
            <div class="alert alert-success">
                <i class="fas fa-file"></i>
                <strong>${file.name}</strong> (${this.formatFileSize(file.size)})
                <button type="button" class="btn btn-sm btn-outline-danger ms-2 remove-file">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Add remove functionality
        preview.querySelector('.remove-file').addEventListener('click', () => {
            input.value = '';
            preview.innerHTML = '';
        });

        // Store file reference
        this.uploadedFiles.set(input.name, file);
    }

    createFilePreview(container, input) {
        const preview = document.createElement('div');
        preview.className = 'file-upload-preview mt-2';
        input.parentNode.insertBefore(preview, input.nextSibling);
        return preview;
    }

    createHiddenInput(container, name, value) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = name;
        input.value = value;
        container.appendChild(input);
        return input;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Public methods for form validation
    validateCodeSubmission(questionId) {
        const editor = this.codeEditors.get(questionId);
        if (editor && editor.textarea.value.trim() === '') {
            return { valid: false, message: 'Please provide code for this question.' };
        }
        return { valid: true };
    }

    validateFileUpload(questionId) {
        const fileInput = document.querySelector(`input[name="file_${questionId}"]`);
        if (fileInput && (!fileInput.files || fileInput.files.length === 0)) {
            return { valid: false, message: 'Please upload a file for this question.' };
        }
        return { valid: true };
    }

    validateDrawing(questionId) {
        const canvas = this.canvases.get(questionId);
        if (canvas) {
            const ctx = canvas.getContext('2d');
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const hasDrawing = imageData.data.some(channel => channel !== 0);
            
            if (!hasDrawing) {
                return { valid: false, message: 'Please create a drawing for this question.' };
            }
        }
        return { valid: true };
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.advancedQuestionHandler = new AdvancedQuestionHandler();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdvancedQuestionHandler;
}