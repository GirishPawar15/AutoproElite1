(function () {
    'use strict';

    if (window.__ap_index_js_loaded__) return;
    window.__ap_index_js_loaded__ = true;

    // Navigation functionality
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    const mainNav = document.querySelector('.main-nav');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
        });
    }

    if (mainNav) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                mainNav.classList.add('scrolled');
            } else {
                mainNav.classList.remove('scrolled');
            }
        });
    }

    // Animation on scroll
    const fadeElements = document.querySelectorAll('.fade-in');

    function checkFade() {
        fadeElements.forEach(element => {
            const elementTop = element.getBoundingClientRect().top;
            const elementVisible = 150;

            if (elementTop < window.innerHeight - elementVisible) {
                element.style.opacity = "1";
                element.style.transform = "translateY(0)";
            }
        });
    }

    window.addEventListener('scroll', checkFade);
    window.addEventListener('load', checkFade);

    // Navigation to dedicated pages for auth
    const loginBtn = document.getElementById('loginBtn');
    const signupBtn = document.getElementById('signupBtn');
    const accountBtn = document.getElementById('accountBtn');
    const logoutBtn = document.getElementById('logoutBtn');

    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            window.location.href = '/login/';
        });
    }

    if (signupBtn) {
        signupBtn.addEventListener('click', () => {
            window.location.href = '/signup/';
        });
    }

    // Toggle navbar actions based on auth state
    (function setAuthNav(){
        const token = localStorage.getItem('authToken');
        const show = (el, on) => { if (el) el.style.display = on ? '' : 'none'; };
        if (token) {
            show(loginBtn, false); show(signupBtn, false);
            show(accountBtn, true); show(logoutBtn, true);
        } else {
            show(loginBtn, true); show(signupBtn, true);
            show(accountBtn, false); show(logoutBtn, false);
        }

        if (logoutBtn) logoutBtn.onclick = () => {
            localStorage.removeItem('authToken');
            localStorage.removeItem('user');
            window.location.href = '/';
        };
    })();
})();
