// Main / parent / top level Editor
function getCurrentTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

function timeStringToDate(timeString) {
    const [hours, minutes] = timeString.split(':').map(Number);
    const date = new Date();

    date.setHours(hours, minutes, 0, 0); // Set hours, minutes, seconds, and milliseconds to 0

    return date;
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
    },
    rowCallback: function(row, data, index) {
        let warnTime = 10; // in minutes
        let alertTime = 15; // in minutes
        let notifiedTimeDiff = 0;
        let agencyArrivalTimeDiff = 0;
        const currentTime = new Date();
        if (data.agency_notified && !data.agency_arrival) {
            const notifiedDate = timeStringToDate(data.agency_notified);
            const notifiedTime = new Date(notifiedDate);
            notifiedTimeDiff = (currentTime - notifiedTime) / (1000 * 60); // difference in minutes
            
        } else if (data.agency_arrival && !data.resolved) {
            const agencyArrivalDate = timeStringToDate(data.agency_arrival);
            const agencyArrivalTime = new Date(agencyArrivalDate);
            agencyArrivalTimeDiff = (currentTime - agencyArrivalTime) / (1000 * 60); // difference in minutes 
        }
        console.log(`Notified: ${notifiedTimeDiff} Arrival: ${agencyArrivalTimeDiff}`);

        if ((notifiedTimeDiff > warnTime && notifiedTimeDiff < alertTime) || (agencyArrivalTimeDiff > warnTime && agencyArrivalTimeDiff < alertTime)) {
            console.log('here');
            $(row).removeClass('row-alert');
            $(row).addClass('row-warn');
        } else if (notifiedTimeDiff > alertTime || agencyArrivalTimeDiff > alertTime)  {
            console.log('here2');
            $(row).removeClass('row-warn');
            $(row).addClass('row-alert');
        } else {
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