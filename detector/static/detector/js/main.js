// RealFace main.js - Handles image upload and analysis
document.addEventListener('DOMContentLoaded', () => {
    // Elements
    const dropArea = document.getElementById('drop-area');
    const imageInput = document.getElementById('image-input');
    const previewContainer = document.querySelector('.preview-container');
    const previewImage = document.getElementById('preview-image');
    const uploadForm = document.getElementById('upload-form');
    const analyzeBtn = document.getElementById('analyze-btn');
    const resultSection = document.getElementById('result-section');
    const uploadError = document.querySelector('.upload-error');
    const errorMessage = document.querySelector('.error-message');
    
    // File data
    let currentFile = null;
    
    // Event listeners for drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropArea.classList.add('dragover');
    }
    
    function unhighlight() {
        dropArea.classList.remove('dragover');
    }
    
    // Handle file drop
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            handleFiles(files);
        }
    }
    
    // Click to upload
    dropArea.addEventListener('click', () => {
        imageInput.click();
    });
    
    imageInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFiles(e.target.files);
        }
    });
    
    // Handle files
    function handleFiles(files) {
        const file = files[0];
        
        // Check file type
        if (!file.type.match('image/jpeg') && !file.type.match('image/png') && !file.type.match('image/webp')) {
            showError('Unsupported file type. Please upload JPEG, PNG, or WebP images.');
            return;
        }
        
        // Check file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            showError('File is too large. Maximum size is 10MB.');
            return;
        }
        
        // Hide error if previously shown
        hideError();
        
        // Show preview
        currentFile = file;
        previewImage.src = URL.createObjectURL(file);
        
        // Update info
        const fileName = document.querySelector('.file-name');
        const fileSize = document.querySelector('.file-size');
        const imageDimensions = document.querySelector('.image-dimensions');
        
        fileName.textContent = `Name: ${file.name}`;
        fileSize.textContent = `Size: ${formatFileSize(file.size)}`;
        
        // Get image dimensions
        const img = new Image();
        img.onload = () => {
            imageDimensions.textContent = `Dimensions: ${img.width}×${img.height}`;
            URL.revokeObjectURL(img.src);
        };
        img.src = previewImage.src;
        
        // Show preview and enable submit button
        previewContainer.classList.remove('d-none');
        analyzeBtn.disabled = false;
        
        // Hide upload prompt
        document.querySelector('.upload-prompt').style.display = 'none';
    }
    
    // Format file size
    function formatFileSize(bytes) {
        if (bytes < 1024) {
            return bytes + ' bytes';
        } else if (bytes < 1024 * 1024) {
            return (bytes / 1024).toFixed(1) + ' KB';
        } else {
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }
    }
    
    // Show error message
    function showError(message) {
        errorMessage.textContent = message;
        uploadError.classList.remove('d-none');
    }
    
    // Hide error message
    function hideError() {
        uploadError.classList.add('d-none');
    }
    
    // Handle form submission
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!currentFile) {
            showError('Please select an image to analyze.');
            return;
        }
        
        // Show loading state
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Analyzing...';
        
        // Create form data
        const formData = new FormData();
        formData.append('image', currentFile);
        
        // Add CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        try {
            // Send request
            const response = await fetch('/analyze/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            // Parse response
            const data = await response.json();
            
            if (data.status === 'success') {
                displayResults(data);
            } else {
                showError(data.message || 'An error occurred during analysis.');
            }
        } catch (error) {
            showError('Network error. Please try again.');
            console.error('Error:', error);
        } finally {
            // Reset button
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="fas fa-search"></i> Analyze Image';
        }
    });
    
    // Display results
    function displayResults(data) {
        // Set result text and class
        const resultText = document.querySelector('.result-text');
        resultText.textContent = data.result;
        resultText.className = 'result-text text-center fs-5';
        resultText.classList.add(data.result === 'Real Image' ? 'real' : 'ai');
        
        // Set confidence bar
        const progressBar = document.querySelector('.progress-bar');
        const confidence = data.confidence * 100;
        progressBar.style.width = `${confidence}%`;
        progressBar.setAttribute('aria-valuenow', confidence);
        progressBar.classList.add(data.result === 'Real Image' ? 'bg-success' : 'bg-danger');
        
        // Set confidence text
        document.querySelector('.confidence-text').textContent = `Confidence: ${confidence.toFixed(1)}%`;
        
        // Set details
        document.querySelector('.details-size').textContent = formatFileSize(data.details.size);
        document.querySelector('.details-dimensions').textContent = `${data.details.width}×${data.details.height}`;
        document.querySelector('.details-filename').textContent = data.details.filename;
        
        // Show result section
        resultSection.classList.remove('d-none');
        
        // Scroll to results
        resultSection.scrollIntoView({ behavior: 'smooth' });
    }
}); 