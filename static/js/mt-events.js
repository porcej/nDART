// Main / parent / top level Editor
function getCurrentTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

let eventsTable;
const eventsEditor = new DataTable.Editor({
    ajax: './api/events/',
    table: '#events-table',
    idSrc: 'id',
    fields: [
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
            name: 'reporter',
            type: 'select',
            options: [
                { label: 'MM 1', value: 'mm1' },
                { label: 'WP 7', value: 'wp7' },
                { label: 'Aid 4/6', value: 'aid46' }
            ]
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
    { data: 'reporter' },
    { data: 'agency_notified' },
    { data: 'agency_arrival' },
    { data: 'resolved' },
    { data: 'notes' }
];

// const manager_cols = [
//     { data: 'bib' },
//     { data: 'first_name' },
//     { data: 'last_name' },
//     { data: 'sex' },
//     { 
//         data: 'participant',
//         render: (data, type, row) =>
//             type === 'display'
//                 ? '<input type="checkbox" class="editor-participant table-checkbox">'
//                 : data,
//         className: 'dt-body-center'
//     },
//     { 
//         data: 'active_duty',
//         render: (data, type, row) =>
//             type === 'display'
//                 ? '<input type="checkbox" class="editor-active-duty table-checkbox">'
//                 : data,
//         className: 'dt-body-center'
//     },
//     { data: 'time_in', },
//     { data: 'time_out', },
//     { data: 'presentation', },
//     { data: 'disposition' },
//     { data: 'aid_station' }
// ];

// Encounters DataTable shown in the page
eventsTable = new DataTable('#events-table', {
    idSrc: 'id',
    ajax: './api/events/',
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
    }
});

// Activate an inline edit on click of a table cell
eventsTable.on('click', 'tbody td:not(:first-child)', function (e) {
    eventsEditor.inline(this);
});

// Encounters DataTable shown in the page
// let participantsTable = new DataTable('#participants-table', {
//     idSrc: 'id',
//     ajax: './api/participants/',
//     columns: [
//         { data: 'bib' },
//         { data: 'first_name' },
//         { data: 'last_name' },
//         { data: 'age', searchable: false, targets: 0 },
//         { data: 'sex', },
//     ],
//     select: {
//         style: 'single'
//     }
// });


// $(document).ready(function () {   
    // let table = $('#participants-table').DataTable();
    // $('#participants-table tbody').on('click', 'tr', function () {
    //     const row = participantsTable.row(this).data();
    //     encounterEditor
    //         .create()
    //         .title(`New Encounter with ${row.last_name}, ${row.first_name}`);
    //     encounterEditor.field('bib').set(row.bib);
    //     encounterEditor.field('first_name').set(row.first_name);
    //     encounterEditor.field('last_name').set(row.last_name);
    //     encounterEditor.field('age').set(row.age);
    //     encounterEditor.field('sex').set(row.sex);
    //     encounterEditor.field('participant').set(1);
    //     encounterEditor.field('active_duty').set(row.active_duty);
    //     encounterEditor.buttons('Create')
    //         .open();
    // });
    // $('input[type="checkbox"].table-checkbox').on('click', function(event) {
    //     event.preventDefault();
    //     event.stopPropagation();
        
    //     return false;
    // });
    // socket = io.connect('//' + document.domain + ':' + location.port + '/api');
    // socket.on('after connect', function(msg) {console.log('Connected')});
    // socket.on('new_encounter', function(msg) { encounterTable.ajax.reload() });
    // socket.on('edit_encounter', function(msg) { encounterTable.ajax.reload() });
    // socket.on('edit_encounter', function(msg) { encounterTable.ajax.reload() });
    // socket.on('remove_encounter', function(msg) { encounterTable.ajax.reload() });

// });
