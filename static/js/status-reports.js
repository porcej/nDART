import { getCurrentTime, timeStringToDate, findLabel, pruneEmptyFields, prepareOptions, handlePreSubmit } from './utils.js';
import { initSocketMessages } from './sio.js';

const DATA_TYPE = 'status';

let statusReportsTable;
let openStatusReportVals = null; 
const pendingStatusReportIds = new Set();

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

statusReportsEditor.on('open', function() {
    openStatusReportVals = statusReportsEditor.get();
    const $wrap = $(statusReportsEditor.displayNode());
    if ($wrap.find('.key-hint').length) return;
    $('.DTE_Footer').prepend('<div class="key-hint">Tip: Use <kbd>Tab</kbd> to move between fields. Press <kbd>Enter</kbd> to submit.</div>');
});

statusReportsEditor.on('postCreate', function(e, data, action) {
    pendingStatusReportIds.delete(data.id);
});

// Pre-submit report handler: prune data and remove empty fields
statusReportsEditor.on('preSubmit', function(e, data, action) {
    handlePreSubmit(e, data, action, openStatusReportVals);
    pendingStatusReportIds.add(openStatusReportVals.id);
});


initSocketMessages(statusReportsTable, DATA_TYPE, pendingStatusReportIds);