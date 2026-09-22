
## Part 0 — The prerequisite: you must be authenticated

Workflow B's `/api/certificates/sign` endpoint is JWT-protected, so before any PDF can be signed you must already hold a valid access token from signup or login (that's Workflow A's Part 0 — same token). You must also already have generated and downloaded your `user_certificate.p12` in Workflow A, because you upload it here. routes.py:150-156

## Part 1 — What you see and fill in (frontend UI)

The 📝 Document Signing panel lives in `frontend-vue/src/views/DashboardView.vue`. It has three inputs and one button:

- A PDF Document file picker (`accept=".pdf"`), wired to `onPdfChange`. DashboardView.vue:121-124
- A Digital Certificate file picker (`accept=".p12,.pfx"`), wired to `onP12Change`. DashboardView.vue:126-129
- A Certificate Password box, bound to `signPassword`. DashboardView.vue:131-139
- The Sign Document button, which calls `submitSigningRequest` on click and shows "Signing…" while `isLoading` is true. DashboardView.vue:141-148

## Part 2 — Certificate signing (step by step)

### 2a. You pick the files (in `frontend-vue/src/views/DashboardView.vue`)

- Choosing the PDF fires `onPdfChange()`, which stores the file in `pdfFile.value`. DashboardView.vue:362-364
- Choosing the `.p12` fires `onP12Change()`, which stores it in `p12File.value`. DashboardView.vue:366-368

### 2b. You click "Sign Document" → `submitSigningRequest()` (in `frontend-vue/src/views/DashboardView.vue`)

- It first clears `signingError`, then does a client-side presence check: if the PDF, the `.p12`, or the password is missing, it stops with the message "Please select a PDF, a certificate, and enter the password." — nothing hits the network. DashboardView.vue:398-404
- It sets `isLoading = true` and calls `requestSign(auth.state.accessToken)`. DashboardView.vue:406-408

### 2c. Building the request → `buildSignFormData()` + `requestSign()` (in `frontend-vue/src/views/DashboardView.vue`)

- `buildSignFormData()` creates a `FormData` and appends the three fields with the exact names the backend expects: `pdf_file`, `p12_file`, and `p12_password`. DashboardView.vue:370-376
- `requestSign(token)` does a raw `fetch` to `POST ${API_BASE_URL}/api/certificates/sign` with an `Authorization: Bearer <token>` header and that `FormData` as the body. Note it does not set `Content-Type` — the browser sets `multipart/form-data` with the correct boundary automatically. `API_BASE_URL` comes from `frontend-vue/src/config.js`. DashboardView.vue:378-384

### 2d. The 401 auto-retry (in `frontend-vue/src/views/DashboardView.vue` + `frontend-vue/src/composables/useAuth.js`)

- If the first response is `401`, `submitSigningRequest()` calls `auth.refreshAccessToken()`, then retries `requestSign()` once with the new token. If the refresh itself fails, it logs you out and redirects to `/`. DashboardView.vue:410-419
- `refreshAccessToken()` lives in `useAuth.js` — it GETs `/auth/refresh_token` using your refresh token, then stores the new access token in state and `localStorage`. useAuth.js:104-113

────────── request leaves the browser, hits the server ──────────

### 2e. Routing + auth gate (in `src/__init__.py` → `src/auth/dependencies.py` → `src/auth/utils.py`)

- `src/__init__.py` mounts the `pki_router` under prefix `/api/certificates`, so `/api/certificates/sign` lands in the PKI routes. __init__.py:89-93
- The endpoint declares `token_details: dict = Depends(AccessTokenBearer())`, so before the handler body runs, the JWT is checked. routes.py:150-156
- `AccessTokenBearer` (in `src/auth/dependencies.py`) inherits `TokenBearer.__call__()`, which pulls the Bearer token, calls `decode_token()` (from `src/auth/utils.py`), and raises 403 if the token is invalid/expired. `AccessTokenBearer.verify_token_data()` additionally raises 403 if you passed a _refresh_ token instead of an access token. dependencies.py:39-62 dependencies.py:80-90

### 2f. The signing handler → `sign_pdf()` (in `src/pki/routes.py`)

- It reads both uploads into memory asynchronously: `pdf_bytes = await pdf_file.read()` and `p12_bytes = await p12_file.read()`. routes.py:177-180
- It hands those bytes plus the password to `sign_pdf_document(pdf_bytes, p12_bytes, p12_password)`. routes.py:182-183

### 2g. The crypto worker → `sign_pdf_document()` (in `src/pki/signer.py`)

- It loads your certificate/key from the `.p12` via `signers.SimpleSigner.load_pkcs12_data(...)`, passing the password. If the password is wrong or the file is corrupt, it raises a `ValueError` reading "Invalid certificate password or corrupt .p12 file". signer.py:35-43
- It sets up a trusted timestamp source: `timestamps.HTTPTimeStamper(url="https://freetsa.org/tsr")` — this is why you must be online when signing. signer.py:45
- It wraps the PDF in an `IncrementalPdfFileWriter` and builds `PdfSignatureMetadata(field_name="DigitalSignature", validation_context=None)` — that `field_name` is the `DigitalSignature` field you later saw in `pdfsig`, and `validation_context=None` means it signs only, no trust checking. signer.py:47-52
- The actual signing runs off the event loop via `await asyncio.to_thread(_do_sign)`, where `_do_sign()` calls `signers.sign_pdf(...)` writing to an in-memory buffer. A `SigningError` becomes a `RuntimeError("Failed to sign PDF document...")`. signer.py:54-69
- It returns the signed PDF bytes, and in the `finally` block deletes the signer and calls `gc.collect()` to clear the key material from memory. signer.py:71-79

### 2h. Response + error mapping (in `src/pki/routes.py`)

- On success it returns the raw signed bytes as a `Response` with `media_type="application/pdf"` and `Content-Disposition: attachment; filename="signed_document.pdf"`. routes.py:186-192
- Errors: a `ValueError` (bad password / corrupt `.p12`) → 400 with the exact message; a `RuntimeError` (corrupt PDF / signing failure) → 400 "Failed to sign PDF document..."; a JWT `HTTPException` is re-raised as-is; anything else → 500. routes.py:194-217

────────── signed PDF comes back to the browser ──────────

### 2i. Frontend handles the download (in `frontend-vue/src/views/DashboardView.vue`)

- Back in `submitSigningRequest()`: if `!response.ok` it parses `errorData.detail` and throws (shown via `alert`). On success it calls `response.blob()`, passes it to `triggerSignedDownload(blob)`, then resets `pdfFile`, `p12File`, and `signPassword` to blank. DashboardView.vue:421-444
- `triggerSignedDownload()` creates an object URL, a hidden `<a download="signed_document.pdf">`, clicks it programmatically, and revokes the URL — that's the signed file landing in your Downloads folder. DashboardView.vue:386-396

---

Notes on CMS:
1. **CMS** (Cryptographic Message Syntax) is the container holding the PDF signature, your certificate, the hash information, and the TSA timestamp token.
2. Your application uses the private key inside your `.p12` file to generate the actual digital signature locally.
3. PyHanko creates a PDF signature placeholder and a `/ByteRange`, then hashes all PDF bytes outside that placeholder.
4. FreeTSA receives a hash of the generated signature, adds its trusted time and TSA signature, and returns a timestamp token—it never receives your PDF or private key.
5. PyHanko then assembles the CMS containing your signature plus the TSA token and fills the reserved PDF gap with that CMS data.

