// crudTableManager.js
(function(window, $) {
    class CrudTable {
      /**
       * @param {Object} cfg
       * @param {string} cfg.tableSelector       CSS selector for the <table> container
       * @param {string[]} cfg.columns           Array of field names (must correspond to form inputs & data attributes)
       * @param {string} cfg.createBtnSelector   Selector for the “Create” button
       * @param {string} cfg.exportBtnSelector   Selector for the “Export” button
       * @param {string} cfg.removeAllBtnSelector Selector for the “Remove All” button
       * @param {string} cfg.importBtnSelector   Selector for the “Import” button
       * @param {string} cfg.showDisabledSelector Selector for the “show inactive” checkbox (optional)
       * @param {string} cfg.createModalSelector Selector for the “create/edit” modal
       * @param {string} cfg.deleteModalSelector Selector for the “delete confirm” modal (optional)
       * @param {string} cfg.importModalSelector Selector for the “import” modal (optional)
       * @param {string} cfg.formSelector        Selector for the create/edit form inside the modal
       * @param {string} cfg.importFormSelector  Selector for the import form inside its modal
       * @param {string} cfg.apiBaseUrl          Base URL for your API (no trailing slash)
       * @param {string} cfg.currentUserId       (Optional) for disabling edits on self
       */
      constructor(cfg) {
        Object.assign(this, cfg);
        this.apiUrl = this.apiBaseUrl.endsWith('/')
          ? this.apiBaseUrl
          : this.apiBaseUrl + '/';
  
        // cache elements
        this.$table        = $(this.tableSelector);
        this.$tbody        = this.$table.find('table tbody');
        this.$createBtn    = $(this.createBtnSelector);
        this.$exportBtn    = $(this.exportBtnSelector);
        this.$removeAllBtn = $(this.removeAllBtnSelector);
        this.$importBtn    = $(this.importBtnSelector);
        this.$showDisabled = this.showDisabledSelector
          ? $(this.showDisabledSelector)
          : null;
  
        this.createModal = new bootstrap.Modal($(this.createModalSelector)[0]);
        this.deleteModal = this.deleteModalSelector
          ? new bootstrap.Modal($(this.deleteModalSelector)[0])
          : null;
        this.importModal = this.importModalSelector
          ? new bootstrap.Modal($(this.importModalSelector)[0])
          : null;
  
        // bind
        this._bindUtilities();
        this._bindEvents();
        this._bindSearch();
        if (this.$showDisabled) {
          this._bindShowDisabled();
        }
      }
  
      // ——— Generic fetch wrapper —————————————————————————————————————————————————————
      async sendRequest({ url, method, data = null }) {
        const opts = {
          method,
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin'
        };
        if (data) opts.body = JSON.stringify(data);
        const res = await fetch(url, opts);
        if (!res.ok) {
          const err = await res.json().catch(()=>({message: res.statusText}));
          throw new Error(err.message || res.statusText);
        }
        return res.json();
      }
  
      showToast(type, message) {
        const toastId = type === 'error' ? 'errorToast' : 'successToast';
        const toastEl = document.getElementById(toastId);
        toastEl.querySelector('.toast-body').textContent = message;
        new bootstrap.Toast(toastEl).show();
      }
  
      // ——— Bind search input inside the table ————————————————————————————————————————
      _bindSearch() {
        const tblId = this.tableSelector.replace('#','');
        $(`${this.tableSelector} #searchInput`).on('keyup', e => {
          const v = e.target.value.toLowerCase();
          this.$tbody.find('tr').each(( _, tr ) => {
            const text = $(tr).find('td')
                            .map((_,td)=>$(td).text().toLowerCase())
                            .get().join(' ');
            $(tr).toggle(text.includes(v));
          });
        });
      }
  
      // ——— Show/Hide disabled rows ——————————————————————————————————————————————
      _bindShowDisabled() {
        this.$showDisabled.on('change', () => {
          const show = this.$showDisabled.is(':checked');
          this.$tbody.find('tr').each((_,tr)=>{
            const active = !!$(tr).data('active');
            $(tr).toggle(show || active);
          });
        }).trigger('change');
      }
  
      // ——— Utility to reset form inputs ————————————————————————————————————————
      resetForm() {
        const $form = $(this.formSelector);
        $form[0].reset();
        // clear id
        $form.find('[name="id"]').val('');
        // reset any notes/checkboxes etc
        $form.find('.role-checkbox').prop('checked', false);
        $form.find('[name="active"]').prop({ checked: true, disabled: false });
      }
  
      // ——— Deletion flow ————————————————————————————————————————————————————————
      async doDelete(id) {
        try {
          await this.sendRequest({url: this.apiUrl + id, method: 'DELETE'});
          this.deleteModal.hide();
          location.reload();
        } catch(err) {
          this.showToast('error', err.message);
        }
      }
  
      // ——— Wire up all buttons/forms —————————————————————————————————————————————
      _bindEvents() {
        // Export
        this.$exportBtn.on('click', ()=> {
          window.location.href = this.$exportBtn.data('url');
        });
  
        // Import
        if (this.importModal) {
          this.$importBtn.on('click', ()=> this.importModal.show());
          $(this.importFormSelector).on('submit', e => {
            e.preventDefault();
            const fd = new FormData(e.target);
            fetch(e.target.action, {method:'POST', body:fd, credentials:'same-origin'})
              .then(r=>r.json()).then(json=>{
                this.showToast('success', json.success);
                location.reload();
              })
              .catch(err=>this.showToast('error', err.message));
          });
        }
  
        // Remove All
        this.$removeAllBtn.on('click', async () => {
          if (!confirm('Are you sure? This cannot be undone.')) return;
          try {
            await this.sendRequest({url: this.$removeAllBtn.data('url'), method:'DELETE'});
            location.reload();
          } catch(err) {
            this.showToast('error', err.message);
          }
        });
  
        // Create
        this.$createBtn.on('click', () => {
          $(this.formSelector + ' .modal-title').text('Create');
          this.resetForm();
          this.createModal.show();
        });
  
        // Edit (delegated)
        this.$table.on('click', '.edit-btn', async e => {
          const id = $(e.currentTarget).data('id');
          $(this.formSelector + ' .modal-title').text('Edit');
          this.resetForm();
          // fetch data
          try {
            const data = await this.sendRequest({url: this.apiUrl + id, method:'GET'});
            // populate inputs
            for (let col of this.columns) {
              const $inp = $(this.formSelector + ` [name="${col}"]`);
              if ($inp.attr('type') === 'checkbox') {
                $inp.prop('checked', data[col]);
              } else {
                $inp.val(data[col]);
              }
            }
            // handle special case: roles array
            if (data.roles) {
              data.roles.forEach(r => {
                $(this.formSelector + ` #role-${r.id}`).prop('checked', true);
              });
            }
            // disable self-modify
            if (this.currentUserId && id == this.currentUserId) {
              $(this.formSelector + ' [name="active"], .role-admin').prop('disabled', true);
            }
            this.createModal.show();
          } catch(err) {
            this.showToast('error', err.message);
          }
        });
  
        // Delete (delegated)
        if (this.deleteModal) {
          this.$table.on('click', '.delete-btn', e => {
            const id = $(e.currentTarget).data('id');
            $('#deleteConfirmBtn').off('click')
              .one('click', ()=> this.doDelete(id));
            this.deleteModal.show();
          });
        }
  
        // Submit create/edit form
        $(this.formSelector).on('submit', async e => {
          e.preventDefault();
          const $f = $(e.target);
          const id  = $f.find('[name="id"]').val();
          const payload = { };
          for (let col of this.columns) {
            const $inp = $f.find(`[name="${col}"]`);
            payload[col] = $inp.attr('type') === 'checkbox'
              ? $inp.is(':checked')
              : $inp.val();
          }
          // roles special
          payload.roles = $f.find('.role-checkbox:checked')
                             .map((_,c)=>$(c).val()).get();
  
          // drop empty password
          if (payload.password === '') delete payload.password;
  
          try {
            const method = id ? 'PUT' : 'POST',
                  url    = id ? this.apiUrl + id : this.apiUrl;
            const res = await this.sendRequest({url, method, data: payload});
            this.showToast('success', res.success);
            location.reload();
          } catch(err) {
            // already toasted
          }
        });
      }
  
      _bindUtilities() {
        // nothing here for now
      }
    }
  
    // expose
    window.CrudTable = CrudTable;
  })(window, jQuery);