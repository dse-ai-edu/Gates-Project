// User authentication check
function checkAuthentication() {
    const user = localStorage.getItem('user');
    if (!user) {
        alert('Please login first to access this page.');
        window.location.href = '/login';
        return false;
    }
    return true;
}

// Initialize authentication check on page load
if (!checkAuthentication()) {
    throw new Error('Authentication required');
}

// Global variables - avoid redeclaration conflict with feedback_input_function.js
let isStyleLocked = false;  // From backend data (renamed to avoid conflict)
let lockedStyleTmp = true;  // Local variable for UI control (renamed to avoid conflict)

let currentConfig = {
    style_keywords: ['calculus  teacher'],
    feedback_templates: ['strength', 'weakness', 'improvement'],
    feedback_pattern: '',
    custom_rubric: ''
};

sessionStorage['userId'] = 'test';

// Navigation functions
function goBack() {
    window.location.href = '/page_2';
}

function saveConfiguration() {
    const finalConfig = {
        'tid': sessionStorage.getItem('tid') || crypto.randomUUID(),
        'finalConfiguration': {
            'timestamp': new Date().toISOString(),
            'completed': true
        }
    };
    
    fetch('/api/configuration/final', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(finalConfig)
    }).then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('✅ Configuration saved successfully! Your feedback system is ready to use.');
        } else {
            alert('❗ Save failed. Please try again.');
        }
    }).catch(error => {
        console.error('Save error:', error);
        alert('❗ An error occurred while saving. Please try again.');
    });
}


// Load configuration data from stored sources
function loadConfiguredSystem() {
    const configData = window.feedbackInputFunctions.getStoredConfigData();
    
    currentConfig = {
        style_keywords: configData.style_keywords || [],
        feedback_templates: configData.feedback_templates || [],
        feedback_pattern: configData.feedback_pattern || '',
        custom_rubric: configData.custom_rubric || ''
    };
    
    // Check if style is locked from previous steps
    isStyleLocked = configData.locked_style === true;
    
    // Initialize UI state
    // updateLockButtonState();
    
    console.log('Loaded configuration:', currentConfig);
    
    // Display configuration
    displayConfigurationAsText();
}


// Display configuration as text in four panels
function displayConfigurationAsText() {
    // 1 Style Keywords
    const styleDisplay = document.getElementById('style-keywords-display');
    const styleText = currentConfig.style_keywords.length > 0 
        ? currentConfig.style_keywords.join(', ') 
        : 'N/A';
    styleDisplay.textContent = styleText;

    // 2 Feedback Templates  
    const templateDisplay = document.getElementById('feedback-templates-display');

    const templateDefault = ['`Strength', '`Weakness', '`Improvement'];

    let lines;
    let templates = currentConfig.feedback_templates;
    if (typeof templates === 'string') {
        try {
            templates = JSON.parse(templates);
        } catch (e) {
            templates = [];
        }
    }

    if (Array.isArray(templates) &&
        templates.length > 0) {
        lines = templates.map((t, i) => `${i + 1}. ${t}`);
    } else {
        lines = [
            '[Default Template]',
            ...templateDefault.map((t, i) => `${i + 1}. ${t}`)
        ];
    }

    const templateText = lines.join('\n');
    templateDisplay.style.whiteSpace = 'pre-line';
    templateDisplay.textContent = templateText;
    // templateDisplay.textContent = "- Strength  - Weakness  - Improvement";
    
    // 3 Pattern
    console.log("FLAG 1")
    console.log(currentConfig.feedback_pattern)
    console.log("FLAG 1")
    const stylePattern = document.getElementById('feedback-pattern-display');
    if (currentConfig.feedback_pattern) {
        stylePattern.textContent = currentConfig.feedback_pattern;
    } else if (currentConfig.custom_rubric) {
        stylePattern.textContent = 'Custom Rubric Pattern';
    } else {
        stylePattern.textContent = 'N/A';
    }

    // 4 custom content
    const exampleDisplay = document.getElementById('custom-rubric-display');
    exampleDisplay.style.whiteSpace = 'pre-line';
    if (currentConfig.feedback_pattern !== "") {
        exampleDisplay.textContent = '<Not Applicable>';
    } else {
        exampleDisplay.textContent =
            currentConfig.custom_rubric || '<Not Applicable>';
    }
}


// Load editable components (when unlocked)
async function loadEditableComponents() {
    try {
        // This is a placeholder - in practice, you'd load the component HTML files
        // and initialize them for editing
        console.log('Loading editable components...');
        
        // For now, just switch back to display mode
        displayConfigurationAsText();
        
    } catch (error) {
        console.error('Failed to load editable components:', error);
    }
}

function updateCurrentConfigFromUI() {
    // This would update currentConfig with current UI values when in edit mode
    // For now, keep existing values
    console.log('Updating config from UI...');
}

// Save current configuration to backend
function saveCurrentConfiguration() {
    const tid = sessionStorage.getItem('tid') || crypto.randomUUID();
    
    const styleData = {
        'tid': tid,
        'style_keywords': currentConfig.style_keywords,
        'feedback_templates': currentConfig.feedback_templates,
        'feedback_pattern': currentConfig.feedback_pattern,
        'custom_rubric': currentConfig.custom_rubric
    };
    
    console.log('Saving configuration:', styleData);
    
    fetch('/api/comment/update_style', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(styleData)
    }).then(response => response.json())
    .then(result => {
        if (result.success) {
            console.log('Configuration saved successfully');
        } else {
            console.error('Failed to save configuration:', result);
        }
    }).catch(error => {
        console.error('Error saving configuration:', error);
    });
}

// Student input and feedback generation functionality
document.addEventListener('DOMContentLoaded', function() {
    const generateFeedbackBtn = document.getElementById('generateFeedbackBtn');
    const feedbackDisplay = document.getElementById("feedback-display");
    const tid = sessionStorage.getItem('tid') || 'N/A';
    
    document.getElementById('tid-value').textContent = tid;

    generateFeedbackBtn.addEventListener('click', function () {
        const studentAnswer = document.getElementById('student-answer').value.trim();
        if (!studentAnswer) {
            alert('Please enter a student answer before generating feedback.');
            return;
        }
        
        feedbackDisplay.style.display = 'block';
        document.getElementById('result-textarea').value = 'Generating Feedback...';
        generatePersonalizedFeedback();
    });
    
    // Load configuration when page loads
    loadConfiguredSystem();
});


function generatePersonalizedFeedback() {
    const studentAnswer = document.getElementById('student-answer').value;
    const resultBox = document.getElementById('result-textarea');
    const tid = sessionStorage.getItem('tid') || crypto.randomUUID();
    const archive_tid = sessionStorage.getItem('archive_tid') || '';
    const predefined_flag = sessionStorage.getItem('predefined_conf') || '';
    
    // Preparing to submit data
    const submitData = {
        'tid': tid,
        'archive_tid': archive_tid,
        'student_answer': studentAnswer,
        'style_keywords': currentConfig.style_keywords,
        'feedback_templates': currentConfig.feedback_templates,
        'feedback_pattern': currentConfig.feedback_pattern,
        'custom_rubric': currentConfig.custom_rubric,
        'predefined_flag': predefined_flag
    };
    
    console.log('Submitting feedback request:', submitData);
    
    // Step 1: Call /api/comment/submit to generate feedback.
    fetch('/api/comment/submit', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(submitData)
    })
    .then(response => response.json())
    .then(submitResult => {
        if (submitResult.success) {
            console.log('Feedback generation submitted successfully');
            let attempt_id=submitResult.attempt_id
            // Step 2: Call /api/comment/load to retrieve the formatted feedback text.
            return fetch(`/api/comment/load?tid=${tid}&attempt_id=${attempt_id}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
        } else {
            throw new Error(submitResult.error || 'Feedback generation failed');
        }
    })
    .then(response => response.json())
    .then(loadResult => {
        if (loadResult.success) {
            console.log('Feedback loaded successfully');

            const htmlText  = loadResult.response;  
            // 1. First render the main body (with <strong>, <span color>, <br>, etc.).
            resultBox.innerHTML = htmlText;

            // 2. Add configuration information at the end (use <hr> with 15 horizontal lines for a simpler style)
            resultBox.innerHTML += `
            <hr style="margin:1rem 0;border:none;border-top:1px solid #ccc;">
            <div style="color:#fb827a;">
            Generated using: ${currentConfig.feedback_pattern} style<br>
            Keywords: ${currentConfig.style_keywords.join(', ') || 'DEV: Default Keywords'}<br>
            Templates: ${
                currentConfig.feedback_templates.length
                    ? currentConfig.feedback_templates.join(', ')
                    : 'DEV: Default Template'
            }
            </div>`;
            
        } else {
            throw new Error(loadResult.error || 'Failed to load formatted feedback');
        }
    })
    .catch(error => {
        console.error('Error generating feedback:', error);
        resultBox.innerText = `❌ Error generating feedback: ${error.message}. Please try again or check your configuration.`;
    });
}


// Store answers loaded from backend
let currentSampleAnswers = [];
let currentSampleAnswerImages = [];

// -------------------------------------
// Step 1: Click Q button → load question + answers
// -------------------------------------
document.querySelectorAll('.sample-q-btn').forEach(btn => {
    btn.addEventListener('click', function () {
        const qIndex = parseInt(this.dataset.index);

        fetch('/api/demo/calculus', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question_index: qIndex
            })
        })
        .then(response => response.json())
        .then(result => {
            if (!result.success) {
                throw new Error(result.error || 'Failed to load demo question');
            }

            // 1. Fill question textarea
            document.getElementById('question-text').value = result.question_code || '';

            // 2. Cache answers
            currentSampleAnswers = Array.isArray(result.answer_code_list)
                ? result.answer_code_list
                : [];
            
            currentSampleAnswerImages = Array.isArray(result.answer_img_list)
                ? result.answer_img_list
                : [];

            // 3. Update sample-a button labels (optional but useful UX)
            document.querySelectorAll('.sample-a-btn').forEach((btn, i) => {
                btn.textContent = `Answer${i + 1}`;
            });

            // 4. Clear student answer box
            document.getElementById('student-answer').value = '';

            // 5. Reset answer image area (IMPORTANT)
            const imgWrapper = document.getElementById('answer-image-wrapper');
            const imgElem = document.getElementById('answer-image');

            if (imgWrapper && imgElem) {
                imgElem.src = '';
                imgWrapper.style.display = 'none';
            }

        })
        .catch(error => {
            console.error('Error loading demo question:', error);
            alert('Failed to load demo question.');
        });
    });
});


// -------------------------------------
// Step 2: Click Answer button → fill student answer
// -------------------------------------
document.querySelectorAll('.sample-a-btn').forEach(btn => {
    btn.addEventListener('click', function () {
        const index = parseInt(this.dataset.index, 10);

        // Guard: no question loaded yet
        if (!currentSampleAnswers.length) {
            return;
        }

        // 1. Fill student answer text
        document.getElementById('student-answer').value =
            currentSampleAnswers[index] || '';

        // 2. Handle answer image
        const imgWrapper = document.getElementById('answer-image-wrapper');
        const imgElem = document.getElementById('answer-image');

        const imgPath = currentSampleAnswerImages[index];
        if (imgPath) {
            // "./img/q1_a1.png" → "/static/images/Images_aug/q1_a1.png"
            const filename = imgPath.split('/').pop();
            imgElem.src = `/static/images/Images_aug/${filename}`;
            imgWrapper.style.display = 'block';
        } else {
            imgElem.src = '';
            imgWrapper.style.display = 'none';
        }
    });
});