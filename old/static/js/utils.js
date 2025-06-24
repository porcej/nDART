// File: utils.js

// Get the current time in HH:mm format
export function getCurrentTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

// Convert a time string (HH:mm) to a Date object
export function timeStringToDate(timeString) {
    const [hours, minutes] = timeString.split(':').map(Number);
    const date = new Date();

    date.setHours(hours, minutes, 0, 0); // Set hours, minutes, seconds, and milliseconds to 0

    return date;
}

// Find the label for a given value in an array of options
export function findLabel(field, value) {
    const item = window.ndart.form_options[field].find(opt => opt.value === value);
    return item ? item.label : null;
}

// Prepare options for a select element based on form options and a field name
export function prepareOptions(field) {
    return [{ label: '', value: '' }, ...window.ndart.form_options[field]];
}

// Prune empty fields from an object
export function pruneEmptyFields(data) {
    Object.entries(data).forEach(([key, value]) => {
        if (value === null || value === '' || value === undefined) {
            delete data[key];
        }
    });
}

// Shared preSubmit handler for DataTables Editor
export function handlePreSubmit(e, data, action, openVals = null) {
    if (action === 'create') {
        // Remove empty fields from data for new records
        Object.entries(data.data).forEach(([index, record]) => {
            pruneEmptyFields(record);
        });
    } else if (action === 'edit' && openVals) {
        // Remove fields that have not changed for edit
        Object.entries(data.data).forEach(([index, record]) => {
            Object.entries(record).forEach(([key, value]) => {
                if (value === openVals[key]) {
                    delete data.data[index][key];
                }
            });
        });
    }
}