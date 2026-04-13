/**
 * OAuth Success Notification
 * Shows a toast notification when user successfully logs in with Google
 */

(function() {
    // Check if user just logged in with Google
    const urlParams = new URLSearchParams(window.location.search);
    const justLoggedIn = sessionStorage.getItem('oauth_login_success');
    
    // Check if we have a token and user data (indicating successful login)
    const token = localStorage.getItem('ap_token');
    const userStr = localStorage.getItem('ap_user');
    
    if (token && userStr && !justLoggedIn) {
        try {
            const user = JSON.parse(userStr);
            
            // Check if this is a fresh login (token created in last 10 seconds)
            const tokenAge = Date.now() - (parseInt(localStorage.getItem('ap_token_timestamp') || '0'));
            
            if (tokenAge < 10000 || window.location.pathname === '/') {
                showSuccessNotification(user);
                sessionStorage.setItem('oauth_login_success', 'shown');
                localStorage.setItem('ap_token_timestamp', Date.now().toString());
            }
        } catch (e) {
            console.error('Error parsing user data:', e);
        }
    }
    
    function showSuccessNotification(user) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'oauth-success-notification';
        notification.innerHTML = `
            <div class="oauth-notification-content">
                <div class="oauth-notification-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                        <polyline points="22 4 12 14.01 9 11.01"></polyline>
                    </svg>
                </div>
                <div class="oauth-notification-text">
                    <div class="oauth-notification-title">Google Login Successful!</div>
                    <div class="oauth-notification-message">Welcome back, ${user.username}!</div>
                </div>
                <button class="oauth-notification-close" onclick="this.parentElement.parentElement.remove()">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
        `;
        
        // Add styles if not already added
        if (!document.getElementById('oauth-notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'oauth-notification-styles';
            styles.textContent = `
                .oauth-success-notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    z-index: 10000;
                    animation: slideInRight 0.5s ease-out;
                }
                
                @keyframes slideInRight {
                    from {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                
                @keyframes slideOutRight {
                    from {
                        transform: translateX(0);
                        opacity: 1;
                    }
                    to {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                }
                
                .oauth-notification-content {
                    background: white;
                    border-radius: 12px;
                    padding: 16px 20px;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    min-width: 320px;
                    max-width: 400px;
                    border-left: 4px solid #4CAF50;
                }
                
                .oauth-notification-icon {
                    width: 40px;
                    height: 40px;
                    background: #4CAF50;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    flex-shrink: 0;
                }
                
                .oauth-notification-text {
                    flex: 1;
                }
                
                .oauth-notification-title {
                    font-weight: 600;
                    color: #333;
                    font-size: 15px;
                    margin-bottom: 4px;
                }
                
                .oauth-notification-message {
                    color: #666;
                    font-size: 13px;
                }
                
                .oauth-notification-close {
                    background: none;
                    border: none;
                    color: #999;
                    cursor: pointer;
                    padding: 4px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 4px;
                    transition: all 0.2s;
                }
                
                .oauth-notification-close:hover {
                    background: #f5f5f5;
                    color: #333;
                }
                
                @media (max-width: 768px) {
                    .oauth-success-notification {
                        top: 10px;
                        right: 10px;
                        left: 10px;
                    }
                    
                    .oauth-notification-content {
                        min-width: auto;
                    }
                }
            `;
            document.head.appendChild(styles);
        }
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.5s ease-out';
            setTimeout(() => {
                notification.remove();
            }, 500);
        }, 5000);
    }
    
    // Clear the flag when navigating away
    window.addEventListener('beforeunload', () => {
        sessionStorage.removeItem('oauth_login_success');
    });
})();
