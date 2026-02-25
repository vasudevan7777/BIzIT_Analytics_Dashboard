/**
 * BizIT Analytics - Dashboard JavaScript
 * Interactive Business Analytics Dashboard
 */

// Chart instances
let revenueChart, profitCostChart, departmentChart, marginChart, salesChart;

// Chart colors - matching new theme
const chartColors = {
    primary: '#7C3AED',
    primaryLight: 'rgba(124, 58, 237, 0.2)',
    secondary: '#EC4899',
    secondaryLight: 'rgba(236, 72, 153, 0.2)',
    success: '#10B981',
    successLight: 'rgba(16, 185, 129, 0.2)',
    danger: '#EF4444',
    dangerLight: 'rgba(239, 68, 68, 0.2)',
    warning: '#FBBF24',
    warningLight: 'rgba(251, 191, 36, 0.2)',
    info: '#3B82F6',
    infoLight: 'rgba(59, 130, 246, 0.2)',
    cyan: '#06B6D4',
    cyanLight: 'rgba(6, 182, 212, 0.2)',
    orange: '#F97316',
    colors: ['#7C3AED', '#EC4899', '#10B981', '#06B6D4', '#FBBF24', '#3B82F6', '#F97316', '#EF4444']
};

// Chart.js global configuration for dark theme
Chart.defaults.color = '#94A3B8';
Chart.defaults.borderColor = 'rgba(148, 163, 184, 0.1)';

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    initializeDashboard();
});

async function initializeDashboard() {
    setCurrentDate();
    loadUserInfo();
    await loadDepartments();
    
    // Initialize with empty/zero values - data loads only after applying filters
    initializeEmptyDashboard();
    await loadAlerts();
    initializeCharts();
    
    // Setup periodic refresh
    setInterval(loadAlerts, 60000); // Refresh alerts every minute
}

function initializeEmptyDashboard() {
    // Set all KPIs to zero
    document.getElementById('totalRevenue').textContent = '₹0.00';
    document.getElementById('totalCost').textContent = '₹0.00';
    document.getElementById('netProfit').textContent = '₹0.00';
    document.getElementById('profitMargin').textContent = '0.00%';
    document.getElementById('monthlyGrowth').textContent = '0.00%';
    document.getElementById('totalSales').textContent = '0';
    
    // Hide trend indicators initially
    const trends = document.querySelectorAll('.kpi-trend');
    trends.forEach(trend => trend.style.display = 'none');
}

function setCurrentDate() {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('currentDate').textContent = new Date().toLocaleDateString('en-US', options);
}

function loadUserInfo() {
    const user = JSON.parse(getToken('user') || '{}');
    document.getElementById('userName').textContent = user.name || 'User';
    document.getElementById('userRole').textContent = user.role || 'Role';
    document.getElementById('userAvatar').textContent = (user.name || 'U').charAt(0).toUpperCase();
    
    // Show admin link if user is admin
    if (user.role === 'Admin') {
        const adminLink = document.getElementById('adminLink');
        if (adminLink) {
            adminLink.style.display = 'flex';
        }
    }
}

// Fetch wrapper with auth
async function fetchWithAuth(url, options = {}) {
    const token = getToken('access_token');
    
    if (!token) {
        console.warn('No access token found');
        return null;
    }
    
    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers
    };
    
    try {
        const response = await fetch(url, { ...options, headers });
        
        if (response.status === 401) {
            // Token expired, try to refresh
            const refreshed = await refreshToken();
            if (refreshed) {
                // Retry the request with new token
                const newToken = getToken('access_token');
                headers['Authorization'] = `Bearer ${newToken}`;
                return fetch(url, { ...options, headers });
            } else {
                // Only logout if refresh explicitly fails, not on first load
                console.warn('Token refresh failed');
                return null;
            }
        }
        
        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        return null;
    }
}

async function refreshToken() {
    try {
        const refreshTokenVal = getToken('refresh_token');
        if (!refreshTokenVal) return false;
        
        const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${refreshTokenVal}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            // Store in same storage as original
            const storage = localStorage.getItem('refresh_token') ? localStorage : sessionStorage;
            storage.setItem('access_token', data.access_token);
            return true;
        }
    } catch (error) {
        console.error('Token refresh failed:', error);
    }
    return false;
}

// Load departments for filter
async function loadDepartments() {
    try {
        const response = await fetchWithAuth('/api/departments');
        if (response && response.ok) {
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

// Load KPI data
async function loadDashboardData() {
    showLoading(true);
    
    try {
        const filters = getFilters();
        const params = new URLSearchParams(filters).toString();
        
        // Load KPIs
        const kpiResponse = await fetchWithAuth(`/api/dashboard/kpis?${params}`);
        if (kpiResponse && kpiResponse.ok) {
            const kpis = await kpiResponse.json();
            updateKPIs(kpis);
        }
        
        // Load chart data
        await loadChartData(filters);
        
        // Load analysis data
        await loadAnalysisData(filters);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showToast('Error loading dashboard data', 'error');
    }
    
    showLoading(false);
}

function getFilters() {
    return {
        start_date: document.getElementById('startDate').value || '',
        end_date: document.getElementById('endDate').value || '',
        department: document.getElementById('departmentFilter').value || 'all'
    };
}

function updateKPIs(kpis) {
    // Animate counter updates
    animateValue('totalRevenue', kpis.total_revenue, true);
    animateValue('totalCost', kpis.total_cost, true);
    animateValue('netProfit', kpis.net_profit, true);
    animateValue('profitMargin', kpis.profit_margin, false, '%');
    animateValue('monthlyGrowth', kpis.monthly_growth, false, '%');
    animateValue('totalSales', kpis.total_sales_volume, false, '', true);
    
    // Update trend indicators
    updateTrend('revenueTrend', kpis.monthly_growth);
    updateTrend('profitTrend', kpis.monthly_growth);
}

function animateValue(elementId, value, isCurrency = false, suffix = '', isInteger = false) {
    const element = document.getElementById(elementId);
    const start = 0;
    const duration = 1000;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeProgress = 1 - Math.pow(1 - progress, 3); // Ease out cubic
        
        const currentValue = start + (value - start) * easeProgress;
        
        if (isCurrency) {
            element.textContent = '₹' + formatNumber(currentValue);
        } else if (isInteger) {
            element.textContent = Math.round(currentValue).toLocaleString() + suffix;
        } else {
            element.textContent = currentValue.toFixed(2) + suffix;
        }
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(2) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(2) + 'K';
    }
    return num.toFixed(2);
}

function updateTrend(elementId, value) {
    const element = document.getElementById(elementId);
    const isPositive = value >= 0;
    
    element.style.display = 'flex'; // Show trend indicator when data is loaded
    element.className = `kpi-trend ${isPositive ? 'up' : 'down'}`;
    element.innerHTML = `<i class="fas fa-arrow-${isPositive ? 'up' : 'down'}"></i> ${Math.abs(value).toFixed(1)}%`;
}

// Load chart data
async function loadChartData(filters) {
    const params = new URLSearchParams(filters).toString();
    
    try {
        // Revenue trend
        const revenueResponse = await fetchWithAuth(`/api/dashboard/revenue-trend?${params}`);
        if (revenueResponse && revenueResponse.ok) {
            const revenueData = await revenueResponse.json();
            updateRevenueChart(revenueData);
            updateProfitCostChart(revenueData);
        }
        
        // Department distribution
        const deptResponse = await fetchWithAuth(`/api/dashboard/department-distribution?${params}`);
        if (deptResponse && deptResponse.ok) {
            const deptData = await deptResponse.json();
            updateDepartmentChart(deptData);
        }
        
        // Profit margin trend
        const marginResponse = await fetchWithAuth(`/api/dashboard/profit-margin-trend?${params}`);
        if (marginResponse && marginResponse.ok) {
            const marginData = await marginResponse.json();
            updateMarginChart(marginData);
        }
        
        // Sales trend
        const salesResponse = await fetchWithAuth(`/api/dashboard/sales-trend?${params}`);
        if (salesResponse && salesResponse.ok) {
            const salesData = await salesResponse.json();
            updateSalesChart(salesData);
        }
    } catch (error) {
        console.error('Error loading chart data:', error);
    }
}

// Initialize Charts
function initializeCharts() {
    // Revenue Chart
    const revenueCtx = document.getElementById('revenueChart').getContext('2d');
    revenueChart = new Chart(revenueCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Revenue',
                data: [],
                borderColor: chartColors.primary,
                backgroundColor: chartColors.primaryLight,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: chartColors.primary,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 8
            }]
        },
        options: getChartOptions('Monthly Revenue (₹)')
    });
    
    // Profit vs Cost Chart
    const profitCostCtx = document.getElementById('profitCostChart').getContext('2d');
    profitCostChart = new Chart(profitCostCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Profit',
                    data: [],
                    backgroundColor: chartColors.success,
                    borderRadius: 6
                },
                {
                    label: 'Cost',
                    data: [],
                    backgroundColor: chartColors.danger,
                    borderRadius: 6
                }
            ]
        },
        options: getChartOptions('Amount (₹)')
    });
    
    // Department Chart 
    const deptCtx = document.getElementById('departmentChart').getContext('2d');
    departmentChart = new Chart(deptCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: chartColors.colors,
                borderWidth: 2,
                borderColor: 'rgba(15, 15, 35, 0.8)',
                hoverBorderColor: '#fff',
                hoverBorderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        padding: 16,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: { size: 12 }
                    }
                }
            }
        }
    });
    
    // Margin Chart
    const marginCtx = document.getElementById('marginChart').getContext('2d');
    marginChart = new Chart(marginCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Profit Margin %',
                data: [],
                borderColor: chartColors.cyan,
                backgroundColor: chartColors.cyanLight,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: chartColors.cyan,
                pointBorderColor: '#fff',
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 8
            }]
        },
        options: getChartOptions('Margin (%)')
    });
    
    // Sales Chart
    const salesCtx = document.getElementById('salesChart').getContext('2d');
    salesChart = new Chart(salesCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Sales Volume',
                data: [],
                backgroundColor: createGradient(salesCtx, chartColors.secondary, chartColors.primary),
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: getChartOptions('Sales Volume')
    });
}

function createGradient(ctx, color1, color2) {
    const gradient = ctx.createLinearGradient(0, 0, 0, 320);
    gradient.addColorStop(0, color1);
    gradient.addColorStop(1, color2);
    return gradient;
}

function getChartOptions(yAxisLabel) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top',
                labels: {
                    padding: 16,
                    usePointStyle: true,
                    pointStyle: 'circle',
                    font: { size: 12 }
                }
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(26, 26, 46, 0.95)',
                titleColor: '#F8FAFC',
                bodyColor: '#94A3B8',
                borderColor: 'rgba(124, 58, 237, 0.3)',
                borderWidth: 1,
                padding: 14,
                cornerRadius: 8,
                displayColors: true
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: yAxisLabel,
                    color: '#94A3B8'
                },
                grid: {
                    color: 'rgba(148, 163, 184, 0.08)'
                },
                ticks: {
                    color: '#64748B'
                }
            },
            x: {
                grid: {
                    color: 'rgba(148, 163, 184, 0.08)'
                },
                ticks: {
                    color: '#64748B'
                }
            }
        },
        interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
        }
    };
}

// Update chart functions
function updateRevenueChart(data) {
    revenueChart.data.labels = data.labels;
    revenueChart.data.datasets[0].data = data.revenue;
    revenueChart.update();
}

function updateProfitCostChart(data) {
    profitCostChart.data.labels = data.labels;
    profitCostChart.data.datasets[0].data = data.profit;
    profitCostChart.data.datasets[1].data = data.cost;
    profitCostChart.update();
}

function updateDepartmentChart(data) {
    departmentChart.data.labels = data.labels;
    departmentChart.data.datasets[0].data = data.revenue;
    departmentChart.update();
}

function updateMarginChart(data) {
    marginChart.data.labels = data.labels;
    marginChart.data.datasets[0].data = data.margins;
    marginChart.update();
}

function updateSalesChart(data) {
    salesChart.data.labels = data.labels;
    salesChart.data.datasets[0].data = data.sales;
    salesChart.update();
}

// Load analysis data
async function loadAnalysisData(filters) {
    try {
        const params = new URLSearchParams(filters).toString();
        const response = await fetchWithAuth(`/api/analysis/profitability?${params}`);
        
        if (response && response.ok) {
            const data = await response.json();
            updateAnalysisTable(data.departments);
        } else {
            document.getElementById('analysisTableBody').innerHTML = 
                '<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--text-muted);">No analysis data available</td></tr>';
        }
    } catch (error) {
        console.error('Error loading analysis:', error);
        document.getElementById('analysisTableBody').innerHTML = 
            '<tr><td colspan="6" style="text-align: center; padding: 40px; color: var(--text-muted);">Error loading analysis data</td></tr>';
    }
}

function updateAnalysisTable(departments) {
    const tbody = document.getElementById('analysisTableBody');
    tbody.innerHTML = '';
    
    if (!departments || departments.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 40px;">No data available. Upload business data to see analysis.</td></tr>';
        return;
    }
    
    departments.forEach(dept => {
        const performanceClass = dept.profit_margin >= 20 ? 'text-success' : 
                                 dept.profit_margin >= 10 ? 'text-warning' : 'text-danger';
        const performanceLabel = dept.profit_margin >= 20 ? 'Excellent' : 
                                 dept.profit_margin >= 10 ? 'Good' : 'Needs Attention';
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${dept.department}</strong></td>
            <td>₹${dept.revenue.toLocaleString()}</td>
            <td>₹${dept.cost.toLocaleString()}</td>
            <td>₹${dept.profit.toLocaleString()}</td>
            <td>${dept.profit_margin}%</td>
            <td><span class="${performanceClass}">${performanceLabel}</span></td>
        `;
        tbody.appendChild(row);
    });
}

// Load alerts
async function loadAlerts() {
    try {
        const response = await fetchWithAuth('/api/alerts?unread_only=true');
        
        if (response && response.ok) {
            const data = await response.json();
            updateAlertsBadge(data.alerts.length);
            updateAlertsList(data.alerts);
        }
    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

function updateAlertsBadge(count) {
    const badges = ['alertBadge', 'alertBadgeSidebar'];
    badges.forEach(id => {
        const badge = document.getElementById(id);
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        }
    });
}

function updateAlertsList(alerts) {
    const container = document.getElementById('alertsList');
    
    if (!alerts || alerts.length === 0) {
        container.innerHTML = '<div style="padding: 30px; text-align: center; color: #7F8C8D;">No alerts at this time</div>';
        return;
    }
    
    container.innerHTML = alerts.slice(0, 5).map(alert => `
        <div class="alert-item ${alert.is_read ? '' : 'unread'}" onclick="markAlertRead(${alert.id})">
            <div class="alert-icon ${alert.severity}">
                <i class="fas fa-${alert.severity === 'danger' ? 'exclamation-triangle' : 'info-circle'}"></i>
            </div>
            <div class="alert-content">
                <h4>${alert.message}</h4>
                <p>${new Date(alert.created_at).toLocaleString()}</p>
            </div>
        </div>
    `).join('');
}

async function markAlertRead(alertId) {
    try {
        await fetchWithAuth(`/api/alerts/${alertId}/read`, { method: 'PUT' });
        await loadAlerts();
    } catch (error) {
        console.error('Error marking alert as read:', error);
    }
}

async function markAllAlertsRead() {
    try {
        await fetchWithAuth('/api/alerts/read-all', { method: 'PUT' });
        await loadAlerts();
        showToast('All alerts marked as read', 'success');
    } catch (error) {
        console.error('Error marking all alerts as read:', error);
    }
}

// Filter functions
function applyFilters() {
    loadDashboardData();
}

function resetFilters() {
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    document.getElementById('departmentFilter').value = 'all';
    loadDashboardData();
}

// Refresh functions
function refreshData() {
    loadDashboardData();
    loadAlerts();
    showToast('Dashboard refreshed', 'success');
}

function refreshAnalysis() {
    loadAnalysisData(getFilters());
}

// Navigation functions
function scrollToCharts() {
    document.getElementById('chartsSection').scrollIntoView({ behavior: 'smooth' });
}

function scrollToAnalysis() {
    document.getElementById('analysisSection').scrollIntoView({ behavior: 'smooth' });
}

// Modal functions
function showAlertsModal() {
    loadAllAlerts();
    document.getElementById('alertsModal').classList.add('active');
}

async function loadAllAlerts() {
    try {
        const response = await fetchWithAuth('/api/alerts');
        
        if (response && response.ok) {
            const data = await response.json();
            const container = document.getElementById('modalAlertsList');
            
            if (!data.alerts || data.alerts.length === 0) {
                container.innerHTML = '<p style="text-align: center; padding: 40px; color: var(--text-muted);">No alerts at this time</p>';
                return;
            }
            
            container.innerHTML = data.alerts.map(alert => `
                <div class="alert-item ${alert.is_read ? '' : 'unread'}" onclick="markAlertRead(${alert.id})">
                    <div class="alert-icon ${alert.severity}">
                        <i class="fas fa-${alert.severity === 'danger' ? 'exclamation-triangle' : alert.severity === 'warning' ? 'exclamation-circle' : 'info-circle'}"></i>
                    </div>
                    <div class="alert-content">
                        <h4>${alert.message}</h4>
                        <p>${alert.department ? `Department: ${alert.department} | ` : ''}${new Date(alert.created_at).toLocaleString()}</p>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading all alerts:', error);
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function showProfileModal() {
    const user = JSON.parse(getToken('user') || '{}');
    document.getElementById('profileAvatar').textContent = (user.name || 'U').charAt(0).toUpperCase();
    document.getElementById('profileName').textContent = user.name || 'Anonymous User';
    document.getElementById('profileEmail').textContent = user.email || 'No email';
    document.getElementById('profileRole').textContent = user.role || 'User';
    document.getElementById('profileModal').classList.add('active');
}

// UI helper functions
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('active');
}

function downloadChart(chartId) {
    const canvas = document.getElementById(chartId);
    if (!canvas) return;
    
    // Create a temporary link element
    const link = document.createElement('a');
    link.download = `${chartId}-${new Date().toISOString().slice(0, 10)}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
    
    showToast('Chart downloaded successfully!', 'success');
}

function showLoading(show) {
    document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const iconMap = {
        success: 'check-circle',
        error: 'times-circle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    
    toast.innerHTML = `
        <div class="toast-icon">
            <i class="fas fa-${iconMap[type] || 'info-circle'}"></i>
        </div>
        <div class="toast-message">${message}</div>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.animation = 'slideInRight 0.3s ease reverse';
            setTimeout(() => toast.remove(), 300);
        }
    }, 4000);
}

function createToastContainer() {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    return container;
}

// User dropdown toggle
document.getElementById('userDropdown').addEventListener('click', function(e) {
    this.classList.toggle('active');
});

// Close dropdown when clicking outside
document.addEventListener('click', function(e) {
    if (!e.target.closest('#userDropdown')) {
        document.getElementById('userDropdown').classList.remove('active');
    }
});

// Close modal on click outside
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function(e) {
        if (e.target === this) {
            this.classList.remove('active');
        }
    });
});
