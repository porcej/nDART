import { getCurrentTime, timeStringToDate, findLabel, prepareOptions, handlePreSubmit, buildFilterDropDown } from './utils.js';
import { initSocketMessages } from './sio.js';

const WARNTIME = 10; // in minutes
const ALERTTIME = 15; // in minutes
const DATA_TYPE = 'event';


let eventsTable;
let openEventsVals = null;
const pendingEventIds = new Set();

// Cleanup timeout for pending IDs (safety net)
const PENDING_CLEANUP_TIMEOUT = 30000; // 30 seconds
const pendingTimeouts = new Map();

buildFilterDropDown('reporterFilter', 'assignments', 3);
buildFilterDropDown('agencyFilter', 'agencies', 5);


const resolvedRadioAll = document.getElementById('resolvedRadioAll');
if (resolvedRadioAll) {
    resolvedRadioAll.addEventListener('change', function() {
        const colIndex = 8;
        eventsTable.column(colIndex).search('').draw();
    });
}

const resolvedRadioResolved = document.getElementById('resolvedRadioResolved');
if (resolvedRadioResolved) {
    resolvedRadioResolved.addEventListener('change', function() {
        const colIndex = 8;
        eventsTable.column(colIndex).search('^.+$', true, false).draw();
    });
}

const resolvedRadioInProgress = document.getElementById('resolvedRadioInProgress');
if (resolvedRadioInProgress) {
    resolvedRadioInProgress.addEventListener('change', function() {
        const colIndex = 8;
        eventsTable.column(colIndex).search('^$', true, false).draw();
    });
}

const eventsEditor = new DataTable.Editor({
    ajax: {
        url: './api/events/',
        dataSrc: 'data',
        create: {
            url: './api/events',
            type: 'POST',
            contentType: 'application/json',
            data: function(d) { 
                return JSON.stringify(d);
            },
        },
        edit: {
            url: './api/events/_id_',
            type: 'PUT',
            contentType: 'application/json',
            data: function (d) {
                return JSON.stringify(d);
            }
        },
        remove: {
            url: './api/events/_id_',
            type: 'DELETE',
            contentType: 'application/json',
            data: function (d) {
                return 1;
            }
        }
    },
    table: '#events-table',
    idSrc: 'id',
    fields: [
        {
            name: 'id',
            type: 'hidden',
            def: function() { return crypto.randomUUID(); }
        },
         {
            label: 'Time',
            name: 'time_in',
            type: 'datetime',
            def: getCurrentTime,
            format: 'HH:mm',
            fieldInfo: 'Start of event - 24 hour clock (HH:mm)'
        },
        {
            label: 'Bib #',
            name: 'bib'
        },
        {
            label: 'Location',
            name: 'location'
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
            label: 'Agency',
            name: 'agency_id',
            type: 'selectize',
            def: null,
            options: prepareOptions('agencies'),
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
            label: 'Agency Notified',
            name: 'agency_notified',
            type: 'datetime',
            format: 'HH:mm',
            fieldInfo: 'Time Agency Notified - 24 hour clock (HH:mm)'
        },
        {
            label: 'Agency Arrival',
            name: 'agency_arrival',
            type: 'datetime',
            format: 'HH:mm',
            fieldInfo: 'Time of Agency Arrival - 24 hour clock (HH:mm)'
        },
        {
            label: 'Resolved',
            name: 'resolved',
            type: 'datetime',
            format: 'HH:mm',
            fieldInfo: 'Time of event resolution - 24 hour clock (HH:mm)'
        },
        {
            label: 'Notes',
            name: 'notes',
            type: 'textarea',
            fieldInfo: 'Notes or other pertinent information related to this event.'
        }     
    ]
});

let filterToolbar = document.createElement('div');
filterToolbar.innerHTML = '<b>Custom tool bar! Text/images etc.</b>';

 
const events_cols = [
    {
            data: null,
            orderable: false,
            render: DataTable.render.select()
    },
    { data: 'time_in' },
    { data: 'bib' },
    { data: 'location' },
    { 
        data: 'reporter_id',
        render: function(data) {
            return findLabel('assignments', data);
        }
    },
    { 
        data: 'agency_id',
        render: function(data) {
            return findLabel('agencies', data);
        }
    },
    { data: 'agency_notified' },
    { data: 'agency_arrival' },
    { data: 'resolved' },
    { data: 'notes' }
];

// Encounters DataTable shown in the page
eventsTable = new DataTable('#events-table', {
    responsive: true,
    stateSave: true,
    idSrc: 'id',
    rowId: function(a) {
        return `${DATA_TYPE}_${a.id}`;
    },
    ajax: './api/events/',
    order: [[1, 'desc']],
    columns: events_cols,
    layout: {
        topStart: {
            buttons: [
                { extend: 'create', editor: eventsEditor },
                { extend: 'edit', editor: eventsEditor },
                { 
                    extend: 'remove', editor: eventsEditor,
                    formMessage: function (e, dt) {
                        let row = dt
                            .rows(e.modifier())
                            .data()[0]
                        return (
                            'Are you sure you want to delete this event?' +
                            `<li> ${row['time']} ${row['bib'] != "" ? `with bib # ${row['bib']}` : ''}</li>`
                        );
                    }
                }
            ]
        }
    },
    select: {
        style: 'os',
        selector: 'td:first-child'
    },
    rowCallback: function(row, data, index) {

        let notifiedTimeDiff = 0;
        let agencyArrivalTimeDiff = 0;
        const currentTime = new Date();

        // Only alert/warn if Agency Notified has been set
        if (data.agency_notified) {
            if (!data.agency_arrival && !data.resolved) {
                const notifiedDate = timeStringToDate(data.agency_notified);
                const notifiedTime = new Date(notifiedDate);
                notifiedTimeDiff = (currentTime - notifiedTime) / (1000 * 60); // difference in minutes
            } else if (!data.resolved) {
                const agencyArrivalDate = timeStringToDate(data.agency_arrival);
                const agencyArrivalTime = new Date(agencyArrivalDate);
                agencyArrivalTimeDiff = (currentTime - agencyArrivalTime) / (1000 * 60); // difference in minutes 
            }

            if ((notifiedTimeDiff > WARNTIME && notifiedTimeDiff < ALERTTIME) || (agencyArrivalTimeDiff > WARNTIME && agencyArrivalTimeDiff < ALERTTIME)) {
                $(row).removeClass('table-danger');
                $(row).addClass('table-warning');
            } else if (notifiedTimeDiff > ALERTTIME || agencyArrivalTimeDiff > ALERTTIME)  {
                $(row).removeClass('table-warning');
                $(row).addClass('table-danger');
            } else {
                $(row).removeClass('table-danger');
                $(row).removeClass('table-warning');
            }   
        } else{
            $(row).removeClass('table-danger');
            $(row).removeClass('table-warning');
        }
    }
});

// Activate the bubble editor on click of a table cell
eventsTable.on('click', 'tbody td:not(:first-child)', function (e) {
    eventsEditor.bubble(this);
});

eventsEditor.on('open', function() {
    openEventsVals = eventsEditor.get();
});

eventsEditor.on('postCreate', function (e, json, data) {
    if (data && data.id) {
        pendingEventIds.delete(data.id);
    }
});

// Clean up on successful edit
eventsEditor.on('postEdit', function (e, json, data) {
    if (data && data.id) {
        pendingEventIds.delete(data.id);
        clearPendingTimeout(data.id);
    }
});

// Clean up on successful remove
eventsEditor.on('postRemove', function (e, json, data) {
    if (data && data.id) {
        pendingEventIds.delete(data.id);
        clearPendingTimeout(data.id);
    }
});

// Clean up on editor close (cancelled operations)
eventsEditor.on('close', function() {
    if (openEventsVals && openEventsVals.id) {
        pendingEventIds.delete(openEventsVals.id);
        clearPendingTimeout(openEventsVals.id);
    }
    openEventsVals = null;
});

// Clean up on errors
eventsEditor.on('error', function(e, json, data) {
    if (openEventsVals && openEventsVals.id) {
        pendingEventIds.delete(openEventsVals.id);
        clearPendingTimeout(openEventsVals.id);
    }
    openEventsVals = null;
});

// Helper function to clear pending timeout
function clearPendingTimeout(id) {
    if (pendingTimeouts.has(id)) {
        clearTimeout(pendingTimeouts.get(id));
        pendingTimeouts.delete(id);
    }
}

// Use the shared preSubmit handler
eventsEditor.on('preSubmit', function(e, data, action) {
    handlePreSubmit(e, data, action, openEventsVals);
    if (openEventsVals && openEventsVals.id) {
        pendingEventIds.add(openEventsVals.id);
        
        // Set timeout to clean up if operation doesn't complete
        const timeoutId = setTimeout(() => {
            pendingEventIds.delete(openEventsVals.id);
            pendingTimeouts.delete(openEventsVals.id);
            console.warn(`Cleaned up pending event ID ${openEventsVals.id} due to timeout`);
        }, PENDING_CLEANUP_TIMEOUT);
        
        pendingTimeouts.set(openEventsVals.id, timeoutId);
    }
});

initSocketMessages(eventsTable, DATA_TYPE, pendingEventIds);