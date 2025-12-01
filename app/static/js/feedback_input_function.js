// Feedback Input Functions JavaScript
// Global variables
let templateCount = 3;
const maxTemplates = 10;
let locked_style = false;

// ==================== Component 1: Style Keywords Functions ====================

function getSelectedStyles() {
    const checkboxes = document.querySelectorAll('#style-grid input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function resetStyles() {
    const checkboxes = document.querySelectorAll('#style-grid input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    // Update localStorage
    saveStyleKeywordsToLocalStorage();
}

function saveStyleKeywordsToLocalStorage() {
    const selectedStyles = getSelectedStyles();
    const styleKeywords = selectedStyles.join('\n');
    localStorage.setItem('step1_style_keywords', styleKeywords);
    console.log('Style keywords saved:', styleKeywords);
}

function loadStyleKeywordsFromLocalStorage() {
    const storedStyles = localStorage.getItem('step1_style_keywords') || '';
    if (storedStyles) {
        const styleArray = storedStyles.split('\n');
        styleArray.forEach(style => {
            const checkbox = document.querySelector(`input[value="${style}"]`);
            if (checkbox) {
                checkbox.checked = true;
            }
        });
    }
}

function initStyleKeywordsComponent() {
    // Load stored data
    loadStyleKeywordsFromLocalStorage();
    
    // Add event listeners
    const resetBtn = document.getElementById('reset-styles-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetStyles);
    }
    
    // Add change listeners to checkboxes
    const checkboxes = document.querySelectorAll('#style-grid input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', saveStyleKeywordsToLocalStorage);
    });
}

// ==================== Component 2: Feedback Templates Functions ====================

function getTemplateTexts() {
    const inputs = document.querySelectorAll('.template-input');
    return Array.from(inputs).map(input => input.value).filter(value => value.trim() !== '');
}

function addTemplate() {
    const templateContainer = document.getElementById('template-container');
    if (templateCount < maxTemplates) {
        const templateRow = document.createElement('div');
        templateRow.className = 'template-row';
        
        templateRow.innerHTML = `
            <input type="text" class="template-input" placeholder="enter one template item (max 50 characters)" maxlength="50">
            <button class="delete-btn" onclick="deleteTemplate(this)">×</button>
        `;
        
        templateContainer.appendChild(templateRow);
        templateCount++;
        updateAddButtonState();
        
        // Add event listener to new input
        const newInput = templateRow.querySelector('.template-input');
        newInput.addEventListener('input', saveFeedbackTemplatesToLocalStorage);
    }
}

function deleteTemplate(button) {
    const templateRow = button.parentElement;
    templateRow.remove();
    templateCount--;
    updateAddButtonState();
    saveFeedbackTemplatesToLocalStorage();
}

function updateAddButtonState() {
    const addTemplateBtn = document.getElementById('add-template-btn');
    if (addTemplateBtn) {
        if (templateCount >= maxTemplates) {
            addTemplateBtn.disabled = true;
            addTemplateBtn.style.opacity = '0.6';
        } else {
            addTemplateBtn.disabled = false;
            addTemplateBtn.style.opacity = '1';
        }
    }
}

function saveFeedbackTemplatesToLocalStorage() {
    const templateTexts = getTemplateTexts();
    const feedbackTemplates = templateTexts.join('\n');
    localStorage.setItem('step1_feedback_templates', feedbackTemplates);
    console.log('Feedback templates saved:', feedbackTemplates);
}

function loadFeedbackTemplatesFromLocalStorage() {
    const storedTemplates = localStorage.getItem('step1_feedback_templates') || '';
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
                input.addEventListener('input', saveFeedbackTemplatesToLocalStorage);
            }
        });
        
        updateAddButtonState();
    }
}

function initFeedbackTemplatesComponent() {
    // Load stored data
    loadFeedbackTemplatesFromLocalStorage();
    
    // Add event listeners
    const addBtn = document.getElementById('add-template-btn');
    if (addBtn) {
        addBtn.addEventListener('click', addTemplate);
    }
    
    // Add event listeners to existing inputs
    const existingInputs = document.querySelectorAll('.template-input');
    existingInputs.forEach(input => {
        input.addEventListener('input', saveFeedbackTemplatesToLocalStorage);
    });
    
    // Update template count
    templateCount = existingInputs.length;
    updateAddButtonState();
}

function resetToDefaultTemplate() {
    const templateContent = document.getElementById('feedback-templates-content');
    templateContent.innerHTML = `
        <button class="default-template-btn" id="default-template-btn" onclick="resetToDefaultTemplate()">Default Template</button>
        <p>* Enter section titles for reply text items, such as "improvement". <br>
           * Use parentheses for additional notes, e.g., "improvement (suggestions on how to enhance mathematical abilities)". <br>
           * For hierarchical categories, use colons to separate levels, e.g., "improvement: knowledge to review" & "improvement: take-away question".<br>
           * If no template is set, the default is "Strength + Weakness + Improvement." </p>
        <div class="template-section">
            <button class="add-template-btn" id="add-template-btn">Add One</button>
            <div class="template-container" id="template-container">
                <div class="template-row">
                    <input type="text" class="template-input" placeholder="enter one template item (max 50 characters)" maxlength="50" value="strength">
                    <button class="delete-btn" onclick="deleteTemplate(this)">×</button>
                </div>
                <div class="template-row">
                    <input type="text" class="template-input" placeholder="enter one template item (max 50 characters)" maxlength="50" value="weakness">
                    <button class="delete-btn" onclick="deleteTemplate(this)">×</button>
                </div>
                <div class="template-row">
                    <input type="text" class="template-input" placeholder="enter one template item (max 50 characters)" maxlength="50" value="improvement">
                    <button class="delete-btn" onclick="deleteTemplate(this)">×</button>
                </div>
            </div>
        </div>
    `;
   // Re-initialize the component
    initFeedbackTemplatesComponent();
}
// ==================== Component 3: Teaching Style Functions ====================

function getSelectedTeachingStyle() {
    const selectedRadio = document.querySelector('input[name="teaching-style"]:checked');
    return selectedRadio ? selectedRadio.value : null;
}

function saveTeachingStyleToStorage() {
    const selectedStyle = getSelectedTeachingStyle();
    if (selectedStyle) {
        sessionStorage.setItem('selected_teach_style', selectedStyle);
        console.log('Teaching style saved:', selectedStyle);
    }
}

function loadTeachingStyleFromStorage() {
    const storedStyle = sessionStorage.getItem('selected_teach_style');
    if (storedStyle) {
        const radio = document.querySelector(`input[name="teaching-style"][value="${storedStyle}"]`);
        if (radio) {
            radio.checked = true;
        }
    }
}

function initTeachingStyleComponent() {
    // Load stored data
    loadTeachingStyleFromStorage();
    
    // Add event listeners to radio buttons
    const radioButtons = document.querySelectorAll('input[name="teaching-style"]');
    radioButtons.forEach(radio => {
        radio.addEventListener('change', saveTeachingStyleToStorage);
    });
}

// ==================== Component 4: Teaching Example Functions ====================

function getAdditionalExamples() {
    const additionalExamples = document.getElementById('additional-instructions');
    return additionalExamples ? additionalExamples.value : '';
}

function saveTeachingExampleToStorage() {
    const example = getAdditionalExamples();
    sessionStorage.setItem('teach_example', example);
    console.log('Teaching example saved:', example);
}

function loadTeachingExampleFromStorage() {
    const storedExample = sessionStorage.getItem('teach_example') || '';
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
    const displayText = keywords.length > 0 ? keywords.join(', ') : 'N/A';
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

function displayTeachingStyleAsText(selectedStyle, container) {
    const teachingStyles = [
        'AUTHORITATIVE', 'SOCRATIC', 'NURTURING', 'CONSTRUCTIVE', 'DIRECT', 'PLAIN'
    ];
    
    let html = '<div class="radio-group">';
    teachingStyles.forEach(style => {
        const isSelected = style === selectedStyle;
        const className = isSelected ? 'radio-item' : 'radio-item grayed';
        const checked = isSelected ? 'checked' : '';
        html += `
            <div class="${className}">
                <input type="radio" name="teach-style-display" value="${style}" ${checked} disabled>
                <label>${style}</label>
            </div>
        `;
    });
    html += '</div>';
    container.innerHTML = html;
}

function displayTeachingExampleAsText(example, container) {
    const exampleText = example || 'N/A';
    container.innerHTML = `<div class="teach-example-display">${exampleText}</div>`;
}

// ==================== Common Utility Functions ====================

function getAllFormData() {
    return {
        selectedStyles: getSelectedStyles(),
        templateTexts: getTemplateTexts(),
        teachingStyle: getSelectedTeachingStyle(),
        additionalExamples: getAdditionalExamples()
    };
}

function clearAllStoredData() {
    localStorage.removeItem('step1_style_keywords');
    localStorage.removeItem('step1_feedback_templates');
    sessionStorage.removeItem('selected_teach_style');
    sessionStorage.removeItem('teach_example');
    sessionStorage.removeItem('locked_style');
    console.log('All stored feedback data cleared');
}

function getStoredConfigData() {
    const styleKeywords = localStorage.getItem('step1_style_keywords') || '';
    const feedbackTemplates = localStorage.getItem('step1_feedback_templates') || '';
    const teachStyle = sessionStorage.getItem('selected_teach_style') || '';
    const teachExample = sessionStorage.getItem('teach_example') || '';
    const lockedStyle = sessionStorage.getItem('locked_style') === 'true';
    
    return {
        style_keywords: styleKeywords ? styleKeywords.split('\n').filter(s => s.trim()) : [],
        feedback_templates: feedbackTemplates ? feedbackTemplates.split('\n').filter(t => t.trim()) : [],
        teach_style: teachStyle,
        teach_example: teachExample,
        locked_style: lockedStyle
    };
}

// ==================== Auto-initialization ====================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize components based on what's present in the page
    if (document.getElementById('style-keywords-component')) {
        initStyleKeywordsComponent();
    }
    
    if (document.getElementById('feedback-templates-component')) {
        initFeedbackTemplatesComponent();
    }
    
    if (document.getElementById('teaching-style-component')) {
        initTeachingStyleComponent();
    }
    
    if (document.getElementById('teaching-example-component')) {
        initTeachingExampleComponent();
    }
    
    console.log('Feedback input components initialized');
});

// ==================== Export functions for global access ====================

// Make functions available globally
window.feedbackInputFunctions = {
    // Component 1
    getSelectedStyles,
    resetStyles,
    initStyleKeywordsComponent,
    
    // Component 2
    getTemplateTexts,
    addTemplate,
    deleteTemplate,
    initFeedbackTemplatesComponent,
    resetToDefaultTemplate,
    
    // Component 3
    getSelectedTeachingStyle,
    initTeachingStyleComponent,
    
    // Component 4
    getAdditionalExamples,
    initTeachingExampleComponent,
    
    // Display functions
    displayStyleKeywordsAsText,
    displayFeedbackTemplatesAsText,
    displayTeachingStyleAsText,
    displayTeachingExampleAsText,
    
    // Utility functions
    getAllFormData,
    clearAllStoredData,
    getStoredConfigData
};
