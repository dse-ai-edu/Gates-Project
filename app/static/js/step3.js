//same as step1, but stores seperate data (possibly can create a shared js file later to avoid redundancy)

//store the file state
let fileState = {
    filename: null,
    content: null
};
  
//load session from backend to update UI
function loadPage() {
    const session = localStorage.getItem('session');
    const pathname = window.location.pathname;
    
    //just in case
    if (!session) return;
    
    //get data from flask
    fetch(`/api/session/load?session=${encodeURIComponent(session)}`)
        .then(response => {
        if (!response.ok) throw Error('Failed to load session data.');
            return response.json();
    })
    .then(result => {
        const data = result?.cache?.[pathname];
        if (!data) return;
            
        // Restore text input
        const textarea = document.getElementById('one-textarea');
        if (data.demoText && textarea) {  // Changed from data.rubric to data.demoText
            textarea.value = data.demoText;
        }
    
        // Restore file data
        if (data.file_data) {
            fileState.filename = data.file_data.filename;
            fileState.content = data.file_data.content;

            //display file name
            document.getElementById('file-name').textContent = fileState.filename || 'No file chosen';

            //keep globally available
            if (fileState.content) window.uploadedDemoContent = fileState.content;  // Changed from uploadedFileContent
        }
    
        // Reset UI, start from option
        const boxOne = document.getElementById('box-one');
        const boxTwo = document.getElementById('box-two');
        const rightContent = document.getElementById('right-content');
        const continueBtn = document.getElementById('continue-btn');

        if (boxOne && boxTwo && rightContent && continueBtn) {
            boxOne.classList.add('hidden');
            boxTwo.classList.add('hidden');
            rightContent.classList.remove('hidden');
            continueBtn.disabled = true;
            continueBtn.classList.remove('enabled');
        }
    })
    .catch(err => console.error("Session load error:", err));
}
  
//switch between options
function showBox(type) {
    const rightContent = document.getElementById('right-content');
    const boxOne = document.getElementById('box-one');
    const boxTwo = document.getElementById('box-two');
    const continueBtn = document.getElementById('continue-btn');
    const fileInput = document.getElementById('two-upload'); // diff from step1js
    const fileName = document.getElementById('file-name');
    
    //hide option screen
    rightContent.classList.add('hidden');
    
    //text input box
    if (type === 'one') {
        boxOne.classList.remove('hidden');
        boxTwo.classList.add('hidden');
    } 
    //file upload box
    else if (type === 'two') {
        boxTwo.classList.remove('hidden');
        boxOne.classList.add('hidden');
        
        //clear file input only if nothing was uploaded
        if (!fileState.filename) {
            fileInput.value = '';
            fileName.textContent = 'No file chosen';
        }
    }
    
    continueBtn.disabled = false;
    continueBtn.classList.add('enabled');
    
    //back to option screen
    continueBtn.onclick = function() {
        rightContent.classList.remove('hidden');
        boxOne.classList.add('hidden');
        boxTwo.classList.add('hidden');
        continueBtn.disabled = true;
        continueBtn.classList.remove('enabled');
    };
}

//save typed and upload data
window.saveSession = function() {
    const session = localStorage.getItem('session');
    const pathname = window.location.pathname;
    const demoText = document.getElementById('one-textarea')?.value || "";  // Changed from typedRubric
    const uploadedFile = document.getElementById('two-upload').files[0]; // diff from step1js

    const cache = {
        [pathname]: {
            demoText: demoText,  // Changed from rubric to demoText
            
            file_data: {
                filename: fileState.filename || (uploadedFile ? uploadedFile.name : null),
                content: fileState.content || window.uploadedDemoContent || null  // Changed from uploadedFileContent
            }
        }
    };

    //send data to flask session
    fetch('/api/session/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session, cache })
    }).then(response => {
        if (!response.ok) throw Error('Failed to save session data.');
        return response.json();
    }).then(result => {
        if (!result.success) alert('Failed to save. Try again.');
    }).catch(err => console.error("Save error:", err));
};

//file upload
document.addEventListener("DOMContentLoaded", () => {
    loadPage();

    // Handle navigation buttons
    document.querySelector('.nav-link[href="/step2"]').addEventListener('click', (e) => {
        // No need to save when going back
    });

    document.querySelector('.nav-link[href="/step4"]').addEventListener('click', (e) => {
        e.preventDefault();
        saveSession();  // Save before navigating forward
        setTimeout(() => {
            window.location.href = '/step4';
        }, 500);  // Small delay to ensure save completes
    });

    //file selection handling
    document.getElementById('two-upload').onchange = async function() { //dif from step1
        const file = this.files[0];
        if (!file) return;

        fileState.filename = file.name;
        document.getElementById('file-name').textContent = file.name;

        try {
            //proccess in files.py
            const formData = new FormData();
            formData.append('file', file);
            formData.append('random', false);

            const response = await fetch('/upload', { method: 'POST', body: formData });
            const result = await response.json();

            if (response.ok) {
                //save content
                fileState.content = result.content;
                window.uploadedDemoContent = result.content;  // Changed from uploadedFileContent
            } else {
                throw new Error(result.error || "Upload failed");
            }
        } catch (err) {
            console.error("Upload error:", err);
            fileState.filename = null;
            document.getElementById('file-name').textContent = 'No file chosen';
        }
    };
});