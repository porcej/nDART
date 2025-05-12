import { getCurrentTime, timeStringToDate, findLabel, pruneEmptyFields} from '../utils.js';
import { initEventSocket } from './sio.js';

const WARNTIME = 10; // in minutes
const ALERTTIME = 15; // in minutes

let eventsTable;
let currentEventId = null;
let openEventsVals = null;

const eventsEditor = new DataTable.Editor({
    // ajax: './api/events/',
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
            type: 'select',
            options: window.ndart.assignment_options
        },
        {
            label: 'Agency',
            name: 'agency_id',
            type: 'select',
            options: window.ndart.agency_options
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
            return findLabel(window.ndart.assignment_options, data);
        }
    },
    { 
        data: 'agency_id',
        render: function(data) {
            return findLabel(window.ndart.agency_options, data);
        }
    },
    { data: 'agency_notified' },
    { data: 'agency_arrival' },
    { data: 'resolved' },
    { data: 'notes' }
];

// Encounters DataTable shown in the page
eventsTable = new DataTable('#events-table', {
    idSrc: 'id',
    rowId: function(a) {
        return 'event_' + a.id;
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
                console.log('here');
                $(row).removeClass('row-alert');
                $(row).addClass('row-warn');
            } else if (notifiedTimeDiff > ALERTTIME || agencyArrivalTimeDiff > ALERTTIME)  {
                console.log('here2');
                $(row).removeClass('row-warn');
                $(row).addClass('row-alert');
            } else {
                $(row).removeClass('row-alert');
                $(row).removeClass('row-warn');
            }   
        } else{
            $(row).removeClass('row-alert');
            $(row).removeClass('row-warn');
        }
    }
});

// Activate an inline edit on click of a table cell
eventsTable.on('click', 'tbody td:not(:first-child)', function (e) {
    eventsEditor.bubble(this, {
        buttons: {
            label: '&gt;',
            fn: function () {
                this.submit();
            }
        }
    });
});

eventsEditor.on('open', function() {
    openEventsVals = eventsEditor.get();
    currentEventId = openEventsVals.id;
});


// Pre-submit event handler: prune data and remove empty fields
eventsEditor.on('preSubmit', function(e, data, action) {

    
    if (action === 'create') {
        // Remove empty fields from data for new event
        Object.entries(data.data).forEach(([index, event]) => {
            // Remove empty data sets
            pruneEmptyFields(event);
        });
    } else if (action === 'edit') {
        // Remove fields that have not changed for edit event
        Object.entries(data.data).forEach(([index, event]) => {
            Object.entries(event).forEach(([key, value]) => {
                if (value === openEventsVals[key]) {
                    delete data.data[index][key];
                }
            });
        });
    }
});


$(document).ready(function () {
    initEventSocket();
});