// File: static/js/events/sio.js
import { socket } from '../utils.js';

export function initEventSocket() {
    socket.on('new_event', msg => {
        const row = eventsTable.row(`#event_${msg.id}`);
        if (!row.any()) eventsTable.row.add(msg).draw(false);
    });

    socket.on('edit_event', msg => {
        const row = eventsTable.row(`#event_${msg.id}`);
        if (row.any()) row.data(msg).draw(false);
    });

    socket.on('remove_event', msg => {
        const row = eventsTable.row(`#event_${msg.id}`);
        if (row.any()) eventsTable.row(`#event_${msg.id}`).remove().draw(false);
    });
}