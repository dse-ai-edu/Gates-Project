const INPUT_CACHE_KEYS = {
    question: 'input_question_text',
    assessment: 'input_assessment_text',
    answer: 'input_answer_text'
};

document.addEventListener('DOMContentLoaded', () => {

    document.querySelectorAll('.information_box').forEach(box => {
        const type = box.dataset.type; // question / assessment / answer
        const uploadBtn = box.querySelector('.upload-btn');
        const uploadText = box.querySelector('.file-name');
        const fileInput = box.querySelector('.hidden-file-input');
        const textarea = box.querySelector('.info-textarea'); // answer 

        /* ---------- load cache ---------- */

        const cachedText = sessionStorage.getItem(INPUT_CACHE_KEYS[type]);
        if (cachedText) {
            if (textarea && type !== 'answer') {
                textarea.value = cachedText;
            }
        }

        if (textarea && type !== 'answer') {
            textarea.addEventListener('input', () => {
                sessionStorage.setItem(
                    INPUT_CACHE_KEYS[type],
                    textarea.value
                );
            });
        }

        /* ---------- Upload ---------- */

        uploadBtn.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', async () => {
            const file = fileInput.files[0];
            if (!file) return;

            const allowed = ['image/png', 'image/jpeg', 'application/pdf'];
            if (!allowed.includes(file.type)) {
                alert('Only PNG, JPG, or PDF files are allowed.');
                fileInput.value = '';
                return;
            }

            uploadText.textContent = file.name;

            const formData = new FormData();
            formData.append('file', file);
            formData.append('type', type);

            try {
                const resp = await fetch('/api/image/convert', {
                    method: 'POST',
                    body: formData
                });
                const data = await resp.json();

                const recognizedText = data.text || '';

                sessionStorage.setItem(
                    INPUT_CACHE_KEYS[type],
                    recognizedText
                );

                if (textarea && type !== 'answer') {
                    textarea.value = recognizedText;
                }

            } catch (e) {
                console.error(e);
                alert('Failed to process file.');
            } finally {
                fileInput.value = '';
            }
        });
    });
});


// ===============================
// User authentication check
// ===============================
function checkAuthentication() {
    const user = localStorage.getItem('user');
    if (!user) {
        alert('Please login first to access this page.');
        window.location.href = '/login';
        return false;
    }
    return true;
}

if (!checkAuthentication()) {
    throw new Error('Authentication required');
}

// ===============================
// Global variables - keyword info
// ===============================
const INFO_CACHE = {};

async function loadInfoByType(type) {
    if (!type || typeof type !== 'string') {
        throw new Error('type must be a non-empty string');
    }
    const key = type.toLowerCase();
    if (INFO_CACHE[key]) return INFO_CACHE[key];

    const url = `/static/data/${key}_info.json`;
    const resp = await fetch(url);
    if (!resp.ok) {
        throw new Error(`Failed to load ${url}`);
    }
    const data = await resp.json();
    INFO_CACHE[key] = data;
    return data;
}

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
        lines = ['N/A**'];
    }
    return lines.join('\n');
}

// ===============================
// Global config
// ===============================
let isStyleLocked = false;
let lockedStyleTmp = true;

let currentConfig = {
    style_keywords: [],
    feedback_templates: [],
    feedback_pattern: '',
    custom_rubric: ''
};

sessionStorage['userId'] = 'test';

// ===============================
// Navigation
// ===============================
function goBack() {
    window.location.href = '/page_2';
}

function saveConfiguration() {
    const finalConfig = {
        tid: sessionStorage.getItem('tid') || crypto.randomUUID(),
        finalConfiguration: {
            timestamp: new Date().toISOString(),
            completed: true
        }
    };

    fetch('/api/configuration/final', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(finalConfig)
    })
    .then(r => r.json())
    .then(result => {
        alert(result.success
            ? '✅ Configuration saved successfully!'
            : '❗ Save failed.');
    })
    .catch(err => {
        console.error(err);
        alert('❗ Error while saving.');
    });
}

// ===============================
// Load configured system
// ===============================
function loadConfiguredSystem() {
    const configData = window.feedbackInputFunctions.getStoredConfigData();

    currentConfig = {
        style_keywords: configData.style_keywords || [],
        feedback_templates: configData.feedback_templates || [],
        feedback_pattern: configData.feedback_pattern || '',
        custom_rubric: configData.custom_rubric || ''
    };

    isStyleLocked = configData.locked_style === true;
    displayConfigurationAsText();
}

async function displayConfigurationAsText() {
    const styleDisplay = document.getElementById('style-keywords-display');
    styleDisplay.style.whiteSpace = 'pre-line';
    styleDisplay.innerHTML =
        await buildInfoDisplayText('keyword', currentConfig.style_keywords);

    const templateDisplay = document.getElementById('feedback-templates-display');
    let templates = currentConfig.feedback_templates || ['Strength', 'Weakness', 'Suggestions for Improvement'];
    if (typeof templates === 'string') {
        templates = templates.trim().replace(/^\[|\]$/g, '');
        templates = templates.split(',').map(t => t.trim().replace(/^['"]|['"]$/g, '')).filter(t => t.length > 0);
    }
    templateDisplay.style.whiteSpace = 'pre-line';
    templateDisplay.textContent =
        templates.length ? templates.map((t, i) => `${i + 1}. ${t}`).join('\n')
                        : '[Default Template]';

    const patternDisplay = document.getElementById('feedback-pattern-display');
    let pattern_custom_flag = false;
    let pattern_text_show = '';

    if (
        typeof currentConfig.feedback_pattern === 'string' &&
        (currentConfig.feedback_pattern.toLowerCase().includes('custom') ||
         currentConfig.feedback_pattern.trim() === '')
    ) {
        pattern_text_show = 'Your Custom Pattern';
        pattern_custom_flag = true;
    } else {
        pattern_text_show =
            await buildInfoDisplayText('pattern', currentConfig.feedback_pattern);
    }

    patternDisplay.style.whiteSpace = 'pre-line';
    patternDisplay.innerHTML = pattern_text_show;

    const customDisplay = document.getElementById('custom-rubric-display');
    customDisplay.style.whiteSpace = 'pre-line';
    customDisplay.textContent =
        pattern_custom_flag
            ? (currentConfig.custom_rubric || '<Custom Content Not Found>')
            : '<Not Applicable>';
}

// ===============================
// Expectation estimator
// ===============================
function estimateExpectation(cfg) {
    const text1 = String(cfg.feedback_pattern || '');
    const text2 = String(cfg.custom_rubric || '');
    const len_estimate = text1.length + text2.length * 10;

    const mean = 12 + (len_estimate - 3000) / 3000;
    const std = 2;

    const u1 = Math.random();
    const u2 = Math.random();
    let x = mean + std * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
    x = Math.min(15, Math.max(10, x));
    return Number(x.toFixed(1));
}


// ===============================
// MAIN: generate feedback
// ===============================function generatePersonalizedFeedback() {
function generatePersonalizedFeedback() {
    const question = document
        .querySelector('.information_box[data-type="question"] textarea')
        ?.value.trim();

    const assessment = document
        .querySelector('.information_box[data-type="assessment"] textarea')
        ?.value.trim();

    const answerText =
        sessionStorage.getItem(INPUT_CACHE_KEYS.answer)?.trim();

    if (!question) {
        alert('Question must contain text.');
        return;
    }
    if (!assessment) {
        alert('Assessment must contain text.');
        return;
    }
    if (!answerText) {
        alert('Answer must be uploaded and recognized.');
        return;
    }

    const tid = sessionStorage.getItem('tid') || crypto.randomUUID();
    sessionStorage.setItem('tid', tid);

    const resultBox = document.getElementById('result-textarea');
    const resultSection = document.getElementById('feedback-display');

    if (resultSection) {
        resultSection.style.display = 'block';
    }

    const expectation = estimateExpectation(currentConfig);

    // === timer ===
    const startTime = Date.now();
    const timerId = setInterval(() => {
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        resultBox.innerText =
            `Generating feedback... (expect ~${expectation}s)\n` +
            `Running ${elapsed}s...`;
    }, 1000);

    // === submit ===
    const formData = new FormData();
    formData.append('tid', tid);
    formData.append('question', question);
    formData.append('assessment', assessment);
    formData.append('answer', answerText);
    formData.append(
        'predefined_flag',
        sessionStorage.getItem('predefined_conf') || ''
    );

    fetch('/api/comment/submit', {
        method: 'POST',
        body: formData
    })
    .then(r => r.json())
    .then(submitResult => {
        if (!submitResult.success) {
            throw new Error(submitResult.error || 'Submit failed');
        }
        return fetch(
            `/api/comment/load?tid=${tid}&attempt_id=${submitResult.attempt_id}`
        );
    })
    .then(r => r.json())
    .then(loadResult => {
        clearInterval(timerId);

        if (!loadResult.success) {
            throw new Error(loadResult.error || 'Load failed');
        }

 
        resultBox.innerHTML = loadResult.response || '';
    })
    .catch(err => {
        clearInterval(timerId);
        console.error(err);
        resultBox.innerText =
            `❌ Error generating feedback:\n${err.message}`;
    });
}


// ===============================
// DOM ready
// ===============================
document.addEventListener('DOMContentLoaded', function () {

    const generateFeedbackBtn = document.getElementById('generateFeedbackBtn');
    const feedbackDisplay = document.getElementById('feedback-display');
    const resultBox = document.getElementById('result-textarea');

    const tid = sessionStorage.getItem('tid') || 'N/A';
    document.getElementById('tid-value').textContent = tid;

    generateFeedbackBtn.addEventListener('click', function () {

        // feedbackDisplay.style.display = 'block';

        resultBox.value = 'Generating feedback...';
        
        generatePersonalizedFeedback();
    });

    loadConfiguredSystem();
});
