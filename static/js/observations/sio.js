// File: static/js/observations/sio.js
import { socket } from '../utils.js';

export function initObservationSocket() {
    socket.on('new_observation', function(msg) {
        observationsTable.row.add(msg).draw(false);
    });

    socket.on('edit_observation', function(msg) {
        const rowIndex = observationsTable.row(`#${msg.id}`);
        // # Check if we have a this encounter
        if (rowIndex.any()) {
            rowIndex.data(msg).draw(false);
        }
    });

    socket.on('remove_observation', function(msg) {
        const rowIndex = observationsTable.row(`#${msg.id}`);
        // check if we have this encounter
        if (rowIndex.any()) {
            observationsTable.row(`#${msg.id}`).remove().draw(false);
        }
    });
}