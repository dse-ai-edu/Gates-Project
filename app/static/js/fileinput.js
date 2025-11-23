function handleFiles(files) {
	[...files].forEach(selectFile);
}

function selectFile(file) {
	const fileItem = document.createElement('div');
	fileItem.className = 'file-item';
	fileItem.fileData = file;
	fileItem.innerHTML = `
	<div style="display: flex; justify-content: space-between;">
		<div class="col-8" style="padding:0pt" id="itemname">${fileItem.fileData.name}
			<img src="./static/images/correct.png" id="finish-img" style="height: 20px; width: auto; display: none;">
		</div>
		<div style="display: flex; align-items: flex-end;" >
			<div class="text-btn" id="upload-btn" style="display:block">Upload</div>
			<div class="text-btn" id="remove-btn" style="display:block">Cancel</div>
		</div>
	</div>
	`;
	document.getElementById('file-list').appendChild(fileItem);

	fileItem.querySelector('#upload-btn').addEventListener("click", function() {
		this.style.display = 'none';
		this.parentElement.querySelector('#remove-btn').style.display = 'none';
		const progressBar = document.createElement('div');
		progressBar.className = 'col-12';
		progressBar.style.padding = '0pt';
		progressBar.innerHTML = `<div class="progress-bar"><div class="progress"></div></div>`
		this.parentElement.parentElement.parentElement.append(progressBar);
		uploadFile(this.parentElement.parentElement.parentElement)
	});

	fileItem.querySelector('#remove-btn').addEventListener("click", function() {
		this.parentElement.parentElement.parentElement.remove();
	});
}


function uploadFile(fileItem) {
	const progressBar = fileItem.querySelector('.progress');
	const uploadBtn = fileItem.querySelector('#upload-btn');
	const removeBtn = fileItem.querySelector('#remove-btn');
	const finishImg = fileItem.querySelector('#finish-img');

	// Fake upload progress
	let progress = 0;
	const interval = setInterval(() => {
		progress += Math.random() * 20;
		if (progress >= 100) {
			progressBar.style.width = '100%';
			progressBar.style.background = 'green';
			progressBar.parentElement.style.display = 'none';
			
			uploadBtn.style.display = 'none';
			removeBtn.textContent = 'Remove';
			removeBtn.style.display = 'block';
			finishImg.style.display = 'inline';
			clearInterval(interval);
		} else {
			progressBar.style.width = `${progress}%`;
		}
	}, 300);
}
