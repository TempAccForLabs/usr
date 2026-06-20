// Backend base URL — change this or set VITE_API_BASE_URL in a .env file.
// Empty string means "same origin" (works when Vite proxies /auth → backend).
// For standalone use point it at the running backend, e.g. "http://localhost:5000"
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''
