        // Navbar handled by partial script

        // Password toggle functionality
        function setupPasswordToggle(toggleId, inputId) {
            const toggle = document.getElementById(toggleId);
            const input = document.getElementById(inputId);

            toggle.addEventListener('click', () => {
                if (input.type === 'password') {
                    input.type = 'text';
                    toggle.classList.remove('fa-eye');
                    toggle.classList.add('fa-eye-slash');
                } else {
                    input.type = 'password';
                    toggle.classList.remove('fa-eye-slash');
                    toggle.classList.add('fa-eye');
                }
            });
        }

        setupPasswordToggle('passwordToggle', 'password');
        setupPasswordToggle('confirmPasswordToggle', 'confirmPassword');

        // Form validation
        const signupForm = document.getElementById('signupForm');
        const inputs = {
            fullName: document.getElementById('fullName'),
            username: document.getElementById('username'),
            email: document.getElementById('email'),
            phone: document.getElementById('phone'),
            password: document.getElementById('password'),
            confirmPassword: document.getElementById('confirmPassword'),
            terms: document.getElementById('terms')
        };

        const errors = {
            fullName: document.getElementById('fullNameError'),
            username: document.getElementById('usernameError'),
            email: document.getElementById('emailError'),
            phone: document.getElementById('phoneError'),
            password: document.getElementById('passwordError'),
            confirmPassword: document.getElementById('confirmPasswordError')
        };

        // Google signup/login
        document.querySelector('.btn-google').addEventListener('click', () => {
            const params = new URLSearchParams(window.location.search);
            const nextUrl = params.get('next') || '/';
            window.location.href = '/api/auth/google/start/?next=' + encodeURIComponent(nextUrl);
        });

        function validateEmail(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        }

        function validatePhone(phone) {
            const phoneRegex = /^[\+]?[1-9][\d]{9,14}$/; // Validating mobile number length
            return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''));
        }

        function checkPasswordStrength(password) {
            const strengthIndicator = document.getElementById('passwordStrength');
            let strength = 0;
            let feedback = '';

            if (password.length >= 8) strength++;
            if (/[a-z]/.test(password)) strength++;
            if (/[A-Z]/.test(password)) strength++;
            if (/[0-9]/.test(password)) strength++;
            if (/[^A-Za-z0-9]/.test(password)) strength++;

            switch (strength) {
                case 0:
                case 1:
                case 2:
                    feedback = 'Weak password';
                    strengthIndicator.className = 'password-strength strength-weak';
                    break;
                case 3:
                case 4:
                    feedback = 'Medium password';
                    strengthIndicator.className = 'password-strength strength-medium';
                    break;
                case 5:
                    feedback = 'Strong password';
                    strengthIndicator.className = 'password-strength strength-strong';
                    break;
            }

            strengthIndicator.textContent = feedback;
            return strength >= 3;
        }

        function showError(input, errorElement, message) {
            input.classList.add('error');
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        }

        function hideError(input, errorElement) {
            input.classList.remove('error');
            errorElement.style.display = 'none';
        }

        // Real-time validation
        inputs.password.addEventListener('input', () => {
            checkPasswordStrength(inputs.password.value);
        });

        inputs.confirmPassword.addEventListener('blur', () => {
            if (inputs.password.value !== inputs.confirmPassword.value) {
                showError(inputs.confirmPassword, errors.confirmPassword, 'Passwords do not match');
            } else {
                hideError(inputs.confirmPassword, errors.confirmPassword);
            }
        });

        inputs.email.addEventListener('blur', () => {
            if (!validateEmail(inputs.email.value)) {
                showError(inputs.email, errors.email, 'Please enter a valid email address');
            } else {
                hideError(inputs.email, errors.email);
            }
        });

        inputs.phone.addEventListener('blur', () => {
            if (!validatePhone(inputs.phone.value)) {
                showError(inputs.phone, errors.phone, 'Please enter a valid mobile number');
            } else {
                hideError(inputs.phone, errors.phone);
            }
        });

        // Form submission
        signupForm.addEventListener('submit', (e) => {
            e.preventDefault();

            // Basic validation
            let ok = true;
            if (!inputs.fullName.value.trim()) { showError(inputs.fullName, errors.fullName, 'Name is required'); ok = false; } else { hideError(inputs.fullName, errors.fullName); }
            if (!inputs.username.value.trim()) { showError(inputs.username, errors.username, 'Username is required'); ok = false; } else { hideError(inputs.username, errors.username); }
            if (!validateEmail(inputs.email.value)) { showError(inputs.email, errors.email, 'Valid email is required'); ok = false; } else { hideError(inputs.email, errors.email); }
            if (!validatePhone(inputs.phone.value)) { showError(inputs.phone, errors.phone, 'Valid mobile number is required'); ok = false; } else { hideError(inputs.phone, errors.phone); }
            if (!inputs.password.value || inputs.password.value.length < 8) { showError(inputs.password, errors.password, 'Password must be at least 8 characters'); ok = false; } else { hideError(inputs.password, errors.password); }
            
            // Password match validation with popup
            if (inputs.password.value !== inputs.confirmPassword.value) { 
                alert('Error: Password and Confirm Password do not match!');
                showError(inputs.confirmPassword, errors.confirmPassword, 'Passwords do not match'); 
                ok = false; 
            } else { 
                hideError(inputs.confirmPassword, errors.confirmPassword); 
            }
            
            if (!ok) return;

            const submitBtn = signupForm.querySelector('.btn-primary');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Account...';
            submitBtn.disabled = true;

            fetch('/api/auth/signup/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    name: inputs.fullName.value.trim(),
                    username: inputs.username.value.trim(), 
                    phone: inputs.phone.value.trim(),
                    email: inputs.email.value.trim(),
                    password: inputs.password.value 
                })
            }).then(async (res) => {
                const data = await res.json().catch(() => ({}));
                if (!res.ok) {
                    console.error('Signup error response:', data);
                    let errorMsg = 'Signup failed';
                    if (data.detail) errorMsg = data.detail;
                    else if (typeof data === 'object') {
                        errorMsg = Object.entries(data)
                            .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : value}`)
                            .join('\n');
                    }
                    throw new Error(errorMsg);
                }
                
                // Store token and user
                localStorage.setItem('ap_token', data.token);
                localStorage.setItem('ap_user', JSON.stringify({ id: data.id, username: data.username, email: data.email }));
                localStorage.setItem('authToken', data.token); 
                localStorage.setItem('user', JSON.stringify({ id: data.id, username: data.username, email: data.email }));
                
                alert('Account created successfully!');
                window.location.href = '/account/';
            }).catch((err) => {
                console.error('Signup catch error:', err);
                alert('Signup failed:\n' + err.message);
            }).finally(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            });
        });

        // Google signup simulation
        document.querySelector('.btn-google').addEventListener('click', () => {
            alert('Google authentication would be implemented here');
        });
