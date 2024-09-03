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
                { label: 'Handcycle', value: 'Handcycle' },
                { label: 'Wheelchair', value: 'Wheelchair' },
                { label: 'Duo', value: 'Duo' },

            ]
        
        }     
    ]
});
 
const observationsCols = [
    {
            data: null,
            orderable: false,
            render: DataTable.render.select()
    },
    { data: 'time' },
    { data: 'bib' },
    { data: 'location' },
    { data: 'category' }
];


// Encounters DataTable shown in the page
observationsTable = new DataTable('#observations-table', {
    idSrc: 'id',
    ajax: './api/observations/',
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

