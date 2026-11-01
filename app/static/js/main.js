/**
 * Skill Resume Certificate Verification System - Core JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
    // 1. Initialize Bootstrap Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 2. Auto-dismiss flash alerts after 6 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {
                // If already closed by user
            }
        }, 6000);
    });

    // 3. Client-side form submission double-click prevention
    const forms = document.querySelectorAll('form:not(.no-disable)');
    forms.forEach(function (form) {
        form.addEventListener('submit', function () {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                // Do not disable immediately if browser validation fails
                if (form.checkValidity()) {
                    submitBtn.dataset.originalHtml = submitBtn.innerHTML;
                    submitBtn.innerHTML = `
                        <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                        Processing...
                    `;
                    submitBtn.disabled = true;
                }
            }
        });
    });

    // 4. File input preview and size warning
    const fileInputs = document.querySelectorAll('input[type="file"][data-max-size]');
    fileInputs.forEach(function (input) {
        input.addEventListener('change', function () {
            const maxBytes = parseInt(input.getAttribute('data-max-size'), 10);
            if (input.files && input.files[0]) {
                const file = input.files[0];
                if (file.size > maxBytes) {
                    const maxMb = (maxBytes / (1024 * 1024)).toFixed(0);
                    alert(`The selected file "${file.name}" exceeds the allowed limit of ${maxMb} MB.`);
                    input.value = '';
                }
            }
        });
    });
});

/**
 * Global helper to attach CSRF headers to fetch() calls
 */
window.secureFetch = function (url, options = {}) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    options.headers = options.headers || {};
    if (csrfToken) {
        options.headers['X-CSRFToken'] = csrfToken;
    }
    return fetch(url, options);
};
