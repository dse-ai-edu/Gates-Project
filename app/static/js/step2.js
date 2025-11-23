//load data from backend
function loadPage() {
    const session = localStorage.getItem('session');
    const pathname = window.location.pathname;

    if (!session) return;

    //grab data from flask
    fetch(`/api/session/load?session=${encodeURIComponent(session)}`)
        .then(response => {
            if (!response.ok) throw Error('Failed to load session');
            return response.json();
        })
        .then(result => {
            const data = result?.cache?.[pathname];

            if (!data) return;

            //grab stage number
            if (data.stage) {
                stage = data.stage;
                updateVisualStage();
            }

            //grab perspectives (stage 2)
            if (data.perspectives) {
                const textareas = document.querySelectorAll('#stage2-content textarea');
                data.perspectives.forEach((text, i) => {
                    if (textareas[i]) textareas[i].value = text;
                });
            }

            //grab grading scale (stage 3)
            if (data.grading_scale) {
                const gradingTextarea = document.querySelector('#stage3-content textarea');
                if (gradingTextarea) gradingTextarea.value = data.grading_scale;
            }
        })
        .catch(err => console.error("Stage load error:", err));
}

//defualt is stage 1
let stage = 1;

//needed elements
const box = document.getElementById('stage-box');
const nextButton = document.getElementById('stage-next');
const backButton = document.getElementById('stage-back');

const stepTexts = {
    1: document.getElementById('step-1-text'),
    2: document.getElementById('step-2-text'),
    3: document.getElementById('step-3-text')
};

//update UI based on stage
function updateVisualStage() {
    // Update right section style
    box.className = 'right-section stage-' + stage;

    // Highlight the current step and reset others (lit up white text)
    Object.keys(stepTexts).forEach(key => {
        if (parseInt(key) === stage) {
            stepTexts[key].classList.add('highlighted-step');
        } else {
            stepTexts[key].classList.remove('highlighted-step');
        }
    });

    // Show/hide stage nav buttons
    nextButton.style.display = stage === 3 ? 'none' : 'inline-block';
    backButton.style.display = stage === 1 ? 'none' : 'inline-block';

    //save each time stage is updated
    window.saveSession();
}

function nextStage() {
    if (stage < 3) {
        stage++;
        updateVisualStage();
    }
}
function previousStage() {
    if (stage > 1) {
        stage--;
        updateVisualStage();
    }
}

//event listner for navigation between stages
nextButton.addEventListener('click', nextStage);
backButton.addEventListener('click', previousStage);

//save stage and inputed data to backend
window.saveSession = function () {
    const session = localStorage.getItem('session');
    const pathname = window.location.pathname;
    if (!session) return;

    //three perspectives
    const perspectives = Array.from(document.querySelectorAll('#stage2-content textarea')).map(t => t.value.trim());
    //grading scale
    const gradingScale = document.querySelector('#stage3-content textarea')?.value.trim() || '';

    //data to send to flask
    const cache = {
        [pathname]: {
            stage: stage,
            perspectives: perspectives,
            grading_scale: gradingScale
        }
    };

    //send data to flask
    fetch('/api/session/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session, cache })
    }).catch(err => console.error("Session save error:", err));
};

//Run when page loads
document.addEventListener('DOMContentLoaded', () => {
    loadPage();
});