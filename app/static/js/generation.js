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


// Global variables - keyword info
const INFO_CACHE = {};

async function loadInfoByType(type) {
    if (!type || typeof type !== 'string') {
        throw new Error('type must be a non-empty string');
    }
    const key = type.toLowerCase();
    if (INFO_CACHE[key]) {
        return INFO_CACHE[key];
    }
    const url = `/static/data/${key}_info.json`;
    const resp = await fetch(url);
    if (!resp.ok) {
        throw new Error(`Failed to load ${url}`);
    }
    const data = await resp.json();
    INFO_CACHE[key] = data;
    return data;
}


// Display for keyword(s) and pattern(s)
async function buildInfoDisplayText(type, value) {
    let info = {};
    try {
        info = await loadInfoByType(type);
    } catch (e) {
        console.error(e);
        return 'N/A*';
    }
    const resolveName = (key) => info?.[key]?.name || key;
    const resolveDescr = (key) => info?.[key]?.short || '';
    const makeLine = (key) => {
        const name = resolveName(key);
        const descr = resolveDescr(key);
        return `- <span title="${name}: ${descr.replace(/"/g, '&quot;')}">${name}</span>`;
    };
    let lines = [];
    if (Array.isArray(value)) {
        lines = value.map(k => makeLine(k));
    } else if (typeof value === 'string' && value.trim() !== '') {
        lines = value
            .split(',')
            .map(k => k.trim())
            .filter(k => k.length > 0)
            .map(k => makeLine(k));
    } else {
        console.log('Unrecognized Info, its type/value are: ', type, '&&', value);
        lines = ['N/A**'];
    }
    return lines.join('\n');
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
async function displayConfigurationAsText() {

    // 1 Selected Keyword
    const styleDisplay = document.getElementById('style-keywords-display');
    const keywords = currentConfig.style_keywords;
    const keyword_text_show = await buildInfoDisplayText('keyword', keywords);
    styleDisplay.style.whiteSpace = 'pre-line';
    styleDisplay.innerHTML = keyword_text_show;

    // 2 Feedback Templates  
    const templateDisplay = document.getElementById('feedback-templates-display');
    const templateDefault = ['`Strength', '`Weakness', '`Improvement'];

    let tp_lines;
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
        tp_lines = templates.map((t, i) => `${i + 1}. ${t}`);
    } else {
        tp_lines = [
            '[Default Template]',
            ...templateDefault.map((t, i) => `${i + 1}. ${t}`)
        ];
    }

    const templateText = tp_lines.join('\n');
    templateDisplay.style.whiteSpace = 'pre-line';
    templateDisplay.textContent = templateText;
    // templateDisplay.textContent = "- Strength  - Weakness  - Improvement";
    
    // 3 Pattern
    const patternDisplay = document.getElementById('feedback-pattern-display');
    const pattern = currentConfig.feedback_pattern;
    let pattern_custom_flag = false;

    let pattern_text_show = '';
    if (
        typeof pattern === 'string' &&
        (
            pattern.toLowerCase().includes('custom') ||
            pattern.trim() === ''
        )
    ) {
        pattern_text_show = 'Your Custom Pattern';
        pattern_custom_flag = true;
    } else {
        pattern_text_show = await buildInfoDisplayText('pattern', pattern);
    }
    patternDisplay.style.whiteSpace = 'pre-line';
    patternDisplay.innerHTML = pattern_text_show;

    // 4 custom content
    const customDisplay = document.getElementById('custom-rubric-display');
    customDisplay.style.whiteSpace = 'pre-line';

    if (pattern_custom_flag === false) {
        customDisplay.textContent = '<Not Applicable>';
    } else {
        const custom_tmp = currentConfig.custom_rubric;
        customDisplay.textContent =
            custom_tmp && custom_tmp.trim()
                ? custom_tmp
                : '<Custom Content Not Found>';
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
    const tid = sessionStorage.getItem('tid') || 'N/A***';
    
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



function estimateExpectation(currentConfig) {
    const text1 = currentConfig.feedback_pattern != null
        ? String(currentConfig.feedback_pattern)
        : '';
    const text2 = currentConfig.custom_rubric != null
        ? (typeof currentConfig.custom_rubric === 'string'
            ? currentConfig.custom_rubric
            : JSON.stringify(currentConfig.custom_rubric))
        : '';
    const len_estimate = text1.length + text2.length * 10;
    const mean = 12 + (len_estimate - 3000) / 3000;
    const std = 2;
    const u1 = Math.random();
    const u2 = Math.random();
    let expectation =
        mean + std * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    expectation = Math.min(15, Math.max(10, expectation));
    return Number(expectation.toFixed(1));
}


function generatePersonalizedFeedback() {
    const questionContent = document.getElementById('question-text').value;
    const studentAnswer = document.getElementById('student-answer').value;
    const resultBox = document.getElementById('result-textarea');
    const tid = sessionStorage.getItem('tid') || crypto.randomUUID();
    const archive_tid = sessionStorage.getItem('archive_tid') || '';
    const predefined_flag = sessionStorage.getItem('predefined_conf') || '';
    const expectation = estimateExpectation(currentConfig);

    // === timer ===
    const startTime = Date.now();
    let timerId = null;

    function updateRunningTime() {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        resultBox.innerHTML =
            `Generating New Feedback... Please Wait (expect ${expectation} seconds)...<br>` +
            `Running ${elapsed} seconds...`;
    }

    updateRunningTime();
    timerId = setInterval(updateRunningTime, 1000);

    const submitData = {
        tid: tid,
        archive_tid: archive_tid,
        question: questionContent,
        student_answer: studentAnswer,
        // style_keywords: currentConfig.style_keywords,
        // feedback_templates: currentConfig.feedback_templates,
        // feedback_pattern: currentConfig.feedback_pattern,
        // custom_rubric: currentConfig.custom_rubric,
        predefined_flag: predefined_flag
    };

    console.log('Submitting feedback request:', submitData);

    fetch('/api/comment/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(submitData)
    })
    .then(response => response.json())
    .then(submitResult => {
        if (submitResult.success) {
            let attempt_id = submitResult.attempt_id;
            return fetch(`/api/comment/load?tid=${tid}&attempt_id=${attempt_id}`);
        } else {
            throw new Error(submitResult.error || 'Feedback generation failed');
        }
    })
    .then(response => response.json())
    .then(loadResult => {
        if (!loadResult.success) {
            throw new Error(loadResult.error || 'Failed to load formatted feedback');
        }

        if (timerId) clearInterval(timerId);

        const htmlText = loadResult.response;
        resultBox.innerHTML = htmlText;

        // keyword showing
        const keywordText =
            (typeof loadResult.keyword_text === 'string' &&
            loadResult.keyword_text.trim() !== '')
                ? `${loadResult.keyword_text}`
                : 'NA[Default]';

        // Template showing
        const templateText =
            (typeof loadResult.template_text === 'string' &&
            loadResult.template_text.trim() !== '')
                ? `${loadResult.template_text}`
                : 'NA[Default]';

        // Pattern showing
        let pattern_custom_flag = false;

        const patternText =
            (typeof loadResult.pattern_text === 'string' &&
            loadResult.pattern_text.trim() !== '')
                ? `${loadResult.pattern_text}`
                : 'NA[Default]';

        if (typeof loadResult.pattern_text === 'string' && (loadResult.pattern_text.toLowerCase().includes('custom') || loadResult.pattern_text.trim() === '')) 
            {
                pattern_custom_flag = true;
            }

        // Custom Rubric showing
        const rubricText =
            (typeof loadResult.custom_rubric === 'string' &&
            loadResult.custom_rubric.trim() !== '' && pattern_custom_flag === true) 
                ? `Your Custom Rubric: ${loadResult.custom_rubric}`
                : null;

        // Pattern text showing
        const patternFullText = '';
        //     (typeof loadResult.pattern_body === 'string' &&
        //     loadResult.pattern_body.trim() !== '' && pattern_custom_flag === false)
        //         ? `Rubric of Current Pattern: ${loadResult.pattern_body}`
        //         : null;
        // const custom_patternFullText = 
        //     (pattern_custom_flag === true)
        //         ? `Rubric of Current Pattern: ${loadResult.pattern_body}`
        //         : null;

        // Showing All Setting
        resultBox.innerHTML += `
            <hr style="margin:1rem 0;border:none;border-top:1px solid #ccc;">
            <div style="color:#fb827a;">
            Generate Feedback with:<br>
            &nbsp;&nbsp;- Character Keywords: "${keywordText}"<br>
            &nbsp;&nbsp;- Feedback Template: "${templateText}"<br>
            &nbsp;&nbsp;- Feedback Pattern: "${patternText}" Style<br>
            ${rubricText ? '&nbsp;&nbsp;- ' + rubricText + '<br>' : ''}
            ${patternFullText ? '&nbsp;&nbsp;- ' + patternFullText + '<br>' : ''}
            </div>`;
    })
    .catch(error => {
        if (timerId) clearInterval(timerId);
        console.error('Error generating feedback:', error);
        resultBox.innerText =
            `❌ Error generating feedback: ${error.message}. Please try again or check your configuration.`;
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




// ==================== Display Functions for step_final ====================

function displayStyleKeywordsAsText(keywords, container) {
    const values = keywords && typeof keywords === 'object'
        ? Object.values(keywords)
        : [];

    const displayText = values.length > 0
        ? values.map(v => `${v}; `).join('')
        : 'N/A';

    container.innerHTML = `<div class="display-text">${displayText}</div>`;
}


function displayFeedbackTemplatesAsText(templates, container) {
    if (templates.length > 0) {
        const html = templates.map(template => 
            `<div class="display-text" style="margin-bottom: 0.3rem; padding: 0.3rem;">${template}</div>`
        ).join('');
        container.innerHTML = html;
    } else {
        container.innerHTML = '<div class="display-text">N/A</div>';
    }
}
