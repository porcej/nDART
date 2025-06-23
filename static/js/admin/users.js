import { initConfig, sendRequest, showToast, searchTable, toolbar, initToggleActive, initButtons } from './table-tools.js';

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', async function() {
    // Constants and modal initialization
    const tblId = 'usersTable';
    const formModalId = 'userModal';
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
    initButtons('Create User', 'Edit User', resetUserForm, loadUserData, processUserForm);

    // Utility: Reset User Form
    function resetUserForm() {
        const form = document.getElementById('userForm');
        if (!form) return;

        form.reset();
        document.getElementById('userId').value = '';
        document.getElementById('passwordNote').textContent = '(required for new users)';
        document.getElementById('userPassword').required = true;
        
        // Reset role checkboxes
        document.querySelectorAll('.role-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        // Reset active status
        const activeCheckbox = document.getElementById('userActive');
        if (activeCheckbox) {
            activeCheckbox.checked = true;
            activeCheckbox.disabled = false;
        }
        
        // Reset admin role checkboxes
        document.querySelectorAll('.role-admin').forEach(checkbox => {
            checkbox.disabled = false;
        });
    }

    // Utility: Load User Data
    function loadUserData(data) {
        if (!data) return;

        const passwordNote = document.getElementById('passwordNote');
        const userPassword = document.getElementById('userPassword');
        const userId = document.getElementById('userId');
        const userName = document.getElementById('userName');
        const userPerson = document.getElementById('userPerson');
        const userActive = document.getElementById('userActive');

        if (passwordNote) passwordNote.textContent = '(leave blank to keep current)';
        if (userPassword) userPassword.required = false;
        if (userId) userId.value = data.id;
        if (userName) userName.value = data.name;
        if (userPerson) userPerson.value = data.person;
        if (userPassword) userPassword.value = '';

        // Reset all role checkboxes
        document.querySelectorAll('.role-checkbox').forEach(checkbox => {
            checkbox.checked = false;
        });

        // Set checked roles
        if (data.roles) {
            data.roles.forEach(role => {
                const roleCheckbox = document.getElementById(`role-${role.id}`);
                if (roleCheckbox) {
                    roleCheckbox.checked = true;
                }
            });
        }

        if (userActive) {
            userActive.checked = data.active;

            // Disable admin role and active status for current user
            if (data.id === table.dataset.currentUserId) {
                document.querySelectorAll('.role-admin').forEach(adminRole => {
                    adminRole.disabled = true;
                });
                userActive.disabled = true;
            }
        }
    }

    // Utility: Process User Form Data
    function processUserForm() {
        const userId = document.getElementById('userId');
        const userName = document.getElementById('userName');
        const userPerson = document.getElementById('userPerson');
        const userPassword = document.getElementById('userPassword');
        const userActive = document.getElementById('userActive');

        if (!userId || !userName || !userPerson || !userActive) {
            throw new Error('Required form elements not found');
        }

        const id = userId.value;
        const isNew = !id;

        // Get selected roles
        const selectedRoles = Array.from(document.querySelectorAll('.role-checkbox:checked'))
            .map(checkbox => checkbox.value);

        // Validate required fields
        if (!userName.value.trim()) {
            throw new Error('Username is required');
        }

        if (isNew && !userPassword.value) {
            throw new Error('Password is required for new users');
        }

        const data = {
            id: id || null,
            name: userName.value.trim(),
            person: userPerson.value.trim(),
            password: userPassword.value,
            roles: selectedRoles,
            active: userActive.checked
        };

        // Remove password if not changed
        if (!isNew && !data.password) {
            delete data.password;
        }

        return { id, isNew, data };
    }
});