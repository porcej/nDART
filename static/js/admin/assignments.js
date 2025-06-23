import { initConfig, sendRequest, showToast, searchTable, toolbar, initToggleActive, initButtons } from './table-tools.js';

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
    // Constants and modal initialization
    const tblId = 'assignmentsTable';
    const formModalId = 'assignmentModal';
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
    initButtons('Create Assignment', 'Edit Assignment', resetAssignmentForm, loadAssignmentData, processAssignmentForm);

    // Utility: Reset User Form
    function resetAssignmentForm() {
        const form = document.getElementById('assignmentForm');
        if (!form) return;

        form.reset();
        document.getElementById('assignmentId').value = '';
        document.getElementById('assignmentName').value = '';
        document.getElementById('assignmentDescription').value = '';
        document.getElementById('assignmentSortOrder').value = '0';
        
        // Reset active status
        const activeCheckbox = document.getElementById('assignmentEnabled').checked = true;
        
    }

    // Utility: Load Assignment Data
    function loadAssignmentData(data) {
        if (!data) return;

        const assignmentId = document.getElementById('assignmentId');
        const assignmentName = document.getElementById('assignmentName');
        const assignmentDescription = document.getElementById('assignmentDescription');
        const assignmentSortOrder = document.getElementById('assignmentSortOrder');
        const assignmentEnabled = document.getElementById('assignmentEnabled');

        if (assignmentId) assignmentId.value = data.id;
        if (assignmentName) assignmentName.value = data.name;
        if (assignmentDescription) assignmentDescription.value = data.description;
        if (assignmentSortOrder) assignmentSortOrder.value = data.sort_order;
        if (assignmentEnabled) assignmentEnabled.checked = data.enabled;
    }

    // Utility: Process Agency Form Data
    function processAssignmentForm() {
        const assignmentId = document.getElementById('assignmentId');
        const assignmentName = document.getElementById('assignmentName');
        const assignmentDescription = document.getElementById('assignmentDescription');
        const assignmentSortOrder = document.getElementById('assignmentSortOrder');
        const assignmentEnabled = document.getElementById('assignmentEnabled');

        if (!assignmentId || !assignmentName || !assignmentDescription || !assignmentSortOrder || !assignmentEnabled) {
            throw new Error('Required form elements not found');
        }

        const id = assignmentId.value;
        const isNew = !id;

        // Validate required fields
        if (!assignmentName.value.trim()) {
            throw new Error('Name is required');
        }

        const data = {
            id: id || null,
            name: assignmentName.value.trim(),
            description: assignmentDescription.value.trim(),
            sort_order: assignmentSortOrder.value,
            enabled: assignmentEnabled.checked
        };

        return { id, isNew, data };
    }
});