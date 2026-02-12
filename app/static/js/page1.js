/**
 * step1.js
 * Page-1-only logic for managing feedback templates (step2)
 */

/* ---------- Read template texts ---------- */
function getTemplateTexts() {
    return Array.from(
        document.querySelectorAll('.template-input')
    )
        .map(input => input.value)
        .filter(v => typeof v === 'string' && v.trim() !== '');
}

/* ---------- Save to sessionStorage ---------- */
function saveFeedbackTemplatesToSessionStorage() {
    const templates = getTemplateTexts();
    sessionStorage.setItem('step2', JSON.stringify(templates));
}

/* ---------- Load from sessionStorage ---------- */
function loadFeedbackTemplatesFromSessionStorage() {
    const container = document.getElementById('template-container');
    if (!container) return;

    let templates = [];
    try {
        const raw = sessionStorage.getItem('step2');
        if (raw) {
            templates = JSON.parse(raw);
        }
    } catch {
        templates = [];
    }

    if (!Array.isArray(templates)) {
        templates = [];
    }

    container.innerHTML = '';

    templates.forEach(text => {
        if (typeof text !== 'string' || !text.trim()) return;

        const row = document.createElement('div');
        row.className = 'template-row';
        row.innerHTML = `
            <input
                type="text"
                class="template-input"
                maxlength="50"
                value="${text}"
            >
        `;

        const input = row.querySelector('.template-input');
        input.addEventListener('input', saveFeedbackTemplatesToSessionStorage);

        container.appendChild(row);
    });
}

/* ---------- Clear UI only ---------- */
function clearTemplateUI() {
    const container = document.getElementById('template-container');
    if (container) {
        container.innerHTML = '';
    }
}
