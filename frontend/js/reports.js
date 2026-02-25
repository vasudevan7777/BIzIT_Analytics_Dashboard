/**
 * BizIT Analytics - Reports Page JavaScript
 */

let currentPage = 1;
const perPage = 20;

document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    initializeReports();
});

async function initializeReports() {
    await loadDepartments();
    await loadDataPreview();
    populateMonthSelect();
}

// Load departments for filter
async function loadDepartments() {
    try {
        const token = getToken('access_token');
        const response = await fetch('/api/departments', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            const select = document.getElementById('departmentFilter');
            
            data.departments.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept;
                option.textContent = dept;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading departments:', error);
    }
}

// Get current filters
function getFilters() {
    return {
        start_date: document.getElementById('startDate').value || '',
        end_date: document.getElementById('endDate').value || '',
        department: document.getElementById('departmentFilter').value || 'all'
    };
}

// Download PDF Report
async function downloadPDF() {
    showLoading(true);
    
    try {
        const token = getToken('access_token');
        const filters = getFilters();
        const params = new URLSearchParams(filters).toString();
        
        const response = await fetch(`/api/reports/pdf?${params}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `business_report_${new Date().toISOString().split('T')[0]}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            showToast('PDF report downloaded successfully!', 'success');
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to generate PDF report', 'error');
        }
    } catch (error) {
        console.error('Error downloading PDF:', error);
        showToast('Error downloading PDF report. Please try again.', 'error');
    }
    
    showLoading(false);
}

// Download Excel Report
async function downloadExcel() {
    showLoading(true);
    
    try {
        const token = getToken('access_token');
        const filters = getFilters();
        const params = new URLSearchParams(filters).toString();
        
        const response = await fetch(`/api/reports/excel?${params}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `business_report_${new Date().toISOString().split('T')[0]}.xlsx`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            showToast('Excel report downloaded successfully!', 'success');
        } else {
            const data = await response.json();
            showToast(data.error || 'Failed to generate Excel report', 'error');
        }
    } catch (error) {
        console.error('Error downloading Excel:', error);
        showToast('Error downloading Excel report. Please try again.', 'error');
    }
    
    showLoading(false);
}

// View Monthly Summary
function viewMonthlySummary() {
    const section = document.getElementById('summarySection');
    section.style.display = section.style.display === 'none' ? 'block' : 'none';
    
    if (section.style.display === 'block') {
        loadMonthlySummary();
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

// Populate month select
function populateMonthSelect() {
    const select = document.getElementById('monthSelect');
    const currentDate = new Date();
    
    for (let i = 0; i < 12; i++) {
        const date = new Date(currentDate.getFullYear(), currentDate.getMonth() - i, 1);
        const value = date.toISOString().slice(0, 7); // YYYY-MM format
        const label = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        
        const option = document.createElement('option');
        option.value = value;
        option.textContent = label;
        select.appendChild(option);
    }
}

// Load Monthly Summary
async function loadMonthlySummary() {
    const month = document.getElementById('monthSelect').value;
    
    try {
        const token = getToken('access_token');
        const response = await fetch(`/api/reports/summary?month=${month}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            renderSummary(data);
        }
    } catch (error) {
        console.error('Error loading monthly summary:', error);
    }
}

function renderSummary(data) {
    const kpis = data.kpis;
    const breakdown = data.department_breakdown;
    
    // Render KPIs
    document.getElementById('summaryKPIs').innerHTML = `
        <div class="kpi-card revenue">
            <div class="kpi-header">
                <div class="kpi-icon"><i class="fas fa-rupee-sign"></i></div>
            </div>
            <div class="kpi-value">₹${formatNumber(kpis.total_revenue)}</div>
            <div class="kpi-label">Revenue</div>
        </div>
        <div class="kpi-card cost">
            <div class="kpi-header">
                <div class="kpi-icon"><i class="fas fa-minus-circle"></i></div>
            </div>
            <div class="kpi-value">₹${formatNumber(kpis.total_cost)}</div>
            <div class="kpi-label">Cost</div>
        </div>
        <div class="kpi-card profit">
            <div class="kpi-header">
                <div class="kpi-icon"><i class="fas fa-chart-line"></i></div>
            </div>
            <div class="kpi-value">₹${formatNumber(kpis.net_profit)}</div>
            <div class="kpi-label">Profit</div>
        </div>
        <div class="kpi-card margin">
            <div class="kpi-header">
                <div class="kpi-icon"><i class="fas fa-percentage"></i></div>
            </div>
            <div class="kpi-value">${kpis.profit_margin}%</div>
            <div class="kpi-label">Margin</div>
        </div>
    `;
    
    // Render department breakdown
    const tbody = document.getElementById('summaryTableBody');
    const totalRevenue = breakdown.reduce((sum, d) => sum + d.revenue, 0);
    
    if (breakdown.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 30px;">No data for this month</td></tr>';
        return;
    }
    
    tbody.innerHTML = breakdown.map(dept => {
        const share = totalRevenue > 0 ? ((dept.revenue / totalRevenue) * 100).toFixed(1) : 0;
        return `
            <tr>
                <td><strong>${dept.department}</strong></td>
                <td>₹${dept.revenue.toLocaleString()}</td>
                <td>₹${dept.profit.toLocaleString()}</td>
                <td>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="flex: 1; height: 8px; background: #E0E6ED; border-radius: 4px; overflow: hidden;">
                            <div style="width: ${share}%; height: 100%; background: var(--primary-color);"></div>
                        </div>
                        <span>${share}%</span>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Load Data Preview
async function loadDataPreview(page = 1) {
    currentPage = page;
    const filters = getFilters();
    
    try {
        const token = getToken('access_token');
        const params = new URLSearchParams({
            ...filters,
            page: page,
            per_page: perPage
        }).toString();
        
        const response = await fetch(`/api/data?${params}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const data = await response.json();
            renderDataPreview(data);
        }
    } catch (error) {
        console.error('Error loading data preview:', error);
    }
}

function renderDataPreview(data) {
    const tbody = document.getElementById('dataPreviewTable');
    
    if (!data.data || data.data.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: #7F8C8D;">
                    No data available. Upload business data to get started.
                </td>
            </tr>
        `;
        document.getElementById('paginationInfo').textContent = 'No records';
        document.getElementById('paginationButtons').innerHTML = '';
        return;
    }
    
    tbody.innerHTML = data.data.map(item => {
        const margin = item.revenue > 0 ? ((item.profit / item.revenue) * 100).toFixed(1) : 0;
        const marginClass = margin >= 20 ? 'text-success' : margin >= 10 ? 'text-warning' : 'text-danger';
        
        return `
            <tr>
                <td>${item.date}</td>
                <td>${item.department}</td>
                <td>₹${item.revenue.toLocaleString()}</td>
                <td>₹${item.cost.toLocaleString()}</td>
                <td>₹${item.profit.toLocaleString()}</td>
                <td>${item.sales_volume.toLocaleString()}</td>
                <td><span class="${marginClass}">${margin}%</span></td>
            </tr>
        `;
    }).join('');
    
    // Update pagination info
    const start = (currentPage - 1) * perPage + 1;
    const end = Math.min(currentPage * perPage, data.total);
    document.getElementById('paginationInfo').textContent = 
        `Showing ${start}-${end} of ${data.total} records`;
    
    // Render pagination buttons
    renderPagination(data.pages, data.current_page);
}

function renderPagination(totalPages, currentPage) {
    const container = document.getElementById('paginationButtons');
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let buttons = '';
    
    // Previous button
    buttons += `
        <button class="pagination-btn" ${currentPage === 1 ? 'disabled' : ''} 
                onclick="loadDataPreview(${currentPage - 1})">
            <i class="fas fa-chevron-left"></i>
        </button>
    `;
    
    // Page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);
    
    if (endPage - startPage < maxVisible - 1) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        buttons += `
            <button class="pagination-btn ${i === currentPage ? 'active' : ''}" 
                    onclick="loadDataPreview(${i})">${i}</button>
        `;
    }
    
    // Next button
    buttons += `
        <button class="pagination-btn" ${currentPage === totalPages ? 'disabled' : ''} 
                onclick="loadDataPreview(${currentPage + 1})">
            <i class="fas fa-chevron-right"></i>
        </button>
    `;
    
    container.innerHTML = buttons;
}

function refreshDataPreview() {
    loadDataPreview(1);
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(2) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(2) + 'K';
    }
    return num.toFixed(2);
}

function showLoading(show) {
    document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'error' : 'success'}`;
    toast.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 250px;';
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}
