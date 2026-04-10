# CSRF Sanity Test Checklist

Use this checklist after CSRF-related changes to confirm forms, DataTables, and admin workflows still function.

## Auth and Session

- [ ] Login succeeds from `/login` or auth login.
- [ ] Logout succeeds and protected pages redirect to login.
- [ ] Profile password change succeeds.

## Dashboard DataTables and Editor Flows

### Events
- [ ] Events table loads.
- [ ] Create event succeeds.
- [ ] Edit event succeeds.
- [ ] Delete event succeeds.

### Observations
- [ ] Observations table loads.
- [ ] Create observation succeeds.
- [ ] Edit observation succeeds.
- [ ] Delete observation succeeds.

### Status Reports
- [ ] Status reports table loads.
- [ ] Create status report succeeds.
- [ ] Edit status report succeeds.
- [ ] Delete status report succeeds.
- [ ] Optional staffer volunteer status update flow succeeds.

## Admin CRUD (Modal + JSON APIs)

- [ ] Users: create, edit, delete.
- [ ] Roles: create, edit, delete.
- [ ] Agencies: create, edit, delete.
- [ ] Assignments: create, edit, delete.
- [ ] Station Status: create, edit, delete.
- [ ] Observation Categories: create, edit, delete.
- [ ] Chat Rooms: create, edit, delete.

## Import and Clear Flows

### XLSX Imports (admin modal import form)
- [ ] Upload/import succeeds for pages using the shared import modal.
- [ ] Validation errors are user-readable and not CSRF failures.

### CSV Imports and Clear Buttons
- [ ] Events import CSV succeeds.
- [ ] Events clear-all succeeds.
- [ ] Observations import CSV succeeds.
- [ ] Observations clear-all succeeds.
- [ ] Status reports import CSV succeeds.
- [ ] Status reports clear-all succeeds.

## Chat

- [ ] Chat page loads and Socket.IO connects.
- [ ] Sending a message succeeds.
- [ ] No repeated reconnect loop due to CSRF checks.

## Regression Signals

- [ ] No broad 400/403 failures on dashboard/admin initial load.
- [ ] Browser console has no repeated failed API calls.
- [ ] Network tab has no "CSRF token missing/invalid" errors for expected write actions.

## If Something Fails

Capture and record:
- Request URL
- HTTP method
- Status code
- Response body (or flash message text)
- Browser console error (if present)
