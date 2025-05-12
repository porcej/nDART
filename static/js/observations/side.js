import { getCurrentTime, timeStringToDate, findLabel, pruneEmptyFields} from '../utils.js';
import { initObservationSocket } from './sio.js';

let observationsTable;
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
            name: 'location',
            type: 'select',
            options: window.ndart.assignment_options
        },
        {
            label: 'Category',
            name: 'category',
            type: 'select',
            options: window.ndart.observation_category_options
        }
    ]
});
 
const observationsCols = [
    { data: 'time' },
    { data: 'bib' },
    { data: 'location' },
    { data: 'category' }
];


// Observation DataTable shown in the page
observationsTable = new DataTable('#observations-table', {
    idSrc: 'id',
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

$(document).ready(function () {
    initObservationSocket();
});