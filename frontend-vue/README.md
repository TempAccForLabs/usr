# USR Authentication — Vue 3 Frontend

A complete Vue 3 rewrite of the USR authentication frontend.
Uses Composition API (`<script setup>`), Vue Router, and composables for all shared state and API calls. No Vuex or Pinia.

## Features

- Login with email + password
- Mandatory 2FA / TOTP verification on every login
- Signup with mandatory 2FA verification to complete account creation
- JWT token refresh (manual and automatic)
- Protected dashboard: profile fetch, token refresh, force refresh
- Debug panel matching the original vanilla-JS debug tools

## Setup

### Prerequisites

- Node.js 18+

### Install & run dev server

```bash
cd frontend-vue
npm install
npm run dev
```

The dev server starts at **http://localhost:5173** and proxies all `/auth/*` requests to the FastAPI backend at `http://localhost:5000`.

Make sure the backend is already running (`uvicorn src:app --host 0.0.0.0 --port 5000 --reload`) before using the frontend.

### Build for production

```bash
npm run build   # output goes to frontend-vue/dist/
npm run preview # preview the production build locally
```

## Configuration

The backend base URL lives in one place:

```
frontend-vue/src/config.js
```

```js
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''
```

- **Empty string** (default) → Vite's dev-server proxy forwards `/auth/*` to `http://localhost:5000`. Works out of the box.
- **Explicit URL** → create a `.env.local` file:

```env
VITE_API_BASE_URL=http://localhost:5000
```

## Project structure

```
frontend-vue/
├── index.html
├── vite.config.js          # Vite + proxy config
├── package.json
├── src/
│   ├── main.js
│   ├── App.vue             # Shell: header, logout, route guard
│   ├── style.css           # Global styles (same design as original)
│   ├── config.js           # Single place for API base URL
│   ├── composables/
│   │   └── useAuth.js      # All API calls + shared reactive auth state
│   ├── router/
│   │   └── index.js        # Vue Router (/ = auth, /dashboard = protected)
│   ├── views/
│   │   ├── AuthView.vue    # Login + Signup tabs
│   │   └── DashboardView.vue  # Protected area
│   └── components/
│       └── TwoFAModal.vue  # Reusable 2FA code entry modal
└── README.md
```
