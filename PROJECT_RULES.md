# nDART Project Rules

## Overview
This document outlines the coding standards, patterns, and best practices for the nDART project. Following these guidelines ensures consistency, maintainability, and security across the codebase.

## JavaScript Patterns

### API Requests
Use the following pattern for all API requests:

```javascript
async function sendRequest({ url, method, data = null }) {
    try {
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: data ? JSON.stringify(data) : undefined,
            credentials: 'same-origin'
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.message || 'Request failed');
        }
        
        return await res.json();
    } catch (error) {
        showToast('error', error.message || 'An error occurred');
        throw error;
    }
}
```

### Toast Messages
Use consistent toast message handling:

```javascript
function showToast(type, message) {
    const toastEl = document.getElementById(type === 'error' ? 'errorToast' : 'successToast');
    toastEl.querySelector('.toast-body').textContent = message;
    new bootstrap.Toast(toastEl).show();
}
```

### Form Handling
Use this pattern for form submissions:

```javascript
async function handleFormSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    try {
        const response = await sendRequest({
            url: formAction,
            method: 'POST',
            data: Object.fromEntries(formData)
        });
        showToast('success', response.success);
        location.reload();
    } catch (error) {
        // Error handled by sendRequest
    }
}
```

### JavaScript Conventions
- Use async/await for asynchronous operations
- Handle errors consistently using try/catch blocks
- Use proper error messages and toast notifications
- Include CSRF protection with credentials: 'same-origin'
- Use proper HTTP methods (GET, POST, PUT, DELETE)
- Validate form data before submission
- Use proper content types for requests

## HTML Patterns

### Modal Structure
Use this consistent modal structure:

```html
<div class="modal fade" id="modalId" tabindex="-1" aria-labelledby="modalLabel" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="modalLabel">Modal Title</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <!-- Modal content -->
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                <button type="button" class="btn btn-primary">Save</button>
            </div>
        </div>
    </div>
</div>
```

### Toast Structure
Use this consistent toast structure:

```html
<div class="toast-container position-fixed top-0 end-0 p-3">
    <div id="toastId" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="toast-header">
            <strong class="me-auto">Toast Title</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body"></div>
    </div>
</div>
```

### HTML Conventions
- Use proper ARIA attributes for accessibility
- Include proper modal structure with header, body, and footer
- Use consistent button styling and positioning
- Include proper form labels and required field indicators
- Use proper data attributes for JavaScript functionality
- Include proper error handling UI elements

## General Conventions

### Code Style
- Use consistent naming conventions for IDs and classes
- Include proper error handling and user feedback
- Use proper security measures (CSRF, input validation)
- Follow responsive design principles
- Use proper documentation and comments
- Follow DRY (Don't Repeat Yourself) principles
- Use proper version control practices

### Project Structure
```
project/
├── templates/
│   ├── admin/
│   ├── components/
│   ├── modals/
│   └── base templates
└── static/
    ├── js/
    ├── css/
    └── images/
```

## Security Guidelines
1. Always use CSRF protection for forms and API requests
2. Validate all user input on both client and server side
3. Use proper content types for requests
4. Implement proper error handling without exposing sensitive information
5. Use secure password handling practices
6. Follow the principle of least privilege for user roles

## Accessibility Guidelines
1. Use proper ARIA attributes
2. Ensure proper color contrast
3. Provide alternative text for images
4. Use semantic HTML elements
5. Ensure keyboard navigation works
6. Test with screen readers

## Performance Guidelines
1. Minimize DOM manipulations
2. Use efficient event delegation
3. Optimize API calls
4. Implement proper caching strategies
5. Minimize page reloads
6. Use proper loading indicators

## Testing Guidelines
1. Write unit tests for critical functionality
2. Test error handling scenarios
3. Test accessibility compliance
4. Test responsive design
5. Test cross-browser compatibility
6. Document test cases and scenarios 