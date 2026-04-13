/**
 * Phone Number Validation - Only 10 Numerical Digits
 * Applies to all phone/mobile/tel input fields
 */

(function() {
    'use strict';
    
    // Function to format and validate phone number
    function validatePhoneNumber(input) {
        // Remove all non-numeric characters
        let value = input.value.replace(/\D/g, '');
        
        // Limit to 10 digits
        if (value.length > 10) {
            value = value.substring(0, 10);
        }
        
        // Update input value
        input.value = value;
        
        // Validate length
        const isValid = value.length === 10;
        
        // Update visual feedback
        if (value.length > 0) {
            if (isValid) {
                input.classList.remove('error');
                input.classList.add('valid');
            } else {
                input.classList.remove('valid');
                input.classList.add('error');
            }
        } else {
            input.classList.remove('error', 'valid');
        }
        
        return isValid;
    }
    
    // Function to show error message
    function showError(input, message) {
        const errorElement = input.parentElement.querySelector('.error-message') || 
                           input.nextElementSibling;
        
        if (errorElement && errorElement.classList.contains('error-message')) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }
    
    // Function to hide error message
    function hideError(input) {
        const errorElement = input.parentElement.querySelector('.error-message') || 
                           input.nextElementSibling;
        
        if (errorElement && errorElement.classList.contains('error-message')) {
            errorElement.style.display = 'none';
        }
    }
    
    // Initialize phone validation on all phone inputs
    function initPhoneValidation() {
        // Find all phone/mobile/tel inputs
        const phoneInputs = document.querySelectorAll(
            'input[type="tel"], ' +
            'input[id*="phone"], ' +
            'input[id*="Phone"], ' +
            'input[id*="mobile"], ' +
            'input[id*="Mobile"], ' +
            'input[name*="phone"], ' +
            'input[name*="mobile"]'
        );
        
        phoneInputs.forEach(input => {
            // Set input attributes
            input.setAttribute('inputmode', 'numeric');
            input.setAttribute('pattern', '[0-9]{10}');
            input.setAttribute('maxlength', '10');
            input.setAttribute('placeholder', 'Enter 10 digit mobile number');
            
            // Prevent non-numeric input
            input.addEventListener('keypress', function(e) {
                // Allow only numbers (0-9)
                const charCode = e.which || e.keyCode;
                
                // Allow: backspace, delete, tab, escape, enter
                if (charCode === 8 || charCode === 9 || charCode === 27 || charCode === 13 ||
                    // Allow: Ctrl+A, Ctrl+C, Ctrl+V, Ctrl+X
                    (charCode === 65 && e.ctrlKey === true) ||
                    (charCode === 67 && e.ctrlKey === true) ||
                    (charCode === 86 && e.ctrlKey === true) ||
                    (charCode === 88 && e.ctrlKey === true)) {
                    return;
                }
                
                // Ensure that it is a number and stop the keypress
                if (charCode < 48 || charCode > 57) {
                    e.preventDefault();
                    return false;
                }
            });
            
            // Validate on input (handles paste, etc.)
            input.addEventListener('input', function(e) {
                validatePhoneNumber(this);
            });
            
            // Validate on paste
            input.addEventListener('paste', function(e) {
                e.preventDefault();
                const pastedText = (e.clipboardData || window.clipboardData).getData('text');
                const numericOnly = pastedText.replace(/\D/g, '').substring(0, 10);
                this.value = numericOnly;
                validatePhoneNumber(this);
            });
            
            // Validate on blur
            input.addEventListener('blur', function() {
                const value = this.value.trim();
                
                if (value.length === 0 && this.hasAttribute('required')) {
                    showError(this, 'Phone number is required');
                    this.classList.add('error');
                } else if (value.length > 0 && value.length !== 10) {
                    showError(this, 'Phone number must be exactly 10 digits');
                    this.classList.add('error');
                } else if (value.length === 10) {
                    hideError(this);
                    this.classList.remove('error');
                    this.classList.add('valid');
                }
            });
            
            // Clear error on focus
            input.addEventListener('focus', function() {
                hideError(this);
            });
        });
    }
    
    // Form submission validation
    function validatePhoneOnSubmit(form) {
        const phoneInputs = form.querySelectorAll(
            'input[type="tel"], ' +
            'input[id*="phone"], ' +
            'input[id*="Phone"], ' +
            'input[id*="mobile"], ' +
            'input[id*="Mobile"], ' +
            'input[name*="phone"], ' +
            'input[name*="mobile"]'
        );
        
        let isValid = true;
        
        phoneInputs.forEach(input => {
            const value = input.value.trim();
            
            if (input.hasAttribute('required') && value.length === 0) {
                showError(input, 'Phone number is required');
                input.classList.add('error');
                isValid = false;
            } else if (value.length > 0 && value.length !== 10) {
                showError(input, 'Phone number must be exactly 10 digits');
                input.classList.add('error');
                isValid = false;
            } else if (value.length > 0 && !/^[0-9]{10}$/.test(value)) {
                showError(input, 'Phone number must contain only digits');
                input.classList.add('error');
                isValid = false;
            }
        });
        
        return isValid;
    }
    
    // Add form validation to all forms
    function initFormValidation() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!validatePhoneOnSubmit(this)) {
                    e.preventDefault();
                    
                    // Scroll to first error
                    const firstError = this.querySelector('input.error');
                    if (firstError) {
                        firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        firstError.focus();
                    }
                    
                    return false;
                }
            });
        });
    }
    
    // Add CSS for validation states
    function addValidationStyles() {
        if (document.getElementById('phone-validation-styles')) {
            return;
        }
        
        const styles = document.createElement('style');
        styles.id = 'phone-validation-styles';
        styles.textContent = `
            input[type="tel"].valid,
            input[id*="phone"].valid,
            input[id*="mobile"].valid {
                border-color: #4CAF50 !important;
            }
            
            input[type="tel"].error,
            input[id*="phone"].error,
            input[id*="mobile"].error {
                border-color: #f44336 !important;
            }
            
            input[type="tel"]:focus,
            input[id*="phone"]:focus,
            input[id*="mobile"]:focus {
                outline: none;
                box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
            }
            
            .error-message {
                color: #f44336;
                font-size: 12px;
                margin-top: 4px;
                display: none;
            }
            
            .error-message.show {
                display: block;
            }
        `;
        document.head.appendChild(styles);
    }
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            addValidationStyles();
            initPhoneValidation();
            initFormValidation();
        });
    } else {
        addValidationStyles();
        initPhoneValidation();
        initFormValidation();
    }
    
    // Re-initialize for dynamically added forms
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                initPhoneValidation();
                initFormValidation();
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
})();
