let currentPdfPath = null;
let imageList = [];

const pdfInput = document.getElementById("pdfInput");
const uploadBtn = document.getElementById("uploadBtn");
const convertBtn = document.getElementById("convertBtn");
const downloadBtn = document.getElementById("downloadBtn");

const pdfPanel = document.getElementById("pdfPanel");
const imagePanel = document.getElementById("imagePanel");

uploadBtn.onclick = () => pdfInput.click();

pdfInput.onchange = async () => {
    const file = pdfInput.files[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
        alert("Not a PDF file");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch("/api/preprocess/upload_pdf", {
        method: "POST",
        body: formData
    });
    const data = await res.json();

    if (!data.success) {
        alert(data.msg || "Upload failed");
        return;
    }

    currentPdfPath = data.pdf_path;
    imageList = [];
    imagePanel.innerHTML = "";

    // after upload success
    currentPdfPath = data.pdf_path;

    pdfPanel.innerHTML = `
        <embed src="/${data.pdf_path}" type="application/pdf">
    `;
};

convertBtn.onclick = async () => {
    if (!currentPdfPath) {
        alert("No PDF uploaded");
        return;
    }

    const res = await fetch("/api/preprocess/segment", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            pdf_path: currentPdfPath
        })
    });

    if (!res.ok) {
        alert("Convert failed");
        return;
    }

    const data = await res.json();
    if (!data.success) return;

    imageList = data.images;
    imagePanel.innerHTML = "";

    imageList.sort().forEach((img, idx) => {
        const imgEl = document.createElement("img");
        imgEl.src = "/" + img;
        imgEl.className = "image-item";
        imagePanel.appendChild(imgEl);

        if (idx < imageList.length - 1) {
            const sep = document.createElement("div");
            sep.className = "separator";
            imagePanel.appendChild(sep);
        }
    });
};


downloadBtn.onclick = async () => {
    if (imageList.length === 0) {
        alert("No images available. Upload a PDF and click Convert first.");
        return;
    }

    const res = await fetch("/api/preprocess/segment_download", {
        method: "POST"
    });

    if (!res.ok) return;

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "figures.zip";
    a.click();
    window.URL.revokeObjectURL(url);
};
