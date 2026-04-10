(function () {
    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    function shouldAttach(method) {
        const m = String(method || 'GET').toUpperCase();
        return !['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(m);
    }

    // Ensure classic HTML forms always carry csrf_token.
    function addHiddenTokenToForms() {
        const token = getCsrfToken();
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
        const token = getCsrfToken();
        const method = (init && init.method) || 'GET';
        const headers = new Headers((init && init.headers) || {});
        if (token && shouldAttach(method) && !headers.has('X-CSRFToken')) {
            headers.set('X-CSRFToken', token);
        }
        return nativeFetch(input, { ...init, headers });
    };

    // Wrap XHR so libraries that bypass fetch/jQuery (e.g. some DataTables paths)
    // still get CSRF headers on mutating requests.
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function (method, url, ...rest) {
        this.__csrfMethod = method;
        this.__csrfUrl = url;
        return originalOpen.call(this, method, url, ...rest);
    };

    XMLHttpRequest.prototype.send = function (body) {
        const token = getCsrfToken();
        if (token && shouldAttach(this.__csrfMethod)) {
            try {
                this.setRequestHeader('X-CSRFToken', token);
            } catch (e) {
                // Ignore header failures for non-HTTP transports.
            }
        }
        return originalSend.call(this, body);
    };

    // jQuery/DataTables editor requests.
    if (window.jQuery) {
        window.jQuery.ajaxSetup({
            beforeSend: function (xhr, settings) {
                const token = getCsrfToken();
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
