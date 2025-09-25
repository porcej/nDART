import { getCurrentTime, timeStringToDate, findLabel, pruneEmptyFields, prepareOptions, handlePreSubmit} from './utils.js';
import { initSocketMessages } from './sio.js';

const DATA_TYPE = 'observation';
const TABLE_PREFIX = 'side_';
let observationsTable;
let openObservationsVals = null;
const pendingObservationIds = new Set();

const observationsEditor = new DataTable.Editor({
    // ajax: './api/observations/',
    ajax: {
        url: './api/observations/',
        dataSrc: 'data',
        create: {
            url: './api/observations',
            type: 'POST',
            contentType: 'application/json',
            data: function(d) { 
                return JSON.stringify(d);
            },
        },
        edit: {
            url: './api/observations/_id_',
            type: 'PUT',
            contentType: 'application/json',
            data: function (d) {
                return JSON.stringify(d);
            }
        },
        remove: {
            url: './api/observations/_id_',
            type: 'DELETE',
            contentType: 'application/json',
            data: function (d) {
                return 1;
            }
        }
    },
    table: '#observations-table',
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
            fieldInfo: 'Start of observation - 24 hour clock (HH:mm)'
        },
        {
            label: 'Bib #',
            name: 'bib'
        },
        {
            label: 'Location',
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
            }
        },
        {
            label: 'Category',
            name: 'category_id',
            type: 'selectize',
            def: null,
            options: prepareOptions('observations_categories'),
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
            }
        }
    ]
});
 
const observationsCols = [
    { data: 'time' },
    { data: 'bib' },
    { data: 'reporter_id',
        render: function(data) {
            return findLabel('assignments', data);
        }
    },
    { data: 'category_id',
        render: function(data) {
            return findLabel('observations_categories', data);
        }
    }
];


// Observation DataTable shown in the page
observationsTable = new DataTable('#observations-table', {
    stateSave: true,
    idSrc: 'id',
    rowId: function(a) {
        return `${TABLE_PREFIX}${DATA_TYPE}_${a.id}`;
    },
    ajax: './api/observations/',
    order: [[0, 'desc']],
    columns: observationsCols,
    layout: {
        topStart: {
            buttons: [
                { extend: 'create', editor: observationsEditor },
                { extend: 'edit', editor: observationsEditor },
                { 
                    extend: 'remove', editor: observationsEditor,
                    formMessage: function (e, dt) {
                        let row = dt
                            .rows(e.modifier())
                            .data()[0]
                        return (
                            'Are you sure you want to delete this observation?' +
                            `<li> ${row['time']} ${row['bib'] != "" ? `with bib # ${row['bib']}` : ''}</li>`
                        );
                    }
                }
            ]
        }
    },
    select: {
        style: 'single'
    }
});

observationsEditor.on('open', function() {
    openObservationsVals = observationsEditor.get();
    const $wrap = $(observationsEditor.displayNode());
    if ($wrap.find('.key-hint').length) return;
    $('.DTE_Footer').prepend('<div class="key-hint">Tip: Use <kbd>Tab</kbd> to move between fields. Press <kbd>Enter</kbd> to submit.</div>');
});

observationsEditor.on('postCreate', function (e, json, data) {
    if (data && data.id) {
        console.log(`Post Create ID: ${data.id} being removed from pending:`, pendingObservationIds);
        pendingObservationIds.delete(data.id);
    }
});

observationsEditor.on('preSubmit', function(e, data, action) {
    // let openObservationsVals = observationsEditor.get();
    handlePreSubmit(e, data, action, openObservationsVals);
    pendingObservationIds.add(openObservationsVals.id);
});

initSocketMessages(observationsTable, DATA_TYPE, pendingObservationIds, TABLE_PREFIX);
