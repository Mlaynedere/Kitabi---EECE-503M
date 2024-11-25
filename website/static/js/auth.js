// Form validation
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const inputs = document.querySelectorAll('input');

    // Form submission
    if (form) {
        form.addEventListener('submit', function(e) {

            let csrfTokenField = form.querySelector('input[name="csrf_token"]');
            if (!csrfTokenField) {
                const csrfMetaTag = document.querySelector('meta[name="csrf-token"]');
                if (csrfMetaTag) {
                    csrfTokenField = document.createElement('input');
                    csrfTokenField.type = 'hidden';
                    csrfTokenField.name = 'csrf_token';
                    csrfTokenField.value = csrfMetaTag.getAttribute('content');
                    form.appendChild(csrfTokenField);
                }
            }
            
            // Check if this is the signup form by looking for password1 field
            const password1Field = form.querySelector('[name="password1"]');
            const password2Field = form.querySelector('[name="password2"]');
            
            if (password1Field && password2Field) {
                const password1 = password1Field.value;
                const password2 = password2Field.value;
                
                if (password1 !== password2) {
                    e.preventDefault(); // Prevent form submission
                    showError('Passwords do not match');
                    return;
                }
                
                if (password1.length < 8) {
                    e.preventDefault(); // Prevent form submission
                    showError('Password must be at least 8 characters long');
                    return;
                }
            }
            
            // Add loading state to submit button
            const submitBtn = form.querySelector('.submit-btn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Processing...';
            }
        });
    }

    // Input validation and animation
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });

        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
            validateInput(this);
        });
    });
});

// Show error message
function showError(message) {
    const notification = createNotification(message, 'error');
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
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