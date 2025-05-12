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
export function findLabel(options, value) {
    const item = options.find(opt => opt.value === value);
    return item ? item.label : null;
}

// Prune empty fields from an object
export function pruneEmptyFields(data) {
    Object.entries(data).forEach(([key, value]) => {
        if (value === null || value === '' || value === undefined) {
            delete data[key];
        }
    });
}

// Initialize the Socket.IO connection
const socket = io.connect('//' + document.domain + ':' + location.port + '/api');
socket.on('after connect', function(msg) { console.log('Connected to nDART Socket') });
socket.on('disconnect', function(msg) { console.log('Disconnected from nDART Socket') });
socket.on('connect_error', (error) => { console.error('Socket connection error:', error); });
export { socket };