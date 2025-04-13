// script.js

function showToast(message, type = 'info') {
    Toastify({
        text: message,
        duration: 5000,
        gravity: 'top',
        position: 'right',
        style: { 
            background: type === 'success' ? '#88C057' : type === 'error' ? '#BF616A' : '#3B4252', 
            color: '#ECEFF4',
            borderRadius: '8px',
            boxShadow: '0 5px 15px rgba(0, 0, 0, 0.3)'
        },
    }).showToast();
}

function appendLog(log) {
    const logContainer = document.getElementById('log-container');
    if (!logContainer) return;
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.style.opacity = '0';
    let logClass = log.includes('[ERROR]') ? 'log-error' : log.includes('[WARNING]') ? 'log-warning' : 'log-info';
    logEntry.innerHTML = `<span class="timestamp">${log.split(' - ')[0]}</span> <span class="${logClass}">${log.split(' - ').slice(1).join(' - ')}</span>`;
    logContainer.appendChild(logEntry);
    setTimeout(() => {
        logEntry.style.transition = 'opacity 0.5s';
        logEntry.style.opacity = '1';
    }, 10);
    logContainer.scrollTop = logContainer.scrollHeight;
}

function clearLogs() {
    const logContainer = document.getElementById('log-container');
    if (logContainer) logContainer.innerHTML = `<div class="log-entry">[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Logs cleared.</div>`;
}

function showLoader(show) {
    document.getElementById('loader').style.display = show ? 'flex' : 'none';
}

function checkConnection() {
    fetch('/grand-total')
        .then(response => response.json())
        .then(data => {
            document.getElementById('status-indicator').className = 'status-online';
            document.getElementById('connection-status').textContent = 'Online';
            appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Connected to server.`);
        })
        .catch(() => {
            document.getElementById('status-indicator').className = 'status-offline';
            document.getElementById('connection-status').textContent = 'Offline';
            appendLog(`[ERROR] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Server offline.`);
        });
}

// Upload handling with live status updates
document.getElementById('upload-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    const fileInput = document.getElementById('file');
    const dateInput = document.getElementById('date');
    const uploadBtn = document.getElementById('upload-btn');
    const statusSteps = {
        upload: document.getElementById('step-upload'),
        process: document.getElementById('step-process'),
        db: document.getElementById('step-db'),
        report: document.getElementById('step-report')
    };
    const statusMessage = document.getElementById('status-message');
    const resultSummary = document.getElementById('result-summary');

    if (!fileInput.files.length || !dateInput.value) {
        showToast('Please select a file and date.', 'error');
        return;
    }

    // Reset UI
    uploadBtn.disabled = true;
    resultSummary.classList.add('d-none');
    statusMessage.classList.add('d-none');
    Object.values(statusSteps).forEach(step => {
        step.classList.remove('active', 'completed');
        step.style.opacity = '0.5';
    });

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('date', dateInput.value);

    try {
        // Step 1: Uploading File
        statusSteps.upload.classList.add('active');
        statusSteps.upload.style.opacity = '1';
        appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Starting file upload...`);

        const response = await fetch('/process', { method: 'POST', body: formData });
        statusSteps.upload.classList.remove('active');
        statusSteps.upload.classList.add('completed');

        // Step 2: Processing Data
        statusSteps.process.classList.add('active');
        statusSteps.process.style.opacity = '1';
        appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Processing data...`);

        const data = await response.json();
        statusSteps.process.classList.remove('active');
        statusSteps.process.classList.add('completed');

        if (data.error) throw new Error(data.error);

        // Step 3: Updating Database
        statusSteps.db.classList.add('active');
        statusSteps.db.style.opacity = '1';
        appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Updating database...`);
        await new Promise(resolve => setTimeout(resolve, 500)); // Simulate DB update
        statusSteps.db.classList.remove('active');
        statusSteps.db.classList.add('completed');

        // Step 4: Generating Report
        statusSteps.report.classList.add('active');
        statusSteps.report.style.opacity = '1';
        appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Generating report...`);
        await new Promise(resolve => setTimeout(resolve, 500)); // Simulate report generation
        statusSteps.report.classList.remove('active');
        statusSteps.report.classList.add('completed');

        // Show Results
        document.getElementById('result-date').textContent = data.results.date;
        
        document.getElementById('result-records').textContent =
          data.results.total_records != null ? data.results.total_records.toLocaleString() : '...';
        
        document.getElementById('result-new').textContent =
          data.results.new_records != null ? data.results.new_records.toLocaleString() : 'Updating...';
        
        document.getElementById('result-updated').textContent =
          data.results.updated_records != null ? data.results.updated_records.toLocaleString() : 'Updating...';
        
        document.getElementById('result-daily-sales').textContent =
          data.results.daily_total_sales != null ? data.results.daily_total_sales.toLocaleString() : '...';
        
        document.getElementById('result-daily-purchases').textContent =
          data.results.daily_total_purchases != null ? data.results.daily_total_purchases.toLocaleString() : '...';
        
        resultSummary.classList.remove('d-none');


        const downloadBtn = document.getElementById('download-btn');
        downloadBtn.disabled = false;
        downloadBtn.onclick = () => window.location.href = `/download/${data.results.file_name}`;

        // Success Message
        statusMessage.textContent = 'Processing Completed Successfully!';
        statusMessage.classList.remove('d-none');
        statusMessage.classList.add('success');

        data.logs.forEach(appendLog);
        showToast('Data processed successfully!', 'success');
    } catch (error) {
        // Error Handling
        Object.values(statusSteps).forEach(step => {
            if (step.classList.contains('active')) {
                step.classList.remove('active');
                step.style.opacity = '0.5';
            }
        });
        statusMessage.textContent = `Error: ${error.message}`;
        statusMessage.classList.remove('d-none');
        statusMessage.classList.add('error');
        appendLog(`[ERROR] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - ${error.message}`);
        showToast(`Error: ${error.message}`, 'error');
    } finally {
        uploadBtn.disabled = false;
    }
});

// Data Preview
function loadDataPreview() {
    const tableBody = document.getElementById('data-table-body');
    if (!tableBody) return;

    showLoader(true);
    fetch('/preview')
        .then(response => response.json())
        .then(data => {
            tableBody.innerHTML = '';
            if (data.warning) {
                tableBody.innerHTML = `<tr><td colspan="10" class="text-center">${data.warning}</td></tr>`;
                showToast(data.warning, 'warning');
            } else {
                data.data.forEach((row, index) => {
                    const tr = document.createElement('tr');
                    tr.style.opacity = '0';
                    tr.innerHTML = `
                        <td>${row.brand}</td>
                        <td>${row.category}</td>
                        <td>${row.size}</td>
                        <td>${row.mrp.toFixed(2)}</td>
                        <td>${row.color}</td>
                        <td>${row.sales_qty}</td>
                        <td>${row.purchase_qty}</td>
                        <td>${row.week}</td>
                        <td>${row.month}</td>
                        <td>${new Date(row.created_at).toLocaleString()}</td>
                    `;
                    tableBody.appendChild(tr);
                    setTimeout(() => {
                        tr.style.transition = 'opacity 0.5s';
                        tr.style.opacity = '1';
                    }, index * 30);
                });

                const animateNumber = (id, value) => {
                    let start = 0;
                    const element = document.getElementById(id);
                    const timer = setInterval(() => {
                        start += Math.ceil(value / 20);
                        element.textContent = start.toLocaleString();
                        if (start >= value) {
                            element.textContent = value.toLocaleString();
                            clearInterval(timer);
                        }
                    }, 50);
                };

                animateNumber('metric-total-records', data.metrics.total_records);
                animateNumber('metric-unique-brands', data.metrics.unique_brands);
                animateNumber('metric-unique-categories', data.metrics.unique_categories);
                const ratio = data.metrics.neon_total_purchases > 0 
                    ? ((data.metrics.neon_total_sales / data.metrics.neon_total_purchases) * 100).toFixed(1) 
                    : 0;
                document.getElementById('metric-ratio').textContent = `${ratio}%`;
            }
            data.logs.forEach(appendLog);
            showLoader(false);
        })
        .catch(error => {
            tableBody.innerHTML = `<tr><td colspan="10" class="text-center">Error loading data</td></tr>`;
            appendLog(`[ERROR] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Failed to load preview: ${error.message}`);
            showToast('Failed to load preview.', 'error');
            showLoader(false);
        });
}

// Visualizations
function loadVisualizations(startDate = null, endDate = null) {
    showLoader(true);
    const requestOptions = startDate && endDate ? {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ start_date: startDate, end_date: endDate })
    } : { method: 'GET' };

    fetch('/visualizations', requestOptions)
        .then(response => response.json())
        .then(data => {
            if (data.warning) {
                showToast(data.warning, 'warning');
                ['brand-chart', 'category-chart', 'monthly-chart', 'weekly-chart'].forEach(id => {
                    document.getElementById(id).innerHTML = '<p class="text-center">No data available</p>';
                });
            } else {
                const animateChart = (id, chartData) => {
                    const chartDiv = document.getElementById(id);
                    chartDiv.style.opacity = '0';
                    Plotly.newPlot(id, chartData.data, chartData.layout, { responsive: true });
                    setTimeout(() => {
                        chartDiv.style.transition = 'opacity 1s';
                        chartDiv.style.opacity = '1';
                    }, 100);
                };

                if (data.visualizations.brand) animateChart('brand-chart', JSON.parse(data.visualizations.brand));
                if (data.visualizations.category) animateChart('category-chart', JSON.parse(data.visualizations.category));
                if (data.visualizations.monthly) animateChart('monthly-chart', JSON.parse(data.visualizations.monthly));
                if (data.visualizations.weekly) animateChart('weekly-chart', JSON.parse(data.visualizations.weekly));
            }
            data.logs.forEach(appendLog);
            showLoader(false);
        })
        .catch(error => {
            appendLog(`[ERROR] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Failed to load visualizations: ${error.message}`);
            showToast('Failed to load visualizations.', 'error');
            showLoader(false);
        });
}

// Export Data
function exportData() {
    fetch('/preview')
        .then(response => response.json())
        .then(data => {
            if (data.warning) {
                showToast(data.warning, 'warning');
                return;
            }
            const csv = Papa.unparse(data.data);
            const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'inventory_data.csv';
            link.click();
            showToast('Data exported successfully!', 'success');
        })
        .catch(error => {
            showToast('Failed to export data.', 'error');
            appendLog(`[ERROR] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Export failed: ${error.message}`);
        });
}

// Theme Toggle
document.getElementById('theme-toggle').addEventListener('click', () => {
    document.body.classList.toggle('light-theme');
    const icon = document.getElementById('theme-toggle').querySelector('i');
    icon.classList.toggle('fa-moon');
    icon.classList.toggle('fa-sun');
    localStorage.setItem('theme', document.body.classList.contains('light-theme') ? 'light' : 'dark');
    
    // Force repaint for smooth theme transition
    document.body.style.transition = 'none';
    document.body.offsetHeight; // Trigger reflow
    document.body.style.transition = 'all 0.4s ease';
});

// Navigation
function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
        section.style.opacity = '0';
    });
    const targetSection = document.getElementById(sectionId);
    targetSection.classList.add('active');
    setTimeout(() => {
        targetSection.style.transition = 'opacity 0.5s';
        targetSection.style.opacity = '1';
    }, 10);

    if (sectionId === 'data-preview') loadDataPreview();
    else if (sectionId === 'visualizations') loadVisualizations();
}

document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        this.classList.add('active');
        showSection(this.getAttribute('data-section'));
    });
});

// Event Listeners
document.getElementById('clear-logs')?.addEventListener('click', clearLogs);
document.getElementById('refresh-preview')?.addEventListener('click', () => {
    loadDataPreview();
    showToast('Data refreshed!', 'success');
});
document.getElementById('date-filter-form')?.addEventListener('submit', function(e) {
    e.preventDefault();
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    if (startDate && endDate) {
        loadVisualizations(startDate, endDate);
        showToast('Filters applied!', 'success');
    } else {
        showToast('Select both dates.', 'warning');
    }
});
document.getElementById('export-data')?.addEventListener('click', exportData);

// Initial Setup
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.section').forEach(section => section.style.opacity = '0');
    showSection('upload');
    checkConnection();
    setInterval(checkConnection, 30000);
    appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - System ready.`);

    // Load theme from localStorage
    if (localStorage.getItem('theme') === 'light') {
        document.body.classList.add('light-theme');
        document.getElementById('theme-toggle').querySelector('i').classList.replace('fa-moon', 'fa-sun');
    }
});

async function loadProcessedFiles() {
    const summary = document.getElementById('processed-files-summary');
    const table = document.getElementById('processed-files-table');
    const loader = document.getElementById('local-files-loader');

    summary.innerHTML = '';
    table.innerHTML = '';
    loader.style.display = 'flex';

    try {
        const res = await fetch('/local-files');
        const data = await res.json();

        loader.style.display = 'none';

        if (data.error) {
            summary.innerHTML = `<span class="text-danger">❌ ${data.error}</span>`;
            return;
        }

        const dailyInfo = data.daily_files?.latest_files_info || [];
        const master = data.master_summary || {};

        summary.innerHTML = `
            <div class="alert alert-primary shadow-sm">
                <strong>${data.daily_files?.file_count || 0}</strong> daily files found.
                ${master.status === 'available' ? '✔️ Master summary file is available.' : '⚠️ Master summary file not found.'}
            </div>`;

        let html = '<div class="accordion" id="processedAccordion">';

        dailyInfo.forEach((f, index) => {
            const fileId = `filePreview${index}`;
            html += `
                <div class="accordion-item" style="animation: fadeIn 0.5s ease-in-out;">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#${fileId}" aria-expanded="false">
                            📄 ${f.file} — ${f.rows} rows
                        </button>
                    </h2>
                    <div id="${fileId}" class="accordion-collapse collapse" data-bs-parent="#processedAccordion">
                        <div class="accordion-body">
                            <p><strong>Grand Total Date:</strong> ${f.grand_total_date || '-'}</p>
                            <p><strong>Columns:</strong> ${Array.isArray(f.columns) ? f.columns.join(', ') : '-'}</p>
                            <p class="text-muted">Detailed file preview is available upon full file integration.</p>
                        </div>
                    </div>
                </div>`;
        });

        if (master.status === 'available') {
            html += `
                <div class="accordion-item table-info" style="animation: fadeIn 0.5s ease-in-out;">
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#masterSummary" aria-expanded="false">
                            📊 master_summary.xlsx — ${master.row_count} rows
                        </button>
                    </h2>
                    <div id="masterSummary" class="accordion-collapse collapse">
                        <div class="accordion-body">
                            <p><strong>Grand Total Date:</strong> ${master.grand_total_date || '-'}</p>
                            <p><strong>Columns:</strong> ${Array.isArray(master.columns) ? master.columns.join(', ') : '-'}</p>
                            <p class="text-muted">Current-month summary data. Rich analytics available through the chatbot assistant.</p>
                        </div>
                    </div>
                </div>`;
        }

        html += '</div>';
        table.innerHTML = html;
    } catch (err) {
        loader.style.display = 'none';
        summary.innerHTML = '<span class="text-danger">❌ Error loading local files.</span>';
        console.error(err);
    }
}


function generateSampleTable(rows) {
    if (!Array.isArray(rows) || rows.length === 0) {
        return '<p class="text-muted">No preview data available.</p>';
    }
    const headers = Object.keys(rows[0]).filter(h => h !== 'record_id');
    let html = '<table class="table table-sm table-striped table-bordered"><thead><tr>';
    headers.forEach(h => {
        html += `<th>${h.charAt(0).toUpperCase() + h.slice(1)}</th>`;
    });
    html += '</tr></thead><tbody>';
    rows.forEach(row => {
        html += '<tr>';
        headers.forEach(h => {
            let value = row[h] !== undefined && row[h] !== null ? row[h] : '-';
            if (h === 'MRP' && !isNaN(parseFloat(value))) {
                value = parseFloat(value).toFixed(2);
            } else if (h === 'date' && value) {
                value = new Date(value).toLocaleDateString();
            }
            html += `<td>${value}</td>`;
        });
        html += '</tr>';
    });
    html += '</tbody></table>';
    return html;
}

async function loadProcessedFiles(filter = '') {
    const summary = document.getElementById('processed-files-summary');
    const table = document.getElementById('processed-files-table');
    const localLoader = document.getElementById('local-files-loader');
    const mainLoader = document.getElementById('loader'); // Reference to futuristic loader

    if (!summary || !table || !localLoader || !mainLoader) return;

    summary.innerHTML = '';
    table.innerHTML = '';
    localLoader.style.display = 'flex';
    mainLoader.style.display = 'flex'; // Show futuristic loader

    try {
        const res = await fetch('/local-files');
        const data = await res.json();

        localLoader.style.display = 'none';
        mainLoader.style.display = 'none'; // Hide futuristic loader

        if (data.error) {
            summary.innerHTML = `<span class="text-danger">❌ ${data.error}</span>`;
            appendLog(`[ERROR] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Failed to load local files: ${data.error}`);
            showToast(`Error: ${data.error}`, 'error');
            return;
        }

        let dailyInfo = data.daily_files?.latest_files_info || [];
        const master = data.master_summary || {};

        if (filter.trim()) {
            const lowerFilter = filter.toLowerCase();
            dailyInfo = dailyInfo.filter(f => 
                f.file.toLowerCase().includes(lowerFilter) || 
                (f.grand_total_date && f.grand_total_date.toLowerCase().includes(lowerFilter))
            );
        }

        summary.innerHTML = `
            <div class="alert alert-primary shadow-sm">
                <strong>${dailyInfo.length}</strong> daily files displayed (of ${data.daily_files?.file_count || 0}).
                ${master.status === 'available' ? '✔️ Master summary available.' : '⚠️ Master summary not found.'}
            </div>`;

        let html = '<div class="accordion" id="processedAccordion">';
        dailyInfo.forEach((f, index) => {
            const fileId = `filePreview${index}`;
            const sampleHtml = generateSampleTable(f.sample);
            html += `
                <div class="accordion-item animate-expand" data-file-data='${JSON.stringify(f).replace(/'/g, "'")}'>
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#${fileId}" aria-expanded="false">
                            📄 ${f.file} — ${f.rows} rows
                        </button>
                    </h2>
                    <div id="${fileId}" class="accordion-collapse collapse" data-bs-parent="#processedAccordion">
                        <div class="accordion-body">
                            <p><strong>Grand Total Date:</strong> ${f.grand_total_date ? new Date(f.grand_total_date).toLocaleDateString() : '-'}</p>
                            <p><strong>Created At:</strong> ${f.created_at ? new Date(f.created_at).toLocaleString() : '-'}</p>
                            <p><strong>Columns:</strong> ${Array.isArray(f.columns) ? f.columns.join(', ') : '-'}</p>
                            <div class="mb-2">
                                <button class="btn btn-sm btn-outline-primary me-2" onclick="downloadFile('${f.file}')" data-bs-toggle="tooltip" title="Download">
                                    <i class="fas fa-download"></i> Download
                                </button>
                                <button class="btn btn-sm btn-outline-danger me-2" onclick="deleteFile('${f.file}')" data-bs-toggle="tooltip" title="Delete">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                                <button class="btn btn-sm btn-outline-info details-btn" data-file="${f.file}" data-bs-toggle="tooltip" title="Details">
                                    <i class="fas fa-info-circle"></i> Details
                                </button>
                            </div>
                            <p><strong>Preview (first 10 rows):</strong></p>
                            <div class="table-responsive">${sampleHtml}</div>
                        </div>
                    </div>
                </div>`;
        });

        if (master.status === 'available') {
            const masterSampleHtml = generateSampleTable(master.sample);
            html += `
                <div class="accordion-item table-info animate-expand" data-file-data='${JSON.stringify(master).replace(/'/g, "'")}'>
                    <h2 class="accordion-header">
                        <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#masterSummary" aria-expanded="false">
                            📊 master_summary.xlsx — ${master.row_count} rows
                        </button>
                    </h2>
                    <div id="masterSummary" class="accordion-collapse collapse" data-bs-parent="#processedAccordion">
                        <div class="accordion-body">
                            <p><strong>Grand Total Date:</strong> ${master.grand_total_date ? new Date(master.grand_total_date).toLocaleDateString() : '-'}</p>
                            <p><strong>Created At:</strong> ${master.created_at ? new Date(master.created_at).toLocaleString() : '-'}</p>
                            <p><strong>Columns:</strong> ${Array.isArray(master.columns) ? master.columns.join(', ') : '-'}</p>
                            <div class="mb-2">
                                <button class="btn btn-sm btn-outline-primary me-2" onclick="downloadFile('master_summary.xlsx')" data-bs-toggle="tooltip" title="Download">
                                    <i class="fas fa-download"></i> Download
                                </button>
                                <button class="btn btn-sm btn-outline-info details-btn" data-file="master_summary.xlsx" data-bs-toggle="tooltip" title="Details">
                                    <i class="fas fa-info-circle"></i> Details
                                </button>
                            </div>
                            <p><strong>Preview (first 10 rows):</strong></p>
                            <div class="table-responsive">${masterSampleHtml}</div>
                        </div>
                    </div>
                </div>`;
        }

        html += '</div>';
        table.innerHTML = html;

        document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => new bootstrap.Tooltip(el));
        document.querySelectorAll('.details-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const fileName = btn.getAttribute('data-file');
                const accordionItem = btn.closest('.accordion-item');
                const fileData = JSON.parse(accordionItem.getAttribute('data-file-data'));
                showFileDetails(fileName, fileData);
            });
        });

        appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Loaded ${dailyInfo.length} files.`);
        showToast('Local files loaded successfully!', 'success');
    } catch (err) {
        localLoader.style.display = 'none';
        mainLoader.style.display = 'none'; // Hide futuristic loader
        summary.innerHTML = '<span class="text-danger">❌ Error loading local files.</span>';
        appendLog(`[ERROR] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - ${err.message}`);
        showToast(`Error: ${err.message}`, 'error');
        console.error(err);
    }
}

function downloadFile(fileName) {
    window.location.href = `/download/${fileName}`;
    appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Downloading ${fileName}`);
    showToast(`Downloading ${fileName}`, 'success');
}

async function deleteFile(fileName) {
    if (!confirm(`Delete ${fileName}? This cannot be undone.`)) return;
    try {
        const res = await fetch(`/delete/${fileName}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.error) throw new Error(data.error);
        appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Deleted ${fileName}`);
        showToast(`Deleted ${fileName}`, 'success');
        loadProcessedFiles(document.getElementById('file-search')?.value || '');
    } catch (err) {
        appendLog(`[ERROR] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - ${err.message}`);
        showToast(`Error: ${err.message}`, 'error');
    }
}

async function downloadAllFiles() {
    window.location.href = '/download-zip';
    appendLog(`[INFO] ${new Date().toISOString().replace('T', ' ').substring(0, 19)} - Downloading all files as ZIP`);
    showToast('Downloading all files', 'success');
}

function showFileDetails(fileName, fileData) {
    try {
        const modal = new bootstrap.Modal(document.getElementById('fileDetailsModal'));
        document.getElementById('fileDetailsModalLabel').textContent = `Details for ${fileName}`;
        document.getElementById('modal-file-name').querySelector('span').textContent = fileName;
        document.getElementById('modal-total-sales').textContent = fileData.stats?.total_sales?.toLocaleString() || '-';
        document.getElementById('modal-total-purchases').textContent = fileData.stats?.total_purchases?.toLocaleString() || '-';
        document.getElementById('modal-unique-brands').textContent = fileData.stats?.unique_brands || '-';
        document.getElementById('modal-unique-categories').textContent = fileData.stats?.unique_categories || '-';
        document.getElementById('modal-created-at').textContent = fileData.created_at ? new Date(fileData.created_at).toLocaleString() : '-';
        document.getElementById('modal-sample').innerHTML = generateSampleTable(fileData.sample || []);
        document.getElementById('modal-download-btn').onclick = () => downloadFile(fileName);
        modal.show();
    } catch (err) {
        console.error('Error in showFileDetails:', err);
        showToast(`Error: ${err.message}`, 'error');
    }
}

function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

document.addEventListener('DOMContentLoaded', () => {
    loadProcessedFiles('');

    const fileSearch = document.getElementById('file-search');
    if (fileSearch) {
        fileSearch.addEventListener('input', debounce(() => {
            loadProcessedFiles(fileSearch.value);
        }, 300));
    }

    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => new bootstrap.Tooltip(el));
});
