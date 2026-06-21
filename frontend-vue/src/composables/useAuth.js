import { reactive, computed } from 'vue'
import { API_BASE_URL } from '../config.js'

const state = reactive({
  accessToken:  localStorage.getItem('access_token')  || null,
  refreshToken: localStorage.getItem('refresh_token') || null,
  userEmail:    localStorage.getItem('user_email')    || null,
  tempToken:    localStorage.getItem('temp_token')    || null,
  pending2FA:   localStorage.getItem('pending_2fa') === 'true',
})

const isAuthenticated = computed(() => !!state.accessToken)

async function request(endpoint, options = {}, useTokenOverride = null) {
  const url = `${API_BASE_URL}${endpoint}`
  const config = {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  }
  const tokenToUse = useTokenOverride !== null ? useTokenOverride : state.accessToken
  if (tokenToUse && !endpoint.includes('/refresh_token')) {
    config.headers['Authorization'] = `Bearer ${tokenToUse}`
  }
  const response = await fetch(url, config)
  const data = await response.json()
  if (!response.ok) throw new Error(data.detail || 'Request failed')
  return data
}

function setTokens(accessToken, refreshToken) {
  state.accessToken  = accessToken
  state.refreshToken = refreshToken
  localStorage.setItem('access_token',  accessToken)
  localStorage.setItem('refresh_token', refreshToken)
}

function setUserEmail(email) {
  state.userEmail = email
  localStorage.setItem('user_email', email)
}

function clear2FAState() {
  state.pending2FA = false
  state.tempToken  = null
  localStorage.removeItem('pending_2fa')
  localStorage.removeItem('temp_token')
}

function logout() {
  state.accessToken  = null
  state.refreshToken = null
  state.userEmail    = null
  clear2FAState()
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user_email')
}

async function login(email, password) {
  const data = await request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
  // Login now issues full JWT directly — no 2FA step on login
  setTokens(data.access_token, data.refresh_token)
  setUserEmail(data.user.email)
  clear2FAState()
  return { requires2FA: false, message: data.message, user: data.user }
}

async function signup(userData) {
  const data = await request('/auth/signup', {
    method: 'POST',
    body: JSON.stringify(userData),
  })
  // Store temp token for the verify-2fa-setup call
  state.tempToken = data.temp_token
  localStorage.setItem('temp_token',  data.temp_token)
  localStorage.setItem('pending_2fa', 'true')
  return {
    requires2fa_verification: true,
    message:    data.message,
    temp_token: data.temp_token,
    user_email: data.user_email,
    qr_code:    data.qr_code,
    manual_code: data.manual_code,
    totp_uri:   data.totp_uri,
  }
}

async function complete2FASignup(code) {
  const data = await request(
    '/auth/verify-2fa-setup',
    { method: 'POST', body: JSON.stringify({ code }) },
    state.tempToken,
  )
  // verify-2fa-setup now returns full tokens after enabling 2FA
  setTokens(data.access_token, data.refresh_token)
  setUserEmail(data.user.email)
  clear2FAState()
  return data
}

async function refreshAccessToken() {
  if (!state.refreshToken) throw new Error('No refresh token available')
  const data = await request('/auth/refresh_token', {
    method: 'GET',
    headers: { Authorization: `Bearer ${state.refreshToken}` },
  })
  state.accessToken = data.access_token
  localStorage.setItem('access_token', state.accessToken)
  return data
}

async function getCurrentUser() {
  try {
    return await request('/auth/me')
  } catch (error) {
    if (error.message.includes('403') || error.message.includes('401')) {
      const refreshData = await refreshAccessToken()
      if (!refreshData) { logout(); throw new Error('Session expired.') }
      return await request('/auth/me')
    }
    throw error
  }
}

async function getCurrentTOTP() {
  return await request('/auth/debug/current-totp')
}

async function getTokenContents() {
  return await request('/auth/debug/token-contents')
}

async function dbPing() {
  return await request('/auth/debug/db-ping')
}

export function useAuth() {
  return {
    state,
    isAuthenticated,
    request,
    login,
    signup,
    logout,
    complete2FASignup,
    refreshAccessToken,
    getCurrentUser,
    getCurrentTOTP,
    getTokenContents,
    dbPing,
    clear2FAState,
  }
}
