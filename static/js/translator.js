(function () {
    'use strict';

    // Lazy-load Google Translate when opening the dropdown to avoid rendering issues in hidden container
    let gteLoaded = false;
    let gteInited = false;
    let gteInitAttempts = 0;

    function setError(msg) {
        const el = document.getElementById('translator-error');
        if (!el) return;
        el.textContent = msg || '';
        el.style.display = msg ? 'block' : 'none';
    }

    function isDropdownVisible() {
        const dropdown = document.getElementById('translator-dropdown');
        if (!dropdown) return false;
        if (dropdown.classList.contains('open')) return true;
        try {
            const cs = window.getComputedStyle(dropdown);
            if (!cs) return false;
            if (cs.display === 'none') return false;
            if (cs.visibility === 'hidden') return false;
            if (Number.parseFloat(cs.opacity || '0') <= 0) return false;
            return true;
        } catch (e) {
            return false;
        }
    }

    function googleTranslateElementInit() {
        if (gteInited) return;
        gteInitAttempts += 1;
        if (gteInitAttempts > 25) {
            setError('Translator failed to start. Please refresh the page or check your internet/certificate settings.');
            return;
        }
        try {
            const el = document.getElementById('google_translate_element');
            if (!el) return;

            // Only init once dropdown is open/visible; otherwise the combo may not render.
            if (!isDropdownVisible()) {
                setTimeout(googleTranslateElementInit, 200);
                return;
            }

            if (!(window.google && google.translate && google.translate.TranslateElement)) {
                setTimeout(googleTranslateElementInit, 300);
                return;
            }

            // Clear any previous error.
            setError('');

            // Some builds do not expose InlineLayout; avoid referencing it.
            new google.translate.TranslateElement({
                pageLanguage: 'en',
                autoDisplay: false
            }, 'google_translate_element');
            gteInited = true;

            // After init, convert the injected select into a scrollable list
            // to match the requested UI (expanded language list).
            setTimeout(enhanceLanguageSelect, 200);
        } catch (e) {
            console.warn('Translate init retry soon', e);
            setTimeout(googleTranslateElementInit, 500);
        }
    }

    function enhanceLanguageSelect() {
        try {
            const select = document.querySelector('#google_translate_element select.goog-te-combo');
            if (!select) return;
            // Show many languages in a scrollable list (like the screenshot)
            select.setAttribute('size', '14');
            select.style.height = 'auto';
        } catch (e) {
            // ignore
        }
    }

    function loadGoogleTranslate() {
        if (gteLoaded) {
            // If the library is loaded but not initialized yet, initialize now
            if (!gteInited && window.google && google.translate) {
                googleTranslateElementInit();
            }
            return;
        }
        // Define callback for Google script
        window.googleTranslateElementInit = googleTranslateElementInit;
        const s = document.createElement('script');
        s.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
        s.async = true;
        s.onerror = function () {
            console.error('Failed to load Google Translate script');
            setError('Translator failed to load (network/certificate blocked).');
        };
        document.head.appendChild(s);
        gteLoaded = true;
    }

    function openDropdown(toggle, dropdown) {
        const willOpen = !dropdown.classList.contains('open');
        dropdown.classList.toggle('open');
        toggle.setAttribute('aria-expanded', dropdown.classList.contains('open') ? 'true' : 'false');
        if (willOpen) {
            requestAnimationFrame(() => {
                setError('');
                loadGoogleTranslate();
                googleTranslateElementInit();
                enhanceLanguageSelect();
            });
        }
    }

    function closeDropdown(toggle, dropdown) {
        dropdown.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
    }

    function bindDelegatedHandlers() {
        if (document.documentElement.dataset && document.documentElement.dataset.translatorBound === '1') return;
        if (document.documentElement.dataset) document.documentElement.dataset.translatorBound = '1';

        // Toggle on click (delegated)
        document.addEventListener('click', function (e) {
            const toggle = e.target && e.target.closest ? e.target.closest('#translator-toggle') : null;
            if (!toggle) return;

            const dropdown = document.getElementById('translator-dropdown');
            if (!dropdown) return;

            e.preventDefault();
            e.stopPropagation();
            openDropdown(toggle, dropdown);
        }, true);

        // If dropdown is opened via CSS (:focus-within) but click handler doesn't fire,
        // ensure we still lazy-load and initialize Google Translate when focus enters.
        document.addEventListener('focusin', function (e) {
            const toggle = e.target && e.target.closest ? e.target.closest('#translator-toggle') : null;
            if (!toggle) return;
            const dropdown = document.getElementById('translator-dropdown');
            if (!dropdown) return;

            if (isDropdownVisible()) {
                loadGoogleTranslate();
                googleTranslateElementInit();
            }
        });

        // Close on outside click
        document.addEventListener('click', function (e) {
            const toggle = document.getElementById('translator-toggle');
            const dropdown = document.getElementById('translator-dropdown');
            if (!toggle || !dropdown) return;

            if (!dropdown.classList.contains('open')) return;

            const menuFrame = document.querySelector('.goog-te-menu-frame.skiptranslate');
            if (menuFrame) return;

            const clickedToggle = e.target && (e.target === toggle || (toggle.contains && toggle.contains(e.target)));
            const clickedDropdown = dropdown.contains(e.target);
            if (!clickedToggle && !clickedDropdown) {
                closeDropdown(toggle, dropdown);
            }
        });

        // Close dropdown shortly after a language is chosen by observing the menu iframe removal
        const observer = new MutationObserver(() => {
            const toggle = document.getElementById('translator-toggle');
            const dropdown = document.getElementById('translator-dropdown');
            if (!toggle || !dropdown) return;

            const menuFrame = document.querySelector('.goog-te-menu-frame.skiptranslate');
            if (!menuFrame && dropdown.classList.contains('open')) {
                closeDropdown(toggle, dropdown);
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bindDelegatedHandlers);
    } else {
        bindDelegatedHandlers();
    }
})();
