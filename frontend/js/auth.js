/**
 * BizIT Analytics - Authentication Utilities
 */

// Get token from either storage
function getToken(key) {
    return sessionStorage.getItem(key) || localStorage.getItem(key);
}

// Check if user is authenticated
function checkAuth() {
    const token = getToken('access_token');
    const pathname = window.location.pathname.toLowerCase();
    const currentPage = pathname.split('/').pop() || '';
    
    // Check if current page is a public page (login/register)
    const isPublicPage = currentPage === '' || 
                         currentPage === 'index.html' || 
                         currentPage === 'register.html' ||
                         pathname === '/' ||
                         pathname.endsWith('/index.html') ||
                         pathname.endsWith('/register.html');
    
    // Check if current page is a protected page
    const isProtectedPage = currentPage === 'dashboard.html' || 
                            currentPage === 'upload.html' || 
                            currentPage === 'reports.html' ||
                            pathname.endsWith('/dashboard.html') ||
                            pathname.endsWith('/upload.html') ||
                            pathname.endsWith('/reports.html');
    
    if (!token && isProtectedPage) {
        // Not authenticated and trying to access protected page
        window.location.href = 'index.html';
        return false;
    }
    
    // Don't auto-redirect from login page - let the page handle it
    return !!token;
}

// Logout function
async function logout() {
    try {
        const token = getToken('access_token');
        
        if (token) {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
        }
    } catch (error) {
        console.error('Logout error:', error);
    }
    
    // Clear both storages
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    sessionStorage.removeItem('user');
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    
    // Redirect to login
    window.location.href = 'index.html';
}

// Get current user info
function getCurrentUser() {
    const userStr = getToken('user');
    return userStr ? JSON.parse(userStr) : null;
}

// Check user role
function hasRole(allowedRoles) {
    const user = getCurrentUser();
    if (!user) return false;
    return allowedRoles.includes(user.role);
}

// Check if user is admin
function isAdmin() {
    return hasRole(['Admin']);
}

// Check if user can manage data
function canManageData() {
    return hasRole(['Admin', 'Business Manager']);
}

// Format date for display
function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format number with commas
function formatNumber(num) {
    return new Intl.NumberFormat('en-US').format(num);
}

// Debounce function for search inputs
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// API request helper
async function apiRequest(url, options = {}) {
    const token = getToken('access_token');
    
    const defaultHeaders = {
        'Content-Type': 'application/json'
    };
    
    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(url, {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers
        }
    });
    
    // Handle token expiration
    if (response.status === 401) {
        const refreshed = await tryRefreshToken();
        if (refreshed) {
            // Retry the request
            defaultHeaders['Authorization'] = `Bearer ${getToken('access_token')}`;
            return fetch(url, {
                ...options,
                headers: {
                    ...defaultHeaders,
                    ...options.headers
                }
            });
        } else {
            logout();
            return null;
        }
    }
    
    return response;
}

async function tryRefreshToken() {
    const refreshToken = getToken('refresh_token');
    if (!refreshToken) return false;
    
    try {
        const response = await fetch('/api/auth/refresh', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${refreshToken}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            // Store in same storage type as original token
            const storage = localStorage.getItem('refresh_token') ? localStorage : sessionStorage;
            storage.setItem('access_token', data.access_token);
            return true;
        }
    } catch (error) {
        console.error('Token refresh failed:', error);
    }
    
    return false;
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        checkAuth,
        logout,
        getCurrentUser,
        hasRole,
        isAdmin,
        canManageData,
        formatDate,
        formatCurrency,
        formatNumber,
        debounce,
        apiRequest,
        toggleSidebar
    };
}

// Shared: Toggle sidebar
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('collapsed');
    }
}
