// Configuration object to store module settings
let config = {
    apiUrl: '',
    deleteModal: null,
    formModal: null,
    importModal: null,
    tblId: '',
    exportUrl: '',
    removeAllUrl: ''
};

// Function to initialize module configuration
export function initConfig(cfg) {
    config = {
        ...config,
        ...cfg
    };
    
    // Get table data attributes
    const table = document.getElementById(config.tblId);
    if (table) {
        config.exportUrl = table.dataset.exportUrl;
        config.removeAllUrl = table.dataset.removeAllUrl;
        config.apiUrl = `${table.dataset.apiUrl}/`;
    }
}

// Function to get current configuration
export function getConfig() {
    return { ...config };
}

// Utility: Fetch wrapper with retry logic
export async function sendRequest({ url, method, data = null, errHandler = null, retries = 1 }) {
    for (let i = 0; i <= retries; i++) {
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
            if (i === retries) {
                if (errHandler) {
                    errHandler(error.message || 'An error occurred');
                } else {
                    throw error;
                }
            }
            // Wait before retrying (exponential backoff)
            await new Promise(resolve => setTimeout(resolve, Math.pow(2, i) * 1000));
        }
    }
}

// Utility: Toast message with auto-hide
export function showToast(type, message, duration = 3000) {
    const toastEl = document.getElementById(type === 'error' ? 'errorToast' : 'successToast');
    const toastBody = toastEl.querySelector('.toast-body');
    toastBody.textContent = message;
    
    const toast = new bootstrap.Toast(toastEl, {
        autohide: true,
        delay: duration
    });
    toast.show();
}

// Utility: Delete item by id with confirmation
export async function doDelete(id) {
    try {
        await sendRequest({
            url: `${config.apiUrl}${id}`,
            method: "DELETE"
        });
        config.deleteModal.hide();
        showToast('success', 'Item deleted successfully');
        setTimeout(() => location.reload(), 1000);
    } catch (error) {
        showToast('error', error.message || 'Failed to delete item');
    }
}

// Debounce function to prevent rapid clicks
const debounce = (fn, delay) => {
    let timeoutId;
    return (...args) => {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => fn(...args), delay);
    };
};

// Utility: Initialize table buttons with debouncing
export function initButtons(createText='Create', editText='Edit', resetFormFnc=null, loadFormDataFnc=null, processFormFnc=null) {
    const table = document.getElementById(config.tblId);
    if (!table) return;

    // Use event delegation from the table container
    table.addEventListener("click", debounce(async function (event) {
        const button = event.target.closest('.delete-btn, .edit-btn');
        if (!button) return;

        try {
            // Button: Delete user
            if (button.classList.contains('delete-btn')) {
                const id = button.dataset.id;
                config.deleteModal.show();
                
                // Remove any existing listeners and add new one
                const confirmBtn = document.getElementById('deleteConfirmBtn');
                const newConfirmBtn = confirmBtn.cloneNode(true);
                confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
                newConfirmBtn.addEventListener('click', () => doDelete(id));

            // Button: Edit user
            } else if (button.classList.contains('edit-btn')) {
                const id = button.dataset.id;
                document.getElementById('modalTitle').textContent = editText;

                const data = await sendRequest({
                    url: `${config.apiUrl}${id}`,
                    method: "GET"
                });
                
                if (loadFormDataFnc) {
                    loadFormDataFnc(data);
                }
                
                config.formModal.show();
            }
        } catch (error) {
            showToast('error', error.message || 'Operation failed');
        }
    }, 300));

    // Button: Create user
    const createBtn = document.querySelector(`#${config.tblId} #createBtn`);
    if (createBtn) {
        createBtn.addEventListener('click', () => {
            document.getElementById('modalTitle').textContent = createText;
            if (resetFormFnc) {
                resetFormFnc();
            }
            config.formModal.show();
        });
    }

    // Form submission with validation
    if (processFormFnc) {
        const form = config.formModal._element.querySelector('form');
        if (form) {
            form.addEventListener('submit', async function(e) {
                e.preventDefault();
                
                try {
                    const {id, isNew, data} = processFormFnc();
                    
                    // Basic validation
                    if (!data.name?.trim()) {
                        throw new Error('Name is required');
                    }
                    
                    const response = await sendRequest({
                        url: isNew ? config.apiUrl : `${config.apiUrl}${id}`,
                        method: isNew ? "POST" : "PUT",
                        data
                    });
                    
                    showToast('success', response.success);
                    config.formModal.hide();
                    setTimeout(() => location.reload(), 1000);
                } catch (error) {
                    showToast('error', error.message || 'Failed to save changes');
                }
            });
        }
    }
}

// Search functionality with debouncing
export function searchTable(showDisabledSelector='#showInactive') {
    const tblId = config.tblId;
    const searchInput = document.querySelector(`#${tblId} #searchInput`);
    if (!searchInput) return;

    const debouncedSearch = debounce(function() {
        const value = searchInput.value.toLowerCase();
        const showDisabled = document.querySelector(`#${tblId} ${showDisabledSelector}`).checked;
        
        document.querySelectorAll(`#${tblId} table tbody tr`).forEach(row => {
            const isActive = row.dataset.active;
            const searchText = Array.from(row.querySelectorAll('td:not(:last-child)'))
                .map(td => td.textContent.toLowerCase())
                .join(' ');
            
            const matchesSearch = searchText.includes(value);
            const shouldShow = (showDisabled || isActive) && matchesSearch;
            row.style.display = shouldShow ? '' : 'none';
        });
    }, 300);

    searchInput.addEventListener('keyup', debouncedSearch);
}

// Toolbar with error handling
export function toolbar() {
    const tblId = config.tblId;
    const exportBtn = document.querySelector(`#${tblId} #exportBtn`);
    const importBtn = document.querySelector(`#${tblId} #importBtn`);
    const removeAllBtn = document.querySelector(`#${tblId} #removeAllBtn`);

    if (exportBtn) {
        exportBtn.addEventListener('click', () => window.location.href = config.exportUrl);
    }
    
    if (importBtn) {
        importBtn.addEventListener('click', () => config.importModal.show());
    }
    
    if (removeAllBtn) {
        removeAllBtn.addEventListener('click', () => removeAll());
    }

    // Import Form Submission with progress indicator
    const importForm = document.getElementById('importForm');
    if (importForm) {
        importForm.onsubmit = async function (e) {
            e.preventDefault();
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            
            try {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Importing...';
                
                const formData = new FormData(e.target);
                const response = await fetch(this.action, {
                    method: "POST",
                    body: formData,
                    credentials: 'same-origin'
                });
                
                const data = await response.json();
                showToast('success', data.success);
                setTimeout(() => location.reload(), 1000);
            } catch (error) {
                showToast('error', "Error: " + (error.message || "Unknown error"));
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        };
    }
}

// Remove All with confirmation
export async function removeAll() {
    if (!confirm("Are you sure you want to remove all items? This action cannot be undone.")) {
        return;
    }

    try {
        await sendRequest({
            url: config.removeAllUrl,
            method: "DELETE"
        });
        showToast('success', "All items removed successfully");
        setTimeout(() => location.reload(), 1000);
    } catch (error) {
        showToast('error', "Error: " + (error.message || "Unknown error"));
    }
}

// Toggle: Show inactive items with performance optimization
export function toggleShowDisabled(tblId, showDisabledSelector='#showInactive', tableRowSelector='tbody tr') {
    const showDisabled = document.querySelector(`#${tblId} ${showDisabledSelector}`).checked;
    const rows = document.querySelectorAll(`#${tblId} ${tableRowSelector}`);
    
    // Use requestAnimationFrame for smooth updates
    requestAnimationFrame(() => {
        rows.forEach(row => {
            const isActive = row.dataset.active.toLowerCase();
            row.style.display = (showDisabled || isActive === 'true') ? '' : 'none';
        });
    });
}

export function initToggleActive(showDisabledSelector='#showInactive', tableRowSelector='tbody tr') {
    const tblId = config.tblId;
    const table = document.querySelector(`#${tblId} table`);
    if (!table) return;

    // Initial state
    toggleShowDisabled(tblId, showDisabledSelector, tableRowSelector);
    table.style.display = '';

    // Toggle handler
    document.querySelector(`#${tblId} ${showDisabledSelector}`).addEventListener('change', function() {
        toggleShowDisabled(tblId, showDisabledSelector, tableRowSelector);
    });
}
    
    