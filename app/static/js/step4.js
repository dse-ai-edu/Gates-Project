function selectTask() {
    let select = document.getElementById('task-select');
    let rubric = document.querySelector("#rubric-content");
    let demonstration = document.querySelector("p#rubric-example");
  
    fetch('/api/task/select', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: select.value })
    }).then(response => {
      if (!response.ok) {
        throw new Error('Fail to find progress status.');
      }
      return response.json();
    }).then(result => {
      rubric.textContent = result.rubric;
      demonstration.textContent = result.demonstration;
    }).catch(error => console.error(error));
}

function loadTask() {
    let userId = localStorage.getItem('userId');
  
    fetch('/api/task/load', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    }).then(response => {
      if (!response.ok) {
        throw new Error('Fail to find progress status.');
      }
      return response.json();
    }).then(result => {
      let select = document.getElementById('task-select');
      result.task_list.forEach(element => {
        const option = document.createElement('option');
        option.textContent = element;
        option.value = element;
        select.appendChild(option);
      });
    }).catch(error => console.error(error));
}

function runTask() {
    let select = document.getElementById('task-select');
    let answerText = document.querySelector("#textInputArea > textarea").value;
    let answerPath = document.querySelector("#fileUploadInput").value;
  
    fetch('/api/task/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        task_id: select.value,
        answer_text: answerText,
        answer_path: answerPath
      })
    }).then(response => {
      if (!response.ok) {
        throw new Error('Fail to find progress status.');
      }
      return response.json();
    }).then(result => {
      let output = document.querySelector("#result-display");
      if (result.grade == null) {
        output.innerHTML = '<h2>Result</h2><p>Fail to grade, please retry.</p>';
      } else {
        let formattedOutput = '<h2>Result</h2>';
        for (const [key, value] of Object.entries(result)) {
          formattedOutput += `<p><strong>${key.charAt(0).toUpperCase() + key.slice(1)}:</strong> ${value}</p>`;
        }
        output.innerHTML = formattedOutput;
      }
    }).catch(error => console.error(error));
  }