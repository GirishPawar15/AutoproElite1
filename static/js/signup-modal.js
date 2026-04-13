(function() {
    const signupModal = document.getElementById('signupModal');
    const loginModal = document.getElementById('loginModal');
    const closeBtn = document.getElementById('closeSignupModal');
    const overlay = signupModal?.querySelector('.modal-overlay');
    
    // Form elements
    const signupForm = document.getElementById('modalSignupForm');
    const usernameInput = document.getElementById('modal-signup-username');
    const emailInput = document.getElementById('modal-signup-email');
    const passwordInput = document.getElementById('modal-signup-password');
    const confirmPasswordInput = document.getElementById('modal-signup-confirmPassword');
    
    // Toggle buttons
    const passwordToggle = document.getElementById('modal-signup-passwordToggle');
    const confirmPasswordToggle = document.getElementById('modal-signup-confirmPasswordToggle');
    
    // Error elements
    const usernameError = document.getElementById('modal-signup-usernameError');
    const passwordError = document.getElementById('modal-signup-passwordError');
    const confirmPasswordError = document.getElementById('modal-signup-confirmPasswordError');
    const passwordStrength = document.getElementById('modal-signup-passwordStrength');
    
    // Modal switching links
    const openLoginFromSignup = document.getElementById('openLoginFromSignup');
    const openSignupModal = document.getElementById('openSignupModal');

    // Close modal function
    function closeModal() {
        if (signupModal) {
            signupModal.classList.remove('active');
            document.body.classList.remove('modal-open');
        }
    }

    // Open signup modal function
    function openModal() {
        if (signupModal) {
            signupModal.classList.add('active');
            document.body.classList.add('modal-open');
        }
    }

    // Close modal on close button click
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }

    // Close modal on overlay click
    if (overlay) {
        overlay.addEventListener('click', closeModal);
    }

    // Close modal on ESC key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && signupModal?.classList.contains('active')) {
            closeModal();
        }
    });

    // Password toggle functionality
    if (passwordToggle && passwordInput) {
        passwordToggle.addEventListener('click', () => {
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                passwordToggle.classList.remove('fa-eye');
                passwordToggle.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                passwordToggle.classList.remove('fa-eye-slash');
                passwordToggle.classList.add('fa-eye');
            }
        });
    }

    // Confirm password toggle functionality
    if (confirmPasswordToggle && confirmPasswordInput) {
        confirmPasswordToggle.addEventListener('click', () => {
            if (confirmPasswordInput.type === 'password') {
                confirmPasswordInput.type = 'text';
                confirmPasswordToggle.classList.remove('fa-eye');
                confirmPasswordToggle.classList.add('fa-eye-slash');
            } else {
                confirmPasswordInput.type = 'password';
                confirmPasswordToggle.classList.remove('fa-eye-slash');
                confirmPasswordToggle.classList.add('fa-eye');
            }
        });
    }

    // Form validation helpers
    function showError(input, errorElement, message) {
        if (input && errorElement) {
            input.classList.add('error');
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }
    }

    function hideError(input, errorElement) {
        if (input && errorElement) {
            input.classList.remove('error');
            errorElement.style.display = 'none';
        }
    }

    // Password strength checker
    function checkPasswordStrength(password) {
        if (!password) return '';
        
        let strength = 0;
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;
        if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++;
        if (/\d/.test(password)) strength++;
        if (/[^a-zA-Z0-9]/.test(password)) strength++;

        if (strength <= 2) {
            return '<span class="strength-weak">Weak password</span>';
        } else if (strength <= 3) {
            return '<span class="strength-medium">Medium password</span>';
        } else {
            return '<span class="strength-strong">Strong password</span>';
        }
    }

    // Password strength indicator
    if (passwordInput && passwordStrength) {
        passwordInput.addEventListener('input', () => {
            passwordStrength.innerHTML = checkPasswordStrength(passwordInput.value);
        });
    }

    // Username validation
    if (usernameInput && usernameError) {
        usernameInput.addEventListener('blur', () => {
            if (!usernameInput.value.trim()) {
                showError(usernameInput, usernameError, 'Username is required');
            } else if (usernameInput.value.trim().length < 3) {
                showError(usernameInput, usernameError, 'Username must be at least 3 characters');
            } else {
                hideError(usernameInput, usernameError);
            }
        });
    }

    // Password validation
    if (passwordInput && passwordError) {
        passwordInput.addEventListener('blur', () => {
            if (passwordInput.value.length < 8) {
                showError(passwordInput, passwordError, 'Password must be at least 8 characters');
            } else {
                hideError(passwordInput, passwordError);
            }
        });
    }

    // Confirm password validation
    if (confirmPasswordInput && confirmPasswordError) {
        confirmPasswordInput.addEventListener('blur', () => {
            if (confirmPasswordInput.value !== passwordInput.value) {
                showError(confirmPasswordInput, confirmPasswordError, 'Passwords do not match');
            } else {
                hideError(confirmPasswordInput, confirmPasswordError);
            }
        });
    }

    // Form submission
    if (signupForm) {
        signupForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            let isValid = true;

            // Validate username
            if (!usernameInput.value.trim()) {
                showError(usernameInput, usernameError, 'Username is required');
                isValid = false;
            } else if (usernameInput.value.trim().length < 3) {
                showError(usernameInput, usernameError, 'Username must be at least 3 characters');
                isValid = false;
            } else {
                hideError(usernameInput, usernameError);
            }

            // Validate password
            if (passwordInput.value.length < 8) {
                showError(passwordInput, passwordError, 'Password must be at least 8 characters');
                isValid = false;
            } else {
                hideError(passwordInput, passwordError);
            }

            // Validate confirm password
            if (confirmPasswordInput.value !== passwordInput.value) {
                showError(confirmPasswordInput, confirmPasswordError, 'Passwords do not match');
                isValid = false;
            } else {
                hideError(confirmPasswordInput, confirmPasswordError);
            }

            if (isValid) {
                const submitBtn = signupForm.querySelector('.btn-primary');
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';
                submitBtn.disabled = true;

                const signupData = {
                    username: usernameInput.value.trim(),
                    password: passwordInput.value
                };

                // Add email if provided
                if (emailInput.value.trim()) {
                    signupData.email = emailInput.value.trim();
                }

                fetch('/api/auth/signup/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(signupData)
                }).then(async (res) => {
                    const data = await res.json().catch(() => ({}));
                    if (!res.ok) {
                        throw new Error(data.detail || data.error || 'Signup failed');
                    }
                    return data;
                }).then((data) => {
                    // Store token and user info
                    localStorage.setItem('ap_token', data.token);
                    localStorage.setItem('ap_user', JSON.stringify({ id: data.id, username: data.username, email: data.email }));
                    localStorage.setItem('authToken', data.token);
                    localStorage.setItem('user', JSON.stringify({ id: data.id, username: data.username, email: data.email }));
                    
                    // Close modal and redirect
                    closeModal();
                    
                    // Show success message and redirect
                    alert('Account created successfully! Welcome to AutoPro Elite.');
                    window.location.reload();
                }).catch((err) => {
                    alert(err.message || 'Unable to create account');
                }).finally(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                });
            }
        });
    }

    // Google signup
    const googleBtn = signupModal?.querySelector('.btn-google');
    if (googleBtn) {
        googleBtn.addEventListener('click', () => {
            const params = new URLSearchParams(window.location.search);
            const nextUrl = params.get('next') || '/';
            window.location.href = '/api/auth/google/start/?next=' + encodeURIComponent(nextUrl);
        });
    }

    // Switch to login modal
    if (openLoginFromSignup && loginModal) {
        openLoginFromSignup.addEventListener('click', (e) => {
            e.preventDefault();
            closeModal();
            loginModal.classList.add('active');
            document.body.classList.add('modal-open');
        });
    }

    // Switch to signup modal from login
    if (openSignupModal) {
        openSignupModal.addEventListener('click', (e) => {
            e.preventDefault();
            if (loginModal) {
                loginModal.classList.remove('active');
            }
            openModal();
        });
    }
})();
