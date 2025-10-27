// SACEL Main JavaScript - Enhanced Dashboard Version

// Mobile menu functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard components
    initializeDashboard();
    initializeMobileMenu();
    initializeNotifications();
    initializeSearch();
    initializeAITools();
    initializeAssignmentForm();
    initializeLanguageFeatures();
    
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
});

// Dashboard functionality
function initializeDashboard() {
    // Active navigation highlighting
    highlightActiveNavigation();
    
    // Initialize profile menu
    initializeProfileMenu();
    
    // Initialize sidebar toggle for mobile
    initializeSidebarToggle();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize card hover effects
    initializeCardEffects();
}

function highlightActiveNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('nav a[href]');
    
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href === currentPath || (currentPath.startsWith(href) && href !== '/')) {
            link.classList.add('bg-blue-50', 'text-blue-700', 'border-r-3', 'border-blue-500');
        }
    });
}

function initializeProfileMenu() {
    const profileMenuBtn = document.getElementById('profileMenuBtn');
    const profileDropdown = document.getElementById('profileDropdown');
    
    if (profileMenuBtn) {
        profileMenuBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            
            if (profileDropdown) {
                profileDropdown.classList.toggle('hidden');
            } else {
                // Create dropdown if it doesn't exist
                createProfileDropdown();
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function() {
            if (profileDropdown && !profileDropdown.classList.contains('hidden')) {
                profileDropdown.classList.add('hidden');
            }
        });
    }
}

function createProfileDropdown() {
    const profileMenuBtn = document.getElementById('profileMenuBtn');
    if (!profileMenuBtn) return;
    
    const dropdown = document.createElement('div');
    dropdown.id = 'profileDropdown';
    dropdown.className = 'absolute right-0 top-full mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50';
    dropdown.innerHTML = `
        <a href="#" class="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-50">
            <i class="fas fa-user w-4 h-4 mr-3"></i>
            Profile
        </a>
        <a href="#" class="flex items-center px-4 py-2 text-gray-700 hover:bg-gray-50">
            <i class="fas fa-cog w-4 h-4 mr-3"></i>
            Settings
        </a>
        <hr class="my-2">
        <a href="/auth/logout" class="flex items-center px-4 py-2 text-red-600 hover:bg-red-50">
            <i class="fas fa-sign-out-alt w-4 h-4 mr-3"></i>
            Logout
        </a>
    `;
    
    profileMenuBtn.parentElement.appendChild(dropdown);
}

function initializeSidebarToggle() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('sidebar-collapsed');
            if (mainContent) {
                mainContent.classList.toggle('sidebar-collapsed');
            }
        });
    }
}

function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    
    tooltipElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            showTooltip(this, this.getAttribute('data-tooltip'));
        });
        
        element.addEventListener('mouseleave', function() {
            hideTooltip();
        });
    });
}

function showTooltip(element, text) {
    const tooltip = document.createElement('div');
    tooltip.id = 'tooltip';
    tooltip.className = 'absolute bg-gray-800 text-white text-xs rounded py-1 px-2 z-50';
    tooltip.textContent = text;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = `${rect.left + element.offsetWidth / 2 - tooltip.offsetWidth / 2}px`;
    tooltip.style.top = `${rect.top - tooltip.offsetHeight - 5}px`;
}

function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

function initializeCardEffects() {
    const cards = document.querySelectorAll('.card-hover');
    
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
            this.style.boxShadow = '0 10px 25px rgba(0, 0, 0, 0.1)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
            this.style.boxShadow = '';
        });
    });
}

function initializeMobileMenu() {
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
}

function initializeNotifications() {
    // Check for new notifications periodically
    if (typeof currentUser !== 'undefined' && currentUser.is_authenticated) {
        setInterval(checkNotifications, 30000); // Every 30 seconds
    }
    
    // Initialize notification bell
    const notificationBell = document.querySelector('.notification-bell');
    if (notificationBell) {
        notificationBell.addEventListener('click', function() {
            toggleNotificationPanel();
        });
    }
}

function checkNotifications() {
    makeRequest('/api/notifications/check')
        .then(response => {
            if (response.success && response.count > 0) {
                updateNotificationBadge(response.count);
            }
        })
        .catch(error => {
            console.error('Error checking notifications:', error);
        });
}

function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-badge');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'block' : 'none';
    }
}

function toggleNotificationPanel() {
    const panel = document.getElementById('notificationPanel');
    if (panel) {
        panel.classList.toggle('hidden');
    } else {
        createNotificationPanel();
    }
}

function createNotificationPanel() {
    const panel = document.createElement('div');
    panel.id = 'notificationPanel';
    panel.className = 'absolute right-0 top-full mt-2 w-80 bg-white rounded-lg shadow-lg border border-gray-200 z-50';
    panel.innerHTML = `
        <div class="p-4 border-b border-gray-200">
            <h3 class="font-semibold text-gray-800">Notifications</h3>
        </div>
        <div class="max-h-64 overflow-y-auto">
            <div class="p-4 text-center text-gray-500">
                <i class="fas fa-bell-slash text-2xl mb-2"></i>
                <p>No new notifications</p>
            </div>
        </div>
    `;
    
    const notificationBell = document.querySelector('.notification-bell');
    if (notificationBell) {
        notificationBell.parentElement.appendChild(panel);
    }
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
// (Note: Main DOMContentLoaded listener is at the top of the file)

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