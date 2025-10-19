import { getCurrentTime, timeStringToDate, findLabel, pruneEmptyFields, prepareOptions, handlePreSubmit } from './utils.js';
import { initSocketMessages } from './sio.js';

const DATA_TYPE = 'status';

let statusReportsTable;

// Make statusReportsTable globally accessible for SocketIO refresh
window.statusReportsTable = null;
let openStatusReportVals = null; 
const pendingStatusReportIds = new Set();
const selectedVolunteersForUpdate = new Set(); // Track which volunteers should be updated in staffer

const statusReportsEditor = new DataTable.Editor({
    ajax: {
        dataSrc: 'data',
        create: {
            url: './api/status_reports',
            type: 'POST', 
            contentType: 'application/json',
            data: function(d) { 
                return JSON.stringify(d);
            },
        },
        edit: {
            url: './api/status_reports/_id_',
            type: 'PUT',
            contentType: 'application/json',
            data: function (d) {
                return JSON.stringify(d);
            }
        },
        remove: {
            url: './api/status_reports/_id_',
            type: 'DELETE',
            contentType: 'application/json',
            data: function (d) {
                return 1;
            }
        }
    },
    table: '#status-reports-table',
    idSrc: 'id',
    fields: [
        {
            name: 'id',
            type: 'hidden',
            def: function() { return crypto.randomUUID(); }
        },
         {
            label: 'Time',
            name: 'time',
            type: 'datetime',
            def: getCurrentTime,
            format: 'HH:mm',
            fieldInfo: 'Start of report - 24 hour clock (HH:mm)'
        },
        {
            label: 'Reported By',
            name: 'reporter_id',
            type: 'selectize',
            def: null,
            options: prepareOptions('assignments'),
            opts: {
                valueField: 'value',
                labelField: 'label',
                searchField: ['label'],         // ← ensure searching works
                create: false,
                persist: false,                          // ← don’t cache across opens
                preload: true,
                openOnFocus: true,
                dropdownParent: 'body',                  // ← avoids clipping/focus issues
                onDropdownOpen() {                       // ← clear any stale query
                  this.setTextboxValue('');
                  this.refreshOptions(false);
                },
                sortField: {
                    field: 'label',
                    direction: 'asc'
                }
            },
        },
        {
            label: 'Status',
            name: 'status_id',
            type: 'selectize',
            def: null,
            options: prepareOptions('station_statuses'),
            opts: {
                valueField: 'value',
                labelField: 'label',
                searchField: ['label'],         // ← ensure searching works
                create: false,
                persist: false,                          // ← don’t cache across opens
                preload: true,
                openOnFocus: true,
                dropdownParent: 'body',                  // ← avoids clipping/focus issues
                onDropdownOpen() {                       // ← clear any stale query
                  this.setTextboxValue('');
                  this.refreshOptions(false);
                },
                sortField: {
                    field: 'label',
                    direction: 'asc'
                }
            },
        },
        {
            label: 'Notes',
            name: 'comment',
            type: 'textarea',
            fieldInfo: 'Notes or other pertinent information related to this report.'
        },
        {
            label: '',
            name: 'volunteers_info',
            type: 'readonly',
            def: ''
        }
    ]
});
 
const statusReports_cols = [
    {
            data: null,
            orderable: false,
            render: DataTable.render.select()
    },
    { data: 'time' },
    { 
        data: 'reporter_id',
        render: function(data) {
            return findLabel('assignments', data);
        }
    },
    { 
        data: 'status_id',
        render: function(data) {
            return findLabel('station_statuses', data);
        }
    },
    { data: 'comment' }
];

// Encounters DataTable shown in the page
statusReportsTable = new DataTable('#status-reports-table', {
    idSrc: 'id',
    rowId: function(a) {
        return 'status_report_' + a.id;
    },
    ajax: './api/status_reports/',
    order: [[1, 'desc']],
    columns: statusReports_cols,
    layout: {
        topStart: {
            buttons: [
                { extend: 'create', editor: statusReportsEditor },
                { extend: 'edit', editor: statusReportsEditor },
                { 
                    extend: 'remove', editor: statusReportsEditor,
                    formMessage: function (e, dt) {
                        let row = dt
                            .rows(e.modifier())
                            .data()[0]
                        return ('Are you sure you want to delete this status report?');
                    }
                }
            ]
        }
    },
    select: {
        style: 'os',
        selector: 'td:first-child'
    }
});

// Make statusReportsTable globally accessible for SocketIO refresh
window.statusReportsTable = statusReportsTable;

statusReportsEditor.on('open', function() {
    openStatusReportVals = statusReportsEditor.get();
    const $wrap = $(statusReportsEditor.displayNode());
    if (!$wrap.find('.key-hint').length) {
        $('.DTE_Footer').prepend('<div class="key-hint">Tip: Use <kbd>Tab</kbd> to move between fields. Press <kbd>Enter</kbd> to submit.</div>');
    }
    
    // Add volunteers display container if it doesn't exist
    if (!$wrap.find('.volunteers-display').length) {
        const reporterField = statusReportsEditor.field('reporter_id');
        const fieldNode = $(reporterField.node());
        fieldNode.after('<div class="volunteers-display mt-2" id="volunteersDisplay" style="display:none;"></div>');
    }
    
    // Load volunteers for current reporter if one is selected
    updateVolunteersDisplay();
});

// Function to update volunteers display
async function updateVolunteersDisplay() {
    const reporterId = statusReportsEditor.field('reporter_id').val();
    const displayDiv = document.getElementById('volunteersDisplay');
    
    if (!displayDiv) return;
    
    if (!reporterId) {
        displayDiv.style.display = 'none';
        displayDiv.innerHTML = '';
        return;
    }
    
    try {
        const response = await fetch(`./api/staffer-volunteers/by-assignment/${reporterId}`);
        
        if (!response.ok) {
            displayDiv.style.display = 'none';
            return;
        }
        
        const result = await response.json();
        const volunteers = result.data || [];
        
        if (volunteers.length === 0) {
            displayDiv.style.display = 'none';
            return;
        }
        
        // Build volunteer table with checkboxes (all checked by default)
        const volunteerRows = volunteers.map(v => {
            // Add to selected set by default
            selectedVolunteersForUpdate.add(v.callsign);
            
            return `
            <tr>
                <td>
                    <div class="form-check">
                        <input class="form-check-input volunteer-update-checkbox" 
                               type="checkbox" 
                               value="${v.callsign}" 
                               id="vol_${v.callsign.replace(/[^a-zA-Z0-9]/g, '_')}"
                               data-callsign="${v.callsign}"
                               data-name="${v.name || ''}"
                               checked>
                        <label class="form-check-label" for="vol_${v.callsign.replace(/[^a-zA-Z0-9]/g, '_')}">
                            Update Status
                        </label>
                    </div>
                </td>
                <td>${v.name || '-'}</td>
                <td><strong>${v.callsign}</strong></td>
                <td>${v.phone_number ? `<a href="tel:${v.phone_number}">${v.phone_number}</a>` : '-'}</td>
                <td>${v.email ? `<a href="mailto:${v.email}">${v.email}</a>` : '-'}</td>
            </tr>
            `;
        }).join('');
        
        displayDiv.innerHTML = `
            <div class="card border-info">
                <div class="card-header bg-info text-white py-1 d-flex justify-content-between align-items-center">
                    <small><strong>Volunteers at this assignment (${volunteers.length})</strong></small>
                    <small class="text-white-50">Check boxes to update their status in staffer database</small>
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-sm table-hover mb-0">
                            <thead>
                                <tr>
                                    <th width="120">Update</th>
                                    <th>Name</th>
                                    <th>Callsign</th>
                                    <th>Phone</th>
                                    <th>Email</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${volunteerRows}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        displayDiv.style.display = 'block';
        
        // Attach checkbox event listeners
        displayDiv.querySelectorAll('.volunteer-update-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', function() {
                if (this.checked) {
                    selectedVolunteersForUpdate.add(this.dataset.callsign);
                } else {
                    selectedVolunteersForUpdate.delete(this.dataset.callsign);
                }
            });
        });
        
    } catch (error) {
        console.error('Error fetching volunteers:', error);
        displayDiv.style.display = 'none';
    }
}

// Update volunteers when reporter changes
statusReportsEditor.field('reporter_id').input().on('change', function() {
    updateVolunteersDisplay();
});

statusReportsEditor.on('postCreate', function(e, data, action) {
    pendingStatusReportIds.delete(data.id);
});

// Pre-submit report handler: prune data and remove empty fields
statusReportsEditor.on('preSubmit', function(e, data, action) {
    handlePreSubmit(e, data, action, openStatusReportVals);
    pendingStatusReportIds.add(openStatusReportVals.id);
});

// After successful submission, update staffer for selected volunteers
statusReportsEditor.on('submitSuccess', async function(e, json, data, action) {
    if (selectedVolunteersForUpdate.size === 0) {
        return; // No volunteers selected for update
    }
    
    // Get the status that was just reported
    const statusId = statusReportsEditor.field('status_id').val();
    const reporterId = statusReportsEditor.field('reporter_id').val();
    
    if (!statusId || !reporterId) {
        return;
    }
    
    // Get the status name
    const statusName = findLabel('station_statuses', statusId);
    
    // Update each selected volunteer in staffer
    const updatePromises = Array.from(selectedVolunteersForUpdate).map(async callsign => {
        try {
            const response = await fetch('./api/staffer-volunteers/checkin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    callsign: callsign,
                    status: statusName
                })
            });
            
            if (!response.ok) {
                console.error(`Failed to update staffer for ${callsign}:`, await response.text());
            }
        } catch (error) {
            console.error(`Error updating staffer for ${callsign}:`, error);
        }
    });
    
    // Wait for all updates to complete
    await Promise.all(updatePromises);
    
    // Clear the selection
    selectedVolunteersForUpdate.clear();
});


initSocketMessages(statusReportsTable, DATA_TYPE, pendingStatusReportIds);