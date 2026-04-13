 // Navbar handled by partial script

        // Password toggle functionality
        const passwordToggle = document.getElementById('passwordToggle');
        const passwordInput = document.getElementById('password');

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

        // Form validation and submission
        const loginForm = document.getElementById('loginForm');
        const usernameInput = document.getElementById('username');
        const usernameError = document.getElementById('usernameError');
        const passwordError = document.getElementById('passwordError');

        function showError(input, errorElement, message) {
            input.classList.add('error');
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }

        function hideError(input, errorElement) {
            input.classList.remove('error');
            errorElement.style.display = 'none';
        }

        usernameInput.addEventListener('blur', () => {
            if (!usernameInput.value.trim()) {
                showError(usernameInput, usernameError, 'Please enter your username');
            } else {
                hideError(usernameInput, usernameError);
            }
        });

        passwordInput.addEventListener('blur', () => {
            if (passwordInput.value.length < 6) {
                showError(passwordInput, passwordError, 'Password must be at least 6 characters');
            } else {
                hideError(passwordInput, passwordError);
            }
        });

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
                    // Store token and user info (standard + backward compatibility)
                    localStorage.setItem('ap_token', data.token);
                    localStorage.setItem('ap_user', JSON.stringify({ id: data.id, username: data.username, email: data.email }));
                    localStorage.setItem('authToken', data.token); // legacy
                    localStorage.setItem('user', JSON.stringify({ id: data.id, username: data.username, email: data.email })); // legacy
                    // Optional: log via API (not required because backend logs login)
                    return data;
                }).then((data) => {
                    // Redirect logic: admins to /admin/, others to next or home
                    const params = new URLSearchParams(window.location.search);
                    const nextUrl = params.get('next');
                    if (data && (data.is_staff || data.is_superuser)) {
                        window.location.href = '/admin/';
                    } else if (nextUrl) {
                        window.location.href = nextUrl;
                    } else {
                        window.location.href = '/';
                    }
                }).catch((err) => {
                    alert(err.message || 'Unable to login');
                }).finally(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                });
            }
        });

        // Google login
        document.querySelector('.btn-google').addEventListener('click', () => {
            const params = new URLSearchParams(window.location.search);
            const nextUrl = params.get('next') || '/';
            window.location.href = '/api/auth/google/start/?next=' + encodeURIComponent(nextUrl);
        });