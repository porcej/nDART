# nDART Bug and Pitfall Review

## Scope

Focused review on:
- app startup and config bootstrapping
- admin import/export flows
- API error handling and response contracts
- DB transaction patterns
- operational health checks

## Findings (Ordered by Severity)

### Critical

1. CSRF protection is configured but not enforced.
- Files: `config.py`, `app.py`, `extensions.py`, `static/js/admin/table-tools.js`
- Details: `WTF_CSRF_ENABLED` is set, but `CSRFProtect` is not initialized. Write actions use cookie auth (`credentials: 'same-origin'`), so CSRF is a real risk.
- Risk: Cross-site requests can trigger authenticated admin actions.

### High

2. App factory does not run environment-specific `init_app` safeguards.
- Files: `app.py`, `config.py`
- Details: `create_app()` uses `Config` by default and calls `app.config.from_object(...)`, but does not call `config_class.init_app(app)`.
- Risk: Production checks like `SECRET_KEY` validation can be bypassed.

3. `start-production.sh` contains a shell syntax bug.
- File: `start-production.sh`
- Details: Broken multiline echo block around lines 15-17.
- Risk: Deployment script can fail before startup.

4. Import operations are not consistently atomic across admin routes.
- Files: `blueprints/admin/agencies_routes.py`, `blueprints/admin/users_routes.py`, `blueprints/admin/station_statuses.py`, `blueprints/admin/observations_categories.py`
- Details: Many imports commit per row inside loops.
- Risk: Partial writes on failure lead to inconsistent datasets.

5. Admin frontend/backend response contract mismatch.
- Files: `static/js/admin/table-tools.js` and multiple admin route files
- Details: UI expects consistent JSON success/error semantics, while some routes return varying payload formats.
- Risk: UX shows false success/failure states.

### Medium

6. Health check queries likely use incorrect table name.
- File: `blueprints/health/routes.py`
- Details: Uses `SELECT COUNT(*) FROM user`; app models indicate table naming is pluralized (for example `users`).
- Risk: False degraded/unhealthy reports.

7. Internal errors are exposed directly to clients.
- Files: multiple blueprint routes (admin and internal API)
- Details: Returns `str(e)` to client in several places.
- Risk: Information leakage and poor error boundaries.

8. Admin role-guard redirect target appears fragile.
- File: `blueprints/admin/utils.py`
- Details: Redirect uses `url_for('main.dashboard')`; blueprint naming needs consistency verification.
- Risk: Potential `BuildError` on unauthorized access paths if endpoint name mismatches.

## Existing Improvements Already Made

- `id` removed from XLSX export output in admin export utility.
- Assignments import improved with duplicate checks and DB conflict checks (`name` and `short_code`).
- Import error handling in admin table tools improved to respect non-OK responses.
- Assignments export width calculation fixed to avoid `TypeError` on NaN/float values.

## Recommended Phased Remediation Plan

### Phase 1: Immediate (Security + Stability)

1. Initialize CSRF protection (`CSRFProtect`) and wire CSRF token handling in forms and JS fetches.
2. Fix `start-production.sh` syntax.
3. Update app factory to select environment config explicitly and call `config_class.init_app(app)`.
4. Replace raw exception text in API responses with safe messages and server-side logging.

### Phase 2: Data Integrity + API Contracts

1. Make all admin imports atomic (validate first, insert batch, single commit, rollback on failure).
2. Standardize JSON response shape across admin/internal routes:
   - success path: `{ "success": "...", "data": ... }`
   - error path: `{ "error": "..." }`
3. Align frontend assumptions in `table-tools.js` with backend response contracts.

### Phase 3: Reliability Hardening

1. Fix health check table queries and make DB checks backend-agnostic.
2. Normalize 4xx vs 5xx behavior for validation/payload errors.
3. Add minimal structured logging for import/export and admin write failures.

## Test Plan (Recommended)

1. App bootstrap tests:
- verifies production config selection and `init_app` execution
- verifies startup fails with missing/unsafe `SECRET_KEY` in production

2. CSRF tests:
- state-changing admin routes reject missing/invalid CSRF token

3. Import transaction tests:
- simulate mid-import failure and assert rollback (no partial data)
- duplicate-in-file and DB-conflict coverage for each import route

4. API contract tests:
- all admin CRUD/import/remove-all routes return expected JSON structure

5. Health endpoint tests:
- DB checks pass against current schema
- endpoint returns expected status codes under degraded/healthy conditions

## Suggested Work Order

1. Ship Phase 1 in one patch set.
2. Ship Phase 2 as a refactor with route-by-route migration and tests.
3. Ship Phase 3 with monitoring/logging and health check polish.

