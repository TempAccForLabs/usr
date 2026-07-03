<template>
  <div class="protected-section">
    <h2>Welcome to Protected Area</h2>

    <div class="protected-content">
      <!-- Primary Actions -->
      <div class="btn-group">
        <button class="btn btn-primary" :disabled="fetchingUser" @click="fetchUserData">
          {{ fetchingUser ? 'Loading…' : 'Get My Profile' }}
        </button>
        <button class="btn btn-secondary" :disabled="refreshing" @click="doRefreshToken">
          {{ refreshing ? 'Refreshing…' : 'Refresh Token' }}
        </button>
      </div>

      <!-- 2FA Status Block -->
      <div style="margin-top:20px; padding:15px; background:#f8f9fa; border-radius:5px;">
        <h3 style="margin-top:0;">🔐 Two-Factor Authentication</h3>
        <div :class="['twofa-status', twoFAEnabled ? 'enabled' : 'disabled']">
          {{ twoFAEnabled ? '🟢 Enabled' : '🔴 Disabled' }}
        </div>

        <div style="margin-top:15px; padding:10px; background:#fff3cd; border:1px solid #ffeaa7; border-radius:4px;">
          <h4>Testing Instructions:</h4>
          <p>To get the current TOTP code for testing:</p>
          <ol style="margin-left:18px; margin-top:6px;">
            <li>Click <strong>Debug Auth</strong> in the debug panel below</li>
            <li>Then click <strong>Test Endpoints</strong> — the current code will appear in the browser console</li>
            <li>Or call <code>/auth/debug/current-totp</code> directly with your token</li>
          </ol>
        </div>
      </div>

      <!-- Debug Panel -->
      <div class="debug-panel" style="margin-top:20px; padding:15px; background:#f8f9fa; border-radius:5px;">
        <h3 style="margin-top:0;">🔧 Debug Tools</h3>
        <div class="debug-buttons" style="display:flex; gap:10px; margin-bottom:15px; flex-wrap:wrap;">
          <button
            class="btn"
            style="background:#ffc107; color:black; flex:1; width:auto;"
            @click="debugAuth"
          >Debug Auth</button>
          <button
            class="btn"
            style="background:#17a2b8; color:white; flex:1; width:auto;"
            @click="testEndpoints"
          >Test Endpoints</button>
          <button
            class="btn"
            style="background:#dc3545; color:white; flex:1; width:auto;"
            @click="debugLogout"
          >Debug Logout</button>
          <button
            class="btn"
            style="background:orange; color:black; flex:1; width:auto;"
            :disabled="forceRefreshing"
            @click="forceRefresh"
          >{{ forceRefreshing ? 'Refreshing…' : 'FORCE REFRESH' }}</button>
        </div>
        <div
          class="debug-info"
          style="font-family:monospace; font-size:12px; background:white; padding:10px; border-radius:3px;"
          v-html="debugInfoHtml"
        />
      </div>

      <!-- PKI Management -->
      <div style="margin-top:20px; padding:15px; background:#f8f9fa; border-radius:5px;">
        <h3 style="margin-top:0;">🔏 PKI Management</h3>
        <p style="color:#495057; font-size:0.95rem;">
          Generate a personal digital certificate (.p12) you can use to sign documents.
        </p>
        <button
          class="btn btn-primary"
          style="width:auto;"
          :disabled="generatingCert"
          @click="openCertModal"
        >
          {{ generatingCert ? 'Generating…' : 'Generate New Certificate' }}
        </button>

        <div style="margin-top:20px;">
          <h4 style="margin-bottom:10px;">Certificate History</h4>
          <p v-if="loadingHistory" style="color:#495057;">Loading certificate history…</p>
          <p v-else-if="historyError" style="color:#b02a37;">{{ historyError }}</p>
          <p v-else-if="certHistory.length === 0" style="color:#495057;">
            No certificates generated yet.
          </p>
          <table v-else class="cert-history-table">
            <thead>
              <tr>
                <th>Serial Number</th>
                <th>Issued Date</th>
                <th>Expiration Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="cert in certHistory" :key="cert.id">
                <td class="cert-serial">{{ cert.serial_number }}</td>
                <td>{{ formatDate(cert.valid_from) }}</td>
                <td>{{ formatDate(cert.valid_until) }}</td>
                <td>
                  <span :class="['cert-status-badge', cert.is_revoked ? 'revoked' : 'active']">
                    {{ cert.is_revoked ? 'Revoked' : 'Active (Whitelisted)' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- User / Token Data -->
      <div class="user-data-box" :style="{ color: userDataColor }">{{ userDataText }}</div>
    </div>

    <!-- Certificate Password Modal -->
    <div v-if="showCertModal" class="modal-overlay" @click.self="closeCertModal">
      <div class="modal-box">
        <h3>Create a Certificate Password</h3>
        <p>
          Choose a password to protect your certificate file. You'll need it to unlock
          the certificate when signing documents later.
        </p>
        <p style="color:#b02a37; font-weight:600;">
          ⚠️ You must remember this password to sign documents later. It cannot be recovered.
        </p>
        <input
          v-model="certPassword"
          type="password"
          placeholder="Certificate Password (min 6 characters)"
          style="margin-bottom:15px;"
          @keyup.enter="submitCertPassword"
        />
        <div v-if="certModalError" class="message error">{{ certModalError }}</div>
        <div class="btn-group" style="margin-top:15px;">
          <button class="btn btn-secondary" :disabled="generatingCert" @click="closeCertModal">
            Cancel
          </button>
          <button class="btn btn-primary" :disabled="generatingCert" @click="submitCertPassword">
            {{ generatingCert ? 'Generating…' : 'Generate' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import { API_BASE_URL } from '../config.js'

const auth = useAuth()
const router = useRouter()

const fetchingUser = ref(false)
const refreshing = ref(false)
const forceRefreshing = ref(false)
const twoFAEnabled = ref(false)
const userDataText = ref('User data and token info will appear here…')
const userDataColor = ref('inherit')
const debugInfoHtml = ref('Debug info will appear here…')

const showCertModal = ref(false)
const certPassword = ref('')
const certModalError = ref('')
const generatingCert = ref(false)

const certHistory = ref([])
const loadingHistory = ref(false)
const historyError = ref('')

// ── helpers ────────────────────────────────────────────────────────────────
function updateDebugDisplay() {
  const authed = auth.isAuthenticated.value
  const status = authed ? '✅ AUTHENTICATED' : '❌ NOT AUTHENTICATED'
  const token = auth.state.accessToken ? '✅ Present' : '❌ Missing'
  const user = auth.state.userEmail || 'None'
  debugInfoHtml.value = `
    <strong>Debug Info:</strong><br>
    Status: ${status}<br>
    Token: ${token}<br>
    User: ${user}
  `
}

// ── lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
  updateDebugDisplay()
  // Check 2FA status by pinging /auth/me
  try {
    const data = await auth.getCurrentUser()
    twoFAEnabled.value = !!data.is_2fa_verified
  } catch {
    twoFAEnabled.value = false
  }
  // auto debug report
  setTimeout(() => debugAuth(), 800)
  fetchCertHistory()
})

// ── actions ────────────────────────────────────────────────────────────────
async function fetchUserData() {
  fetchingUser.value = true
  userDataText.value = 'Loading…'
  userDataColor.value = 'inherit'
  try {
    const data = await auth.getCurrentUser()
    userDataText.value = JSON.stringify(data, null, 2)
    userDataColor.value = 'green'
    updateDebugDisplay()
  } catch (err) {
    userDataText.value = `Error: ${err.message}`
    userDataColor.value = 'red'
  } finally {
    fetchingUser.value = false
  }
}

async function doRefreshToken() {
  refreshing.value = true
  userDataText.value = 'Refreshing token…'
  userDataColor.value = 'blue'
  const oldToken = auth.state.accessToken
  const oldLast50 = oldToken ? oldToken.slice(-50) : 'No previous token'
  try {
    const data = await auth.refreshAccessToken()
    const newToken = data.access_token
    const newLast50 = newToken.slice(-50)
    const diff = oldToken !== newToken
    userDataText.value =
      `${diff ? '✅' : '⚠️'} TOKEN REFRESH COMPLETE\n\n` +
      `Token Change: ${diff ? 'DIFFERENT' : 'SAME'}\n` +
      `Old Token (last 50): ${oldLast50}\n` +
      `New Token (last 50): ${newLast50}\n` +
      `Full Token Match: ${!diff ? 'YES ⚠️' : 'NO ✅'}\n\nToken refresh was successful!`
    userDataColor.value = diff ? 'green' : 'orange'
    updateDebugDisplay()
  } catch (err) {
    userDataText.value = `❌ REFRESH FAILED:\n${err.message}`
    userDataColor.value = 'red'
  } finally {
    refreshing.value = false
  }
}

function debugAuth() {
  console.log('🔍 === AUTHENTICATION DEBUG REPORT ===')
  console.log('🔐 TOKEN ANALYSIS:')
  console.log('   Access Token Present:', auth.state.accessToken ? '✅ Yes' : '❌ No')
  console.log('   Refresh Token Present:', auth.state.refreshToken ? '✅ Yes' : '❌ No')
  if (auth.state.accessToken) {
    try {
      const tokenData = JSON.parse(atob(auth.state.accessToken.split('.')[1]))
      const expiryTime = new Date(tokenData.exp * 1000)
      const minutes = Math.floor((expiryTime - new Date()) / 60000)
      console.log('   Token Expires:', expiryTime.toLocaleString())
      console.log('   Time Until Expiry:', minutes + ' minutes')
      console.log('   Token User:', tokenData.user)
      console.log('   2FA Verified:', tokenData.is_2fa_verified)
      if (minutes < 5) console.log('   ⚠️ Token expires soon!')
    } catch (e) {
      console.log('   Token Parse Error:', e.message)
    }
  }
  console.log('📦 LOCAL STORAGE:')
  console.log('   Access Token:', auth.state.accessToken ? '✅ Present' : '❌ Missing')
  console.log('   Refresh Token:', auth.state.refreshToken ? '✅ Present' : '❌ Missing')
  console.log('   User Email:', auth.state.userEmail || '❌ Missing')
  console.log('   2FA Pending:', auth.state.pending2FA ? '✅ Yes' : '❌ No')
  console.log('   Temp Token:', auth.state.tempToken ? '✅ Present' : '❌ Missing')
  console.log('🔐 AUTH STATE:')
  console.log('   isAuthenticated():', auth.isAuthenticated.value)
  console.log('   User Email (Memory):', auth.state.userEmail)
  console.log('========================================')
  updateDebugDisplay()
}

async function testEndpoints() {
  console.log('🚀 === TESTING API ENDPOINTS ===')
  try {
    const dbPing = await auth.dbPing()
    console.log('✅ Database Ping:', dbPing.status)
  } catch (err) {
    console.log('❌ DB Ping failed:', err.message)
  }
  if (auth.isAuthenticated.value) {
    try {
      const userData = await auth.getCurrentUser()
      console.log('✅ Protected Route: Access granted')
      console.log('   User Data:', userData)
    } catch (err) {
      console.log('❌ Protected Route:', err.message)
    }
    try {
      const totp = await auth.getCurrentTOTP()
      console.log('✅ Current TOTP Code:', totp.current_code)
    } catch (err) {
      console.log('❌ Current TOTP endpoint error:', err.message)
    }
  } else {
    console.log('⏸️ Protected routes skipped (not authenticated)')
  }
  console.log('================================')
}

function debugLogout() {
  console.log('🔄 Debug: Clearing all auth data')
  auth.logout()
  router.replace('/')
}

// ── PKI certificate generation ────────────────────────────────────────────
function openCertModal() {
  certPassword.value = ''
  certModalError.value = ''
  showCertModal.value = true
}

function closeCertModal() {
  if (generatingCert.value) return
  showCertModal.value = false
  certPassword.value = ''
  certModalError.value = ''
}

async function requestCertificate(token) {
  return fetch(`${API_BASE_URL}/api/certificates/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ p12_password: certPassword.value }),
  })
}

function triggerP12Download(blob) {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.style.display = 'none'
  link.href = url
  link.download = 'user_certificate.p12'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

function formatDate(isoString) {
  if (!isoString) return '—'
  const date = new Date(isoString)
  if (Number.isNaN(date.getTime())) return isoString
  return date.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

async function fetchCertHistory() {
  if (!auth.isAuthenticated.value) return
  loadingHistory.value = true
  historyError.value = ''
  try {
    certHistory.value = await auth.request('/api/certificates/history')
  } catch (err) {
    historyError.value = `Failed to load certificate history: ${err.message}`
  } finally {
    loadingHistory.value = false
  }
}

async function submitCertPassword() {
  certModalError.value = ''

  if (!certPassword.value || certPassword.value.length < 6) {
    certModalError.value = 'Password must be at least 6 characters.'
    return
  }

  generatingCert.value = true
  try {
    let response = await requestCertificate(auth.state.accessToken)

    // Access token expired — refresh once and retry automatically
    if (response.status === 401) {
      try {
        await auth.refreshAccessToken()
        response = await requestCertificate(auth.state.accessToken)
      } catch (refreshErr) {
        auth.logout()
        router.replace('/')
        throw new Error('Your session expired. Please log in again.')
      }
    }

    if (!response.ok) {
      let detail = 'Failed to generate certificate.'
      try {
        const errorData = await response.json()
        detail = errorData.detail || detail
      } catch {
        // response body wasn't JSON — keep default message
      }
      throw new Error(detail)
    }

    const blob = await response.blob()
    triggerP12Download(blob)

    showCertModal.value = false
    certPassword.value = ''
    fetchCertHistory()
  } catch (err) {
    certModalError.value = err.message || 'Something went wrong generating your certificate.'
    alert(`Certificate generation failed: ${certModalError.value}`)
  } finally {
    generatingCert.value = false
  }
}

async function forceRefresh() {
  forceRefreshing.value = true
  userDataText.value = 'Force refreshing token…'
  userDataColor.value = 'purple'
  const oldToken = auth.state.accessToken
  const oldFirst30 = oldToken ? oldToken.slice(0, 30) : 'N/A'
  const oldLast50 = oldToken ? oldToken.slice(-50) : 'N/A'
  try {
    const data = await auth.refreshAccessToken()
    const newToken = data.access_token
    const newFirst30 = newToken.slice(0, 30)
    const newLast50 = newToken.slice(-50)
    const diff = oldToken !== newToken
    userDataText.value =
      `${diff ? '🎉' : '🔁'} FORCE REFRESH RESULTS\n\n` +
      `STATUS: ${diff ? 'CHANGED SUCCESSFULLY' : 'REMAINED THE SAME'}\n\n` +
      `COMPARISON:\n` +
      `• Full Match: ${!diff ? 'YES ⚠️' : 'NO ✅'}\n` +
      `• Old Length: ${oldToken?.length ?? 0} chars\n` +
      `• New Length: ${newToken.length} chars\n\n` +
      `TOKEN PREVIEWS:\n` +
      `Old (first 30): ${oldFirst30}...\n` +
      `New (first 30): ${newFirst30}...\n\n` +
      `LAST 50 CHARACTERS:\n` +
      `Old: ${oldLast50}\n` +
      `New: ${newLast50}`
    userDataColor.value = diff ? 'darkgreen' : 'darkorange'
    updateDebugDisplay()
  } catch (err) {
    userDataText.value = `❌ FORCE REFRESH FAILED:\n${err.message}`
    userDataColor.value = 'red'
  } finally {
    forceRefreshing.value = false
  }
}
</script>
