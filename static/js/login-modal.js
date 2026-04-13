(function() {
    const modal = document.getElementById('loginModal');
    const closeBtn = document.getElementById('closeLoginModal');
    const overlay = modal?.querySelector('.modal-overlay');
    const passwordToggle = document.getElementById('modal-passwordToggle');
    const passwordInput = document.getElementById('modal-password');
    const loginForm = document.getElementById('modalLoginForm');
    const usernameInput = document.getElementById('modal-username');
    const usernameError = document.getElementById('modal-usernameError');
    const passwordError = document.getElementById('modal-passwordError');

    // Close modal function
    function closeModal() {
        if (modal) {
            modal.classList.remove('active');
            document.body.classList.remove('modal-open');
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
        if (e.key === 'Escape' && modal?.classList.contains('active')) {
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

    // Username validation
    if (usernameInput && usernameError) {
        usernameInput.addEventListener('blur', () => {
            if (!usernameInput.value.trim()) {
                showError(usernameInput, usernameError, 'Please enter your username');
            } else {
                hideError(usernameInput, usernameError);
            }
        });
    }

    // Password validation
    if (passwordInput && passwordError) {
        passwordInput.addEventListener('blur', () => {
            if (passwordInput.value.length < 6) {
                showError(passwordInput, passwordError, 'Password must be at least 6 characters');
            } else {
                hideError(passwordInput, passwordError);
            }
        });
    }

    // Form submission
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            let isValid = true;

            // Validate username
            if (!usernameInput.value.trim()) {
                showError(usernameInput, usernameError, 'Please enter your username');
                isValid = false;
            } else {
                hideError(usernameInput, usernameError);
            }

            // Validate password
            if (passwordInput.value.length < 6) {
                showError(passwordInput, passwordError, 'Password must be at least 6 characters');
                isValid = false;
            } else {
                hideError(passwordInput, passwordError);
            }

            if (isValid) {
                const submitBtn = loginForm.querySelector('.btn-primary');
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Signing In...';
                submitBtn.disabled = true;

                fetch('/api/auth/login/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: usernameInput.value.trim(),
                        password: passwordInput.value
                    })
                }).then(async (res) => {
                    const data = await res.json().catch(() => ({}));
                    if (!res.ok) {
                        throw new Error(data.detail || 'Login failed');
                    }
                    // Store token and user info
                    localStorage.setItem('ap_token', data.token);
                    localStorage.setItem('ap_user', JSON.stringify({ id: data.id, username: data.username, email: data.email }));
                    localStorage.setItem('authToken', data.token);
                    localStorage.setItem('user', JSON.stringify({ id: data.id, username: data.username, email: data.email }));
                    return data;
                }).then((data) => {
                    // Close modal and redirect
                    closeModal();
                    
                    // Redirect logic
                    const params = new URLSearchParams(window.location.search);
                    const nextUrl = params.get('next');
                    if (data && (data.is_staff || data.is_superuser)) {
                        window.location.href = '/admin/';
                    } else if (nextUrl) {
                        window.location.href = nextUrl;
                    } else {
                        window.location.reload();
                    }
                }).catch((err) => {
                    alert(err.message || 'Unable to login');
                }).finally(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                });
            }
        });
    }

    // Google login
    const googleBtn = modal?.querySelector('.btn-google');
    if (googleBtn) {
        googleBtn.addEventListener('click', () => {
            const params = new URLSearchParams(window.location.search);
            const nextUrl = params.get('next') || '/';
            window.location.href = '/api/auth/google/start/?next=' + encodeURIComponent(nextUrl);
        });
    }

    // Open modal when body has modal-open class (for programmatic opening)
    if (modal && document.body.classList.contains('modal-open')) {
        modal.classList.add('active');
    }
})();
