// Feedback Input Functions JavaScript
// Global variables
let templateCount = 3;
const maxTemplates = 10;
let locked_style = false;
// ==================== Component 1: Style Keywords Functions (Multi-Module) ====================

// const STYLE_KEYWORDS_STORAGE_KEY = 'step1_style_keywords';

/**
//  * Get selected style keywords from all submodules
//  * @returns {Object} e.g. { A: "First Person", B: "Neutral", ... }
//  */
// function getSelectedStyles() {
//     const result = {};
//     const modules = document.querySelectorAll('.style-keywords-submodule');

//     modules.forEach(module => {
//         const moduleKey = module.dataset.module;
//         const checked = module.querySelector('input[type="checkbox"]:checked');
//         if (checked) {
//             result[moduleKey] = checked.value;
//         }
//     });

//     return result;
// }

/**
 * Save current selections to sessionStorage
 */
// function saveStyleKeywordsToSessionStorage() {
//     const selectedStyles = getSelectedStyles();
//     sessionStorage.setItem(
//         STYLE_KEYWORDS_STORAGE_KEY,
//         JSON.stringify(selectedStyles)
//     );
//     console.log('Style keywords saved:', selectedStyles);
// }

/**
 * Load selections from sessionStorage
 * Falls back to default (first checkbox checked) if missing
 */
// function loadStyleKeywordsFromSessionStorage() {
//     const raw = sessionStorage.getItem(STYLE_KEYWORDS_STORAGE_KEY);
//     if (!raw) return;

//     let stored;
//     try {
//         stored = JSON.parse(raw);
//     } catch (e) {
//         console.warn('Invalid style keyword storage format');
//         return;
//     }

//     Object.entries(stored).forEach(([moduleKey, value]) => {
//         const module = document.querySelector(
//             `.style-keywords-submodule[data-module="${moduleKey}"]`
//         );
//         if (!module) return;

//         const checkbox = module.querySelector(
//             `input[type="checkbox"][value="${value}"]`
//         );
//         if (checkbox) {
//             checkbox.checked = true;
//         }
//     });
// }

/**
 * Reset a single submodule:
 * - uncheck all
 * - check the first checkbox
 */
// function resetSubmodule(module) {
//     const checkboxes = module.querySelectorAll('input[type="checkbox"]');
//     checkboxes.forEach(cb => cb.checked = false);
//     if (checkboxes.length > 0) {
//         checkboxes[0].checked = true;
//     }
// }

/**
 * Initialize style keyword components
 */
// function initStyleKeywordsComponent() {
//     // Load stored selections
//     loadStyleKeywordsFromSessionStorage();

//     const modules = document.querySelectorAll('.style-keywords-submodule');

//     modules.forEach(module => {
//         const checkboxes = module.querySelectorAll('input[type="checkbox"]');
//         const resetBtn = module.querySelector('.reset-submodule-btn');

//         // Enforce single selection per module (radio-like)
//         checkboxes.forEach(cb => {
//             cb.addEventListener('change', () => {
//                 if (cb.checked) {
//                     checkboxes.forEach(other => {
//                         if (other !== cb) other.checked = false;
//                     });
//                 }
//                 saveStyleKeywordsToSessionStorage();
//             });
//         });

//         // Reset button (module-local)
//         if (resetBtn) {
//             resetBtn.addEventListener('click', () => {
//                 resetSubmodule(module);
//                 saveStyleKeywordsToSessionStorage();
//             });
//         }
//     });
// }

window.feedbackInputFunctions.resetSingleStep = function (stepName) {
    const radios = document.querySelectorAll(`input[type="radio"][name="${stepName}"]`);
    if (!radios.length) return;

    let defaultRadio = null;
    radios.forEach(r => {
        if (r.hasAttribute("checked")) {
            defaultRadio = r;
        }
        r.checked = false;
    });
    if (defaultRadio) {
        defaultRadio.checked = true;
    } else {
        radios[0].checked = true;
    };

    const selected = defaultRadio || radios[0];
    sessionStorage.setItem(stepName, selected.value);
};


function initStyleKeywordsComponent() {
    const radios = document.querySelectorAll('input[type="radio"][name^="step1"]');

    radios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.checked) {
                sessionStorage.setItem(radio.name, radio.value);
            }
        });
    });

    // reset value in sessionStorage
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

// ==================== Component 2: Feedback Templates Functions ====================

function getTemplateTexts() {
    const inputs = document.querySelectorAll('.template-input');
    return Array.from(inputs).map(input => input.value).filter(value => value.trim() !== '');
}

// function addTemplate() {
//     const templateContainer = document.getElementById('template-container');
//     if (templateCount < maxTemplates) {
//         const templateRow = document.createElement('div');
//         templateRow.className = 'template-row';
        
//         templateRow.innerHTML = `
//             <input type="text" class="template-input" placeholder="enter one template item (max 50 characters)" maxlength="50">
//             <button class="delete-btn" onclick="deleteTemplate(this)">×</button>
//         `;
        
//         templateContainer.appendChild(templateRow);
//         templateCount++;
//         updateAddButtonState();
        
//         // Add event listener to new input
//         const newInput = templateRow.querySelector('.template-input');
//         newInput.addEventListener('input', saveFeedbackTemplatesToSessionStorage);
//     }
// }

// function deleteTemplate(button) {
//     const templateRow = button.parentElement;
//     templateRow.remove();
//     templateCount--;
//     updateAddButtonState();
//     saveFeedbackTemplatesToSessionStorage();
// }

// function updateAddButtonState() {
//     const addTemplateBtn = document.getElementById('add-template-btn');
//     if (addTemplateBtn) {
//         if (templateCount >= maxTemplates) {
//             addTemplateBtn.disabled = true;
//             addTemplateBtn.style.opacity = '0.6';
//         } else {
//             addTemplateBtn.disabled = false;
//             addTemplateBtn.style.opacity = '1';
//         }
//     }
// }

function saveFeedbackTemplatesToSessionStorage() {
    const templateTexts = getTemplateTexts();
    const feedbackTemplates = templateTexts.join('\n');
    sessionStorage.setItem('step1_feedback_templates', feedbackTemplates);
    console.log('Feedback templates saved:', feedbackTemplates);
}

function loadFeedbackTemplatesFromSessionStorage() {
    const storedTemplates = sessionStorage.getItem('step1_feedback_templates') || '';
    if (storedTemplates) {
        const templateArray = storedTemplates.split('\n').filter(t => t.trim());
        const templateContainer = document.getElementById('template-container');
        
        // Clear existing templates first
        templateContainer.innerHTML = '';
        templateCount = 0;
        
        // Add stored templates
        templateArray.forEach(template => {
            if (template.trim()) {
                const templateRow = document.createElement('div');
                templateRow.className = 'template-row';
                templateRow.innerHTML = `
                    <input type="text" class="template-input" placeholder="enter one template item (max 50 characters)" maxlength="50" value="${template.trim()}">
                    <button class="delete-btn" onclick="deleteTemplate(this)">×</button>
                `;
                templateContainer.appendChild(templateRow);
                templateCount++;
                
                // Add event listener to input
                const input = templateRow.querySelector('.template-input');
                input.addEventListener('input', saveFeedbackTemplatesToSessionStorage);
            }
        });
        
        // updateAddButtonState();
    }
}

function initFeedbackTemplatesComponent() {
    // Load stored data
    loadFeedbackTemplatesFromSessionStorage();
    
    // Add event listeners
    // const addBtn = document.getElementById('add-template-btn');
    // if (addBtn) {
    //     addBtn.addEventListener('click', addTemplate);
    // }
    
    // Add event listeners to existing inputs
    const existingInputs = document.querySelectorAll('.template-input');
    existingInputs.forEach(input => {
        input.addEventListener('input', saveFeedbackTemplatesToSessionStorage);
    });
    
    // Update template count
    templateCount = existingInputs.length;
    // updateAddButtonState();
    updateStep2FromTemplates();
}

// function resetToDefaultTemplate() {
//    // Clear sessionStorage first to prevent loading old data
//     sessionStorage.removeItem('step1_feedback_templates');
    
//     const templateContainer = document.getElementById('template-container');
//     templateContainer.innerHTML = `
//         <div class="template-row">
//             <input type="text" class="template-input" placeholder="enter one template item (max 50 characters)" maxlength="50" value="strength">
//             <button class="delete-btn" onclick="window.feedbackInputFunctions.deleteTemplate(this)">×</button>
//         </div>
//         <div class="template-row">
//             <input type="text" class="template-input" placeholder="enter one template item (max 50 characters)" maxlength="50" value="weakness">
//             <button class="delete-btn" onclick="window.feedbackInputFunctions.deleteTemplate(this)">×</button>
//         </div>
//         <div class="template-row">
//             <input type="text" class="template-input" placeholder="enter one template item (max 50 characters)" maxlength="50" value="improvement">
//             <button class="delete-btn" onclick="window.feedbackInputFunctions.deleteTemplate(this)">×</button>
//         </div>
//     `;
//    // Reset template count and update button state
//     templateCount = 3;
//     updateAddButtonState();
    
//    // Add event listeners to new inputs
//     const inputs = templateContainer.querySelectorAll('.template-input');
//     inputs.forEach(input => {
//         input.addEventListener('input', saveFeedbackTemplatesToSessionStorage);
//     });
    
//    // Save the default state to sessionStorage
//     saveFeedbackTemplatesToSessionStorage();
// }


function updateStep2FromTemplates() {
    const inputs = document.querySelectorAll('.template-input');
    const value = Array.from(inputs)
        .map(i => i.value.trim())
        .filter(Boolean)
        .join(', ');

    sessionStorage.setItem('step2', value);
}

// ==================== Component 3: Teaching Style Functions ====================

// function getSelectedTeachingStyle() {
//     const selectedRadio = document.querySelector('input[name="teaching-style"]:checked');
//     if (selectedRadio) {
//         return selectedRadio.value;
//     }
    
//    // Check if teaching style was set from sessionStorage
//     const storedStyle = sessionStorage.getItem('step2_selected_teach_style');
//     if (storedStyle && storedStyle.trim()) {
//         return storedStyle;
//     }
    
//     return null;
// }

// function saveTeachingStyleToStorage() {
//     const selectedStyle = getSelectedTeachingStyle();
//     if (selectedStyle) {
//         sessionStorage.setItem('step2_selected_teach_style', selectedStyle);
//         console.log('Teaching style saved:', selectedStyle);
//     }
// }

// function loadTeachingStyleFromStorage() {
//     const storedStyle = sessionStorage.getItem('step2_selected_teach_style');
//     if (storedStyle) {
//         const radio = document.querySelector(`input[name="teaching-style"][value="${storedStyle}"]`);
//         if (radio) {
//             radio.checked = true;
//         }
//     }
// }

// function initTeachingStyleComponent() {
//     // Load stored data
//     loadTeachingStyleFromStorage();
    
//     // Add event listeners to radio buttons
//     const radioButtons = document.querySelectorAll('input[name="teaching-style"]');
//     radioButtons.forEach(radio => {
//         radio.addEventListener('change', saveTeachingStyleToStorage);
//     });
// }


function initTeachingStyleComponent() {
    const radios = document.querySelectorAll('input[name="step3"]');
    const container = document.getElementById('custom-rubric-container');
    const textarea = document.getElementById('custom-rubric-text');

    radios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (!radio.checked) return;

            if (radio.value === '') {
                // Fourth option
                sessionStorage.setItem('step3', '');
                container.style.display = 'block';
            } else {
                sessionStorage.setItem('step3', radio.value);
                container.style.display = 'none';
            }
        });
    });

    if (textarea) {
        textarea.addEventListener('input', () => {
            sessionStorage.setItem('step3A', textarea.value);
        });
    }

    // Restore state
    const step3 = sessionStorage.getItem('step3');
    const step3A = sessionStorage.getItem('step3A');

    if (step3) {
        const radio = document.querySelector(
            `input[name="step3"][value="${step3}"]`
        );
        if (radio) radio.checked = true;
        container.style.display = 'none';
    } else if (step3A) {
        const customRadio = document.querySelector('input[name="step3"][value=""]');
        if (customRadio) customRadio.checked = true;
        container.style.display = 'block';
        textarea.value = step3A;
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

// function displayTeachingStyleAsText(selectedStyle, container) {
//     const teachingStyles = [
//         'AUTHORITATIVE', 'SOCRATIC', 'NURTURING', 'CONSTRUCTIVE', 'DIRECT', 'PLAIN'
//     ];
    
//     let html = '<div class="radio-group">';
//     teachingStyles.forEach(style => {
//         const isSelected = style === selectedStyle;
//         const className = isSelected ? 'radio-item' : 'radio-item grayed';
//         const checked = isSelected ? 'checked' : '';
//         html += `
//             <div class="${className}">
//                 <input type="radio" name="teach-style-display" value="${style}" ${checked} disabled>
//                 <label>${style}</label>
//             </div>
//         `;
//     });
//     html += '</div>';
//     container.innerHTML = html;
// }

// function displayTeachingExampleAsText(example, container) {
//     const exampleText = example || 'N/A';
//     container.innerHTML = `<div class="teach-example-display">${exampleText}</div>`;
// }

// ==================== Common Utility Functions ====================

function getAllFormData() {
    return {
        // selectedStyles: getSelectedStyles(),
        // templateTexts: getTemplateTexts(),
        // teachingStyle: getSelectedTeachingStyle(),
        // additionalExamples: getAdditionalExamples()
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


// function getStoredConfigData() {
//     const rawStyleKeywords = sessionStorage.getItem('step1_style_keywords');
//     const feedbackTemplates = sessionStorage.getItem('step1_feedback_templates') || '';
//     const teachStyle = sessionStorage.getItem('step2_selected_teach_style') || '';
//     const teachExample = sessionStorage.getItem('step2_teach_example') || '';
//     const lockedStyle = sessionStorage.getItem('locked_style') === 'true';

//     let styleKeywords = [];
//     if (rawStyleKeywords) {
//         try {
//             const parsed = JSON.parse(rawStyleKeywords);
//             styleKeywords = Object.values(parsed).filter(v => v && v.trim());
//         } catch (e) {
//             console.warn('Failed to parse style keywords from sessionStorage');
//         }
//     }

//     return {
//         style_keywords: styleKeywords,
//         feedback_templates: feedbackTemplates
//             ? feedbackTemplates.split('\n').filter(t => t.trim())
//             : [],
//         teach_style: teachStyle,
//         teach_example: teachExample,
//         locked_style: lockedStyle
//     };
// }


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
        feedback_pattern_custom: sessionStorage.getItem('step3A') || ''
    };
}


// Load prior setting from database (updated for multi-module style keywords)
// function loadPriorSetting() {
//     // Initialize archive_tid as empty string
//     sessionStorage.setItem('archive_tid', '');

//     const archive_tid_local = prompt(
//         "Please enter the History Session ID (archive_tid) to retrieve your prior settings:"
//     );

//     if (archive_tid_local === null) {
//         return;
//     }

//     if (!archive_tid_local.trim()) {
//         alert("History Session ID cannot be empty");
//         return;
//     }

//     const status = document.getElementById('save-status');
//     status.textContent = '🔄 Loading...';
//     status.style.color = 'blue';

//     fetch('/api/comment/retrieve_style', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json'
//         },
//         body: JSON.stringify({ tid: archive_tid_local.trim() })
//     })
//     .then(response => {
//         if (!response.ok) {
//             throw Error('Retrieve failed! Please try again.');
//         }
//         return response.json();
//     })
//     .then(result => {
//         if (result.success && result.config) {
//             const lastConfig = result.config;

//             /* === Step 1: Style Keywords (map array -> object) === */
//             let styleKeywordMap = {};
//             if (Array.isArray(lastConfig.style_keywords)) {
//                 const keys = ['A', 'B', 'C', 'D'];
//                 lastConfig.style_keywords.forEach((value, idx) => {
//                     if (keys[idx] && value) {
//                         styleKeywordMap[keys[idx]] = value;
//                     }
//                 });
//             }

//             sessionStorage.setItem(
//                 'step1_style_keywords',
//                 JSON.stringify(styleKeywordMap)
//             );

//             /* === Step 1: Feedback Templates === */
//             sessionStorage.setItem(
//                 'step1_feedback_templates',
//                 (lastConfig.feedback_templates || []).join('\n')
//             );

//             /* === Step 2 data === */
//             sessionStorage.setItem(
//                 'step2_selected_teach_style',
//                 lastConfig.teach_style || ''
//             );
//             sessionStorage.setItem(
//                 'step2_teach_example',
//                 lastConfig.step2_teach_example || ''
//             );

//             /* === Archive TID === */
//             sessionStorage.setItem('archive_tid', archive_tid_local.trim());

//             status.textContent = '✔️ Settings Loaded Successfully';
//             status.style.color = 'green';

//             // Re-initialize components to reflect loaded data
//             setTimeout(() => {
//                 window.feedbackInputFunctions.initStyleKeywordsComponent();
//                 window.feedbackInputFunctions.initTeachingStyleComponent();
//                 window.feedbackInputFunctions.initTeachingExampleComponent();
//             }, 500);

//             // Auto-save after loading
//             setTimeout(() => {
//                 saveAndProceed_page2();
//             }, 1500);

//         } else {
//             status.textContent = '❌ Load failed';
//             status.style.color = 'red';
//             alert("No Setting Found in our Records...");
//         }
//     })
//     .catch(error => {
//         console.error(error);
//         status.textContent = '❌ Load failed';
//         status.style.color = 'red';
//         alert("No Setting Found in our Records...");
//     });
// }


// ==================== Auto-initialization ====================

// document.addEventListener('DOMContentLoaded', function() {
//     // Initialize components based on what's present in the page
//     if (document.getElementById('style-keywords-component')) {
//         initStyleKeywordsComponent();
//     }
    
//     if (document.getElementById('feedback-templates-component')) {
//         initFeedbackTemplatesComponent();
//     }
    
//     if (document.getElementById('teaching-style-component')) {
//         initTeachingStyleComponent();
//     }
    
//     if (document.getElementById('teaching-example-component')) {
//         initTeachingExampleComponent();
//     }
    
//     console.log('Feedback input components initialized');
// });


document.addEventListener('DOMContentLoaded', function () {
    const page = document.body.dataset.page;

    switch (page) {

        case 'page_1':
            // Step 1: style keywords (step11–step14)
            // Step 2: templates (step2, read-only)
            initStyleKeywordsComponent();
            initFeedbackTemplatesComponent();
            break;

        case 'page_2':
            // Step 3: feedback pattern (step3 / step3A)
            initTeachingStyleComponent();
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


// procedding functions
function saveAndProceed_page2() {
    // const teachingStyle = window.feedbackInputFunctions.getSelectedTeachingStyle();
    // const additionalExamples = window.feedbackInputFunctions.getAdditionalExamples();
    const step3  = sessionStorage.getItem('step3') || '';
    const step3A = sessionStorage.getItem('step3A') || '';

    let tid = sessionStorage.getItem('tid');
    
    // Create session ID if it doesn't exist
    if (!tid) {
        tid = crypto.randomUUID();
        sessionStorage.setItem('tid', tid);
    }
    
    // if (!teachingStyle) {
    //     alert("❗ Please select a Primary Feedback Pattern");
    //     return;
    // }
    if (!step3 && !step3A) {
        alert("❗ Please select a Feedback Pattern or provide a custom one.");
        return;
    }

    // Get step1 data from sessionStorage
    const configData = window.feedbackInputFunctions.getStoredConfigData();
    
    // Prepare data for backend
    const styleData = {
        'tid': tid,
        'style_keywords': configData.style_keywords,
        'feedback_templates': configData.feedback_templates,
        'feedback_pattern': step3 || '',
        'feedback_pattern_custom': step3A || ''
    };
    
    console.log('Sending styleData to backend:', styleData);
    
    // Show saving status
    const status = document.getElementById('save-status');
    status.textContent = '💾 Saving...';
    status.style.color = 'blue';
    
    fetch('/api/comment/update_style', {
        method: 'POST', 
        headers: {
            'Content-Type': 'application/json'
        }, 
        body: JSON.stringify(styleData)
    }).then(response => {
        if (!response.ok) {
            throw Error('Save failed! Please try again.');
        }
        return response.json()
    }).then(result => {
        if (result.success) {
            status.textContent = '✔️ Saved';
            status.style.color = 'green';
            
            // Redirect to step_final after successful save
            setTimeout(() => {
                window.location.href = '/page_final';
            }, 1000);
        } else {
            console.log("Failed result is", result);
            throw Error('Save failed! Please try again.');
        }
    }).catch(error => {
        console.error(error);
        status.textContent = '❌ Save failed';
        status.style.color = 'red';
        alert(error);
    });
}
// ==================== Export functions for global access ====================

// Make functions available globally
window.feedbackInputFunctions = {
    // Component 1
    // getSelectedStyles,
    // resetStyles,
    resetSingleStep,
    initStyleKeywordsComponent,
    
    // Component 2
    getTemplateTexts,
    // addTemplate,
    // deleteTemplate,
    initFeedbackTemplatesComponent,
    // resetToDefaultTemplate,
    
    // Component 3
    // getSelectedTeachingStyle,
    initTeachingStyleComponent,
    
    // Component 4
    // getAdditionalExamples,
    // initTeachingExampleComponent,
    
    // Display functions
    displayStyleKeywordsAsText,
    displayFeedbackTemplatesAsText,
    // displayTeachingStyleAsText,
    // displayTeachingExampleAsText,
    
    // Utility functions
    getAllFormData,
    clearAllStoredData,
    getStoredConfigData,
    loadPriorSetting,

    // Utility functions
    saveAndProceed_page2
};
