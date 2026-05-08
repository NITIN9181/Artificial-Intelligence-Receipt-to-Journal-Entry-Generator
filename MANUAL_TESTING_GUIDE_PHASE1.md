# Manual Testing Guide — Phase 1
## Receipt-to-Journal-Entry Application

**Version:** 1.0.0  
**Date:** May 2026  
**Environment:** Production + Staging + Local Development

---

# Table of Contents

1. [INFRA: Infrastructure & Deployment](#infra-infrastructure--deployment)
2. [DB: Database Schema, Migrations, Triggers, RLS](#db-database-schema-migrations-triggers-rls)
3. [AUTH: Authentication & Authorization](#auth-authentication--authorization)
4. [API-B1: Config & JWT](#api-b1-config--jwt)
5. [API-B2: Pydantic Schema Validation](#api-b2-pydantic-schema-validation)
6. [API-B3: LLM Client & Extraction](#api-b3-llm-client--extraction)
7. [API-B4: Receipt Endpoints & State Machine](#api-b4-receipt-endpoints--state-machine)
8. [API-B5: Bookkeeping Engine](#api-b5-bookkeeping-engine)
9. [API-B6: Journal Entry Endpoints](#api-b6-journal-entry-endpoints)
10. [API-B7: Error Handling](#api-b7-error-handling)
11. [UI-D: Design System](#ui-d-design-system)
12. [UI-F1: Auth Pages](#ui-f1-auth-pages)
13. [UI-F2: API Client](#ui-f2-api-client)
14. [UI-F3: Upload Page](#ui-f3-upload-page)
15. [UI-F4: Review Page](#ui-f4-review-page)
16. [UI-F5: Journal Entries List](#ui-f5-journal-entries-list)
17. [UI-F6: Toasts](#ui-f6-toasts)
18. [UI-F7: Settings Page](#ui-f7-settings-page)
19. [E2E: End-to-End Flows](#e2e-end-to-end-flows)
20. [SEC: Security & Compliance](#sec-security--compliance)
21. [Production Smoke Test](#production-smoke-test)
22. [Rollback Test](#rollback-test)

---

# INFRA: Infrastructure & Deployment

## TEST-INFRA-01: Supabase Project Verification

**Objective:** Verify Supabase project is properly created and configured.

**Prerequisites:** Access to Supabase dashboard

**Steps:**
1. Navigate to https://supabase.com/dashboard
2. Select the project for this application
3. Verify project status shows "Active" (green indicator)
4. Go to Settings → Database
5. Copy the connection string (URI format)

**Expected Result:**
- Project status: Active (green)
- Connection string format: `postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
- Project URL format: `https://[project-ref].supabase.co`

**Pass Criteria:** Project is active and connection string is retrievable.

**Failure Indicators:**
- Project shows "Paused" or "Inactive" status
- Connection string is not visible or incomplete

**Screenshot/Log Evidence:** Screenshot of Supabase dashboard showing active project status.

---

## TEST-INFRA-02: Render Web Service Configuration

**Objective:** Verify Render web service is deployed with correct environment variables.

**Prerequisites:** Access to Render dashboard

**Steps:**
1. Navigate to https://dashboard.render.com
2. Select the web service for this application
3. Verify service status shows "Live" (green)
4. Go to Environment tab
5. Verify all required environment variables are set:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `SUPABASE_JWT_SECRET`
   - `DATABASE_URL`
   - `NVIDIA_NIM_API_KEY` (or `OLLAMA_HOST` for local)
   - `CORS_ORIGINS`

**Expected Result:**
- Service status: Live (green)
- All 7+ environment variables present
- No variables show "(empty)" or placeholder values

**Pass Criteria:** Service is live and all required environment variables are configured.

**Failure Indicators:**
- Service shows "Deploy failed" or "Crashed"
- Missing environment variables
- Variables contain placeholder text like "your-key-here"

**Screenshot/Log Evidence:** Screenshot of Render environment variables panel (redact sensitive values).

---

## TEST-INFRA-03: Vercel Project Linkage

**Objective:** Verify Vercel project is linked to Git repository.

**Prerequisites:** Access to Vercel dashboard

**Steps:**
1. Navigate to https://vercel.com/dashboard
2. Select the project for this application
3. Verify deployment status shows "Ready" (green checkmark)
4. Go to Settings → Git
5. Verify connected repository is correct
6. Check that production branch is set to `main` or `master`

**Expected Result:**
- Deployment status: Ready
- Connected repository URL matches expected repo
- Production branch: `main` or `master`
- Auto-deploy enabled for production branch

**Pass Criteria:** Project is connected to correct repo and deployments succeed.

**Failure Indicators:**
- "Not Connected" status
- Failed deployments in activity log
- Wrong repository connected

**Screenshot/Log Evidence:** Screenshot of Vercel project settings → Git section.

---

## TEST-INFRA-04: UptimeRobot Health Check

**Objective:** Verify UptimeRobot is configured to ping the health endpoint.

**Prerequisites:** Access to UptimeRobot dashboard

**Steps:**
1. Navigate to https://uptimerobot.com/dashboard
2. Locate the monitor for this application
3. Verify monitor URL is: `https://[backend-url]/api/v1/health`
4. Verify monitoring interval is 14 minutes (or less)
5. Check status shows green/up

**Expected Result:**
- Monitor status: Up (green)
- URL ends with `/api/v1/health`
- Interval: 14 minutes or less
- Response time: < 5000ms typical

**Pass Criteria:** Monitor is active and shows "Up" status with correct endpoint.

**Failure Indicators:**
- Monitor shows "Down" status
- URL is incorrect or returns 404
- Interval is greater than 15 minutes

**Screenshot/Log Evidence:** Screenshot of UptimeRobot monitor details.

---

## TEST-INFRA-05: CORS Configuration Verification

**Objective:** Verify CORS is properly configured between frontend and backend.

**Prerequisites:** Frontend and backend deployed

**Steps:**
1. Open browser DevTools (F12)
2. Go to Network tab
3. Navigate to the frontend application
4. Attempt to login or make an authenticated request
5. Look for CORS errors in console
6. Check response headers on API requests

**Expected Result:**
- No CORS errors in browser console
- Response headers include:
  - `access-control-allow-origin: [frontend-url]`
  - `access-control-allow-credentials: true`
  - `access-control-allow-methods: GET, POST, PUT, DELETE, OPTIONS`

**Pass Criteria:** No CORS errors; API requests succeed from frontend.

**Failure Indicators:**
- Console error: "Access to XMLHttpRequest... has been blocked by CORS policy"
- Preflight OPTIONS requests fail with 403
- Credentials not included in requests

**Screenshot/Log Evidence:** Screenshot of Network tab showing successful API request with CORS headers.

---

# DB: Database Schema, Migrations, Triggers, RLS

## TEST-DB-01: Alembic Migration 001 Runs Clean

**Objective:** Verify the initial schema migration executes without errors.

**Prerequisites:** Database connection configured, alembic installed

**Steps:**
1. Open terminal in backend directory
2. Run: `alembic upgrade 001`
3. Check for any errors in output
4. Connect to database and verify tables exist

**Expected Result:**
```bash
$ alembic upgrade 001
INFO  [alembic.runtime.migration] Running upgrade -> 001, Initial schema
# No error messages
```

**Verification SQL (run in Supabase SQL Editor):**
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

**Expected tables:**
- `users`
- `receipts`
- `chart_of_accounts`
- `vendor_category_mappings`
- `journal_entries`
- `journal_entry_lines`
- `audit_logs`

**Pass Criteria:** Migration completes with no errors; all 7 tables exist.

**Failure Indicators:**
- "relation already exists" errors
- Migration rolls back
- Missing tables in database

**Screenshot/Log Evidence:** Terminal output of migration command + SQL query results.

---

## TEST-DB-02: Alembic Migration 002 Seed Defaults

**Objective:** Verify seed data migration populates default accounts and vendor mappings.

**Prerequisites:** Migration 001 completed

**Steps:**
1. Run: `alembic upgrade 002`
2. Query chart_of_accounts for default entries
3. Query vendor_category_mappings for default entries

**Verification SQL:**
```sql
-- Check default accounts
SELECT code, name, type, is_default FROM chart_of_accounts WHERE is_default = TRUE;

-- Check default vendor mappings
SELECT vendor_name_pattern, account_code FROM vendor_category_mappings WHERE is_default = TRUE;
```

**Expected Result:**
- At least 15+ default chart of accounts entries
- Common vendor patterns mapped (e.g., "uber", "doordash", "amazon")
- All have `is_default = TRUE`

**Pass Criteria:** Default accounts and vendor mappings are populated.

**Failure Indicators:**
- Empty chart_of_accounts table
- No vendor_category_mappings
- Migration fails with constraint violation

**Screenshot/Log Evidence:** SQL query results showing seeded data.

---

## TEST-DB-03: RLS Policies Verified

**Objective:** Verify all 5 RLS policies are created and active.

**Prerequisites:** Migrations completed

**Steps:**
1. Open Supabase SQL Editor
2. Run the verification query for each policy

**Verification SQL:**
```sql
-- Check RLS is enabled on all tables
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('receipts', 'chart_of_accounts', 'vendor_category_mappings', 'journal_entries', 'journal_entry_lines');

-- List all RLS policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE schemaname = 'public';
```

**Expected Result:**
- All 5 tables show `rowsecurity = true`
- 5 policies listed:
  1. `user_receipts_isolation` on `receipts`
  2. `user_coa_isolation` on `chart_of_accounts`
  3. `user_vcm_isolation` on `vendor_category_mappings`
  4. `user_je_isolation` on `journal_entries`
  5. `user_jel_isolation` on `journal_entry_lines`

**Pass Criteria:** RLS enabled on all 5 tables; all 5 policies exist.

**Failure Indicators:**
- `rowsecurity = false` on any table
- Missing policy names
- Policies with `permissive = false`

**Screenshot/Log Evidence:** SQL query results showing RLS status.

---

## TEST-DB-04: RLS User Isolation — Receipts

**Objective:** Verify users can only access their own receipts.

**Prerequisites:** Two test users created (User A and User B)

**Steps:**
1. Create User A via Supabase Auth
2. Create User B via Supabase Auth
3. Insert receipt for User A
4. Query as User B — should see no results

**Verification SQL:**
```sql
-- First, create test users in the users table
INSERT INTO users (id, full_name) VALUES 
  ('00000000-0000-0000-0000-000000000001', 'Test User A'),
  ('00000000-0000-0000-0000-000000000002', 'Test User B');

-- Insert test receipt for User A
INSERT INTO receipts (id, user_id, image_url, status)
VALUES (
  '10000000-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-000000000001',
  'https://test.com/image.jpg',
  'UPLOADED'
);

-- Now run as User A (set JWT claims)
SET LOCAL jwt.claims.sub = '00000000-0000-0000-0000-000000000001';
SELECT id, user_id, status FROM receipts;

-- Now run as User B
SET LOCAL jwt.claims.sub = '00000000-0000-0000-0000-000000000002';
SELECT id, user_id, status FROM receipts;
```

**Expected Result:**
- User A query returns 1 row
- User B query returns 0 rows

**Pass Criteria:** User B cannot see User A's receipts.

**Failure Indicators:**
- User B sees User A's receipt
- User A sees 0 rows (RLS too restrictive)

**Screenshot/Log Evidence:** SQL query results for both users.

---

## TEST-DB-05: Audit Log Trigger Verification

**Objective:** Verify audit_logs are written on INSERT/UPDATE/DELETE.

**Prerequisites:** Migrations completed

**Steps:**
1. Insert a test receipt
2. Update the receipt status
3. Delete the receipt
4. Query audit_logs for the entries

**Verification SQL:**
```sql
-- Clear previous test data
DELETE FROM receipts WHERE image_url LIKE '%test-audit%';

-- Insert test receipt
INSERT INTO receipts (id, user_id, image_url, status)
VALUES (
  '20000000-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-000000000001',
  'https://test-audit.com/image.jpg',
  'UPLOADED'
);

-- Update the receipt
UPDATE receipts SET status = 'EXTRACTED' 
WHERE id = '20000000-0000-0000-0000-000000000001';

-- Delete the receipt
DELETE FROM receipts WHERE id = '20000000-0000-0000-0000-000000000001';

-- Check audit logs
SELECT table_name, action, record_id, 
       old_values->>'status' as old_status,
       new_values->>'status' as new_status,
       performed_at
FROM audit_logs 
WHERE record_id = '20000000-0000-0000-0000-000000000001'
ORDER BY performed_at;
```

**Expected Result:**
- 3 audit log entries created
- Actions: INSERT, UPDATE, DELETE
- UPDATE shows old_status: UPLOADED, new_status: EXTRACTED

**Pass Criteria:** All 3 operations logged to audit_logs.

**Failure Indicators:**
- Missing audit log entries
- old_values or new_values are null for UPDATE
- Actions recorded incorrectly

**Screenshot/Log Evidence:** SQL query results showing audit log entries.

---

## TEST-DB-06: Journal Entry Balance Constraint

**Objective:** Verify the CHECK constraint prevents unbalanced entries.

**Prerequisites:** Migrations completed

**Steps:**
1. Attempt to insert an unbalanced journal entry
2. Verify constraint violation error

**Verification SQL:**
```sql
-- Attempt unbalanced entry (debits ≠ credits)
INSERT INTO journal_entries (
  id, receipt_id, entry_number, entry_date, 
  total_debit, total_credit, status
)
VALUES (
  '30000000-0000-0000-0000-000000000001',
  '20000000-0000-0000-0000-000000000001',
  'JE-2026-00001',
  '2026-05-08',
  100.00,
  50.00,  -- Unbalanced!
  'POSTED'
);
```

**Expected Result:**
```
ERROR: new row for relation "journal_entries" violates check constraint "chk_balanced"
DETAIL: Failing row contains (30000000-..., 100.00, 50.00).
```

**Pass Criteria:** Constraint violation error prevents insertion.

**Failure Indicators:**
- Entry is inserted successfully
- No error message
- total_debit ≠ total_credit in database

**Screenshot/Log Evidence:** SQL error message showing constraint violation.

---

## TEST-DB-07: Migration Downgrade (Rollback Test)

**Objective:** Verify alembic downgrade works correctly.

**Prerequisites:** All migrations applied

**Steps:**
1. Record current migration: `alembic current`
2. Downgrade one step: `alembic downgrade -1`
3. Verify tables/structures removed
4. Re-upgrade: `alembic upgrade head`
5. Verify tables restored

**Commands:**
```bash
# Check current state
alembic current

# Downgrade to 002
alembic downgrade 002

# Verify RLS policies removed
psql -c "SELECT COUNT(*) FROM pg_policies WHERE tablename = 'receipts';"

# Re-upgrade
alembic upgrade head

# Verify back to normal
alembic current
```

**Expected Result:**
- Downgrade removes triggers and RLS policies
- Re-upgrade restores everything
- No data loss after re-upgrade

**Pass Criteria:** Downgrade and upgrade both complete without errors.

**Failure Indicators:**
- Downgrade fails with dependency errors
- Re-upgrade fails
- Data loss after restore

**Screenshot/Log Evidence:** Terminal output showing successful downgrade/upgrade.

---

# AUTH: Authentication & Authorization

## TEST-AUTH-01: Magic Link Login

**Objective:** Verify magic link authentication works end-to-end.

**Prerequisites:** Valid email address, access to email inbox

**Steps:**
1. Navigate to `/login`
2. Enter email address
3. Click "Send Magic Link"
4. Check email inbox for magic link
5. Click the link in the email
6. Verify redirect to dashboard

**Expected Result:**
- Email received within 60 seconds
- Email subject: "Sign in to [App Name]" or similar
- Clicking link redirects to `/dashboard`
- User is authenticated (can access protected routes)

**Pass Criteria:** User can login via magic link and access dashboard.

**Failure Indicators:**
- Email not received within 2 minutes
- Link returns 404 or invalid token error
- User not authenticated after clicking link

**Screenshot/Log Evidence:** Screenshot of email + dashboard after successful login.

---

## TEST-AUTH-02: Email/Password Login

**Objective:** Verify email/password authentication works.

**Prerequisites:** User account created with email/password

**Steps:**
1. Navigate to `/login`
2. Enter email and password
3. Click "Sign In"
4. Verify redirect to dashboard
5. Check browser DevTools Application tab for JWT cookie

**Expected Result:**
- Successful login redirects to `/dashboard`
- No error toast displayed
- JWT cookie present in Application → Cookies

**Pass Criteria:** User can login with email/password.

**Failure Indicators:**
- "Invalid login credentials" error
- No redirect after login
- Missing JWT cookie

**Screenshot/Log Evidence:** Screenshot of dashboard + DevTools cookies panel.

---

## TEST-AUTH-03: JWT Token Validation

**Objective:** Verify JWT tokens are properly validated on protected routes.

**Prerequisites:** Valid user account

**Steps:**
1. Login to get valid JWT
2. Open DevTools → Network tab
3. Make request to `/api/v1/receipts`
4. Verify Authorization header is included
5. Copy the JWT token
6. Make curl request with invalid token:
   ```bash
   curl -H "Authorization: Bearer invalid_token" https://[backend]/api/v1/receipts
   ```
7. Make curl request with valid token:
   ```bash
   curl -H "Authorization: Bearer [valid_token]" https://[backend]/api/v1/receipts
   ```

**Expected Result:**
- Invalid token returns 401 Unauthorized
- Valid token returns 200 with receipts list

**Pass Criteria:** JWT validation correctly accepts valid and rejects invalid tokens.

**Failure Indicators:**
- Invalid token returns 200
- Valid token returns 401
- No Authorization header sent from frontend

**Screenshot/Log Evidence:** curl output showing 401 for invalid, 200 for valid.

---

## TEST-AUTH-04: Unauthenticated Access Blocked

**Objective:** Verify protected routes return 401 without token.

**Prerequisites:** None

**Steps:**
```bash
# Test without any auth header
curl -i https://[backend]/api/v1/receipts

# Test health endpoint (should work without auth)
curl -i https://[backend]/api/v1/health
```

**Expected Result:**
- `/api/v1/receipts` returns 403 Forbidden or 401 Unauthorized
- `/api/v1/health` returns 200

**Pass Criteria:** Protected routes blocked; public routes accessible.

**Failure Indicators:**
- `/api/v1/receipts` returns 200 with data
- `/api/v1/health` requires authentication

**Screenshot/Log Evidence:** curl output showing correct status codes.

---

## TEST-AUTH-05: Admin Access Control

**Objective:** Verify admin-only endpoints require is_admin flag.

**Prerequisites:** 
- Regular user account
- Admin user account (with `is_admin = TRUE`)

**Steps:**
1. Login as regular user
2. Attempt to access `/api/v1/admin/usage`
   ```bash
   curl -H "Authorization: Bearer [regular_user_token]" https://[backend]/api/v1/admin/usage
   ```
3. Login as admin user
4. Access `/api/v1/admin/usage`
   ```bash
   curl -H "Authorization: Bearer [admin_token]" https://[backend]/api/v1/admin/usage
   ```

**Expected Result:**
- Regular user: 403 Forbidden
- Admin user: 200 with usage stats

**Pass Criteria:** Admin endpoints restricted to admin users only.

**Failure Indicators:**
- Regular user receives 200
- Admin user receives 403

**Screenshot/Log Evidence:** curl output for both requests.

---

# API-B1: Config & JWT

## TEST-API-B1-01: Environment Variables Loaded

**Objective:** Verify all required environment variables are loaded correctly.

**Prerequisites:** Backend running

**Steps:**
1. Check startup logs for configuration
2. Call health endpoint to verify LLM provider is set

```bash
curl -s https://[backend]/api/v1/health | jq
```

**Expected Result:**
```json
{
  "status": "ok",
  "db": "connected",
  "llm_provider": "nvidia_nim" or "ollama",
  "llm_healthy": true,
  "timestamp": "2026-05-08T..."
}
```

**Pass Criteria:** Health endpoint returns `db: connected` and `llm_provider` is set.

**Failure Indicators:**
- `db: disconnected`
- `llm_provider: null` or missing
- 500 error on health endpoint

**Screenshot/Log Evidence:** Health endpoint response JSON.

---

## TEST-API-B1-02: Secret Protection — API Keys Never Exposed

**Objective:** Verify API keys are never returned in responses or logs.

**Prerequisites:** Backend running, access to logs

**Steps:**
1. Make various API requests
2. Search responses for API key patterns
3. Check logs for key exposure
4. Attempt to trigger an error and check error response

```bash
# Make a request
curl -s https://[backend]/api/v1/health

# Try to trigger an error
curl -s -X POST https://[backend]/api/v1/receipts/upload

# Check if any response contains API key pattern
curl -s https://[backend]/api/v1/health | grep -i "nvapi-"
curl -s https://[backend]/api/v1/health | grep -i "service_role"
```

**Expected Result:**
- No responses contain `nvapi-` (NVIDIA key prefix)
- No responses contain `service_role` or `supabase_service_role_key`
- Error responses show generic messages, not stack traces

**Pass Criteria:** No API keys or secrets in any HTTP response.

**Failure Indicators:**
- Response contains full API key
- Error message includes sensitive configuration
- Stack trace in production response

**Screenshot/Log Evidence:** Grep output showing no matches, error response screenshot.

---

## TEST-API-B1-03: JWT Secret Verification

**Objective:** Verify JWT verification uses the correct secret.

**Prerequisites:** Valid JWT token, backend logs

**Steps:**
1. Obtain valid JWT from Supabase Auth
2. Decode the JWT header (not verify) at jwt.io
3. Note the algorithm used
4. Make request with the token

**Expected Result:**
- JWT algorithm: HS256
- Token successfully verified
- User ID extracted from token sub claim

**Pass Criteria:** JWT verification succeeds for valid tokens.

**Failure Indicators:**
- "Invalid token" error for valid token
- Wrong algorithm used
- Token claims not extracted correctly

**Screenshot/Log Evidence:** JWT decoded at jwt.io + successful API response.

---

# API-B2: Pydantic Schema Validation

## TEST-API-B2-01: Line Item Math Validator

**Objective:** Verify line_item_math validator: `abs(qty × unit_price − line_total) ≤ 0.05`

**Prerequisites:** Authenticated user, extracted receipt

**Steps:**
1. Create a correction with invalid line item math
2. Verify 400 error with specific message
3. Create a correction with valid math (within 0.05 tolerance)
4. Verify 200 success

**Test Cases:**

```bash
# Invalid: 2 × 10.00 = 20.00, but line_total = 15.00 (diff = 5.00 > 0.05)
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{
    "line_items": [{
      "description": "Test Item",
      "quantity": 2,
      "unit_price": 10.00,
      "line_total": 15.00
    }]
  }'

# Valid: 2 × 10.00 = 20.00, line_total = 20.02 (diff = 0.02 ≤ 0.05)
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{
    "line_items": [{
      "description": "Test Item",
      "quantity": 2,
      "unit_price": 10.00,
      "line_total": 20.02
    }]
  }'
```

**Expected Result:**
- Invalid: 400 Bad Request with "Line item math error" message
- Valid: 200 OK with updated receipt

**Pass Criteria:** Validator accepts differences ≤ 0.05, rejects > 0.05.

**Failure Indicators:**
- Invalid math accepted with 200
- Valid math rejected with 400
- No validation performed

**Screenshot/Log Evidence:** Both curl responses showing 400 and 200 respectively.

---

## TEST-API-B2-02: Receipt Math Validator

**Objective:** Verify receipt_math validator: `abs(subtotal + tax + tip − total) ≤ 0.05`

**Prerequisites:** Authenticated user, extracted receipt

**Steps:**
Similar to line_item_math, test with various subtotal/tax/tip/total combinations.

**Test Cases:**

```bash
# Invalid: subtotal=50 + tax=5 + tip=5 = 60, but total = 100 (diff = 40)
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{
    "subtotal": 50.00,
    "tax_amount": 5.00,
    "tip_amount": 5.00,
    "total_amount": 100.00
  }'

# Valid: subtotal=50 + tax=5 + tip=5 = 60, total = 60.03 (diff = 0.03)
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{
    "subtotal": 50.00,
    "tax_amount": 5.00,
    "tip_amount": 5.00,
    "total_amount": 60.03
  }'
```

**Expected Result:**
- Invalid: 400 with "Receipt math error" message
- Valid: 200 with updated receipt

**Pass Criteria:** Validator correctly checks receipt math balance.

**Failure Indicators:**
- Invalid math accepted
- Valid math rejected

**Screenshot/Log Evidence:** Both curl responses.

---

## TEST-API-B2-03: Date Sanity Validator

**Objective:** Verify date_sanity validator rejects future dates and dates > 10 years old.

**Prerequisites:** Authenticated user, extracted receipt

**Steps:**

```bash
# Test 1: Future date (should fail)
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"date": "2030-01-01"}'

# Test 2: Date more than 10 years ago (should fail)
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"date": "2000-01-01"}'

# Test 3: Valid date (today or recent)
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"date": "2026-05-07"}'
```

**Expected Result:**
- Future date: 400 "is in the future"
- Old date: 400 "is more than 10 years ago"
- Valid date: 200 OK

**Pass Criteria:** Future and too-old dates rejected; valid dates accepted.

**Failure Indicators:**
- Future date accepted
- 10+ year old date accepted
- Valid date rejected

**Screenshot/Log Evidence:** All three curl responses.

---

## TEST-API-B2-04: Currency Code Validator

**Objective:** Verify currency_code validator accepts only valid ISO 4217 codes.

**Prerequisites:** Authenticated user, extracted receipt

**Steps:**

```bash
# Invalid currency code
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"currency": "XXX"}'

# Valid currency code (USD)
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"currency": "USD"}'

# Valid currency code (EUR)
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"currency": "EUR"}'
```

**Expected Result:**
- Invalid code: 400 "Invalid ISO 4217 currency code"
- Valid codes: 200 OK

**Pass Criteria:** Only valid ISO 4217 codes accepted.

**Failure Indicators:**
- Invalid code accepted
- Valid code rejected

**Screenshot/Log Evidence:** curl responses.

---

## TEST-API-B2-05: Amount Sign Validator

**Objective:** Verify all amount fields must be ≥ 0.

**Prerequisites:** Authenticated user, extracted receipt

**Steps:**

```bash
# Negative total (should fail)
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"total_amount": -50.00}'

# Negative tax (should fail)
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"tax_amount": -5.00}'

# Zero amount (should pass)
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"tax_amount": 0}'

# Positive amount (should pass)
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"total_amount": 50.00}'
```

**Expected Result:**
- Negative amounts: 422 validation error
- Zero and positive: 200 OK

**Pass Criteria:** Negative amounts rejected; non-negative accepted.

**Failure Indicators:**
- Negative amount accepted
- Zero amount rejected

**Screenshot/Log Evidence:** curl responses.

---

## TEST-API-B2-06: Confidence Scores Range

**Objective:** Verify confidence scores are between 0.0 and 1.0.

**Prerequisites:** LLM extraction completed

**Steps:**
1. Get an extracted receipt
2. Check confidence_scores field

```bash
curl -s https://[backend]/api/v1/receipts/[id] \
  -H "Authorization: Bearer [token]" | jq '.confidence_scores'
```

**Expected Result:**
```json
{
  "vendor_name": 0.85,
  "date": 0.92,
  "total_amount": 0.97,
  "subtotal": 0.88,
  "tax_amount": 0.75,
  "line_items": 0.90
}
```

All values between 0.0 and 1.0 inclusive.

**Pass Criteria:** All confidence scores in [0.0, 1.0] range.

**Failure Indicators:**
- Values > 1.0
- Values < 0.0
- Missing confidence_scores field

**Screenshot/Log Evidence:** JSON response showing confidence scores.

---

# API-B3: LLM Client & Extraction

## TEST-API-B3-01: Semaphore Concurrency Control

**Objective:** Verify Semaphore(5) limits concurrent LLM requests.

**Prerequisites:** Backend running, monitoring access

**Steps:**
1. Trigger 10 simultaneous extraction requests
2. Monitor backend logs for queue behavior
3. Verify max 5 concurrent requests

**Note:** This is difficult to test manually without load testing tools. In production, verify via:
- Backend logs showing queue position
- Response times during concurrent loads

**Expected Result:**
- Logs show max 5 concurrent requests
- Additional requests queue with position indicator

**Pass Criteria:** No more than 5 concurrent LLM calls observed.

**Failure Indicators:**
- 6+ concurrent LLM calls in logs
- Rate limit errors from NVIDIA NIM

**Screenshot/Log Evidence:** Backend logs during concurrent load.

---

## TEST-API-B3-02: Provider Switching (NVIDIA/Ollama)

**Objective:** Verify system correctly selects LLM provider based on environment.

**Prerequisites:** 
- Access to two environments (one with NVIDIA, one with Ollama)

**Steps:**
1. Check health endpoint on NVIDIA-configured environment
2. Check health endpoint on Ollama-configured environment

```bash
# NVIDIA environment
curl -s https://[nvidia-backend]/api/v1/health | jq '.llm_provider'
# Expected: "nvidia_nim"

# Ollama environment
curl -s https://[ollama-backend]/api/v1/health | jq '.llm_provider'
# Expected: "ollama"
```

**Expected Result:**
- NVIDIA environment shows `llm_provider: "nvidia_nim"`
- Ollama environment shows `llm_provider: "ollama"`

**Pass Criteria:** Correct provider detected and reported.

**Failure Indicators:**
- Wrong provider reported
- Provider null or missing

**Screenshot/Log Evidence:** Health endpoint responses from both environments.

---

## TEST-API-B3-03: Exponential Backoff on Rate Limit (429)

**Objective:** Verify backoff delays: 3s, 9s, 27s on HTTP 429.

**Prerequisites:** 
- NVIDIA NIM configured
- Ability to trigger rate limiting (difficult in practice)

**Steps:**
1. Make rapid sequential extraction requests
2. Monitor backend logs for retry behavior
3. Note timing of retries

**Expected Log Pattern{}
```
WARNING:app.llm_client:NVIDIA NIM 429 rate limit. Retrying in 3s (attempt 1/3)
WARNING:app.llm_client:NVIDIA NIM 429 rate limit. Retrying in 9s (attempt 2/3)
WARNING:app.llm_client:NVIDIA NIM 429 rate limit. Retrying in 27s (attempt 3/3)
```

**Expected Result:**
- Backoff delays of 3s, 9s, 27s logged
- After 3 retries, appropriate error returned to client

**Pass Criteria:** Backoff delays match specification.

**Failure Indicators:**
- Immediate retry (no delay)
- Same delay repeated
- More than 3 retries

**Screenshot/Log Evidence:** Backend logs showing backoff timing.

---

## TEST-API-B3-04: JSON Repair on Malformed Output

**Objective:** Verify json_repair handles malformed LLM output.

**Prerequisites:** 
- Backend running
- Test receipt image

**Steps:**
1. Upload a receipt
2. Trigger extraction
3. Check if extraction succeeds even if LLM returns slightly malformed JSON

**Note:** This is tested implicitly during normal extraction. Malformed outputs that can be repaired will succeed.

**Expected Result:**
- Extraction succeeds with valid JSON
- If unrepairable, status becomes EXTRACTION_FAILED with raw_llm_output preserved

**Pass Criteria:** JSON repair handles common LLM output issues.

**Failure Indicators:**
- Extraction fails on minor JSON issues
- No raw_llm_output preserved on failure

**Screenshot/Log Evidence:** Successful extraction after JSON repair.

---

## TEST-API-B3-05: Image Encoding (Base64 JPEG 85%)

**Objective:** Verify images are re-encoded to JPEG at 85% quality before LLM.

**Prerequisites:** 
- Various image formats (PNG, HEIC, large JPEG)
- Backend logs access

**Steps:**
1. Upload PNG image (test transparency handling)
2. Upload HEIC image (test format conversion)
3. Upload large image > 5MB
4. Check logs for encoding confirmation
5. Verify extraction succeeds

**Expected Result:**
- All formats successfully encoded to JPEG
- Image quality 85% (reduced file size)
- Transparent images converted to RGB

**Pass Criteria:** All image formats handled correctly.

**Failure Indicators:**
- PNG with transparency fails
- HEIC format not recognized
- Large images cause timeout

**Screenshot/Log Evidence:** Successful extractions from various formats.

---

## TEST-API-B3-06: Queue Position Returned on Rate Limit

**Objective:** Verify queue position is returned, not raw 429 error.

**Prerequisites:** 
- Backend running
- Concurrent extraction requests

**Steps:**
1. Trigger multiple extractions simultaneously
2. Check response for queue_position field

```bash
curl -s -X POST https://[backend]/api/v1/receipts/[id]/extract \
  -H "Authorization: Bearer [token]" | jq
```

**Expected Result:**
```json
{
  "id": "...",
  "status": "EXTRACTING",
  "queue_position": 3
}
```

**Pass Criteria:** Response includes queue_position, not HTTP 429 error.

**Failure Indicators:**
- HTTP 429 returned to client
- No queue_position in response
- Client sees "Too Many Requests" error

**Screenshot/Log Evidence:** Extraction response showing queue_position.

---

# API-B4: Receipt Endpoints & State Machine

## TEST-API-B4-01: Upload Receipt (Success)

**Objective:** Verify successful receipt upload with valid file.

**Prerequisites:** 
- Authenticated user
- Valid image file (JPEG, PNG, HEIC, or PDF)
- File < 20MB

**Steps:**

```bash
# Upload a JPEG image
curl -X POST https://[backend]/api/v1/receipts/upload \
  -H "Authorization: Bearer [token]" \
  -F "file=@test_receipt.jpg"
```

**Expected Result:**
```json
{
  "id": "uuid-here",
  "status": "UPLOADED",
  "image_url": "https://supabase.co/storage/...",
  "created_at": "2026-05-08T..."
}
```

**Pass Criteria:** 
- Status code: 201
- Returns valid receipt ID
- Signed image URL generated

**Failure Indicators:**
- 400 Bad Request
- 413 Request Entity Too Large
- Missing image_url

**Screenshot/Log Evidence:** curl response with 201 status.

---

## TEST-API-B4-02: Upload Receipt (Invalid File Type)

**Objective:** Verify rejection of unsupported file types.

**Prerequisites:** Authenticated user

**Steps:**

```bash
# Try to upload a text file
curl -X POST https://[backend]/api/v1/receipts/upload \
  -H "Authorization: Bearer [token]" \
  -F "file=@test.txt"

# Try to upload a video
curl -X POST https://[backend]/api/v1/receipts/upload \
  -H "Authorization: Bearer [token]" \
  -F "file=@video.mp4"
```

**Expected Result:**
- Status code: 400 Bad Request
- Error message: "Invalid file type: text/plain. Allowed: image/jpeg, image/png, ..."

**Pass Criteria:** Non-image/PDF files rejected with 400.

**Failure Indicators:**
- File accepted with 201
- No validation error

**Screenshot/Log Evidence:** 400 error response.

---

## TEST-API-B4-03: Upload Receipt (File Too Large)

**Objective:** Verify 20MB file size limit.

**Prerequisites:** 
- Authenticated user
- File > 20MB

**Steps:**

```bash
# Create a 21MB test file
dd if=/dev/zero of=large_file.jpg bs=1M count=21

# Attempt upload
curl -X POST https://[backend]/api/v1/receipts/upload \
  -H "Authorization: Bearer [token]" \
  -F "file=@large_file.jpg"
```

**Expected Result:**
- Status code: 413 Request Entity Too Large
- Error message: "File too large: 22020096 bytes. Maximum: 20971520 bytes (20 MB)"

**Pass Criteria:** Files > 20MB rejected with 413.

**Failure Indicators:**
- Large file accepted
- No size validation

**Screenshot/Log Evidence:** 413 error response.

---

## TEST-API-B4-04: Upload Receipt (Daily Limit)

**Objective:** Verify daily upload limit of 20 receipts.

**Prerequisites:** 
- Authenticated user
- Already uploaded 20 receipts today

**Steps:**
1. Upload 20 receipts
2. Attempt to upload 21st receipt

```bash
# After 20 uploads, try another
curl -X POST https://[backend]/api/v1/receipts/upload \
  -H "Authorization: Bearer [token]" \
  -F "file=@receipt21.jpg"
```

**Expected Result:**
- Status code: 429 Too Many Requests
- Error message: "Daily receipt limit reached (20). Try again tomorrow."

**Pass Criteria:** 21st upload rejected with 429.

**Failure Indicators:**
- 21st upload accepted
- Wrong error code

**Screenshot/Log Evidence:** 429 error response.

---

## TEST-API-B4-05: Trigger Extraction (Success)

**Objective:** Verify extraction can be triggered on UPLOADED receipt.

**Prerequisites:** 
- Uploaded receipt in UPLOADED status
- Authenticated user

**Steps:**

```bash
curl -X POST https://[backend]/api/v1/receipts/[receipt_id]/extract \
  -H "Authorization: Bearer [token]"
```

**Expected Result:**
```json
{
  "id": "receipt-uuid",
  "status": "EXTRACTED" or "EXTRACTING",
  "queue_position": 0
}
```

**Pass Criteria:** 
- Status code: 202 Accepted
- Receipt transitions to EXTRACTING/EXTRACTED

**Failure Indicators:**
- 409 Conflict (wrong status)
- 500 error

**Screenshot/Log Evidence:** 202 response with updated status.

---

## TEST-API-B4-06: Get Receipt (Full Data)

**Objective:** Verify GET returns complete receipt data with signed URL.

**Prerequisites:** 
- Extracted receipt
- Authenticated user

**Steps:**

```bash
curl -s https://[backend]/api/v1/receipts/[receipt_id] \
  -H "Authorization: Bearer [token]" | jq
```

**Expected Result:**
```json
{
  "id": "uuid",
  "status": "EXTRACTED",
  "image_url": "https://supabase.co/storage/sign/...",
  "original_filename": "receipt.jpg",
  "mime_type": "image/jpeg",
  "file_size_bytes": 1234567,
  "extracted_data": {
    "vendor_name": "Starbucks",
    "date": "2026-05-07",
    "currency": "USD",
    "subtotal": 15.50,
    "tax_amount": 1.40,
    "tip_amount": 2.00,
    "total_amount": 18.90,
    "payment_method": "Card",
    "line_items": [...]
  },
  "confidence_scores": {...},
  "extracted_at": "2026-05-08T...",
  "created_at": "2026-05-08T...",
  "updated_at": "2026-05-08T..."
}
```

**Pass Criteria:** 
- All fields populated
- Signed URL valid (accessible)
- extracted_data contains LLM output

**Failure Indicators:**
- Missing extracted_data
- Unsigned/invalid image URL
- Wrong receipt returned

**Screenshot/Log Evidence:** Full JSON response.

---

## TEST-API-B4-07: Correct Receipt (Partial Update)

**Objective:** Verify partial update of extracted data.

**Prerequisites:** 
- Extracted receipt
- Authenticated user

**Steps:**

```bash
# Update only vendor_name and total
curl -X PUT https://[backend]/api/v1/receipts/[receipt_id]/correct \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_name": "Correct Vendor Name",
    "total_amount": 25.00
  }'
```

**Expected Result:**
```json
{
  "id": "uuid",
  "status": "REVIEWED",
  "extracted_data": {
    "vendor_name": "Correct Vendor Name",
    ...
    "total_amount": 25.00
  },
  "reviewed_at": "2026-05-08T..."
}
```

**Pass Criteria:** 
- Status code: 200
- Only specified fields updated
- Status transitions to REVIEWED

**Failure Indicators:**
- All fields overwritten
- Status remains EXTRACTED
- Validation errors on partial data

**Screenshot/Log Evidence:** Before/after comparison.

---

## TEST-API-B4-08: Journalize Receipt (Success)

**Objective:** Verify journal entry creation from reviewed receipt.

**Prerequisites:** 
- Receipt in REVIEWED status
- Authenticated user

**Steps:**

```bash
curl -X POST https://[backend]/api/v1/receipts/[receipt_id]/journalize \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Result:**
```json
{
  "journal_entry_id": "uuid",
  "entry_number": "JE-2026-00001",
  "status": "POSTED",
  "total_debit": 18.90,
  "total_credit": 18.90
}
```

**Pass Criteria:** 
- Status code: 201
- Journal entry created
- total_debit == total_credit

**Failure Indicators:**
- 422 Unprocessable Entity
- Debits ≠ credits
- No journal entry created

**Screenshot/Log Evidence:** 201 response with journal entry details.

---

## TEST-API-B4-09: Journalize with Account Overrides

**Objective:** Verify account_overrides parameter works.

**Prerequisites:** 
- Receipt in REVIEWED status
- Valid account codes

**Steps:**

```bash
curl -X POST https://[backend]/api/v1/receipts/[receipt_id]/journalize \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{
    "account_overrides": {
      "expense": "5200",
      "payment": "1020"
    }
  }'
```

**Expected Result:**
- Journal entry uses account 5200 for expense debit
- Journal entry uses account 1020 for credit

**Pass Criteria:** Overridden accounts used in journal entry lines.

**Failure Indicators:**
- Default accounts used instead
- Error on invalid account code

**Screenshot/Log Evidence:** Journal entry lines showing override accounts.

---

## State Machine Tests

### TEST-API-B4-10: Valid Transition — UPLOADED → EXTRACTING

**Objective:** Verify valid state transition.

**Steps:**
1. Create receipt with status UPLOADED
2. Trigger extraction
3. Verify status changes to EXTRACTING

**Expected Result:** Status transitions successfully.

---

### TEST-API-B4-11: Valid Transition — EXTRACTING → EXTRACTED

**Objective:** Verify valid state transition.

**Steps:**
1. Receipt in EXTRACTING status
2. Extraction completes successfully
3. Verify status changes to EXTRACTED

**Expected Result:** Status transitions successfully.

---

### TEST-API-B4-12: Valid Transition — EXTRACTING → EXTRACTION_FAILED

**Objective:** Verify valid state transition on LLM failure.

**Steps:**
1. Receipt in EXTRACTING status
2. Trigger LLM failure (use invalid/unparseable image)
3. Verify status changes to EXTRACTION_FAILED

**Expected Result:** Status transitions to EXTRACTION_FAILED with error message.

---

### TEST-API-B4-13: Valid Transition — EXTRACTED → REVIEWED

**Objective:** Verify valid state transition after correction.

**Steps:**
1. Receipt in EXTRACTED status
2. Submit correction via /correct endpoint
3. Verify status changes to REVIEWED

**Expected Result:** Status transitions to REVIEWED with reviewed_at timestamp.

---

### TEST-API-B4-14: Valid Transition — REVIEWED → POSTED

**Objective:** Verify valid state transition after journalizing.

**Steps:**
1. Receipt in REVIEWED status
2. Call /journalize endpoint
3. Verify status changes to POSTED

**Expected Result:** Status transitions to POSTED with journal entry created.

---

### TEST-API-B4-15: Valid Transition — REVIEWED → REJECTED

**Objective:** Verify valid state transition on rejection.

**Steps:**
1. Receipt in REVIEWED status
2. Reject the receipt (if implemented)
3. Verify status changes to REJECTED

**Expected Result:** Status transitions to REJECTED (terminal state).

---

### TEST-API-B4-16: Valid Transition — REVIEWED → QUARANTINED

**Objective:** Verify valid state transition on bookkeeping assertion failure.

**Steps:**
1. Receipt in REVIEWED status with unbalanced data
2. Attempt to journalize
3. Verify status changes to QUARANTINED

**Expected Result:** Status transitions to QUARANTINED, audit log written.

---

### TEST-API-B4-17: Valid Transition — EXTRACTION_FAILED → EXTRACTING (Retry)

**Objective:** Verify retry is allowed.

**Steps:**
1. Receipt in EXTRACTION_FAILED status
2. Trigger extraction again
3. Verify status changes to EXTRACTING

**Expected Result:** Retry allowed, status transitions to EXTRACTING.

---

## Invalid State Transition Tests (Must Return 409)

### TEST-API-B4-18: Invalid Transition — EXTRACTED → EXTRACTING

**Objective:** Verify 409 on invalid transition.

```bash
# Receipt in EXTRACTED status
curl -X POST https://[backend]/api/v1/receipts/[id]/extract \
  -H "Authorization: Bearer [token]"
```

**Expected:** 409 Conflict with message about invalid transition.

---

### TEST-API-B4-19: Invalid Transition — POSTED → EXTRACTING

**Objective:** Verify 409 on invalid transition (immutability).

**Expected:** 409 Conflict.

---

### TEST-API-B4-20: Invalid Transition — POSTED → REVIEWED

**Objective:** Verify 409 on invalid transition (immutability).

**Expected:** 409 Conflict.

---

### TEST-API-B4-21: Invalid Transition — POSTED → CORRECT

**Objective:** Verify posted receipts cannot be corrected.

```bash
curl -X PUT https://[backend]/api/v1/receipts/[id]/correct \
  -H "Authorization: Bearer [token]" \
  -d '{"vendor_name": "New Name"}'
```

**Expected:** 409 Conflict "Cannot correct a posted receipt".

---

### TEST-API-B4-22: Invalid Transition — REJECTED → EXTRACTING

**Objective:** Verify 409 on terminal state.

**Expected:** 409 Conflict.

---

### TEST-API-B4-23: Invalid Transition — QUARANTINED → EXTRACTING

**Objective:** Verify 409 on terminal state.

**Expected:** 409 Conflict.

---

### TEST-API-B4-24: Invalid Transition — UPLOADED → REVIEWED

**Objective:** Verify 409 (must extract first).

**Expected:** 409 Conflict.

---

### TEST-API-B4-25: Invalid Transition — UPLOADED → POSTED

**Objective:** Verify 409 (must extract and review first).

**Expected:** 409 Conflict.

---

# API-B5: Bookkeeping Engine

## TEST-API-B5-01: Vendor Lookup (Case-Insensitive)

**Objective:** Verify vendor lookup matches case-insensitively.

**Prerequisites:** 
- Vendor mapping exists: "uber" → "5100 Travel Expense"
- Test receipt from "UBER TECHNOLOGIES"

**Steps:**
1. Upload receipt with vendor "UBER TECHNOLOGIES"
2. Extract and journalize
3. Check journal entry uses account 5100

**Verification SQL:**
```sql
SELECT * FROM vendor_category_mappings WHERE vendor_name_pattern ILIKE '%uber%';
```

**Expected Result:**
- Journal entry debit line uses account code matching vendor pattern
- Case-insensitive match succeeds

**Pass Criteria:** Correct account code used regardless of case.

**Failure Indicators:**
- Fallback account 5999 used when mapping exists
- Case-sensitive matching fails

**Screenshot/Log Evidence:** Journal entry lines showing correct account.

---

## TEST-API-B5-02: Vendor Fallback (Account 5999)

**Objective:** Verify unknown vendors default to 5999 Miscellaneous Expense.

**Prerequisites:** 
- Receipt from completely unknown vendor "XYZABC123"

**Steps:**
1. Upload receipt with unrecognized vendor
2. Extract and journalize
3. Check journal entry uses account 5999

**Expected Result:**
- Journal entry debit line uses account 5999
- Account name: "Miscellaneous Expense"

**Pass Criteria:** Unknown vendors mapped to 5999.

**Failure Indicators:**
- Error on unknown vendor
- No journal entry created

**Screenshot/Log Evidence:** Journal entry showing 5999 account.

---

## TEST-API-B5-03: Payment Method — Cash (Credit to 1010)

**Objective:** Verify Cash payment creates credit to account 1010.

**Prerequisites:** Receipt with payment_method: "Cash"

**Steps:**
1. Upload and extract receipt with payment_method: "Cash"
2. Journalize
3. Check credit line uses account 1010 "Cash"

**Expected Result:**
```
Credit line:
  account_code: "1010"
  account_name: "Cash"
  credit: [total_amount]
```

**Pass Criteria:** Credit uses account 1010 for Cash.

**Failure Indicators:**
- Wrong account code
- Missing credit line

**Screenshot/Log Evidence:** Journal entry lines.

---

## TEST-API-B5-04: Payment Method — Card (Credit to 2010)

**Objective:** Verify Card payment creates credit to account 2010.

**Prerequisites:** Receipt with payment_method: "Card"

**Steps:**
Same as above, verify account 2010 "Credit Card Liability".

**Expected Result:**
```
Credit line:
  account_code: "2010"
  account_name: "Credit Card Liability"
  credit: [total_amount]
```

**Pass Criteria:** Credit uses account 2010 for Card.

---

## TEST-API-B5-05: Payment Method — Check (Credit to 1020)

**Objective:** Verify Check payment creates credit to account 1020.

**Prerequisites:** Receipt with payment_method: "Check"

**Expected Result:**
```
Credit line:
  account_code: "1020"
  account_name: "Checking Account"
  credit: [total_amount]
```

**Pass Criteria:** Credit uses account 1020 for Check.

---

## TEST-API-B5-06: Payment Method — Split (Credit to 1010)

**Objective:** Verify Split payment creates credit to account 1010.

**Prerequisites:** Receipt with payment_method: "Split"

**Expected Result:**
```
Credit line:
  account_code: "1010"
  account_name: "Cash"
  credit: [total_amount]
```

**Pass Criteria:** Credit uses account 1010 for Split.

---

## TEST-API-B5-07: Payment Method — Null/Unknown (Credit to 2000)

**Objective:** Verify null payment method defaults to 2000 Accounts Payable.

**Prerequisites:** Receipt with payment_method: null

**Expected Result:**
```
Credit line:
  account_code: "2000"
  account_name: "Accounts Payable"
  credit: [total_amount]
```

**Pass Criteria:** Credit uses account 2000 when payment method unknown.

---

## TEST-API-B5-08: Tax Line (Debit to 2100)

**Objective:** Verify tax amount creates separate debit line.

**Prerequisites:** Receipt with tax_amount > 0

**Expected Result:**
```
Debit line:
  account_code: "2100"
  account_name: "Sales Tax Payable"
  debit: [tax_amount]
```

**Pass Criteria:** Separate tax debit line created.

---

## TEST-API-B5-09: Tip Line (Debit to 5300)

**Objective:** Verify tip amount creates separate debit line.

**Prerequisites:** Receipt with tip_amount > 0

**Expected Result:**
```
Debit line:
  account_code: "5300"
  account_name: "Meals & Entertainment"
  debit: [tip_amount]
```

**Pass Criteria:** Separate tip debit line created.

---

## TEST-API-B5-10: Full Journal Entry Structure

**Objective:** Verify complete journal entry with expense, tax, tip, and payment.

**Prerequisites:** 
- Receipt with:
  - subtotal: $50.00
  - tax_amount: $4.50
  - tip_amount: $10.00
  - total_amount: $64.50
  - payment_method: "Card"

**Expected Journal Entry Lines:**
```
Line 1 (Debit):  Account [vendor_account]  $50.00
Line 2 (Debit):  Account 2100 Tax          $4.50
Line 3 (Debit):  Account 5300 Tip          $10.00
Line 4 (Credit): Account 2010 Card         $64.50

Total Debit:  $64.50
Total Credit: $64.50
```

**Pass Criteria:** 
- All lines present with correct amounts
- Debits = Credits

**Screenshot/Log Evidence:** Full journal entry JSON.

---

## TEST-API-B5-11: Bookkeeping Assertion Failure (Quarantine)

**Objective:** Verify unbalanced entries are quarantined, not posted.

**Prerequisites:** 
- Receipt with math that would create imbalance
- (This is difficult to trigger normally; requires corrupted data)

**Steps:**
1. Manually update receipt extracted_data to have unbalanced amounts
2. Attempt to journalize
3. Verify receipt status becomes QUARANTINED
4. Check audit_logs for quarantine entry

**Expected Result:**
- Status code: 422 Unprocessable Entity
- Receipt status: QUARANTINED
- audit_logs contains entry with error details
- No journal entry created

**Pass Criteria:** Unbalanced entries never enter the ledger.

**Failure Indicators:**
- Unbalanced journal entry posted
- Receipt not quarantined
- No audit log entry

**Screenshot/Log Evidence:** 
- 422 response
- Receipt status QUARANTINED
- Audit log query results

---

## TEST-API-B5-12: Entry Number Format

**Objective:** Verify entry number format: JE-YYYY-XXXXX.

**Prerequisites:** Journal entry created

**Steps:**
1. Journalize a receipt
2. Check entry_number field

**Expected Result:**
```
entry_number: "JE-2026-00001"
```
Format: `JE-[4-digit year]-[5-digit zero-padded sequence]`

**Pass Criteria:** Entry number matches format exactly.

**Failure Indicators:**
- Wrong format
- Missing year
- Non-zero-padded sequence

**Screenshot/Log Evidence:** Journal entry response showing entry_number.

---

## TEST-API-B5-13: Entry Number Sequence

**Objective:** Verify sequence increments correctly.

**Prerequisites:** Create multiple journal entries

**Steps:**
1. Create first journal entry → note number
2. Create second journal entry → note number
3. Verify increment

**Expected Result:**
```
Entry 1: JE-2026-00001
Entry 2: JE-2026-00002
Entry 3: JE-2026-00003
```

**Pass Criteria:** Sequence increments by 1.

**Failure Indicators:**
- Same number repeated
- Non-sequential numbers
- Gaps in sequence

**Screenshot/Log Evidence:** Multiple entry numbers.

---

# API-B6: Journal Entry Endpoints

## TEST-API-B6-01: List Journal Entries (Pagination)

**Objective:** Verify paginated list with 25 rows default.

**Prerequisites:** 
- 30+ journal entries in database
- Authenticated user

**Steps:**

```bash
# Get first page (default 25)
curl -s "https://[backend]/api/v1/journal-entries" \
  -H "Authorization: Bearer [token]" | jq

# Get page 2
curl -s "https://[backend]/api/v1/journal-entries?page=2" \
  -H "Authorization: Bearer [token]" | jq

# Get with custom page size
curl -s "https://[backend]/api/v1/journal-entries?page=1&per_page=10" \
  -H "Authorization: Bearer [token]" | jq
```

**Expected Result:**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total": 30,
    "total_pages": 2
  }
}
```

**Pass Criteria:** 
- Default 25 entries per page
- Pagination metadata accurate
- Correct entries on each page

**Failure Indicators:**
- All entries returned (no pagination)
- Wrong page size
- Missing pagination metadata

**Screenshot/Log Evidence:** Two page responses.

---

## TEST-API-B6-02: List with Date Filters

**Objective:** Verify filtering by date range.

**Prerequisites:** Journal entries with various dates

**Steps:**

```bash
curl -s "https://[backend]/api/v1/journal-entries?date_from=2026-05-01&date_to=2026-05-07" \
  -H "Authorization: Bearer [token]" | jq
```

**Expected Result:** Only entries within date range returned.

**Pass Criteria:** Date filters work correctly.

---

## TEST-API-B6-03: List with Vendor Filter

**Objective:** Verify filtering by vendor name.

**Prerequisites:** Journal entries with various vendors

**Steps:**

```bash
curl -s "https://[backend]/api/v1/journal-entries?vendor=starbucks" \
  -H "Authorization: Bearer [token]" | jq
```

**Expected Result:** Only entries with "starbucks" in reference field.

**Pass Criteria:** Vendor filter performs case-insensitive match.

---

## TEST-API-B6-04: List with Status Filter

**Objective:** Verify filtering by status.

**Prerequisites:** Journal entries with various statuses

**Steps:**

```bash
curl -s "https://[backend]/api/v1/journal-entries?status=POSTED" \
  -H "Authorization: Bearer [token]" | jq
```

**Expected Result:** Only POSTED entries returned.

**Pass Criteria:** Status filter works.

---

## TEST-API-B6-05: Get Journal Entry by ID

**Objective:** Verify single entry retrieval with lines and image URL.

**Prerequisites:** Existing journal entry

**Steps:**

```bash
curl -s "https://[backend]/api/v1/journal-entries/[id]" \
  -H "Authorization: Bearer [token]" | jq
```

**Expected Result:**
```json
{
  "id": "uuid",
  "receipt_id": "uuid",
  "entry_number": "JE-2026-00001",
  "entry_date": "2026-05-08",
  "reference": "Starbucks - 2026-05-07",
  "description": "Receipt from Starbucks",
  "total_debit": 18.90,
  "total_credit": 18.90,
  "status": "POSTED",
  "lines": [
    {
      "id": "uuid",
      "account_code": "5100",
      "account_name": "Travel Expense",
      "debit": 15.50,
      "credit": 0,
      "line_order": 1
    },
    ...
  ],
  "receipt_image_url": "https://supabase.co/storage/sign/..."
}
```

**Pass Criteria:** 
- All fields present
- Lines included
- Receipt image URL accessible

**Failure Indicators:**
- Missing lines
- Missing receipt_image_url
- Wrong entry returned

**Screenshot/Log Evidence:** Full JSON response.

---

## TEST-API-B6-06: Reverse Journal Entry

**Objective:** Verify reversal creates mirror entry.

**Prerequisites:** 
- POSTED journal entry
- Authenticated user

**Steps:**

```bash
curl -X DELETE "https://[backend]/api/v1/journal-entries/[id]/reverse" \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"reason": "Duplicate entry - clerical error"}'
```

**Expected Result:**
- Status code: 201
- New journal entry created with swapped debits/credits
- Original entry status: REVERSED
- New entry has `reversal_of_id` pointing to original

**Pass Criteria:** 
- Mirror entry created
- Original never deleted
- Both entries visible in ledger

**Failure Indicators:**
- Original entry deleted
- No mirror entry created
- Status not updated to REVERSED

**Screenshot/Log Evidence:** 
- Original entry showing REVERSED status
- Reversal entry showing swapped amounts
- Both entries in list

---

## TEST-API-B6-07: Reverse Already Reversed Entry

**Objective:** Verify cannot reverse a reversal.

**Prerequisites:** Entry that is already a reversal

**Steps:**
1. Create reversal of entry A (entry B)
2. Try to reverse entry B

**Expected Result:**
- Status code: 409 Conflict
- Error: "This entry is itself a reversal and cannot be reversed again"

**Pass Criteria:** Reversal entries cannot be reversed.

---

## TEST-API-B6-08: Double Reversal Prevention

**Objective:** Verify cannot reverse same entry twice.

**Prerequisites:** Entry that has already been reversed

**Steps:**
1. Reverse entry A (creates entry B)
2. Try to reverse entry A again

**Expected Result:**
- Status code: 409 Conflict
- Error: "This entry has already been reversed"

**Pass Criteria:** Single reversal only.

---

## TEST-API-B6-09: Health Endpoint

**Objective:** Verify health endpoint returns db + llm_provider status.

**Steps:**

```bash
curl -s https://[backend]/api/v1/health | jq
```

**Expected Result:**
```json
{
  "status": "ok",
  "db": "connected",
  "llm_provider": "nvidia_nim",
  "llm_healthy": true,
  "timestamp": "2026-05-08T12:00:00Z"
}
```

**Pass Criteria:** 
- db: "connected"
- llm_provider populated
- No authentication required

**Failure Indicators:**
- db: "disconnected"
- llm_healthy: false
- 401 error

**Screenshot/Log Evidence:** Health endpoint response.

---

## TEST-API-B6-10: Export CSV

**Objective:** Verify CSV export functionality.

**Prerequisites:** Journal entries exist

**Steps:**

```bash
curl -s "https://[backend]/api/v1/journal-entries/export/csv" \
  -H "Authorization: Bearer [token]" \
  -o entries.csv

# Check CSV structure
head -5 entries.csv
```

**Expected Result:**
- CSV file downloaded
- Headers: entry_number, entry_date, account_code, account_name, debit, credit, description
- Multiple rows for multi-line entries

**Pass Criteria:** Valid CSV with correct structure.

---

## TEST-API-B6-11: Export PDF

**Objective:** Verify PDF export functionality.

**Prerequisites:** Journal entries exist

**Steps:**

```bash
curl -s "https://[backend]/api/v1/journal-entries/export/pdf" \
  -H "Authorization: Bearer [token]" \
  -o entries.pdf

# Verify PDF
file entries.pdf
```

**Expected Result:**
- PDF file downloaded
- Valid PDF format
- Contains journal entry data

**Pass Criteria:** Valid PDF generated.

---

# API-B7: Error Handling

## TEST-API-B7-01: NVIDIA NIM 429 → Queue Position

**Objective:** Verify rate limit returns queue position, not raw 429.

**Prerequisites:** 
- NVIDIA NIM configured
- Backend under load

**Steps:**
1. Trigger multiple concurrent extractions
2. Check response for queue_position

**Expected Result:**
- Response includes queue_position
- No HTTP 429 returned to client
- Client sees "Queue position: X" message

**Pass Criteria:** Client receives queue position, not error.

**Failure Indicators:**
- HTTP 429 returned to client
- No queue_position in response
- Client sees "Too Many Requests" error

**Screenshot/Log Evidence:** Response showing queue_position.

---

## TEST-API-B7-02: EXTRACTION_FAILED Preserves raw_llm_output

**Objective:** Verify raw LLM output preserved on extraction failure.

**Prerequisites:** 
- Receipt that will fail extraction (blurry/corrupted image)

**Steps:**
1. Upload problematic receipt
2. Trigger extraction
3. Wait for EXTRACTION_FAILED status
4. Get receipt and check raw_llm_output field

```bash
curl -s "https://[backend]/api/v1/receipts/[id]" \
  -H "Authorization: Bearer [token]" | jq '.raw_llm_output'
```

**Expected Result:**
- raw_llm_output contains the LLM's raw response
- extraction_error contains error message
- Status: EXTRACTION_FAILED

**Pass Criteria:** Raw LLM output preserved for debugging.

**Failure Indicators:**
- raw_llm_output is null
- No extraction_error
- Unable to debug failure

**Screenshot/Log Evidence:** Receipt JSON with raw_llm_output.

---

## TEST-API-B7-03: QUARANTINED Logs to Audit

**Objective:** Verify quarantined entries are logged to audit_logs.

**Prerequisites:** 
- Receipt that will trigger bookkeeping assertion failure

**Steps:**
1. Create receipt with unbalanced amounts
2. Trigger quarantine
3. Query audit_logs

```sql
SELECT * FROM audit_logs 
WHERE new_values->>'status' = 'QUARANTINED'
ORDER BY performed_at DESC
LIMIT 1;
```

**Expected Result:**
- Audit log entry created
- Action: UPDATE
- new_values includes error details

**Pass Criteria:** Quarantine events logged.

**Failure Indicators:**
- No audit log entry
- Missing error details

**Screenshot/Log Evidence:** Audit log query results.

---

## TEST-API-B7-04: No Stack Traces in Production

**Objective:** Verify production errors don't expose stack traces.

**Prerequisites:** Production environment

**Steps:**
1. Trigger various errors:
   - Invalid JSON body
   - Missing required field
   - Non-existent resource
   - Internal server error trigger

```bash
# Invalid JSON
curl -X POST https://[backend]/api/v1/receipts/upload \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{invalid json'

# Missing required field
curl -X POST https://[backend]/api/v1/receipts/[id]/journalize \
  -{}
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{"account_overrides": '
```

**Expected Result:**
- Generic error messages
- No file paths
- No line numbers
- No function names

**Pass Criteria:** All error responses are user-friendly, no stack traces.

**Failure Indicators:**
- "File "/app/..." line 123" in response
- "TypeError: ..." with code context
- Raw Python exception

**Screenshot/Log Evidence:** Error responses showing clean messages.

---

# UI-D: Design System

## TEST-UI-D-01: Font Stack

**Objective:** Verify correct fonts are loaded (Manrope/Inter/Space Grotesk).

**Prerequisites:** Frontend deployed

**Steps:**
1. Open frontend in browser
2. Open DevTools → Network tab → Filter for "font"
3. Reload page
4. Check which fonts are loaded

**Expected Result:**
- Manrope loaded for headings
- Inter loaded for body text
- Space Grotesk loaded for monospace/technical text

**Pass Criteria:** All three fonts loaded successfully.

**Failure Indicators:**
- Fallback fonts (Arial, system-ui) used
- 404 errors on font files
- FOUT (flash of unstyled text)

**Screenshot/Log Evidence:** Network tab showing font files loaded.

---

## TEST-UI-D-02: Color Scheme — Deep Indigo Background

**Objective:** Verify background color is Deep Indigo #0b1326.

**Prerequisites:** Frontend deployed

**Steps:**
1. Open frontend in browser
2. Right-click background → Inspect
3. Check computed background-color

**Expected Result:**
```css
background-color: rgb(11, 19, 38); /* #0b1326 */
```

**Pass Criteria:** Background matches Deep Indigo specification.

**Failure Indicators:**
- Different background color
- White or light background

**Screenshot/Log Evidence:** DevTools showing background color.

---

## TEST-UI-D-03: Glassmorphism Effect

**Objective:** Verify glass panels have blur(20px) effect.

**Prerequisites:** Frontend deployed

**Steps:**
1. Locate a glass-panel element
2. Right-click → Inspect
3. Check CSS backdrop-filter property

**Expected Result:**
```css
backdrop-filter: blur(20px);
-webkit-backdrop-filter: blur(20px);
```

**Pass Criteria:** Glass panels have 20px blur effect.

**Failure Indicators:**
- No blur effect
- Solid opaque panels
- blur() missing or different value

**Screenshot/Log Evidence:** DevTools showing backdrop-filter.

---

## TEST-UI-D-04: Status Badge Colors

**Objective:** Verify status badges use correct colors.

**Prerequisites:** Frontend deployed, receipts in various statuses

**Steps:**
1. Navigate to receipts list or journal entries
2. Locate status badges
3. Check colors for each status

**Expected Status Colors (typical):**
- UPLOADED: Blue (#3b82f6)
- EXTRACTING: Yellow/Amber (#f59e0b)
- EXTRACTED: Cyan (#06b6d4)
- REVIEWED: Purple (#8b5cf6)
- POSTED: Green (#10b981)
- REJECTED: Red (#ef4444)
- QUARANTINED: Orange (#f97316)

**Pass Criteria:** Each status has distinct, appropriate color.

**Failure Indicators:**
- All badges same color
- Missing status indicators
- Colors don't match design spec

**Screenshot/Log Evidence:** Screenshot of status badges.

---

# UI-F1: Auth Pages

## TEST-UI-F1-01: Login Page Layout

**Objective:** Verify login page has correct elements.

**Prerequisites:** Navigate to `/login`

**Steps:**
1. Open `/login`
2. Verify email input field
3. Verify password input field
4. Verify "Sign In" button
5. Verify "Sign in with magic link" option
6. Verify link to signup page

**Expected Result:**
- Email input with placeholder
- Password input (masked)
- Primary action button: "Sign In"
- Secondary option: Magic link
- Link to `/signup`

**Pass Criteria:** All auth elements present and functional.

**Failure Indicators:**
- Missing password field
- No magic link option
- No signup link

**Screenshot/Log Evidence:** Login page screenshot.

---

## TEST-UI-F1-02: Signup Page Layout

**Objective:** Verify signup page has correct elements.

**Prerequisites:** Navigate to `/signup`

**Steps:**
1. Open `/signup`
2. Verify email input
3. Verify password input
4. Verify password confirmation (if applicable)
5. Verify "Create Account" button
6. Verify link to login page

**Expected Result:**
- Email and password fields
- Submit button
- Link to login for existing users

**Pass Criteria:** Signup flow works end-to-end.

**Failure Indicators:**
- Cannot create account
- No validation on password
- No redirect after signup

**Screenshot/Log Evidence:** Signup page screenshot.

---

## TEST-UI-F1-03: JWT Stored in SSR Cookie

**Objective:** Verify JWT is stored securely as HTTP-only cookie.

**Prerequisites:** Successfully logged in

**Steps:**
1. Login successfully
2. Open DevTools → Application → Cookies
3. Look for JWT-related cookies

**Expected Result:**
- Cookie name: `sb-access-token` or similar
- HttpOnly flag: true
- Secure flag: true (in production)
- SameSite: Lax or Strict

**Pass Criteria:** JWT stored as secure, HTTP-only cookie.

**Failure Indicators:**
- JWT in localStorage
- Cookie without HttpOnly flag
- Cookie accessible via JavaScript

**Screenshot/Log Evidence:** DevTools cookies panel showing secure cookie.

---

## TEST-UI-F1-04: Auth Callback Route

**Objective:** Verify magic link callback route works.

**Prerequisites:** Magic link email sent

**Steps:**
1. Request magic link from `/login`
2. Click link in email
3. Verify redirect through `/api/auth/callback`
4. Verify final redirect to `/dashboard`
5. Verify authenticated state

**Expected Result:**
- URL briefly shows `/api/auth/callback?...`
- Redirects to `/dashboard`
- User is logged in

**Pass Criteria:** Magic link flow completes successfully.

**Failure Indicators:**
- Stuck on callback route
- "Invalid token" error
- Not authenticated after redirect

**Screenshot/Log Evidence:** Browser URL history + dashboard screenshot.

---

# UI-F2: API Client

## TEST-UI-F2-01: JWT Injection

**Objective:** Verify API client injects JWT on all requests.

**Prerequisites:** Logged in, DevTools open

**Steps:**
1. Login to application
2. Open DevTools → Network tab
3. Make any API call (navigate to dashboard)
4. Check request headers for Authorization

**Expected Result:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Pass Criteria:** Authorization header present on all API requests.

**Failure Indicators:**
- Missing Authorization header
- Wrong format (not "Bearer")
- Token missing

**Screenshot/Log Evidence:** Network tab showing request headers.

---

## TEST-UI-F2-02: ApiError Thrown on Failure

**Objective:** Verify API client throws ApiError on non-2xx responses.

**Prerequisites:** Frontend running

**Steps:**
1. Open DevTools → Console tab
2. Trigger an API error (invalid action)
3. Check console for error handling

**Expected Result:**
- ApiError caught and handled
- Toast notification shown
- No unhandled promise rejection

**Pass Criteria:** Errors properly caught and displayed.

**Failure Indicators:**
- Unhandled promise rejection
- No user feedback
- Page crashes

**Screenshot/Log Evidence:** Console + toast screenshot.

---

## TEST-UI-F2-03: Base URL from Environment

**Objective:** Verify API base URL is configurable via environment.

**Prerequisites:** Access to different environments

**Steps:**
1. Check `.env.local` or environment variables
2. Verify `NEXT_PUBLIC_FASTAPI_BASE_URL` is set
3. Make API request
4. Verify it goes to correct backend

**Expected Result:**
- Production: `https://api.example.com`
- Development: `http://localhost:8000`

**Pass Criteria:** API calls go to correct backend URL.

**Failure Indicators:**
- Calls go to wrong URL
- 404 errors
- CORS errors from wrong origin

**Screenshot/Log Evidence:** Network tab showing request URL.

---

# UI-F3: Upload Page

## TEST-UI-F3-01: Drag-Drop Zone

**Objective:** Verify drag-drop functionality works.

**Prerequisites:** Navigate to `/upload`

**Steps:**
1. Open `/upload`
2. Drag a JPEG file from file system
3. Drop onto the upload zone
4. Verify file is accepted

**Expected Result:**
- Drop zone highlights when dragging over
- File appears in selected files list
- "Upload All" button enabled

**Pass Criteria:** Drag-drop adds file to upload queue.

**Failure Indicators:**
- Drop zone doesn't respond
- File not added to queue
- No visual feedback

**Screenshot/Log Evidence:** Drag-drop action + file in queue.

---

## TEST-UI-F3-02: Mobile Camera Capture

**Objective:** Verify mobile camera capture works.

**Prerequisites:** Mobile device or mobile emulator

**Steps:**
1. Open `/upload` on mobile device
2. Tap "Take Photo" button
3. Camera should open
4. Take photo
5. Verify photo appears in queue

**Expected Result:**
- Camera opens when tapping button
- Photo captured and added to queue
- Ready to upload

**Pass Criteria:** Mobile camera integration works.

**Failure Indicators:**
- Camera doesn't open
- Photo not added to queue
- Wrong camera app opens

**Screenshot/Log Evidence:** Camera capture + queue screenshot.

---

## TEST-UI-F3-03: Image Compression (>5MB)

**Objective:** Verify large images are compressed before upload.

**Prerequisites:** 
- Image file > 5MB
- Navigate to `/upload`

**Steps:**
1. Select an image > 5MB
2. Watch for "Compressing large image..." toast
3. Check Network tab for actual upload size

**Expected Result:**
- Compression toast appears
- Upload proceeds
- Final upload size < 5MB
- Quality maintained (2400x2400 max, 85% JPEG)

**Pass Criteria:** Large images compressed successfully.

**Failure Indicators:**
- No compression
- Upload fails (file too large)
- Image quality severely degraded

**Screenshot/Log Evidence:** Toast + network upload size.

---

## TEST-UI-F3-04: File Size Rejection (>20MB)

**Objective:** Verify files > 20MB are rejected.

**Prerequisites:** File > 20MB

**Steps:**
1. Try to upload a 21MB file
2. Verify rejection

**Expected Result:**
- Error toast: "File [name] too large. Maximum file size is 20MB."
- File not added to queue

**Pass Criteria:** Files > 20MB rejected with clear message.

**Failure Indicators:**
- File accepted
- No error message
- Upload fails silently

**Screenshot/Log Evidence:** Error toast screenshot.

---

## TEST-UI-F3-05: Daily Upload Counter

**Objective:** Verify 20/day counter is displayed and accurate.

**Prerequisites:** Some uploads today

**Steps:**
1. Navigate to `/upload`
2. Look for upload counter
3. Upload a receipt
4. Verify counter increments

**Expected Result:**
- Shows "X of 20 files" or similar
- Counter increments after upload
- Reaches 20/20 shows limit message

**Pass Criteria:** Counter accurate and visible.

**Failure Indicators:**
- No counter displayed
- Counter incorrect
- Counter doesn't update

**Screenshot/Log Evidence:** Counter display before/after upload.

---

## TEST-UI-F3-06: Auto-Redirect to Review

**Objective:** Verify redirect to review page after single upload.

**Prerequisites:** Upload a single receipt

**Steps:**
1. Upload a single receipt
2. Wait for extraction to start
3. Verify redirect to `/review/[id]`

**Expected Result:**
- Automatic redirect to review page
- Review page shows extracting state
- No manual navigation needed

**Pass Criteria:** Seamless flow from upload to review.

**Failure Indicators:**
- Stays on upload page
- Manual navigation required
- Wrong page loaded

**Screenshot/Log Evidence:** Browser URL after upload.

---

## TEST-UI-F3-07: Bulk Upload (Up to 20)

**Objective:** Verify multiple files can be uploaded at once.

**Prerequisites:** Multiple receipt images ready

**Steps:**
1. Select 5-10 files at once
2. Click "Upload All"
3. Verify all upload
4. Check batch status

**Expected Result:**
- All files appear in queue
- "Upload All" uploads all files
- Batch ID returned
- Queue page shows batch progress

**Pass Criteria:** Bulk upload handles multiple files.

**Failure Indicators:**
- Only one file uploads
- Files lost
- No batch tracking

**Screenshot/Log Evidence:** Bulk upload + batch status.

---

# UI-F4: Review Page (Most Detailed)

## TEST-UI-F4-01: Two-Column Layout (Desktop)

**Objective:** Verify 50/50 split layout on desktop.

**Prerequisites:** 
- Desktop browser (width > 1024px)
- Extracted receipt

**Steps:**
1. Navigate to `/review/[id]` on desktop
2. Measure column widths
3. Verify left column (image) is 50%
4. Verify right column (form) is 50%

**Expected Result:**
- Equal width columns
- Left: Image viewer
- Right: Editable form
- No overlap

**Pass Criteria:** Exact or near-exact 50/50 split.

**Failure Indicators:**
- Uneven columns
- Columns overlap
- Single column layout on desktop

**Screenshot/Log Evidence:** Desktop screenshot showing columns.

---

## TEST-UI-F4-02: Stacked Layout (Mobile)

**Objective:** Verify stacked layout on mobile.

**Prerequisites:** 
- Mobile viewport (< 768px)
- Extracted receipt

**Steps:**
1. Open review page
2. Resize browser to mobile width
3. Verify columns stack vertically

**Expected Result:**
- Image viewer on top
- Form below
- Full width each

**Pass Criteria:** Responsive stacked layout.

**Failure Indicators:**
- Side-by-side on mobile
- Horizontal scroll required
- Elements cut off

**Screenshot/Log Evidence:** Mobile screenshot.

---

## TEST-UI-F4-03: Image Zoom Controls

**Objective:** Verify zoom in/out/reset controls work.

**Prerequisites:** Review page with image

**Steps:**
1. Navigate to review page
2. Click zoom in (+) button
3. Verify image enlarges
4. Click zoom out (-) button
5. Verify image shrinks
6. Click reset button
7. Verify image returns to original size

**Expected Result:**
- Zoom in increases image scale
- Zoom out decreases image scale
- Reset returns to fit
- Controls visible in bottom-right corner

**Pass Criteria:** All zoom controls functional.

**Failure Indicators:**
- Buttons don't respond
- Image doesn't zoom
- No reset option

**Screenshot/Log Evidence:** Image at different zoom levels.

---

## TEST-UI-F4-04: Image Pan/Drag

**Objective:** Verify image can be panned when zoomed.

**Prerequisites:** Zoomed-in image

**Steps:**
1. Zoom in on image
2. Click and drag to pan
3. Verify image moves
4. Release mouse
5. Verify new position held

**Expected Result:**
- Image draggable when zoomed
- Smooth pan movement
- No "stuck" behavior

**Pass Criteria:** Pan works smoothly.

**Failure Indicators:**
- Cannot pan zoomed image
- Jumpy or laggy movement
- Image resets on drag

**Screenshot/Log Evidence:** Panned image screenshot.

---

## TEST-UI-F4-05: Confidence Border — High (≥0.80)

**Objective:** Verify no border on high confidence fields.

**Prerequisites:** Field with confidence ≥ 0.80

**Steps:**
1. Load receipt with high confidence extraction
2. Examine field borders

**Expected Result:**
- No colored border
- Normal field appearance
- class: "border-transparent"

**Pass Criteria:** High confidence fields have no warning border.

**Failure Indicators:**
- Yellow/orange/red border shown
- Incorrect border class

**Screenshot/Log Evidence:** High confidence field close-up.

---

## TEST-UI-F4-06: Confidence Border — Medium (0.60-0.79)

**Objective:** Verify yellow border on medium confidence.

**Prerequisites:** Field with confidence 0.60-0.79

**Steps:**
1. Load receipt with medium confidence extraction
2. Examine field borders

**Expected Result:**
- Yellow/warning border on left side
- class: "border-l-warning"
- Visible but not alarming

**Pass Criteria:** Yellow border indicates medium confidence.

**Failure Indicators:**
- Wrong color
- No border
- Full border (not just left)

**Screenshot/Log Evidence:** Medium confidence field.

---

## TEST-UI-F4-07: Confidence Border — Low (0.40-0.59)

**Objective:** Verify orange border on low confidence.

**Prerequisites:** Field with confidence 0.40-0.59

**Expected Result:**
- Orange border on left side
- class: "border-l-orange-500"

**Pass Criteria:** Orange border indicates low confidence.

---

## TEST-UI-F4-08: Confidence Border — Very Low (<0.40)

**Objective:** Verify red border on very low confidence.

**Prerequisites:** Field with confidence < 0.40

**Expected Result:**
- Red/error border on left side
- class: "border-l-error"

**Pass Criteria:** Red border indicates very low confidence.

---

## TEST-UI-F4-09: Real-Time Math Validation

**Objective:** Verify math validation updates as user types.

**Prerequisites:** Review page with extracted data

**Steps:**
1. Locate T-Account preview section
2. Change total_amount value
3. Verify validation updates immediately
4. Check "Ledger Balanced" or "Ledger Imbalance" indicator

**Expected Result:**
- Validation updates in real-time
- Green "Ledger Balanced" when math correct
- Red "Ledger Imbalance Detected" when wrong
- Difference amount shown when imbalanced

**Pass Criteria:** Instant feedback on math changes.

**Failure Indicators:**
- No real-time update
- Must save to see validation
- Incorrect balance calculation

**Screenshot/Log Evidence:** Validation states before/after change.

---

## TEST-UI-F4-10: Approve & Post Disabled on Error

**Objective:** Verify button disabled when math is imbalanced.

**Prerequisites:** Receipt with imbalanced math

**Steps:**
1. Modify total to create imbalance
2. Check "Approve & Post" button state

**Expected Result:**
- Button has disabled styling (grayed out, lower opacity)
- Hover shows "not-allowed" cursor
- Click does nothing

**Pass Criteria:** Cannot post imbalanced entry.

**Failure Indicators:**
- Button appears enabled
- Click triggers error
- No visual indication

**Screenshot/Log Evidence:** Disabled button screenshot.

---

## TEST-UI-F4-11: T-Account Preview — Debits Left

**Objective:** Verify debits display on left side of T-Account.

**Prerequisites:** Review page with line items

**Steps:**
1. Scroll to T-Account preview
2. Verify left column shows debits
3. Check all expense items listed

**Expected Result:**
- Left column header: "Debits (Expenses)"
- Line items with amounts
- Tax and tip listed separately
- Total at bottom

**Pass Criteria:** Debits correctly displayed on left.

**Failure Indicators:**
- Wrong column
- Missing line items
- Incorrect amounts

**Screenshot/Log Evidence:** T-Account left side.

---

## TEST-UI-F4-12: T-Account Preview — Credits Right

**Objective:** Verify credits display on right side of T-Account.

**Prerequisites:** Review page

**Steps:**
1. Check right column of T-Account
2. Verify credit amount

**Expected Result:**
- Right column header: "Credits (Liabilities)"
- Accounts Payable or payment account
- Amount matches total debits

**Pass Criteria:** Credits correctly displayed on right.

**Failure Indicators:**
- Wrong column
- Wrong account
- Amount mismatch

**Screenshot/Log Evidence:** T-Account right side.

---

## TEST-UI-F4-13: T-Account Imbalance Highlight

**Objective:** Verify amber highlight when imbalanced.

**Prerequisites:** Create imbalance

**Steps:**
1. Change total to create imbalance
2. Check T-Account styling

**Expected Result:**
- Border changes to red/orange
- Error shadow appears
- Difference shown in red text

**Pass Criteria:** Visual indication of imbalance.

**Failure Indicators:**
- No visual change
- Same appearance as balanced

**Screenshot/Log Evidence:** Imbalanced T-Account.

---

## TEST-UI-F4-14: Queue Polling (5s Interval)

**Objective:** Verify page polls for status updates every 5 seconds.

**Prerequisites:** Receipt in EXTRACTING status

**Steps:**
1. Load review page for extracting receipt
2. Open DevTools → Network tab
3. Watch for GET requests every 5 seconds
4. Wait for status to change to EXTRACTED
5. Verify polling stops

**Expected Result:**
- GET requests to `/receipts/[id]` every 5 seconds
- Status updates when extraction completes
- Polling stops after extraction

**Pass Criteria:** Auto-refresh during extraction.

**Failure Indicators:**
- No polling
- Wrong interval
- Polling continues after completion

**Screenshot/Log Evidence:** Network tab showing polling requests.

---

## TEST-UI-F4-15: Extraction In-Progress Animation

**Objective:** Verify loading animation during extraction.

**Prerequisites:** Trigger extraction

**Steps:**
1. Upload and extract a receipt
2. Watch review page during extraction

**Expected Result:**
- Animated spinner or loader
- "Extraction in Progress" message
- Queue position displayed

**Pass Criteria:** Clear indication of processing.

**Failure Indicators:**
- Static page
- No loading state
- Confusing UI

**Screenshot/Log Evidence:** Extraction loading state.

---

## TEST-UI-F4-16: Rate Limit Toast

**Objective:** Verify rate limit shows toast with queue position.

**Prerequisites:** Trigger rate limit

**Steps:**
1. Upload multiple receipts rapidly
2. Watch for rate limit toast

**Expected Result:**
- Toast notification appears
- Shows queue position
- Bottom-right corner (Sonner default)

**Pass Criteria:** User informed of queue status.

**Failure Indicators:**
- No notification
- Generic error
- Blocking error modal

**Screenshot/Log Evidence:** Rate limit toast.

---

## TEST-UI-F4-17: Save Draft Functionality

**Objective:** Verify "Save Draft" saves without posting.

**Prerequisites:** Modified receipt data

**Steps:**
1. Make changes to receipt data
2. Click "Save Draft" button
3. Verify success toast
4. Reload page
5. Verify changes persisted

**Expected Result:**
- Changes saved
- Status remains EXTRACTED or REVIEWED
- Toast confirms save
- Data persisted

**Pass Criteria:** Can save without posting.

**Failure Indicators:**
- Changes not saved
- Status changes unexpectedly
- Error on save

**Screenshot/Log Evidence:** Save success toast + persisted data.

---

# UI-F5: Journal Entries List

## TEST-UI-F5-01: Sortable Table

**Objective:** Verify table can be sorted by columns.

**Prerequisites:** Multiple journal entries

**Steps:**
1. Navigate to `/journal-entries`
2. Click column header (e.g., "Date")
3. Verify sort order changes
4. Click again for reverse sort

**Expected Result:**
- Clicking header sorts by that column
- Arrow indicator shows sort direction
- Toggle between asc/desc

**Pass Criteria:** All sortable columns work.

**Failure Indicators:**
- Headers not clickable
- No visual feedback
- Sort doesn't apply

**Screenshot/Log Evidence:** Table in different sort states.

---

## TEST-UI-F5-02: Filter Controls

**Objective:** Verify filters work correctly.

**Prerequisites:** Journal entries with various attributes

**Steps:**
1. Use date range filter
2. Use vendor filter
3. Use status filter
4. Verify results match filters

**Expected Result:**
- Filters narrow down results
- Multiple filters can be combined
- Clear filters option

**Pass Criteria:** All filters work individually and combined.

**Failure Indicators:**
- Filters don't apply
- Wrong results
- Cannot clear filters

**Screenshot/Log Evidence:** Filtered results.

---

## TEST-UI-F5-03: Expandable Rows

**Objective:** Verify rows expand to show line items.

**Prerequisites:** Journal entries with multiple lines

**Steps:**
1. Click on a journal entry row
2. Verify it expands
3. Check line items are shown

**Expected Result:**
- Row expands on click
- All journal entry lines visible
- Account codes and amounts shown

**Pass Criteria:** Can view full entry details.

**Failure Indicators:**
- Rows don't expand
- Missing line items
- Wrong data shown

**Screenshot/Log Evidence:** Expanded row.

---

## TEST-UI-F5-04: Server Pagination

**Objective:** Verify pagination loads from server.

**Prerequisites:** 25+ journal entries

**Steps:**
1. Note total entries count
2. Click "Next" or page 2
3. Verify new data loaded
4. Check Network tab for API call

**Expected Result:**
- Only 25 entries per page
- Page change triggers API call
- URL updates with page parameter

**Pass Criteria:** Server-side pagination works.

**Failure Indicators:**
- All entries loaded at once
- No pagination
- Client-side pagination only

**Screenshot/Log Evidence:** Network tab + paginated results.

---

## TEST-UI-F5-05: Export Buttons (CSV/PDF)

**Objective:** Verify export buttons are present and functional.

**Prerequisites:** Journal entries exist

**Steps:**
1. Locate export buttons
2. Click "Export CSV"
3. Verify file downloads
4. Click "Export PDF"
5. Verify PDF downloads

**Expected Result:**
- Buttons visible in header
- CSV downloads with correct data
- PDF downloads and opens

**Pass Criteria:** Both export formats work.

**Failure Indicators:**
- Buttons missing
- Export fails
- Empty/corrupt files

**Screenshot/Log Evidence:** Downloaded files.

---

# UI-F6: Toasts

## TEST-UI-F6-01: Toast Position (Bottom-Right)

**Objective:** Verify toasts appear in bottom-right corner.

**Prerequisites:** Action that triggers toast

**Steps:**
1. Perform action that triggers success toast
2. Note toast position on screen

**Expected Result:**
- Toast appears bottom-right
- Doesn't block main content
- Stacks if multiple

**Pass Criteria:** Correct positioning.

**Failure Indicators:**
- Top of screen
- Center overlay
- Blocks interaction

**Screenshot/Log Evidence:** Toast position screenshot.

---

## TEST-UI-F6-02: Success Toast

**Objective:** Verify success toast appearance.

**Prerequisites:** Successful action (save, upload)

**Expected Result:**
- Green checkmark icon
- Success message
- Light green background or border

**Pass Criteria:** Clear success indication.

---

## TEST-UI-F6-03: Error Toast

**Objective:** Verify error toast appearance.

**Prerequisites:** Failed action

**Expected Result:**
- Red X or alert icon
- Error message
- Red background or border

**Pass Criteria:** Clear error indication.

---

## TEST-UI-F6-04: 5s Auto-Dismiss

**Objective:** Verify toasts dismiss after 5 seconds.

**Prerequisites:** Trigger a toast

**Steps:**
1. Trigger toast
2. Start timer
3. Wait for auto-dismiss

**Expected Result:**
- Toast visible for ~5 seconds
- Fades out smoothly
- No manual dismissal needed

**Pass Criteria:** Auto-dismiss works.

**Failure Indicators:**
- Toast stays forever
- Dismisses too quickly (< 3s)
- Requires manual close

**Screenshot/Log Evidence:** Timer showing dismiss timing.

---

# UI-F7: Settings Page

## TEST-UI-F7-01: Chart of Accounts List

**Objective:** Verify COA displays correctly.

**Prerequisites:** Navigate to `/settings`

**Steps:**
1. View chart of accounts section
2. Verify default accounts listed
3. Verify custom accounts (if any)

**Expected Result:**
- Account code, name, type shown
- System defaults marked
- Active/inactive status visible

**Pass Criteria:** COA displays correctly.

**Failure Indicators:**
- Empty list
- Missing default accounts
- Can't view details

**Screenshot/Log Evidence:** COA section.

---

## TEST-UI-F7-02: Add Custom Account

**Objective:** Verify can add new account to COA.

**Prerequisites:** Settings page

**Steps:**
1. Click "Add Account" button
2. Enter code, name, type
3. Save
4. Verify account appears in list

**Expected Result:**
- Form for new account
- Validation on code format
- Account added to list

**Pass Criteria:** Can create custom account.

**Failure Indicators:**
- No add button
- Validation fails
- Account not saved

**Screenshot/Log Evidence:** New account in list.

---

## TEST-UI-F7-03: Rename Account

**Objective:** Verify can rename custom account.

**Prerequisites:** Custom account exists

**Steps:**
1. Click edit on custom account
2. Change name
3. Save
4. Verify new name shown

**Expected Result:**
- Name updated
- Code unchanged
- Audit log entry

**Pass Criteria:** Can rename non-system accounts.

**Failure Indicators:**
- Cannot edit
- System account editable
- Changes not saved

**Screenshot/Log Evidence:** Renamed account.

---

## TEST-UI-F7-04: Deactivate Account (No Delete)

**Objective:** Verify accounts can be deactivated, not deleted.

**Prerequisites:** Custom account

**Steps:**
1. Try to delete an account
2. Verify only deactivate option
3. Deactivate the account
4. Verify it shows as inactive

**Expected Result:**
- No "Delete" button
- "Deactivate" option available
- Account shows as inactive
- Still visible in list

**Pass Criteria:** Soft delete only.

**Failure Indicators:**
- Delete option available
- Account disappears completely
- Can deactivate system defaults

**Screenshot/Log Evidence:** Deactivated account.

---

## TEST-UI-F7-05: Vendor Mappings

**Objective:** Verify vendor mapping configuration.

**Prerequisites:** Settings page

**Steps:**
1. Navigate to vendor mappings section
2. View existing mappings
3. Add new mapping
4. Test with a receipt

**Expected Result:**
- List of vendor → account mappings
- Can add new mapping
- Mapping applied on next receipt

**Pass Criteria:** Vendor mappings work.

**Failure Indicators:**
- Mappings not applied
- Cannot add new mapping
- System defaults not visible

**Screenshot/Log Evidence:** Vendor mapping section.

---

# E2E: End-to-End Flows

## TEST-E2E-01: Complete Happy Path

**Objective:** Verify full flow from signup to reversal.

**Prerequisites:** Clean user account, test receipt image

**Steps:**

### 1. Signup
```
1. Navigate to /signup
2. Enter email: test@example.com
3. Enter password: TestPass123!
4. Click "Create Account"
5. Verify redirect to /dashboard
```

### 2. Upload
```
6. Navigate to /upload
7. Drag and drop receipt image
8. Click "Upload All"
9. Verify redirect to /review/[id]
```

### 3. Extract
```
10. Wait for extraction (max 60s)
11. Verify status changes to EXTRACTED
12. Verify data appears in form
```

### 4. Review
```
13. Verify vendor name
14. Verify total amount
15. Check line items
16. Make any corrections needed
17. Click "Save Draft"
```

### 5. Approve
```
18. Verify T-Account shows balanced
19. Click "Approve & Post"
20. Verify redirect to /journal-entries
21. Verify toast: "Receipt Approved & Posted to Ledger!"
```

### 6. View Journal Entry
```
22. Find new entry in list
23. Click to expand
24. Verify entry number format: JE-YYYY-XXXXX
25. Verify debits = credits
26. Click to view details
27. Verify receipt image visible
```

### 7. Reverse
```
28. Click "Reverse" button
29. Enter reason: "Test reversal"
30. Confirm
31. Verify original status: REVERSED
32. Verify new reversal entry created
33. Verify debits/credits swapped
```

**Expected Result:** All steps complete without errors.

**Pass Criteria:** Complete happy path succeeds.

**Failure Indicators:**
- Any step fails
- Redirect wrong
- Data missing

**Screenshot/Log Evidence:** Screenshots at each major step.

---

## TEST-E2E-02: Extraction Failure Recovery

**Objective:** Verify recovery from extraction failure.

**Steps:**
```
1. Upload blurry/unreadable receipt
2. Wait for EXTRACTION_FAILED status
3. Verify error message shown
4. Click "Retry" or re-trigger extraction
5. If still fails, manually enter data
6. Proceed to post
```

**Expected Result:** Can recover from extraction failure.

---

## TEST-E2E-03: Validation Error Flow

**Objective:** Verify handling of validation errors.

**Steps:**
```
1. Upload receipt
2. After extraction, modify data to create math error
3. Verify "Approve & Post" disabled
4. Fix the error
5. Verify button enabled
6. Proceed to post
```

**Expected Result:** Cannot post invalid data; can fix and proceed.

---

## TEST-E2E-04: Daily Limit Flow

**Objective:** Verify daily limit enforcement.

**Steps:**
```
1. Upload 20 receipts
2. Attempt 21st upload
3. Verify 429 error
4. Verify clear error message
5. Wait until next day (or test with different user)
6. Verify uploads work again
```

**Expected Result:** Limit enforced with clear message.

---

## TEST-E2E-05: Multi-User Isolation

**Objective:** Verify users cannot see each other's data.

**Prerequisites:** Two user accounts

**Steps:**
```
1. Login as User A
2. Upload receipt
3. Note receipt ID
4. Logout
5. Login as User B
6. Try to access User A's receipt via URL
7. Verify 404 or access denied
8. Verify User A's journal entries not visible
```

**Expected Result:** Complete data isolation.

---

# SEC: Security & Compliance

## TEST-SEC-01: API Keys Never Exposed

**Objective:** Verify NVIDIA_NIM_API_KEY and SUPABASE_SERVICE_ROLE_KEY never in responses.

**Prerequisites:** All endpoints tested

**Steps:**
1. Make requests to all endpoints
2. Search all responses for key patterns
3. Check error responses
4. Check logs

```bash
# Search all responses for API key patterns
grep -r "nvapi-" [responses]
grep -r "service_role" [responses]
grep -r "supabase_service_role_key" [responses]
```

**Expected Result:** No API keys in any response or client-accessible location.

**Pass Criteria:** Keys never exposed.

**Failure Indicators:**
- Key visible in response
- Key in error message
- Key in localStorage

---

## TEST-SEC-02: Bookkeeping Assertion Sacred

**Objective:** Verify Python assert + Postgres CHECK both enforce balance.

**Prerequisites:** 
- Database access
- Ability to bypass API (direct DB insert)

**Steps:**

### Python Assert Test
```
1. Try to create journal entry with imbalanced amounts
2. Verify Python assertion fails
3. Verify receipt quarantined
```

### Postgres CHECK Test
```sql
-- Try direct insert bypassing API
INSERT INTO journal_entries (
  id, receipt_id, entry_number, entry_date,
  total_debit, total_credit, status
) VALUES (
  gen_random_uuid(), 
  'valid-receipt-id',
  'JE-2026-99999',
  '2026-05-08',
  100.00,
  50.00,  -- Imbalanced!
  'POSTED'
);
```

**Expected Result:**
- Python: BookkeepingAssertionError raised
- Postgres: CHECK constraint violation

**Pass Criteria:** Both layers enforce balance.

{}
---

## TEST-SEC-03: Immutability of Posted Entries

**Objective:** Verify posted journal entries cannot be modified or deleted.

**Prerequisites:** Posted journal entry

**Steps:**

### 1. Try to modify posted entry
```bash
# Attempt to update via API (should not exist)
curl -X PUT "https://[backend]/api/v1/journal-entries/[id]" \
  -H "Authorization: Bearer [token]" \
  -d '{"total_debit": 999.00}'
```

### 2. Try to delete posted entry
```bash
curl -X DELETE "https://[backend]/api/v1/journal-entries/[id]" \
  -H "Authorization: Bearer [token]"
```

### 3. Direct database test
```sql
-- Try to update posted entry
UPDATE journal_entries SET total_debit = 999.00 WHERE id = '[id]';
-- Note: This may succeed at DB level, verify API prevents it
```

**Expected Result:**
- No UPDATE endpoint exists
- DELETE endpoint creates reversal, doesn't delete
- Original entry preserved

**Pass Criteria:** Posted entries immutable via API.

**Failure Indicators:**
- UPDATE endpoint exists
- DELETE removes entry
- Data modification allowed

---

## TEST-SEC-04: Card Number Redaction

**Objective:** Verify full card numbers are never stored or returned.

**Prerequisites:** Receipt with card number visible

**Steps:**
1. Upload receipt showing full card number
2. Trigger extraction
3. Check extracted_data for card fields

**Expected Result:**
- extracted_data contains at most "last4": "4321"
- No full card number
- LLM prompt instructs redaction

**Pass Criteria:** Card numbers redacted in extraction.

**Failure Indicators:**
- Full card number in extracted_data
- Raw card number in raw_llm_output
- Card number in audit_logs

---

## TEST-SEC-05: Signed URLs Expire (1hr)

**Objective:** Verify image URLs expire after 1 hour.

**Prerequisites:** Receipt with image

**Steps:**
1. Get receipt image URL
2. Note the URL parameters (should have token/expiry)
3. Wait 61 minutes (or test with manipulated expiry)
4. Try to access the URL

**Expected Result:**
- URL contains signature/expiry parameters
- Access denied after expiry
- Fresh URL generated on next request

**Pass Criteria:** Signed URLs time-limited.

**Failure Indicators:**
- URL has no expiry
- URL works indefinitely
- Public/unsigned URL returned

---

## TEST-SEC-06: State Machine Strict (Invalid = 409)

**Objective:** Verify all invalid transitions return 409.

**Prerequisites:** Test all transition combinations

**Steps:**
Test each invalid transition (see TEST-API-B4-18 through 25).

**Pass Criteria:** All invalid transitions return 409 Conflict.

---

## TEST-SEC-07: No Raw 429s to Client

**Objective:** Verify client never sees raw HTTP 429.

**Prerequisites:** Rate limiting triggered

**Steps:**
1. Trigger rate limiting (rapid requests)
2. Check response status code
3. Check response body

**Expected Result:**
- Response is 202 or 200 with queue_position
- No 429 status code to client
- Clear message about queue

**Pass Criteria:** Rate limits handled gracefully.

**Failure Indicators:**
- 429 returned to client
- No queue position
- Blocking error

---

## TEST-SEC-08: Environment Parity (Docker Compose = Cloud)

**Objective:** Verify Docker Compose environment matches cloud deployment.

**Prerequisites:** 
- Docker Compose setup
- Cloud deployment

**Steps:**
1. Run `docker-compose up`
2. Test all endpoints locally
3. Compare with cloud responses
4. Verify same behavior

**Expected Result:**
- Same API responses
- Same error messages
- Same feature set

**Pass Criteria:** Local and cloud environments behave identically.

**Failure Indicators:**
- Features work only in one environment
- Different error messages
- Configuration differences

---

## TEST-SEC-09: Rollback Safety

**Objective:** Verify all migrations have working downgrades.

**Prerequisites:** All migrations applied

**Steps:**
```bash
# Check current migration
alembic current

# Downgrade all the way
alembic downgrade base

# Verify database is clean
psql -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"

# Upgrade back
alembic upgrade head

# Verify all tables restored
alembic current
```

**Expected Result:**
- Downgrade completes without errors
- Database clean after downgrade
- Upgrade restores everything
- No data loss

**Pass Criteria:** Full rollback and restore works.

**Failure Indicators:**
- Downgrade fails
- Orphaned tables/indexes
- Cannot re-upgrade

---

# Production Smoke Test

**Quick checks to run immediately after deployment:**

## 1. Health Check
```bash
curl -s https://[production-backend]/api/v1/health | jq
```
**Expected:** `{"status": "ok", "db": "connected", "llm_provider": "..."}`

## 2. Frontend Loads
```bash
curl -s -o /dev/null -w "%{http_code}" https://[production-frontend]
```
**Expected:** 200

## 3. Login Works
- Navigate to `/login`
- Login with test account
- Verify redirect to dashboard

## 4. Upload Works
- Navigate to `/upload`
- Upload a test receipt
- Verify success

## 5. Journal Entry Created
- Complete the review flow
- Verify journal entry appears in list

---

# Rollback Test

## TEST-ROLLBACK-01: Full Database Rollback

**Objective:** Verify complete database rollback and restore.

**Prerequisites:** Production database backup

**Steps:**
1. Take database backup
2. Apply new migration
3. Verify new features work
4. Rollback migration
5. Verify system still works
6. Restore backup if needed

**Commands:**
```bash
# Before deployment
pg_dump -h [host] -U postgres -d postgres > backup_before.sql

# After deployment
alembic downgrade -1

# Verify tables
psql -c "SELECT COUNT(*) FROM receipts;"

# If needed, restore
psql -h [host] -U postgres -d postgres < backup_before.sql
```

**Pass Criteria:** Rollback completes; system functional.

**Failure Indicators:**
- Rollback fails
- Data loss
- System unavailable after rollback

---

# Test Data Requirements

## Sample Receipt Images

For comprehensive testing, prepare these receipt images:

1. **Standard Receipt**
   - Clear, well-lit photo
   - Multiple line items
   - Tax and tip
   - Card payment

2. **Handwritten Receipt**
   - Handwritten amounts
   - Lower confidence expected

3. **Large Receipt (>5MB)**
   - Test compression

4. **PDF Receipt**
   - Test PDF parsing

5. **Blurred/Unreadable**
   - Test extraction failure

6. **Foreign Currency**
   - Non-USD currency
   - Test currency validation

7. **No Line Items**
   - Just total
   - Test minimal extraction

## Test Account Codes

Use these account codes for override testing:
- `1010` - Cash
- `1020` - Checking Account
- `2000` - Accounts Payable
- `2010` - Credit Card Liability
- `2100` - Sales Tax Payable
- `5100` - Travel Expense
- `5300` - Meals & Entertainment
- `5999` - Miscellaneous Expense

---

# Test Execution Checklist

## Pre-Deployment
- [ ] All migrations tested on staging
- [ ] Rollback procedure verified
- [ ] Environment variables configured
- [ ] CORS origins set correctly

## Post-Deployment
- [ ] Health check returns ok
- [ ] Login works
- [ ] Upload works
- [ ] Extraction works
- [ ] Journal entry creation works
- [ ] Reversal works

## Security
- [ ] No API keys exposed
- [ ] RLS policies active
- [ ] Signed URLs expire
- [ ] Immutability enforced

## Performance
- [ ] Response times acceptable (<3s for most endpoints)
- [ ] Pagination works
- [ ] No memory leaks during extraction

---

# Known Limitations

1. **Rate Limit Testing**: Difficult to trigger NVIDIA 429 without significant load
2. **Semaphore Testing**: Requires load testing tools for accurate validation
3. **10-Year Date Test**: Requires mocking system date or waiting
4. **Daily Limit**: Requires 21 uploads to test; clear test data after
5. **Mobile Testing**: Requires actual device or proper emulator

---

# Reporting Template

For each failed test, document:

```
Test ID: TEST-[SECTION]-[NUMBER]
Test Name: [Test Name]
Date/Time: [When tested]
Environment: [Production/Staging/Local]
Status: FAILED

Steps to Reproduce:
1. [Step 1]
2. [Step 2]

Expected Result:
[What should happen]

Actual Result:
[What actually happened]

Error Messages:
[Any error text]

Screenshots/Logs:
[Links or attachments]

Severity: [Critical/High/Medium/Low]
```

---

# Appendix: Useful Commands

## Database Queries

```sql
-- Count receipts by status
SELECT status, COUNT(*) FROM receipts GROUP BY status;

-- Recent audit logs
SELECT * FROM audit_logs ORDER BY performed_at DESC LIMIT 20;

-- User's journal entries
SELECT je.entry_number, je.total_debit, je.status
FROM journal_entries je
JOIN receipts r ON r.id = je.receipt_id
WHERE r.user_id = '[user-uuid]'
ORDER BY je.created_at DESC;

-- Check RLS policies
SELECT * FROM pg_policies WHERE schemaname = 'public';
```

## API Testing

```bash
# Get auth token from Supabase
# Use browser DevTools → Application → Local Storage → sb-*-auth-token

# Test with curl
curl -H "Authorization: Bearer [token]" \
     -H "Content-Type: application/json" \
     https://[backend]/api/v1/receipts

# Test upload
curl -X POST \
     -H "Authorization: Bearer [token]" \
     -F "file=@receipt.jpg" \
     https://[backend]/api/v1/receipts/upload
```

## Log Analysis

```bash
# Search logs for errors
grep -i "error" /var/log/app.log | tail -50

# Count extraction failures
grep -c "EXTRACTION_FAILED" /var/log/app.log

# Find rate limit events
grep "429" /var/log/app.log | tail -20
```

---

**End of Manual Testing Guide — Phase 1**

*Document Version: 1.0.0*  
*Last Updated: May 2026*  
*Maintainer: QA Team*
