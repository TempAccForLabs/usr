
Here is that exact walkthrough, rewritten with the folder structure built in. Read the folder map first, then every step below names the **folder → file → method**.

## The folder map

Root is `~/usr/`. Two halves: `frontend-vue/` (browser) and `src/` (server).

```
~/usr/
├── frontend-vue/                      ← FRONTEND (browser)
│   └── src/
│       ├── config.js                  ← API_BASE_URL
│       ├── composables/
│       │   └── useAuth.js             ← all fetch() network calls
│       └── views/
│           ├── AuthView.vue           ← Login / Sign Up page
│           └── DashboardView.vue      ← dashboard + certificate buttons
│
└── src/                               ← BACKEND (FastAPI / Python)
    ├── __init__.py                    ← maps URL prefixes to routers
    ├── auth/
    │   ├── routes.py                  ← /auth/signup, /auth/login, /auth/verify-2fa-setup
    │   ├── dependencies.py            ← JWT gatekeeper (AccessTokenBearer)
    │   └── utils.py                   ← create_access_token(), decode_token()
    └── pki/
        ├── routes.py                  ← /generate, /sign, /history
        ├── schemas.py                 ← CertificateGenerateModel (password rules)
        ├── pki_engine.py              ← get_root_ca() (reads ~/usr/certs/)
        └── models.py                  ← ClientCertificate (DB table)
``` 

---

## Part 0 — The prerequisite: you must be authenticated

Workflow A's `/api/certificates/generate` endpoint is JWT-protected, so before any certificate can be generated you must already hold a valid access token from signup or login. Below is how you got that token. routes.py:28-33

### 0a. Signup (frontend → backend)

- `frontend-vue/src/views/AuthView.vue` → `handleSignup()` handles the Sign Up form submit. It first runs a client-side password check via `clientValidatePassword()` before touching the network. AuthView.vue:236-239
- `handleSignup()` then calls `auth.signup(signupForm)`, which lives in `frontend-vue/src/composables/useAuth.js` → `signup(userData)`. That function POSTs to `/auth/signup` through the shared `request()` helper. useAuth.js:71-75
- `frontend-vue/src/composables/useAuth.js` → `request()` prefixes the URL with `API_BASE_URL` (from `frontend-vue/src/config.js`, empty string = same origin) and attaches `Authorization: Bearer` only if a token exists. useAuth.js:14-23
- On the backend, `src/__init__.py` routes the request — the `auth_router` is mounted under prefix `/auth`. __init__.py:83-87
- It lands in `src/auth/routes.py` → `create_user_account()`. This checks for a duplicate email via `user_service.user_exists()`, creates the user via `user_service.create_user()`, generates a TOTP secret, encrypts it with `encrypt_data()`, and mints a short-lived (60-minute) `temp_token` via `create_access_token()`. It returns the QR code + `temp_token`, but crucially `is_2fa_enabled = False` — you are NOT fully logged in yet. routes.py:61-91
- Back in the frontend, `frontend-vue/src/composables/useAuth.js` → `signup()` stores that `temp_token` in `localStorage`. useAuth.js:77-79

### 0b. 2FA verification completes the login

- You scan the QR in an authenticator app, type the 6-digit code; `frontend-vue/src/views/AuthView.vue` → `verify2FASignup(code)` runs. AuthView.vue:257-262
- It calls `frontend-vue/src/composables/useAuth.js` → `complete2FASignup(code)`, which POSTs to `/auth/verify-2fa-setup` — and importantly passes `state.tempToken` as the token override (the third arg to `request()`), because you only have the temp token at this point. useAuth.js:91-96
- On success the backend returns the real `access_token` + `refresh_token`; `complete2FASignup()` calls `setTokens()` to persist them in `localStorage`, then routes you to `/dashboard`. useAuth.js:97-101
- (If you instead use the Login tab later, `frontend-vue/src/composables/useAuth.js` → `login(email, password)` POSTs `/auth/login` and gets full tokens directly, no 2FA prompt.) useAuth.js:59-68

The token itself is built by `src/auth/utils.py` → `create_access_token()`, which packs `user`, `exp`, `jti`, `refresh: false`, and `is_2fa_verified` into a JWT signed with `Config.JWT_SECRET`. utils.py:114-160

---

## Part 1 — Landing on the dashboard

When the dashboard mounts, it immediately calls `frontend-vue/src/views/DashboardView.vue` → `fetchCertHistory()`, which uses `auth.request('/api/certificates/history')` to populate the Certificate History table. This is the same table you'll see update after generating. DashboardView.vue:491-496

---

## Part 2 — The certificate generation flow (the actual Workflow A)

### 2a. UI input

- You click "Generate New Certificate". The button's `@click` fires `frontend-vue/src/views/DashboardView.vue` → `openCertModal()`, which clears state and shows the password modal. DashboardView.vue:448-452
- You type a certificate password and click "Generate", which triggers `frontend-vue/src/views/DashboardView.vue` → `submitCertPassword()`. DashboardView.vue:504-510

### 2b. Frontend checks + call

- `frontend-vue/src/views/DashboardView.vue` → `submitCertPassword()` does a client-side check: password must be ≥ 6 characters, else it sets `certModalError` and returns without any network call. DashboardView.vue:507-510
- It then calls `frontend-vue/src/views/DashboardView.vue` → `requestCertificate(auth.state.accessToken)`, which fetch-POSTs to `${API_BASE_URL}/api/certificates/generate` with `Content-Type: application/json`, an `Authorization: Bearer <token>` header, and body `{ p12_password: certPassword.value }`. DashboardView.vue:461-470
- Auto-retry on expiry: if the response is 401, `submitCertPassword()` calls `frontend-vue/src/composables/useAuth.js` → `refreshAccessToken()` (which GETs `/auth/refresh_token` with the refresh token) and retries once; if the refresh fails it logs you out and redirects. DashboardView.vue:516-526 useAuth.js:104-112

### 2c. Backend routing + auth checks

- `src/__init__.py` routes the request — `pki_router` is mounted under prefix `/api/certificates`, so `/generate` resolves to `generate_client_certificate()`. __init__.py:89-93
- `src/pki/routes.py` → `generate_client_certificate()` declares two dependencies that run BEFORE the body: `cert_data: CertificateGenerateModel` and `token_details = Depends(AccessTokenBearer())`. routes.py:28-33
- Schema check: Pydantic validates the body against `src/pki/schemas.py` → `CertificateGenerateModel`, which enforces `p12_password` min length 6 server-side too. A shorter password is rejected before any code runs. schemas.py:4-5
- JWT check: `src/auth/dependencies.py` → `AccessTokenBearer` extends `TokenBearer.__call__()`, which extracts the bearer token, runs `decode_token()`, raises 403 if invalid/expired, then calls the polymorphic `verify_token_data()`. `AccessTokenBearer.verify_token_data()` specifically rejects the token if it's a refresh token (`token_data["refresh"]` is true). dependencies.py:39-62 dependencies.py:80-90
- `src/auth/utils.py` → `decode_token()` verifies the signature with `Config.JWT_SECRET`, with 10-second leeway for clock skew. utils.py:177-185

### 2d. Inside the endpoint body — the crypto (all in `src/pki/routes.py`)

- It reads `user_email` from the token and loads the user via `user_service.get_user_by_email()`; a missing user yields 404. routes.py:36-43
- It generates a fresh RSA-2048 private key for you. routes.py:45-49
- It builds your X.509 certificate: subject CN = your email, validity 1 year, a random serial, and issuer = the Root CA subject. routes.py:52-73
- It loads the issuer via `src/pki/pki_engine.py` → `get_root_ca()`, which reads `~/usr/certs/root_ca.key` and `~/usr/certs/root_ca.pem` from disk. (Those files were created at startup by `ensure_root_ca_exists()`, called in the app lifespan.) routes.py:60-61 pki_engine.py:110-135
- It signs your certificate with the Root CA private key using `certificate_builder.sign(root_ca_key, hashes.SHA256())`. routes.py:98-99

### 2e. Persistence (the "whitelist" DB row)

- It builds a `src/pki/models.py` → `ClientCertificate` record (table `client_certificates`) with your `user_id`, hex serial, validity dates, `is_revoked=False`, and the PEM, then `session.add()` + `await session.commit()`. This is the row that later shows in `/history`. routes.py:107-117 models.py:10-11

### 2f. Bundling + response (in `src/pki/routes.py`)

- It bundles your private key + your cert + the CA cert into an encrypted PKCS#12 archive via `pkcs12.serialize_key_and_certificates()`, encrypted with the `p12_password` you supplied. routes.py:120-128
- It returns the raw `.p12` bytes as a `Response` with `Content-Disposition: attachment; filename="user_certificate.p12"`. routes.py:131-137
- Errors: an `HTTPException` (e.g. the 404) is re-raised as-is; any other exception triggers `session.rollback()` and a 500. routes.py:139-147

### 2g. Frontend handles the download (in `frontend-vue/src/views/DashboardView.vue`)

- Back in `submitCertPassword()`: if `!response.ok` it parses `errorData.detail` and throws (shown via `alert`). On success it calls `response.blob()`, passes it to `triggerP12Download(blob)`, closes the modal, and calls `fetchCertHistory()` to refresh the table. DashboardView.vue:528-544
- `triggerP12Download()` creates an object URL, a hidden `<a download="user_certificate.p12">`, clicks it programmatically, and revokes the URL — that's the file landing in your Downloads folder. DashboardView.vue:472-482