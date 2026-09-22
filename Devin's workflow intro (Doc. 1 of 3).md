
Here's a complete manual test workflow for both PKI flows, based on the actual endpoints in the code.

## Prerequisites

- App running at `http://127.0.0.1:5000` (uvicorn), with `frontend-vue/dist` built so the dashboard loads. 
- **Internet access** — Workflow B calls the external TSA `https://freetsa.org/tsr` at sign time, so signing fails offline. 
- Two easy testing surfaces: the **Swagger UI at `http://127.0.0.1:5000/docs`** (fastest for the API), or the **Vue dashboard** (tests the real UI). Both hit the same endpoints.

## Step 0 — Get a logged-in account (needed for everything)

Every PKI route is JWT-protected via `AccessTokenBearer()`, so you need an access token first. 

Signup forces 2FA setup, and the signup password rules are strict — min 16 chars, max 50, an uppercase, a digit, a special char, **at least two non-adjacent spaces**. A valid example: `My Secret Pass 9!`

Two ways:

**Option A — via the dashboard UI (end-to-end):**
1. Go to the site, Sign Up, fill in the form with a valid password.
2. A 2FA modal appears with a QR code. Scan it with an authenticator app (Google Authenticator, etc.), or grab the code without an app (next bullet).
3. To get the code without scanning: the signup response gives you a `temp_token`. Hit the debug endpoint `GET /auth/debug/current-totp` with that token to read the current 6-digit code. 
4. Enter the code → you're logged in and land on `/dashboard`. Thereafter just use Login (email + password), which issues tokens directly with no 2FA step. 

**Option B — via `/docs` (pure API):**
1. `POST /auth/signup` → copy `temp_token` and `manual_code` from the response.
2. Authorize Swagger with `temp_token`, call `GET /auth/debug/current-totp` → copy `current_code`. 
3. `POST /auth/verify-2fa-setup` with `{ "code": "<current_code>" }` → returns real `access_token` + `refresh_token`. 
4. Put the `access_token` into Swagger's Authorize box (as `Bearer <token>`) for the PKI calls below.

## Step 1 — Test Workflow A (certificate enrollment)

Endpoint: `POST /api/certificates/generate`, JSON body `{ "p12_password": "<min 6 chars>" }`. 

- **UI:** Dashboard → "PKI Management" → "Generate New Certificate" → enter a password (≥6) → submit. A `user_certificate.p12` file downloads.
- **API:** call the endpoint with the bearer token; the response is the binary `.p12`. In Swagger use "Download file".

**Verify success:**
1. You got a `.p12` back (200, `Content-Type: application/x-pkcs12`). 
2. It's a real, password-protected archive — from a terminal: `openssl pkcs12 -info -in user_certificate.p12` and enter your password. It should show your email as the cert CN and the "USR Automated Root CA" as issuer. 
3. A DB row was written — call `GET /api/certificates/history`; the new cert appears with `is_revoked: false`.   On the dashboard, the history table shows a green "Active (Whitelisted)" badge.

**Keep the `.p12` file and its password — Workflow B needs both.**

## Step 2 — Test Workflow B (document signing)

Endpoint: `POST /api/certificates/sign`, `multipart/form-data` with `pdf_file`, `p12_file`, `p12_password`. 

- **UI:** Dashboard → "Document Signing" → choose any PDF for `pdf_file`, choose the `.p12` from Step 1 for `p12_file`, type the same p12 password → "Sign Document". A `signed_document.pdf` downloads. 
- **API:** in `/docs`, upload the two files and the password field, execute, download the returned PDF.

**Verify success:**
1. You got a PDF back (200, `Content-Type: application/pdf`, filename `signed_document.pdf`). 
2. Open it in Adobe Acrobat Reader → the Signature Panel should show a signature in field `DigitalSignature` with a timestamp from freetsa.org.  (The signer's Root CA isn't in Adobe's trust store, so it may say "identity unknown" — that's expected for a self-made CA, not a failure.)
3. Terminal check: `openssl` or `pdfsig signed_document.pdf` lists the signature and TSA time.

## Negative / error tests worth running

- **Wrong p12 password** on signing → expect **400** "Invalid certificate password or corrupt .p12 file". 
- **Non-PDF / corrupt file** as `pdf_file` → expect **400** "Failed to sign PDF document...". 
- **No token / expired token** on any PKI route → expect **401/403** (both the UI and the code auto-retry once via `auth.refreshAccessToken()`). 
- **`p12_password` shorter than 6** on generate → pydantic rejects with a validation error before any crypto runs. 

## Note:
## Neon PostgreSQL — Data Persistence

The application uses a Neon-hosted PostgreSQL database as its single system of record for both identity and PKI state, connected asynchronously via SQLAlchemy/SQLModel over the `asyncpg` driver. The `DATABASE_URL` from configuration is normalized at startup by `get_async_db_url()`, which rewrites a `postgresql://`/`postgres://` prefix to `postgresql+asyncpg://` and strips any `?ssl` query parameter main.py:13-22 ; because Neon is an external cloud host (not Replit's internal `helium` database), the engine automatically attaches a TLS `ssl.create_default_context()` via `connect_args`, ensuring all traffic to Neon is encrypted in transit main.py:26-34 . The async engine is created with connection resiliency tuned for Neon's serverless, connection-pooling nature — `pool_pre_ping=True` validates connections before use and `pool_recycle=300` recycles them every five minutes to avoid stale/idle drops main.py:36-42 , while `initdb()` provisions the schema on boot by running `SQLModel.metadata.create_all` and per-request sessions are yielded (with rollback-on-error) through `get_session()` main.py:44-65 . Two tables are persisted in Neon: `user_accounts` (the `User` model — UUID primary key, credentials as `password_hash`, and 2FA fields including the encrypted `totp_secret`) models.py:6-34 and `client_certificates` (the `ClientCertificate` model — auto-increment id, a `user_id` foreign key to `user_accounts.uid` with `ON DELETE CASCADE`, the unique `serial_number`, validity window, PEM-encoded certificate text, and the `is_revoked` whitelist flag) models.py:10-66 , giving each user a one-to-many relationship to the certificates they generate.