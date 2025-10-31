// SACEL Main JavaScript

// Mobile menu functionality
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuButton = document.querySelector('.mobile-menu-button');
    const mobileMenu = document.querySelector('.mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!mobileMenuButton.contains(e.target) && !mobileMenu.contains(e.target)) {
                mobileMenu.classList.add('hidden');
            }
        });
        
        // Close mobile menu when window is resized to desktop size
        window.addEventListener('resize', function() {
            if (window.innerWidth >= 768) { // md breakpoint
                mobileMenu.classList.add('hidden');
            }
        });
    }
    
    // Auto-hide flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    if (alerts.length > 0) {
        setTimeout(function() {
            alerts.forEach(alert => {
                alert.style.opacity = '0';
                alert.style.transition = 'opacity 0.3s ease-in-out';
                setTimeout(() => {
                    if (alert.parentNode) {
                        alert.parentNode.removeChild(alert);
                    }
                }, 300);
            });
        }, 5000);
    }
    
    // Form validation enhancement
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('border-red-500');
                    
                    // Remove error styling when user starts typing
                    field.addEventListener('input', function() {
                        field.classList.remove('border-red-500');
                    }, { once: true });
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                showNotification('Please fill in all required fields.', 'error');
            }
        });
    });
    
    // File upload enhancement
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const fileName = this.files[0]?.name || 'No file selected';
            const label = this.parentNode.querySelector('.file-upload-label');
            if (label) {
                label.textContent = fileName;
            }
        });
    });
});

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} fixed top-4 right-4 z-50 max-w-sm fade-in`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

function toggleLoading(element, isLoading = true) {
    if (isLoading) {
        element.classList.add('loading');
        element.disabled = true;
    } else {
        element.classList.remove('loading');
        element.disabled = false;
    }
}

// AJAX helper function
function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };
    
    // Add CSRF token for POST, PUT, DELETE requests
    if (options.method && ['POST', 'PUT', 'DELETE'].includes(options.method.toUpperCase())) {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (csrfToken) {
            defaultOptions.headers['X-CSRFToken'] = csrfToken;
        }
    }
    
    const config = { ...defaultOptions, ...options };
    
    return fetch(url, config)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Request failed:', error);
            showNotification('An error occurred. Please try again.', 'error');
            throw error;
        });
}

// Search functionality enhancement
function initializeSearch() {
    const searchForms = document.querySelectorAll('[data-search-form]');
    
    searchForms.forEach(form => {
        const searchInput = form.querySelector('input[type="text"]');
        let searchTimeout;
        
        if (searchInput) {
            searchInput.addEventListener('input', function() {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    performSearch(this.value, form);
                }, 300);
            });
        }
    });
}

function performSearch(query, form) {
    if (query.length < 2) return;
    
    const resultsContainer = document.querySelector('[data-search-results]');
    if (!resultsContainer) return;
    
    toggleLoading(resultsContainer);
    
    // This would be replaced with actual search endpoint
    console.log('Searching for:', query);
    
    // Simulated search results
    setTimeout(() => {
        toggleLoading(resultsContainer, false);
        showNotification(`Showing results for "${query}"`, 'info');
    }, 500);
}

// Initialize components when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
    initializeAITools();
    initializeAssignmentForm();
});

// AI Tools functionality
function initializeAITools() {
    const generateQuestionsBtn = document.getElementById('generateQuestions');
    const generateRubricBtn = document.getElementById('generateRubric');
    const enhanceInstructionsBtn = document.getElementById('enhanceInstructions');
    const useGeneratedBtn = document.getElementById('useGeneratedBtn');
    const regenerateBtn = document.getElementById('regenerateBtn');
    const closePreviewBtn = document.getElementById('closePreviewBtn');
    
    if (generateQuestionsBtn) {
        generateQuestionsBtn.addEventListener('click', () => generateAIContent('questions'));
    }
    
    if (generateRubricBtn) {
        generateRubricBtn.addEventListener('click', () => generateAIContent('rubric'));
    }
    
    if (enhanceInstructionsBtn) {
        enhanceInstructionsBtn.addEventListener('click', () => generateAIContent('instructions'));
    }
    
    if (useGeneratedBtn) {
        useGeneratedBtn.addEventListener('click', useGeneratedContent);
    }
    
    if (regenerateBtn) {
        regenerateBtn.addEventListener('click', () => regenerateContent());
    }
    
    if (closePreviewBtn) {
        closePreviewBtn.addEventListener('click', closePreview);
    }
}

let currentGenerationType = '';
let currentGeneratedContent = null;

function generateAIContent(type) {
    currentGenerationType = type;
    
    // Get form data
    const subject = document.getElementById('subject')?.value;
    const gradeLevel = document.getElementById('grade_level')?.value;
    const title = document.getElementById('title')?.value;
    const topic = document.getElementById('topic')?.value;
    const assignmentType = document.getElementById('assignment_type')?.value;
    const difficulty = document.getElementById('aiDifficulty')?.value || 'medium';
    const questionCount = document.getElementById('aiQuestionCount')?.value || '10';
    const language = document.getElementById('aiLanguage')?.value || 'english';
    const specificTopics = document.getElementById('aiSpecificTopics')?.value;
    
    // Validation
    if (!subject || !gradeLevel || !topic || !assignmentType) {
        showNotification('Please fill in the basic assignment details first (Subject, Grade, Topic, Type)', 'error');
        return;
    }
    
    // Show loading
    showAILoading(getLoadingMessage(type));
    
    // Prepare request data
    const requestData = {
        subject: subject,
        grade: parseInt(gradeLevel),
        topic: specificTopics || topic,
        assignment_type: assignmentType,
        difficulty: difficulty,
        question_count: parseInt(questionCount),
        language: language,
        title: title
    };
    
    // Make AI request
    const endpoint = type === 'questions' ? '/api/ai/generate-assignment' : '/api/ai/generate-content';
    
    makeRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(requestData)
    })
    .then(response => {
        hideAILoading();
        if (response.success) {
            currentGeneratedContent = response;
            showGeneratedPreview(response, type);
        } else {
            showNotification(response.error || 'Failed to generate content', 'error');
        }
    })
    .catch(error => {
        hideAILoading();
        showNotification('Failed to generate AI content. Please try again.', 'error');
        console.error('AI Generation Error:', error);
    });
}

function getLoadingMessage(type) {
    const messages = {
        'questions': 'Generating questions with AI...',
        'rubric': 'Creating grading rubric...',
        'instructions': 'Enhancing instructions...'
    };
    return messages[type] || 'Processing with AI...';
}

function showAILoading(message) {
    const loadingDiv = document.getElementById('aiGenerationLoading');
    const loadingText = document.getElementById('loadingText');
    
    if (loadingDiv && loadingText) {
        loadingText.textContent = message;
        loadingDiv.style.display = 'flex';
    }
}

function hideAILoading() {
    const loadingDiv = document.getElementById('aiGenerationLoading');
    if (loadingDiv) {
        loadingDiv.style.display = 'none';
    }
}

function showGeneratedPreview(response, type) {
    const previewDiv = document.getElementById('generatedPreview');
    const contentDiv = document.getElementById('generatedContent');
    
    if (!previewDiv || !contentDiv) return;
    
    let content = '';
    
    if (type === 'questions' && response.assignment) {
        content = formatAssignmentPreview(response.assignment);
    } else if (type === 'rubric' && response.rubric) {
        content = formatRubricPreview(response.rubric);
    } else if (type === 'instructions' && response.instructions) {
        content = formatInstructionsPreview(response.instructions);
    }
    
    contentDiv.innerHTML = content;
    previewDiv.style.display = 'block';
    
    // Scroll to preview
    previewDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function formatAssignmentPreview(assignment) {
    let html = `<div class="space-y-4">`;
    
    if (assignment.title) {
        html += `<div><strong>Title:</strong> ${assignment.title}</div>`;
    }
    
    if (assignment.description) {
        html += `<div><strong>Description:</strong> ${assignment.description}</div>`;
    }
    
    if (assignment.instructions) {
        html += `<div><strong>Instructions:</strong> ${assignment.instructions}</div>`;
    }
    
    if (assignment.questions && assignment.questions.length > 0) {
        html += `<div><strong>Questions:</strong></div>`;
        html += `<ol class="list-decimal ml-4 space-y-2">`;
        assignment.questions.forEach(q => {
            html += `<li class="text-sm">${q.question}`;
            if (q.type === 'multiple_choice' && q.options) {
                html += `<ul class="list-alpha ml-4 mt-1">`;
                q.options.forEach(option => {
                    html += `<li>${option}</li>`;
                });
                html += `</ul>`;
            }
            html += `</li>`;
        });
        html += `</ol>`;
    }
    
    if (assignment.estimated_time) {
        html += `<div><strong>Estimated Time:</strong> ${assignment.estimated_time}</div>`;
    }
    
    html += `</div>`;
    return html;
}

function formatRubricPreview(rubric) {
    return `<div class="space-y-2">
        <div><strong>Grading Rubric:</strong></div>
        <div class="text-sm whitespace-pre-line">${rubric}</div>
    </div>`;
}

function formatInstructionsPreview(instructions) {
    return `<div class="space-y-2">
        <div><strong>Enhanced Instructions:</strong></div>
        <div class="text-sm whitespace-pre-line">${instructions}</div>
    </div>`;
}

function useGeneratedContent() {
    if (!currentGeneratedContent || !currentGenerationType) return;
    
    if (currentGenerationType === 'questions' && currentGeneratedContent.assignment) {
        const assignment = currentGeneratedContent.assignment;
        
        // Fill form fields
        if (assignment.title) {
            const titleField = document.getElementById('title');
            if (titleField && !titleField.value) {
                titleField.value = assignment.title;
            }
        }
        
        if (assignment.description) {
            const descField = document.getElementById('description');
            if (descField && !descField.value) {
                descField.value = assignment.description;
            }
        }
        
        if (assignment.instructions) {
            const instrField = document.getElementById('instructions');
            if (instrField) {
                instrField.value = assignment.instructions;
            }
        }
        
        // Store questions data for form submission
        if (assignment.questions) {
            window.generatedQuestions = assignment.questions;
            showNotification('AI generated questions added to assignment!', 'success');
        }
        
    } else if (currentGenerationType === 'instructions' && currentGeneratedContent.instructions) {
        const instrField = document.getElementById('instructions');
        if (instrField) {
            instrField.value = currentGeneratedContent.instructions;
            showNotification('Instructions enhanced with AI!', 'success');
        }
    }
    
    closePreview();
}

function regenerateContent() {
    if (currentGenerationType) {
        generateAIContent(currentGenerationType);
    }
}

function closePreview() {
    const previewDiv = document.getElementById('generatedPreview');
    if (previewDiv) {
        previewDiv.style.display = 'none';
    }
}

// Assignment form enhancements
function initializeAssignmentForm() {
    const form = document.getElementById('assignmentForm');
    if (!form) return;
    
    // File upload enhancement
    const fileInput = document.getElementById('attachment');
    const fileDropZone = document.getElementById('fileDropZone');
    const filePreview = document.getElementById('filePreview');
    const fileName = document.getElementById('fileName');
    const removeFileBtn = document.getElementById('removeFile');
    
    if (fileInput && fileDropZone) {
        // Click to upload
        fileDropZone.addEventListener('click', () => fileInput.click());
        
        // File selection
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                const file = this.files[0];
                fileName.textContent = file.name;
                fileDropZone.style.display = 'none';
                filePreview.classList.remove('hidden');
            }
        });
        
        // Remove file
        if (removeFileBtn) {
            removeFileBtn.addEventListener('click', function() {
                fileInput.value = '';
                fileDropZone.style.display = 'block';
                filePreview.classList.add('hidden');
            });
        }
        
        // Drag and drop
        fileDropZone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('border-blue-400', 'bg-blue-50');
        });
        
        fileDropZone.addEventListener('dragleave', function(e) {
            e.preventDefault();
            this.classList.remove('border-blue-400', 'bg-blue-50');
        });
        
        fileDropZone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('border-blue-400', 'bg-blue-50');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
            }
        });
    }
    
    // Form submission with AI data
    form.addEventListener('submit', function(e) {
        // Add generated questions to form data if available
        if (window.generatedQuestions) {
            const questionsInput = document.createElement('input');
            questionsInput.type = 'hidden';
            questionsInput.name = 'ai_generated_questions';
            questionsInput.value = JSON.stringify(window.generatedQuestions);
            form.appendChild(questionsInput);
        }
        
        // Show loading modal
        const loadingModal = document.getElementById('loadingModal');
        if (loadingModal) {
            loadingModal.classList.remove('hidden');
            loadingModal.classList.add('flex');
        }
    });
    
    // Save draft functionality
    const saveDraftBtn = document.getElementById('saveDraft');
    if (saveDraftBtn) {
        saveDraftBtn.addEventListener('click', function() {
            const formData = new FormData(form);
            formData.append('is_draft', 'true');
            
            // Add AI questions if available
            if (window.generatedQuestions) {
                formData.append('ai_generated_questions', JSON.stringify(window.generatedQuestions));
            }
            
            toggleLoading(this);
            
            fetch(form.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                toggleLoading(this, false);
                if (data.success) {
                    showNotification('Draft saved successfully!', 'success');
                } else {
                    showNotification(data.error || 'Failed to save draft', 'error');
                }
            })
            .catch(error => {
                toggleLoading(this, false);
                showNotification('Failed to save draft', 'error');
                console.error('Save draft error:', error);
            });
        });
    }
}

// Export functions for global use
window.SACEL = {
    showNotification,
    toggleLoading,
    makeRequest,
    performSearch
};

// Language switching functionality
function switchLanguage(languageCode) {
    if (!languageCode) return;
    
    // Show loading state
    showNotification('Switching language...', 'info');
    
    // Make API request to switch language
    makeRequest('/api/language/switch', {
        method: 'POST',
        body: JSON.stringify({ language: languageCode })
    })
    .then(response => {
        if (response.success) {
            showNotification(`Language switched to ${response.language_name}`, 'success');
            // Reload page to apply language changes
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showNotification(response.error || 'Failed to switch language', 'error');
        }
    })
    .catch(error => {
        showNotification('Failed to switch language. Please try again.', 'error');
        console.error('Language switch error:', error);
    });
}

// Initialize language features
function initializeLanguageFeatures() {
    // Auto-detect language if not set
    const currentLang = document.documentElement.lang || 'en';
    
    // Update language selector if present
    const languageSelector = document.getElementById('languageSelector');
    if (languageSelector && !languageSelector.value) {
        languageSelector.value = currentLang;
    }
    
    // Set page direction for RTL languages (none of SA languages are RTL, but good to have)
    const rtlLanguages = ['ar', 'he', 'fa', 'ur'];
    if (rtlLanguages.includes(currentLang)) {
        document.documentElement.dir = 'rtl';
        document.body.classList.add('rtl');
    }
}

// Add language features to global SACEL object
window.SACEL.switchLanguage = switchLanguage;
window.SACEL.initializeLanguageFeatures = initializeLanguageFeatures;