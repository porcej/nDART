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
                { label: 'MMO', value: 'MMO' },
                { label: 'MM1', value: 'MM1' },
                { label: 'MM2', value: 'MM2' },
                { label: 'WP1', value: 'WP1' },
                { label: 'MM2.7', value: 'MM2.7' },
                { label: 'MM3.6', value: 'MM3.6' },
                { label: 'MM4', value: 'MM4' },
                { label: 'MM4.5', value: 'MM4.5' },
                { label: 'MM50.1', value: 'MM50.1' },
                { label: 'MM50.2', value: 'MM50.2' },
                { label: 'AS50', value: 'AS50' },
                { label: 'MM50.3', value: 'MM50.3' },
                { label: 'AS1', value: 'AS1' },
                { label: 'WP2', value: 'WP2' },
                { label: 'MM5', value: 'MM5' },
                { label: 'MM5.5', value: 'MM5.5' },
                { label: 'MM6', value: 'MM6' },
                { label: 'WP3', value: 'WP3' },
                { label: 'AS2/3', value: 'AS2/3' },
                { label: 'MM7', value: 'MM7' },
                { label: 'MM7.5', value: 'MM7.5' },
                { label: 'MM8', value: 'MM8' },
                { label: 'MM9', value: 'MM9' },
                { label: 'MM10', value: 'MM10' },
                { label: 'WP5/7', value: 'WP5/7' },
                { label: 'AS4/6', value: 'AS4/6' },
                { label: 'MM11', value: 'MM11' },
                { label: 'MM11.5', value: 'MM11.5' },
                { label: 'MM12', value: 'MM12' },
                { label: 'MM12.5', value: 'MM12.5' },
                { label: 'MM13', value: 'MM13' },
                { label: 'MM13.5', value: 'MM13.5' },
                { label: 'WP6', value: 'WP6' },
                { label: 'MM14', value: 'MM14' },
                { label: 'MM14.5', value: 'MM14.5' },
                { label: 'MM15', value: 'MM15' },
                { label: 'MM15.5', value: 'MM15.5' },
                { label: 'MM16', value: 'MM16' },
                { label: 'MM16.5', value: 'MM16.5' },
                { label: 'MM17', value: 'MM17' },
                { label: 'AS7', value: 'AS7' },
                { label: 'MM17.5', value: 'MM17.5' },
                { label: 'MM18', value: 'MM18' },
                { label: 'MM18.5', value: 'MM18.5' },
                { label: 'FS1', value: 'FS1' },
                { label: 'MM19', value: 'MM19' },
                { label: 'AS8', value: 'AS8' },
                { label: 'MM19.5', value: 'MM19.5' },
                { label: 'MM20', value: 'MM20' },
                { label: 'MM20.5', value: 'MM20.5' },
                { label: 'MM21', value: 'MM21' },
                { label: 'MM21.5', value: 'MM21.5' },
                { label: 'AS9', value: 'AS9' },
                { label: 'WP10', value: 'WP10' },
                { label: 'MM22', value: 'MM22' },
                { label: 'MM22.5', value: 'MM22.5' },
                { label: 'MM22.7', value: 'MM22.7' },
                { label: 'MM23', value: 'MM23' },
                { label: 'MM23.5', value: 'MM23.5' },
                { label: 'FS2', value: 'FS2' },
                { label: 'WP11', value: 'WP11' },
                { label: 'AS10', value: 'AS10' },
                { label: 'MM24', value: 'MM24' },
                { label: 'MM24.5', value: 'MM24.5' },
                { label: 'WP12', value: 'WP12' },
                { label: 'MM25', value: 'MM25' },
                { label: 'MM25.5', value: 'MM25.5' },
                { label: 'MM26', value: 'MM26' },
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


// Observation DataTable shown in the page
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

