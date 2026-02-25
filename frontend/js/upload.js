/**
 * BizIT Analytics - Upload Page JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    initializeUpload();
    loadUploadHistory();
});

function initializeUpload() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    
    // Drag and drop handlers
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
    
    // File input handler
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
}

function handleFile(file) {
    // Validate file type
    const validTypes = ['text/csv', 'application/vnd.ms-excel', 
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    const validExtensions = ['.csv', '.xlsx', '.xls'];
    
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validExtensions.includes(extension)) {
        showResult('error', 'Invalid File Type', 
            'Please upload a CSV or Excel file (.csv, .xlsx, .xls)');
        return;
    }
    
    // Check file size (max 16MB)
    if (file.size > 16 * 1024 * 1024) {
        showResult('error', 'File Too Large', 
            'Maximum file size is 16MB. Please upload a smaller file.');
        return;
    }
    
    uploadFile(file);
}

async function uploadFile(file) {
    const progressBar = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const statusText = document.getElementById('uploadStatus');
    
    progressBar.style.display = 'block';
    progressFill.style.width = '0%';
    statusText.textContent = 'Preparing upload...';
    
    const formData = new FormData();
    formData.append('file', file);
    
    const token = getToken('access_token');
    
    try {
        // Simulate progress
        let progress = 0;
        const progressInterval = setInterval(() => {
            progress += 10;
            if (progress <= 90) {
                progressFill.style.width = progress + '%';
                statusText.textContent = `Uploading... ${progress}%`;
            }
        }, 200);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });
        
        clearInterval(progressInterval);
        progressFill.style.width = '100%';
        statusText.textContent = 'Processing...';
        
        const data = await response.json();
        
        setTimeout(() => {
            progressBar.style.display = 'none';
            
            if (response.ok) {
                showResult('success', 'Upload Successful', `
                    <div style="text-align: center;">
                        <i class="fas fa-check-circle text-success" style="font-size: 48px; margin-bottom: 20px;"></i>
                        <p style="margin-bottom: 15px;">${data.message}</p>
                        <div style="background: rgba(124, 58, 237, 0.1); padding: 15px; border-radius: 8px; text-align: left; margin-bottom: 20px;">
                            <p><strong>Records Added:</strong> ${data.records_added}</p>
                            <p><strong>Records Updated:</strong> ${data.records_updated}</p>
                            ${data.errors && data.errors.length > 0 ? 
                                `<p class="text-warning" style="margin-top: 10px;"><strong>Warnings:</strong></p>
                                 <ul style="padding-left: 20px; font-size: 0.9rem;">
                                    ${data.errors.map(e => `<li>${e}</li>`).join('')}
                                 </ul>` : ''}
                        </div>
                        <button class="btn btn-primary" onclick="window.location.href='dashboard.html'" style="padding: 12px 24px;">
                            <i class="fas fa-chart-line"></i> View Dashboard
                        </button>
                    </div>
                `);
                loadUploadHistory();
            } else {
                showResult('error', 'Upload Failed', `
                    <div style="text-align: center;">
                        <i class="fas fa-times-circle text-danger" style="font-size: 48px; margin-bottom: 20px;"></i>
                        <p>${data.message || data.error || 'An error occurred during upload'}</p>
                    </div>
                `);
            }
        }, 500);
        
    } catch (error) {
        progressBar.style.display = 'none';
        showResult('error', 'Upload Error', `
            <div style="text-align: center;">
                <i class="fas fa-exclamation-triangle text-danger" style="font-size: 48px; margin-bottom: 20px;"></i>
                <p>Connection error. Please check your network and try again.</p>
            </div>
        `);
    }
    
    // Reset file input
    document.getElementById('fileInput').value = '';
}

async function loadUploadHistory() {
    const token = getToken('access_token');
    const tbody = document.getElementById('uploadHistoryTable');
    
    try {
        const response = await fetch('/api/upload/history', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            
            if (!data.history || data.history.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="4" style="text-align: center; padding: 40px; color: #7F8C8D;">
                            No upload history yet
                        </td>
                    </tr>
                `;
                return;
            }
            
            tbody.innerHTML = data.history.map(item => `
                <tr>
                    <td>
                        <i class="fas fa-file-${item.filename.endsWith('.csv') ? 'csv' : 'excel'}" 
                           style="color: ${item.filename.endsWith('.csv') ? '#27AE60' : '#2E7D32'}; margin-right: 8px;">
                        </i>
                        ${item.filename}
                    </td>
                    <td>${item.records_count.toLocaleString()}</td>
                    <td>
                        <span class="kpi-trend ${item.status === 'success' ? 'up' : item.status === 'partial' ? '' : 'down'}"
                              style="font-size: 0.85rem;">
                            <i class="fas fa-${item.status === 'success' ? 'check' : item.status === 'partial' ? 'exclamation' : 'times'}"></i>
                            ${item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                        </span>
                    </td>
                    <td>${new Date(item.created_at).toLocaleString()}</td>
                </tr>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading upload history:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; padding: 40px; color: #E74C3C;">
                    Error loading upload history
                </td>
            </tr>
        `;
    }
}

function downloadSampleFile() {
    const sampleData = `Date,Revenue,Cost,Profit,Department,Expenses,Sales Volume
2024-01-15,150000,85000,65000,Sales,12000,350
2024-01-15,120000,70000,50000,Marketing,15000,280
2024-01-15,95000,55000,40000,Operations,8000,200
2024-01-15,180000,100000,80000,Technology,20000,150
2024-01-16,160000,90000,70000,Sales,13000,380
2024-01-16,130000,75000,55000,Marketing,16000,300
2024-01-16,100000,60000,40000,Operations,9000,220
2024-01-16,190000,105000,85000,Technology,22000,160
2024-02-15,170000,95000,75000,Sales,14000,400
2024-02-15,140000,80000,60000,Marketing,17000,320
2024-02-15,110000,65000,45000,Operations,10000,240
2024-02-15,200000,110000,90000,Technology,24000,170`;
    
    const blob = new Blob([sampleData], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sample_business_data.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function showResult(type, title, content) {
    document.getElementById('resultTitle').textContent = title;
    document.getElementById('resultBody').innerHTML = content;
    document.getElementById('resultModal').classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// Close modal on click outside
document.getElementById('resultModal').addEventListener('click', function(e) {
    if (e.target === this) {
        this.classList.remove('active');
    }
});
