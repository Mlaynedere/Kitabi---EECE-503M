function storeToken(token) {
    localStorage.setItem('jwt', token);
}

function getToken() {
    return localStorage.getItem('jwt');
}

// Global fetch interceptor
(function() {
    const originalFetch = window.fetch;
    window.fetch = async function(resource, config = {}) {
        // Ensure config and headers exist
        config.headers = config.headers || {};
        
        // Get token
        const token = getToken();
        console.log('Token:', token); // Debug log
        
        // Add token if exists
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        
        // Always include credentials
        config.credentials = 'include';
        
        try {
            const response = await originalFetch(resource, config);
            console.log('Response status:', response.status); // Debug log
            
            // Handle auth errors
            if (response.status === 401 || response.status === 403) {
                console.error('Auth error:', response.status);
                if (resource !== '/login') {
                    localStorage.removeItem('jwt');
                    window.location.href = '/login';
                }
            }
            
            return response;
        } catch (error) {
            console.error('Fetch error:', error);
            throw error;
        }
    };
})();

// Form validation
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('form[action="/login"]');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            try {
                const formData = new FormData(loginForm);
                const jsonData = Object.fromEntries(formData.entries());
                
                const response = await fetch('/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': document.querySelector('input[name="csrf_token"]')?.value || ''
                    },
                    credentials: 'include',
                    body: JSON.stringify(jsonData)
                });
                
                const result = await response.json();
                
                if (response.ok && result.Authorization) {
                    // Store token
                    storeToken(result.Authorization);
                    console.log('Stored token:', result.Authorization); // Debug log
                    
                    // Wait a moment to ensure token is stored
                    await new Promise(resolve => setTimeout(resolve, 100));
                    
                    // Redirect
                    if (result.redirect_url) {
                        window.location.replace(result.redirect_url);
                    }
                } else {
                    throw new Error(result.error || 'Login failed');
                }
            } catch (error) {
                console.error('Login error:', error);
                showError(error.message || 'An unexpected error occurred');
            }
        });
    }
});

// Show error message
function showError(message) {
    const notification = document.createElement('div');
    notification.className = 'alert alert-danger';
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem;
        z-index: 1000;
        background-color: #ef4444;
        color: white;
        border-radius: 4px;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

function isAuthenticated() {
    return !!getToken();
}

const addAuthorizationHeader = (request) => {
    const token = getToken();
    if (token) {
        request.headers.Authorization = `Bearer ${token}`;
    }
    return request;
};

async function fetchProtectedRoute(url) {
    try {
        const token = getToken();
        if (!token) {
            showError('Authorization token is missing');
            return;
        }

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        if (response.ok) {
            const html = await response.text();
            document.open();
            document.write(html);
            document.close();
        } else {
            const error = await response.json();
            showError(error.error || 'Unauthorized access');
        }
    } catch (error) {
        console.error('Error accessing protected route:', error);
        showError('An error occurred while accessing the page');
    }
}

// Show success message
function showSuccess(message) {
    const notification = createNotification(message, 'success');
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Create notification element
function createNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 2rem;
        border-radius: 4px;
        color: white;
        font-weight: 500;
        animation: slideIn 0.3s ease;
        z-index: 1000;
    `;
    
    notification.style.backgroundColor = type === 'error' ? '#ef4444' : '#10b981';
    notification.textContent = message;
    
    return notification;
}

// Validate individual input
function validateInput(input) {
    const value = input.value.trim();
    
    if (input.required && value === '') {
        input.classList.add('error');
        showError(`${input.placeholder} is required`);
        return false;
    }
    
    if (input.type === 'email' && !validateEmail(value)) {
        input.classList.add('error');
        showError('Please enter a valid email address');
        return false;
    }
    
    input.classList.remove('error');
    return true;
}

// Email validation helper
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    .fade-out {
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
    }
    
    .notification {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    .input-group.focused input {
        border-color: #4f46e5;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
    }
    
    input.error {
        border-color: #ef4444;
    }
    
    input.error:focus {
        box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
    }
`;
document.head.appendChild(style);