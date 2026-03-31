window.feedbackInputFunctions = window.feedbackInputFunctions || {};


let templateCount = 3;
const maxTemplates = 10;
let locked_style = false;


function initStyleKeywordsComponent() {
    const radios = document.querySelectorAll('input[type="radio"][name^="step1"]');

    radios.forEach(radio => {
        if (radio.checked) {
            sessionStorage.setItem(radio.name, radio.value);
        }
    });

    radios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.checked) {
                sessionStorage.setItem(radio.name, radio.value);
            }
        });
    });

    ['step11', 'step12', 'step13', 'step14'].forEach(step => {
        const value = sessionStorage.getItem(step);
        if (!value) return;

        const radio = document.querySelector(
            `input[type="radio"][name="${step}"][value="${value}"]`
        );
        if (radio) {
            radio.checked = true;
        }
    });
}


function getTemplateTexts() {
    const inputs = document.querySelectorAll('.template-input');
    return Array.from(inputs).map(input => input.value).filter(value => value.trim() !== '');
}


function saveFeedbackTemplatesToSessionStorage() {
    const templateTexts = getTemplateTexts();
    sessionStorage.setItem('step2', JSON.stringify(templateTexts));
    console.log('Feedback templates saved:', templateTexts);
}


function loadFeedbackTemplatesFromSessionStorage() {
    const raw = sessionStorage.getItem('step2');
    if (!raw) {
        clearTemplateUI();
        return;
    }

    let templateArray;
    try {
        templateArray = JSON.parse(raw);
    } catch (e) {
        console.warn('Invalid step2 template format');
        clearTemplateUI();
        return;
    }

    if (!Array.isArray(templateArray)) {
        clearTemplateUI();
        return;
    }

    const templateContainer = document.getElementById('template-container');
    templateContainer.innerHTML = '';
    templateCount = 0;

    templateArray.forEach(template => {
        if (typeof template !== 'string' || !template.trim()) return;

        const templateRow = document.createElement('div');
        templateRow.className = 'template-row';
        templateRow.innerHTML = `
            <input type="text" class="template-input"
                   maxlength="50"
                   value="${template}">
        `;
        templateContainer.appendChild(templateRow);
        templateCount++;

        const input = templateRow.querySelector('.template-input');
        input.addEventListener('input', saveFeedbackTemplatesToSessionStorage);
    });
}

/* clear template UI（sessionStorage） */
function clearTemplateUI() {
    const templateContainer = document.getElementById('template-container');
    if (templateContainer) {
        templateContainer.innerHTML = '';
    }
    templateCount = 0;
}


function initFeedbackTemplatesComponent() {
    const DEFAULT_FEEDBACK_TEMPLATES = ["Strengths", "Weaknesses","Suggestions for improvement"];
    if (!sessionStorage.getItem('step2')) {
        sessionStorage.setItem(
            'step2',
            JSON.stringify([...DEFAULT_FEEDBACK_TEMPLATES])
        );
    }
    loadFeedbackTemplatesFromSessionStorage();
}


function initFeedbackPatternComponent() {
    const radios = document.querySelectorAll('input[name="step3"]');
    const exampleBox = document.getElementById('teaching-example-component');
    const textarea = document.getElementById('additional-instructions');

    // ===== init =====
    const initiallyChecked = document.querySelector('input[name="step3"]:checked');

    if (initiallyChecked) {
        const needExtra = initiallyChecked.dataset.needExtra === "1";

        if (needExtra) {
            sessionStorage.setItem('step3', '');
            if (exampleBox) exampleBox.style.display = 'block';
        } else {
            sessionStorage.setItem('step3', initiallyChecked.value);
            if (exampleBox) exampleBox.style.display = 'none';
        }
    }

    // ===== listen to changes =====
    radios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (!radio.checked) return;

            const needExtra = radio.dataset.needExtra === "1";

            if (needExtra) {
                sessionStorage.setItem('step3', '');
                if (exampleBox) exampleBox.style.display = 'block';
            } else {
                sessionStorage.setItem('step3', radio.value);
                if (exampleBox) exampleBox.style.display = 'none';
            }
        });
    });

    // ===== textarea input =====
    if (textarea) {
        textarea.addEventListener('input', () => {
            const checked = document.querySelector('input[name="step3"]:checked');
            if (checked && checked.dataset.needExtra === "1") {
                sessionStorage.setItem('step3A', textarea.value);
            }
        });
    }

    // ===== reset =====
    const step3 = sessionStorage.getItem('step3');
    const step3A = sessionStorage.getItem('step3A');

    if (step3) {
        const radio = document.querySelector(
            `input[name="step3"][value="${step3}"]`
        );
        if (radio) radio.checked = true;
        if (exampleBox) exampleBox.style.display = 'none';

    } else if (step3 === '' && step3A) {
        const radio = Array.from(radios).find(r => r.dataset.needExtra === "1");
        if (radio) radio.checked = true;

        if (exampleBox) exampleBox.style.display = 'block';
        if (textarea) textarea.value = step3A;
    }
}

// ==================== Component 4: Teaching Example Functions ====================

function getAdditionalExamples() {
    const additionalExamples = document.getElementById('additional-instructions');
    return additionalExamples ? additionalExamples.value : '';
}

function saveTeachingExampleToStorage() {
    const example = getAdditionalExamples();
    sessionStorage.setItem('step2_teach_example', example);
    console.log('Teaching example saved:', example);
}

function loadTeachingExampleFromStorage() {
    const storedExample = sessionStorage.getItem('step2_teach_example') || '';
    const textarea = document.getElementById('additional-instructions');
    if (textarea && storedExample) {
        textarea.value = storedExample;
    }
}

function initTeachingExampleComponent() {
    // Load stored data
    loadTeachingExampleFromStorage();
    
    // DOM element references
    const resetResponsesBtn = document.getElementById('reset-responses-btn');
    const addResponsesBtn = document.getElementById('add-responses-btn');
    const additionalExamples = document.getElementById('additional-instructions');
    
    // Button event listeners
    if (resetResponsesBtn) {
        resetResponsesBtn.addEventListener('click', function() {
            locked_style = false;
            additionalExamples.value = '';
            additionalExamples.disabled = true;
            saveTeachingExampleToStorage();
            sessionStorage.setItem('locked_style', 'false');
            console.log('Personalized responses reset. locked_style:', locked_style);
        });
    }
    
    if (addResponsesBtn) {
        addResponsesBtn.addEventListener('click', function() {
            locked_style = true;
            additionalExamples.disabled = false;
            additionalExamples.focus();
            sessionStorage.setItem('locked_style', 'true');
            console.log('Personalized responses enabled. locked_style:', locked_style);
        });
    }
    
    // Auto-save on textarea changes
    if (additionalExamples) {
        additionalExamples.addEventListener('input', saveTeachingExampleToStorage);
    }
    
    // Load locked state
    const storedLockedStyle = sessionStorage.getItem('locked_style');
    if (storedLockedStyle === 'true') {
        locked_style = true;
        if (additionalExamples) {
            additionalExamples.disabled = false;
        }
    }
}

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


// ==================== Common Utility Functions ====================

function getAllFormData() {
    return {
        step11: sessionStorage.getItem('step11'),
        step12: sessionStorage.getItem('step12'),
        step13: sessionStorage.getItem('step13'),
        step14: sessionStorage.getItem('step14'),
        step2: sessionStorage.getItem('step2'),
        step3: sessionStorage.getItem('step3'),
        step3A: sessionStorage.getItem('step3A')
    };
}

function clearAllStoredData() {
    sessionStorage.removeItem('step1_style_keywords');
    sessionStorage.removeItem('step1_feedback_templates');
    sessionStorage.removeItem('step2_selected_teach_style');
    sessionStorage.removeItem('step2_teach_example');
    sessionStorage.removeItem('locked_style');
    console.log('All stored feedback data cleared');
}


function getStoredConfigData() {
    return {
        style_keywords: [
            sessionStorage.getItem('step11'),
            sessionStorage.getItem('step12'),
            sessionStorage.getItem('step13'),
            sessionStorage.getItem('step14')
        ].filter(Boolean),
        feedback_templates: sessionStorage.getItem('step2') || '',
        feedback_pattern: sessionStorage.getItem('step3') || '',
        custom_rubric: sessionStorage.getItem('step3A') || ''
    };
}


document.addEventListener('DOMContentLoaded', function () {
    const page = document.body.dataset.page;

    switch (page) {

        case 'page_1':
            initStyleKeywordsComponent();

            if (document.getElementById('template-container')) {
                initFeedbackTemplatesComponent();
            }

            break;

        case 'page_2':
            // Step 3: feedback pattern (step3 / step3A)
            if (document.getElementById('teaching-style-component')){
                initFeedbackPatternComponent();
            }
            break;

            
        case 'page_final':
            // Display-only page
            // No interactive components to initialize
            break;

        default:
            console.warn('Unknown page type:', page);
    }

    console.log(`Feedback input components initialized for ${page}`);
});



function bindStyleKeywordSession() {
    const validSteps = new Set(["step11", "step12", "step13", "step14"]);

    document.querySelectorAll('.style-keywords-submodule[data-step]').forEach(module => {
        const stepName = module.dataset.step;
        if (!validSteps.has(stepName)) return;

        const radios = module.querySelectorAll(`input[type="radio"][name="${stepName}"]`);

        radios.forEach(radio => {
            radio.addEventListener("change", () => {
                if (radio.checked) {
                    sessionStorage.setItem(stepName, radio.value);
                }
            });
        });


        const checked = module.querySelector(`input[type="radio"][name="${stepName}"]:checked`);
        if (checked) {
            sessionStorage.setItem(stepName, checked.value);
        }
    });
}


// ==================== Export functions for global access ====================

// Make functions available globally
window.feedbackInputFunctions = {
    // Component 1
    initStyleKeywordsComponent,   

    // Component 2
    getTemplateTexts,
    initFeedbackTemplatesComponent,

    // Component 3
    initFeedbackPatternComponent,

    // Component 4
    initTeachingExampleComponent,

    // Display / Utility
    displayStyleKeywordsAsText,
    displayFeedbackTemplatesAsText,
    getAllFormData,
    clearAllStoredData,
    getStoredConfigData,

};
