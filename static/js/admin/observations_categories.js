import { initConfig, sendRequest, showToast, searchTable, toolbar, initToggleActive, initButtons } from './table-tools.js';

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
    // Constants and modal initialization
    const tblId = 'observationsCategoriesTable';
    const formModalId = 'observationsCategoryModal';
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
    initButtons('Create Observation Category', 'Edit Observation Category', resetObservationCategoryForm, loadObservationCategoryData, processObservationCategoryForm);

    // Utility: Reset User Form
    function resetObservationCategoryForm() {
        const form = document.getElementById('observationsCategoryForm');
        if (!form) return;

        form.reset();
        document.getElementById('observationsCategoryId').value = '';
        document.getElementById('observationsCategoryName').value = '';
        document.getElementById('observationsCategoryDescription').value = '';
        document.getElementById('observationsCategorySortOrder').value = '0';
        
        // Reset active status
        const activeCheckbox = document.getElementById('observationsCategoryEnabled').checked = true;
    }

    // Utility: Load Agency Data
    function loadObservationCategoryData(data) {
        if (!data) return;

        const observationsCategoryId = document.getElementById('observationsCategoryId');
        const observationsCategoryName = document.getElementById('observationsCategoryName');
        const observationsCategoryDescription = document.getElementById('observationsCategoryDescription');
        const observationsCategorySortOrder = document.getElementById('observationsCategorySortOrder');
        const observationsCategoryEnabled = document.getElementById('observationsCategoryEnabled');

        if (observationsCategoryId) observationsCategoryId.value = data.id;
        if (observationsCategoryName) observationsCategoryName.value = data.name;
        if (observationsCategoryDescription) observationsCategoryDescription.value = data.description;
        if (observationsCategorySortOrder) observationsCategorySortOrder.value = data.sort_order;
        if (observationsCategoryEnabled) observationsCategoryEnabled.checked = data.enabled;

    }

    // Utility: Process Agency Form Data
    function processObservationCategoryForm() {
        const observationsCategoryId = document.getElementById('observationsCategoryId');
        const observationsCategoryName = document.getElementById('observationsCategoryName');
        const observationsCategoryDescription = document.getElementById('observationsCategoryDescription');
        const observationsCategorySortOrder = document.getElementById('observationsCategorySortOrder');
        const observationsCategoryEnabled = document.getElementById('observationsCategoryEnabled');

        if (!observationsCategoryId || !observationsCategoryName || !observationsCategoryDescription || !observationsCategorySortOrder || !observationsCategoryEnabled) {
            throw new Error('Required form elements not found');
        }

        const id = observationsCategoryId.value;
        const isNew = !id;

        // Validate required fields
        if (!observationsCategoryName.value.trim()) {
            throw new Error('Name is required');
        }

        const data = {
            id: id || null,
            name: observationsCategoryName.value.trim(),
            description: observationsCategoryDescription.value.trim(),
            sort_order: observationsCategorySortOrder.value,
            enabled: observationsCategoryEnabled.checked
        };

        return { id, isNew, data };
    }
});