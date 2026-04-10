(function () {
    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    function shouldAttach(method) {
        const m = String(method || 'GET').toUpperCase();
        return !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(m);
    }

    const token = getCsrfToken();

    // Ensure classic HTML forms always carry csrf_token.
    function addHiddenTokenToForms() {
        if (!token) return;
        document.querySelectorAll('form').forEach((form) => {
            if (form.querySelector('input[name="csrf_token"]')) return;
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'csrf_token';
            input.value = token;
            form.appendChild(input);
        });
    }

    // Wrap fetch so all mutating requests include CSRF header.
    const nativeFetch = window.fetch.bind(window);
    window.fetch = function (input, init = {}) {
        const method = (init && init.method) || 'GET';
        const headers = new Headers((init && init.headers) || {});
        if (token && shouldAttach(method) && !headers.has('X-CSRFToken')) {
            headers.set('X-CSRFToken', token);
        }
        return nativeFetch(input, { ...init, headers });
    };

    // jQuery/DataTables editor requests.
    if (window.jQuery && token) {
        window.jQuery.ajaxSetup({
            beforeSend: function (xhr, settings) {
                if (shouldAttach(settings && settings.type)) {
                    xhr.setRequestHeader('X-CSRFToken', token);
                }
            },
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', addHiddenTokenToForms);
    } else {
        addHiddenTokenToForms();
    }
})();
