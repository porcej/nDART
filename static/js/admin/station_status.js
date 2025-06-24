import { initConfig, sendRequest, showToast, searchTable, toolbar, initToggleActive, initButtons } from './table-tools.js';

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
    // Constants and modal initialization
    const tblId = 'stationStatusTable';
    const formModalId = 'stationStatusModal';
    const importModalId = 'importModal';
    const deleteModalId = 'deleteModal';
    
    const table = document.getElementById(tblId);
    if (!table) return;

    // Initialize configuration
    initConfig({
        tblId: tblId,
        importModal: new bootstrap.Modal(document.getElementById(importModalId)),
        formModal: new bootstrap.Modal(document.getElementById(formModalId)),
        deleteModal: new bootstrap.Modal(document.getElementById(deleteModalId))
    });

    // Initialize table tools
    searchTable();
    toolbar();
    initToggleActive();
    initButtons('Create Station Status', 'Edit Station Status', resetStationStatusForm, loadStationStatusData, processStationStatusForm);

    // Utility: Reset User Form
    function resetStationStatusForm() {
        const form = document.getElementById('stationStatusForm');
        if (!form) return;

        form.reset();
        document.getElementById('stationStatusId').value = '';
        document.getElementById('stationStatusName').value = '';
        document.getElementById('stationStatusSortOrder').value = '0';
        
        // Reset active status
        const activeCheckbox = document.getElementById('stationStatusEnabled').checked = true;
       
    }

    // Utility: Load Assignment Data
    function loadStationStatusData(data) {
        if (!data) return;

        const stationStatusId = document.getElementById('stationStatusId');
        const stationStatusName = document.getElementById('stationStatusName');
        const stationStatusSortOrder = document.getElementById('stationStatusSortOrder');
        const stationStatusEnabled = document.getElementById('stationStatusEnabled');

        if (stationStatusId) stationStatusId.value = data.id;
        if (stationStatusName) stationStatusName.value = data.name;
        if (stationStatusSortOrder) stationStatusSortOrder.value = data.sort_order;
        if (stationStatusEnabled) stationStatusEnabled.checked = data.enabled;
    }

    // Utility: Process Agency Form Data
    function processStationStatusForm() {
        const stationStatusId = document.getElementById('stationStatusId');
        const stationStatusName = document.getElementById('stationStatusName');
        const stationStatusSortOrder = document.getElementById('stationStatusSortOrder');
        const stationStatusEnabled = document.getElementById('stationStatusEnabled');

        if (!stationStatusId || !stationStatusName || !stationStatusSortOrder || !stationStatusEnabled) {
            throw new Error('Required form elements not found');
        }

        const id = stationStatusId.value;
        const isNew = !id;

        // Validate required fields
        if (!stationStatusName.value.trim()) {
            throw new Error('Name is required');
        }

        const data = {
            id: id || null,
            name: stationStatusName.value.trim(),
            sort_order: stationStatusSortOrder.value,
            enabled: stationStatusEnabled.checked
        };

        return { id, isNew, data };
    }
});