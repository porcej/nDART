// File: static/js/sio.js

// Initialize the Socket.IO connection
const socket = io.connect('//' + document.domain + ':' + location.port + '/api');
socket.on('after connect', function(msg) { console.log('Connected to nDART Socket') });
socket.on('disconnect', function(msg) { console.log('Disconnected from nDART Socket') });
socket.on('connect_error', (error) => { console.error('Socket connection error:', error); });
export { socket };


export function initSocketMessages(tbl, msg_type, pendingIds, table_prefix = '') {
    socket.on(`new_${msg_type}`, msg => {
        if (!pendingIds.has(msg.id)) {
            const row = tbl.row(`#${table_prefix}${msg_type}_${msg.id}`);
            if (!row.any()) tbl.row.add(msg).draw(false);
        }
    });

    socket.on(`edit_${msg_type}`, msg => {
        const row = tbl.row(`#${table_prefix}${msg_type}_${msg.id}`);
        if (row.any()) row.data(msg).draw(false);
    });

    socket.on(`remove_${msg_type}`, msg => {
        const row = tbl.row(`#${table_prefix}${msg_type}_${msg.id}`);
        if (row.any()) tbl.row(`#${table_prefix}${msg_type}_${msg.id}`).remove().draw(false);
    });
}