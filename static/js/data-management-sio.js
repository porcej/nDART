// Data Management SocketIO Events
// This file handles real-time updates for events, observations, and status reports management

// Initialize SocketIO connection for data management
const dataManagementSocket = io.connect('//' + document.domain + ':' + location.port + '/api');

// Toast notification helper
function showDataManagementToast(type, title, message) {
    // Create toast element
    const toastContainer = document.querySelector('.toast-container') || createToastContainer();
    
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header">
                <i class="bi bi-${type === 'success' ? 'check-circle-fill text-success' : type === 'warning' ? 'exclamation-triangle-fill text-warning' : 'info-circle-fill text-info'} me-2"></i>
                <strong class="me-auto">${title}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Show toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement);
    toast.show();
    
    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Create toast container if it doesn't exist
function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Update dashboard counts in real-time
function updateDashboardCount(type, count, operation) {
    // Only update if we're on the admin dashboard
    if (window.location.pathname === '/admin/' || window.location.pathname === '/admin') {
        const countElement = document.querySelector(`[data-count-type="${type}"]`);
        if (countElement) {
            const currentCount = parseInt(countElement.textContent) || 0;
            let newCount;
            
            if (operation === 'add') {
                newCount = currentCount + count;
            } else if (operation === 'set') {
                newCount = count;
            } else {
                newCount = currentCount;
            }
            
            countElement.textContent = newCount;
            
            // Add a subtle animation to show the update
            countElement.style.transition = 'all 0.3s ease';
            countElement.style.transform = 'scale(1.1)';
            countElement.style.color = '#28a745';
            
            setTimeout(() => {
                countElement.style.transform = 'scale(1)';
                countElement.style.color = '';
            }, 300);
        }
    }
}

// Force refresh for any admin page when data changes significantly
function forceRefreshIfNeeded(type, operation) {
    // If it's a clear operation, refresh all admin pages
    if (operation === 'clear') {
        // Check if we're on any admin page
        if (window.location.pathname.startsWith('/admin')) {
            console.log(`Data cleared for ${type}, refreshing page...`);
            setTimeout(() => location.reload(), 1000);
        }
    }
}

// Refresh events table on main dashboard and events pages
function refreshEventsTable() {
    // Check if we're on dashboard or events page
    if (window.location.pathname === '/' || 
        window.location.pathname === '/dashboard' || 
        window.location.pathname === '/events') {
        
        console.log('Refreshing events table...');
        
        // If DataTable exists, reload it
        if (window.eventsTable && typeof window.eventsTable.ajax.reload === 'function') {
            window.eventsTable.ajax.reload();
        }
        // If events table exists but not as DataTable, refresh the page
        else if (document.getElementById('events-table')) {
            setTimeout(() => location.reload(), 1000);
        }
    }
}

// Refresh observations table on main dashboard and observations page
function refreshObservationsTable() {
    // Check if we're on dashboard or observations page
    if (window.location.pathname === '/' || 
        window.location.pathname === '/dashboard' || 
        window.location.pathname === '/observations') {
        console.log('Refreshing observations table...');
        
        // If DataTable exists, reload it
        if (window.observationsTable && typeof window.observationsTable.ajax.reload === 'function') {
            window.observationsTable.ajax.reload();
        }
        // If observations table exists but not as DataTable, refresh the page
        else if (document.getElementById('observations-table')) {
            setTimeout(() => location.reload(), 1000);
        }
    }
}

// Refresh status reports table on status reports page
function refreshStatusReportsTable() {
    // Check if we're on status reports page
    if (window.location.pathname === '/status-reports' || window.location.pathname === '/status_reports') {
        console.log('Refreshing status reports table...');
        
        // If DataTable exists, reload it
        if (window.statusReportsTable && typeof window.statusReportsTable.ajax.reload === 'function') {
            window.statusReportsTable.ajax.reload();
        }
        // If status reports table exists but not as DataTable, refresh the page
        else if (document.getElementById('status-reports-table')) {
            setTimeout(() => location.reload(), 1000);
        }
    }
}

// Events SocketIO Events
dataManagementSocket.on('events_imported', function(data) {
    const title = data.success ? 'Events Imported' : 'Events Import Warning';
    const message = data.success 
        ? `Successfully imported ${data.count} events`
        : `Imported ${data.count} events with ${data.errors.length} errors`;
    
    showDataManagementToast(data.success ? 'success' : 'warning', title, message);
    
    // Update dashboard count if we're on the admin dashboard
    updateDashboardCount('events', data.count, 'add');
    
    // Refresh events table on main dashboard and events pages
    refreshEventsTable();
    
    // Refresh the page if we're on the admin events page
    if (window.location.pathname.includes('/admin/events')) {
        setTimeout(() => location.reload(), 2000);
    }
});

dataManagementSocket.on('events_exported', function(data) {
    showDataManagementToast('success', 'Events Exported', 
        `Exported ${data.count} events to ${data.filename}`);
});

dataManagementSocket.on('events_cleared', function(data) {
    showDataManagementToast('success', 'Events Cleared', 
        `Successfully cleared ${data.count} events`);
    
    // Update dashboard count to 0
    updateDashboardCount('events', 0, 'set');
    
    // Refresh events table on main dashboard and events pages
    refreshEventsTable();
    
    // Force refresh for any admin page
    forceRefreshIfNeeded('events', 'clear');
});

// Observations SocketIO Events
dataManagementSocket.on('observations_imported', function(data) {
    const title = data.success ? 'Observations Imported' : 'Observations Import Warning';
    const message = data.success 
        ? `Successfully imported ${data.count} observations`
        : `Imported ${data.count} observations with ${data.errors.length} errors`;
    
    showDataManagementToast(data.success ? 'success' : 'warning', title, message);
    
    // Update dashboard count if we're on the admin dashboard
    updateDashboardCount('observations', data.count, 'add');
    
    // Refresh observations table on main dashboard
    refreshObservationsTable();
    
    // Refresh the page if we're on the observations page
    if (window.location.pathname.includes('/admin/observations')) {
        setTimeout(() => location.reload(), 2000);
    }
});

dataManagementSocket.on('observations_exported', function(data) {
    showDataManagementToast('success', 'Observations Exported', 
        `Exported ${data.count} observations to ${data.filename}`);
});

dataManagementSocket.on('observations_cleared', function(data) {
    showDataManagementToast('success', 'Observations Cleared', 
        `Successfully cleared ${data.count} observations`);
    
    // Update dashboard count to 0
    updateDashboardCount('observations', 0, 'set');
    
    // Refresh observations table on main dashboard
    refreshObservationsTable();
    
    // Force refresh for any admin page
    forceRefreshIfNeeded('observations', 'clear');
});

// Status Reports SocketIO Events
dataManagementSocket.on('status_reports_imported', function(data) {
    const title = data.success ? 'Status Reports Imported' : 'Status Reports Import Warning';
    const message = data.success 
        ? `Successfully imported ${data.count} status reports`
        : `Imported ${data.count} status reports with ${data.errors.length} errors`;
    
    showDataManagementToast(data.success ? 'success' : 'warning', title, message);
    
    // Update dashboard count if we're on the admin dashboard
    updateDashboardCount('status_reports', data.count, 'add');
    
    // Refresh status reports table on status reports page
    refreshStatusReportsTable();
    
    // Refresh the page if we're on the admin status reports page
    if (window.location.pathname.includes('/admin/status-reports')) {
        setTimeout(() => location.reload(), 2000);
    }
});

dataManagementSocket.on('status_reports_exported', function(data) {
    showDataManagementToast('success', 'Status Reports Exported', 
        `Exported ${data.count} status reports to ${data.filename}`);
});

dataManagementSocket.on('status_reports_cleared', function(data) {
    showDataManagementToast('success', 'Status Reports Cleared', 
        `Successfully cleared ${data.count} status reports`);
    
    // Update dashboard count to 0
    updateDashboardCount('status_reports', 0, 'set');
    
    // Refresh status reports table on status reports page
    refreshStatusReportsTable();
    
    // Force refresh for any admin page
    forceRefreshIfNeeded('status_reports', 'clear');
});

// Connection status logging
dataManagementSocket.on('connect', function() {
    console.log('Data Management SocketIO connected');
});

dataManagementSocket.on('disconnect', function() {
    console.log('Data Management SocketIO disconnected');
});

dataManagementSocket.on('after connect', function(data) {
    console.log('Data Management SocketIO after connect:', data);
});
