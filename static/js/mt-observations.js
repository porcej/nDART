// Main / parent / top level Editor
function getCurrentTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

let observationsTable;
const observationsEditor = new DataTable.Editor({
    ajax: './api/observations/',
    table: '#observations-table',
    idSrc: 'id',
    fields: [
         {
            label: 'Time',
            name: 'time_in',
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
            name: 'location',
            type: 'select',
            options: [
                { label: 'MM 1', value: 'mm1' },
                { label: 'WP 7', value: 'wp7' },
                { label: 'Aid 4/6', value: 'aid46' }
            ]
        },
        {
            label: 'Category',
            name: 'category',
            type: 'select',
            options: [
                { label: 'Male', value: 'Male' },
                { label: 'Female', value: 'Female' },
                { label: 'Handcyle', value: 'Handcyle' }
                { label: 'Wheelchair', value: 'Wheelchair' },
                { label: 'Duo', value: 'Duo' },

            ]
        
        }     
    ]
});
 
const observations_cols = [
    {
            data: null,
            orderable: false,
            render: DataTable.render.select()
    },
    { data: 'time_in' },
    { data: 'bib' },
    { data: 'location' },
    { data: 'category' }
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
observationsTable = new DataTable('#observations-table', {
    idSrc: 'id',
    ajax: './api/observations/',
    columns: observations_cols,
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
                            'Are you sure you want to delete this ?' +
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
    // $('input[type="checkbox"].table-checkbox').on('click', function(observation) {
    //     observation.probservationDefault();
    //     observation.stopPropagation();
        
    //     return false;
    // });
    // socket = io.connect('//' + document.domain + ':' + location.port + '/api');
    // socket.on('after connect', function(msg) {console.log('Connected')});
    // socket.on('new_encounter', function(msg) { encounterTable.ajax.reload() });
    // socket.on('edit_encounter', function(msg) { encounterTable.ajax.reload() });
    // socket.on('edit_encounter', function(msg) { encounterTable.ajax.reload() });
    // socket.on('remove_encounter', function(msg) { encounterTable.ajax.reload() });

// });
