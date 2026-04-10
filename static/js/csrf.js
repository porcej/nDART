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

    // Wrap XHR so libraries that bypass fetch (e.g. jQuery/DataTables) still get CSRF
    // on mutating requests. Track outgoing X-CSRFToken via setRequestHeader so we never
    // append a second value (duplicate headers become "token, token" and break Flask-WTF).
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSetRequestHeader = XMLHttpRequest.prototype.setRequestHeader;
    const originalSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function (method, url, ...rest) {
        this.__csrfMethod = method;
        this.__csrfUrl = url;
        this.__csrfTokenHeaderPresent = false;
        return originalOpen.call(this, method, url, ...rest);
    };

    XMLHttpRequest.prototype.setRequestHeader = function (name, value) {
        if (String(name).toLowerCase() === 'x-csrftoken') {
            this.__csrfTokenHeaderPresent = true;
        }
        return originalSetRequestHeader.call(this, name, value);
    };

    XMLHttpRequest.prototype.send = function (body) {
        const token = getCsrfToken();
        if (
            token &&
            shouldAttach(this.__csrfMethod) &&
            !this.__csrfTokenHeaderPresent
        ) {
            try {
                this.setRequestHeader('X-CSRFToken', token);
            } catch (e) {
                // Ignore header failures for non-HTTP transports.
            }
        }
        return originalSend.call(this, body);
    };

    // jQuery uses XMLHttpRequest; the send() wrapper above supplies the token. Do not
    // also use ajaxSetup(beforeSend), or the header would be set twice and validation fails.

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', addHiddenTokenToForms);
    } else {
        addHiddenTokenToForms();
    }
})();
