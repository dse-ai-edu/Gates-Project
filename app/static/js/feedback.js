// Global variables
let templateCount = 3;
const maxTemplates = 10;

// Template management functions
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
    }
}

function deleteTemplate(button) {
    const templateRow = button.parentElement;
    templateRow.remove();
    templateCount--;
    updateAddButtonState();
}

function updateAddButtonState() {
    const addTemplateBtn = document.getElementById('add-template-btn');
    if (templateCount >= maxTemplates) {
        addTemplateBtn.disabled = true;
        addTemplateBtn.style.opacity = '0.6';
    } else {
        addTemplateBtn.disabled = false;
        addTemplateBtn.style.opacity = '1';
    }
}

// Style management functions
function resetStyles() {
    const checkboxes = document.querySelectorAll('#style-grid input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
}

// Teaching style management functions (from original script)
function setTeachingStyle() {
    const teachingStyleGroup = document.getElementById('teaching-style-group');
    const additionalInstructions = document.getElementById('additional-instructions');
    const setBtn = document.getElementById('set-btn');
    const editBtn = document.getElementById('edit-btn');
    
    teachingStyleGroup.classList.add('disabled');
    additionalInstructions.disabled = true;
    additionalInstructions.classList.add('disabled');
    
    setBtn.style.display = 'none';
    editBtn.style.display = 'inline-block';
    
    const selectedStyle = document.querySelector('input[name="teaching-style"]:checked').value;
    const instructions = additionalInstructions.value;
    
    console.log('Selected Teaching Style:', selectedStyle);
    console.log('Additional Instructions:', instructions);
}

function editTeachingStyle() {
    const teachingStyleGroup = document.getElementById('teaching-style-group');
    const additionalInstructions = document.getElementById('additional-instructions');
    const setBtn = document.getElementById('set-btn');
    const editBtn = document.getElementById('edit-btn');
    
    teachingStyleGroup.classList.remove('disabled');
    additionalInstructions.disabled = false;
    additionalInstructions.classList.remove('disabled');
    
    setBtn.style.display = 'inline-block';
    editBtn.style.display = 'none';
}

// Data retrieval functions
function getSelectedStyles() {
    const checkboxes = document.querySelectorAll('#style-grid input[type="checkbox"]:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function getTemplateTexts() {
    const inputs = document.querySelectorAll('.template-input');
    return Array.from(inputs).map(input => input.value).filter(value => value.trim() !== '');
}

function getSelectedTeachingStyle() {
    const selectedRadio = document.querySelector('input[name="teaching-style"]:checked');
    return selectedRadio ? selectedRadio.value : null;
}

function getAdditionalInstructions() {
    const additionalInstructions = document.getElementById('additional-instructions');
    return additionalInstructions ? additionalInstructions.value : '';
}

// Utility function to get all form data
function getAllFormData() {
    return {
        selectedStyles: getSelectedStyles(),
        templateTexts: getTemplateTexts(),
        teachingStyle: getSelectedTeachingStyle(),
        additionalInstructions: getAdditionalInstructions()
    };
}