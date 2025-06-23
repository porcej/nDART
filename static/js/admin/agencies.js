import { initConfig, sendRequest, showToast, searchTable, toolbar, initToggleActive, initButtons } from './table-tools.js';

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
    // Constants and modal initialization
    const tblId = 'agenciesTable';
    const formModalId = 'agencyModal';
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
    initButtons('Create Agency', 'Edit Agency', resetAgencyForm, loadAgencyData, processAgencyForm);

    // Utility: Reset User Form
    function resetAgencyForm() {
        const form = document.getElementById('agencyForm');
        if (!form) return;

        form.reset();
        document.getElementById('agencyId').value = '';
        document.getElementById('agencyName').value = '';
        document.getElementById('agencyDescription').value = '';
        document.getElementById('agencySortOrder').value = '0';
        
        // Reset active status
        const activeCheckbox = document.getElementById('agencyEnabled').checked = true;
    }

    // Utility: Load Agency Data
    function loadAgencyData(data) {
        if (!data) return;

        const agencyId = document.getElementById('agencyId');
        const agencyName = document.getElementById('agencyName');
        const agencyDescription = document.getElementById('agencyDescription');
        const agencySortOrder = document.getElementById('agencySortOrder');
        const agencyEnabled = document.getElementById('agencyEnabled');

        if (agencyId) agencyId.value = data.id;
        if (agencyName) agencyName.value = data.name;
        if (agencyDescription) agencyDescription.value = data.description;
        if (agencySortOrder) agencySortOrder.value = data.sort_order;

        // Set checked roles
        if (data.roles) {
            data.roles.forEach(role => {
                const roleCheckbox = document.getElementById(`role-${role.id}`);
                if (roleCheckbox) {
                    roleCheckbox.checked = true;
                }
            });
        }

        if (agencyEnabled) agencyEnabled.checked = data.enabled;
    }

    // Utility: Process Agency Form Data
    function processAgencyForm() {
        const agencyId = document.getElementById('agencyId');
        const agencyName = document.getElementById('agencyName');
        const agencyDescription = document.getElementById('agencyDescription');
        const agencySortOrder = document.getElementById('agencySortOrder');
        const agencyEnabled = document.getElementById('agencyEnabled');

        if (!agencyId || !agencyName || !agencyDescription || !agencySortOrder || !agencyEnabled) {
            throw new Error('Required form elements not found');
        }

        const id = agencyId.value;
        const isNew = !id;

        // Validate required fields
        if (!agencyName.value.trim()) {
            throw new Error('Name is required');
        }

        const data = {
            id: id || null,
            name: agencyName.value.trim(),
            description: agencyDescription.value.trim(),
            sort_order: agencySortOrder.value,
            enabled: agencyEnabled.checked
        };

        return { id, isNew, data };
    }
});