document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('upload-form');
    const answerInput = document.getElementById('answer_file');
    const sheetInput = document.getElementById('sheet_files');
    const sheetFolderInput = document.getElementById('sheet_folder');
    const answerDrop = document.getElementById('answer-drop-area');
    const sheetDrop = document.getElementById('sheet-drop-area');
    const sheetMessage = document.getElementById('sheet-message');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const loader = submitBtn.querySelector('.loader');
    
    const resultsSection = document.getElementById('results-section');
    const errorContainer = document.getElementById('error-container');
    const errorMessage = document.getElementById('error-message');
    
    const thead = document.getElementById('table-head-row');
    const tbody = document.getElementById('table-body');
    const downloadCsvBtn = document.getElementById('download-csv');

    let currentResults = [];
    let sheetFilesArray = [];

    // Helper to prevent default drag behaviors
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        answerDrop.addEventListener(eventName, preventDefaults, false);
        sheetDrop.addEventListener(eventName, preventDefaults, false);
    });

    // Visual feedback for drag and drop
    ['dragenter', 'dragover'].forEach(eventName => {
        answerDrop.addEventListener(eventName, () => answerDrop.classList.add('dragover'), false);
        sheetDrop.addEventListener(eventName, () => sheetDrop.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        answerDrop.addEventListener(eventName, () => answerDrop.classList.remove('dragover'), false);
        sheetDrop.addEventListener(eventName, () => sheetDrop.classList.remove('dragover'), false);
    });

    // Handle Answer Key Drop/Change
    function updateAnswerUI() {
        const msgSpan = answerDrop.querySelector('.file-message');
        if (answerInput.files.length > 0) {
            answerDrop.classList.add('has-file');
            msgSpan.textContent = answerInput.files[0].name;
        } else {
            answerDrop.classList.remove('has-file');
            msgSpan.textContent = "Upload answer.txt (leave empty to use existing)";
        }
    }

    answerDrop.addEventListener('drop', (e) => {
        answerInput.files = e.dataTransfer.files;
        updateAnswerUI();
    });

    answerInput.addEventListener('change', updateAnswerUI);

    // Handle OMR Sheets Drop/Change
    function updateSheetUI() {
        if (sheetFilesArray.length > 0) {
            sheetDrop.classList.add('has-file');
            sheetMessage.textContent = `${sheetFilesArray.length} file(s) ready for processing`;
        } else {
            sheetDrop.classList.remove('has-file');
            sheetMessage.textContent = "Drop PDF/PNG sheets here or choose below";
        }
    }

    function addSheetFiles(fileList) {
        const validExtensions = ['.pdf', '.png', '.jpg', '.jpeg'];
        for (let i = 0; i < fileList.length; i++) {
            const file = fileList[i];
            const name = file.name.toLowerCase();
            // Filter by extension and ignore hidden files
            if (!name.startsWith('.') && validExtensions.some(ext => name.endsWith(ext))) {
                // Prevent duplicates
                const isDuplicate = sheetFilesArray.some(f => f.name === file.name && f.size === file.size);
                if (!isDuplicate) {
                    sheetFilesArray.push(file);
                }
            }
        }
        updateSheetUI();
    }

    sheetDrop.addEventListener('drop', (e) => {
        addSheetFiles(e.dataTransfer.files);
    });

    sheetInput.addEventListener('change', (e) => {
        addSheetFiles(e.target.files);
        e.target.value = ''; // Reset input so same file can be selected again if removed
    });

    sheetFolderInput.addEventListener('change', (e) => {
        addSheetFiles(e.target.files);
        e.target.value = ''; // Reset
    });

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (sheetFilesArray.length === 0) {
            showError("Please select at least one OMR sheet to process.");
            return;
        }

        const formData = new FormData();
        
        if (answerInput.files.length > 0) {
            formData.append('answer_file', answerInput.files[0]);
        }
        
        for (let i = 0; i < sheetFilesArray.length; i++) {
            formData.append('sheet_files', sheetFilesArray[i]);
        }

        // UI State: Loading
        submitBtn.disabled = true;
        btnText.classList.add('hidden');
        loader.classList.remove('hidden');
        errorContainer.classList.add('hidden');
        resultsSection.classList.add('hidden');

        // Configure this when deploying frontend (Vercel) and backend (Render) separately.
        // Example: const API_BASE_URL = 'https://my-omr-backend.onrender.com';
        const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
            ? '' 
            : 'https://omr-checker-7rom.onrender.com'; // <-- Insert Render URL here!

        try {
            const response = await fetch(`${API_BASE_URL}/process`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (response.ok && data.success) {
                renderResults(data.results);
            } else {
                showError(data.error || "An unknown error occurred during processing.");
            }
        } catch (err) {
            showError("Failed to connect to the server. Please check if the backend is running.");
        } finally {
            // UI State: Restored
            submitBtn.disabled = false;
            btnText.classList.remove('hidden');
            loader.classList.add('hidden');
        }
    });

    function showError(msg) {
        errorMessage.textContent = msg;
        errorContainer.classList.remove('hidden');
        resultsSection.classList.add('hidden');
    }

    function renderResults(results) {
        currentResults = results;
        thead.innerHTML = '';
        tbody.innerHTML = '';

        if (results.length === 0) {
            showError("No valid results found. Evaluation may have failed to extract data.");
            return;
        }

        const keys = Object.keys(results[0]);
        
        // Headers
        keys.forEach(key => {
            const th = document.createElement('th');
            th.textContent = key;
            thead.appendChild(th);
        });

        // Rows
        results.forEach(row => {
            const tr = document.createElement('tr');
            keys.forEach(key => {
                const td = document.createElement('td');
                td.textContent = row[key];
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });

        resultsSection.classList.remove('hidden');
        errorContainer.classList.add('hidden');
    }

    // CSV Download
    downloadCsvBtn.addEventListener('click', () => {
        if (!currentResults || currentResults.length === 0) return;
        
        const keys = Object.keys(currentResults[0]);
        let csvContent = "data:text/csv;charset=utf-8," 
            + keys.join(",") + "\n"
            + currentResults.map(row => {
                return keys.map(k => `"${row[k]}"`).join(",");
            }).join("\n");
            
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "omr_grades.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });
});
