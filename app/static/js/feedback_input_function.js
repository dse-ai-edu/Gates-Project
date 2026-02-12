/**
 * feedback_input_function.js
 *
 * Shared logic used by page_1 and page_2 only.
 * This file MUST NOT contain page routing or DOMContentLoaded dispatch.
 */

window.feedbackInputFunctions = window.feedbackInputFunctions || {};

/* ==================== Component 1: Style Keywords ==================== */

function initStyleKeywordsComponent() {
    const radios = document.querySelectorAll(
        'input[type="radio"][name^="step1"]'
    );

    // Restore previous selections
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

    // Save on change
    radios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.checked) {
                sessionStorage.setItem(radio.name, radio.value);
            }
        });
    });
}

/* ==================== Component 2: Feedback Templates ==================== */

function initFeedbackTemplatesComponent() {
    const DEFAULT_FEEDBACK_TEMPLATES = [
        "Strengths",
        "Weaknesses",
        "Suggestions for improvement"
    ];

    if (!sessionStorage.getItem('step2')) {
        sessionStorage.setItem(
            'step2',
            JSON.stringify(DEFAULT_FEEDBACK_TEMPLATES)
        );
    }
}

/* ==================== Component 3: Feedback Pattern ==================== */

function initFeedbackPatternComponent() {
    const radios = document.querySelectorAll('input[name="step3"]');
    const container = document.getElementById('custom-rubric-container');
    const textarea = document.getElementById('custom-rubric-text');
    const customRadio = document.querySelector(
        'input[name="step3"][value=""]'
    );

    const step3  = sessionStorage.getItem('step3');
    const step3A = sessionStorage.getItem('step3A');

    // Restore state
    if (step3) {
        const radio = document.querySelector(
            `input[name="step3"][value="${step3}"]`
        );
        if (radio) radio.checked = true;
        if (container) container.style.display = 'none';
    } else if (step3 === '' && step3A) {
        if (customRadio) customRadio.checked = true;
        if (container) container.style.display = 'block';
        if (textarea) textarea.value = step3A;
    }

    // Bind events
    radios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (!radio.checked) return;

            if (radio === customRadio) {
                sessionStorage.setItem('step3', '');
                if (container) container.style.display = 'block';
            } else {
                sessionStorage.setItem('step3', radio.value);
                sessionStorage.removeItem('step3A');
                if (container) container.style.display = 'none';
            }
        });
    });

    if (textarea) {
        textarea.addEventListener('input', () => {
            if (customRadio && customRadio.checked) {
                sessionStorage.setItem('step3A', textarea.value);
            }
        });
    }
}

/* ==================== Export ==================== */

window.feedbackInputFunctions = {
    initStyleKeywordsComponent,
    initFeedbackTemplatesComponent,
    initFeedbackPatternComponent
};
