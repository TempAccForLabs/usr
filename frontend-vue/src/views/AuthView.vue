<template>
  <main>
    <div class="auth-section">
      <div class="tabs">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'login' }"
          @click="activeTab = 'login'"
        >Login</button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'signup' }"
          @click="activeTab = 'signup'"
        >Sign Up</button>
      </div>

      <!-- Login Tab -->
      <div v-show="activeTab === 'login'" class="tab-content">
        <form class="auth-form" @submit.prevent="handleLogin">
          <h2>Login to Your Account</h2>
          <div class="form-group">
            <label for="login-email">Email:</label>
            <input
              id="login-email"
              v-model="loginForm.email"
              type="email"
              required
              autocomplete="email"
            />
          </div>
          <div class="form-group">
            <label for="login-password">Password:</label>
            <input
              id="login-password"
              v-model="loginForm.password"
              type="password"
              required
              autocomplete="current-password"
            />
          </div>
          <button type="submit" class="btn btn-primary" :disabled="loginLoading">
            {{ loginLoading ? 'Logging in…' : 'Login' }}
          </button>
          <div v-if="loginMessage" :class="['message', loginMessageType]">{{ loginMessage }}</div>
        </form>
      </div>

      <!-- Signup Tab -->
      <div v-show="activeTab === 'signup'" class="tab-content">
        <form class="auth-form" autocomplete="off" @submit.prevent="handleSignup">
          <h2>Create New Account</h2>
          <div class="form-group">
            <label for="signup-firstname">First Name:</label>
            <input
              id="signup-firstname"
              v-model="signupForm.first_name"
              type="text"
              required
              autocomplete="given-name"
            />
          </div>
          <div class="form-group">
            <label for="signup-lastname">Last Name:</label>
            <input
              id="signup-lastname"
              v-model="signupForm.last_name"
              type="text"
              required
              autocomplete="family-name"
            />
          </div>
          <div class="form-group">
            <label for="signup-username">Username:</label>
            <input
              id="signup-username"
              v-model="signupForm.username"
              type="text"
              required
              maxlength="8"
              autocomplete="off"
            />
          </div>
          <div class="form-group">
            <label for="signup-email">Email:</label>
            <input
              id="signup-email"
              v-model="signupForm.email"
              type="email"
              required
              autocomplete="email"
            />
          </div>

          <!-- Password field + live requirements panel -->
          <div class="form-group">
            <label for="signup-password">Password:</label>
            <input
              id="signup-password"
              v-model="signupForm.password"
              type="password"
              required
              autocomplete="new-password"
              @focus="passwordFocused = true"
            />
          </div>

          <div v-if="passwordFocused || signupForm.password.length > 0" class="password-requirements">
            <p class="req-title">Password requirements:</p>
            <ul>
              <li :class="checks.minLen   ? 'req-ok' : 'req-fail'">{{ checks.minLen   ? '✓' : '✗' }} At least 16 characters</li>
              <li :class="checks.maxLen   ? 'req-ok' : 'req-fail'">{{ checks.maxLen   ? '✓' : '✗' }} No more than 50 characters</li>
              <li :class="checks.upper    ? 'req-ok' : 'req-fail'">{{ checks.upper    ? '✓' : '✗' }} At least one capital letter</li>
              <li :class="checks.digit    ? 'req-ok' : 'req-fail'">{{ checks.digit    ? '✓' : '✗' }} At least one digit</li>
              <li :class="checks.special  ? 'req-ok' : 'req-fail'">{{ checks.special  ? '✓' : '✗' }} At least one special character (!@#$% etc.)</li>
              <li :class="checks.twoSpaces ? 'req-ok' : 'req-fail'">{{ checks.twoSpaces ? '✓' : '✗' }} At least two spaces in the password</li>
              <li :class="checks.noAdjacent ? 'req-ok' : 'req-fail'">{{ checks.noAdjacent ? '✓' : '✗' }} Spaces must not be adjacent to each other</li>
            </ul>
            <p class="req-example">
              Example: <code>I am a P@ssw0rd here</code>
            </p>
          </div>

          <button type="submit" class="btn btn-primary" :disabled="signupLoading || !allChecksPassed">
            {{ signupLoading ? 'Creating account…' : 'Sign Up' }}
          </button>
          <div v-if="signupMessage" :class="['message', signupMessageType]">{{ signupMessage }}</div>
        </form>
      </div>
    </div>

    <!-- 2FA Signup Modal -->
    <TwoFAModal
      v-if="show2FASignup"
      title="Set Up Two-Factor Authentication"
      :user-email="signupUserEmail"
      :qr-code="signupQrCode"
      :manual-code="signupManualCode"
      input-id="signup-2fa-code"
      ref="signupModalRef"
      @submit="verify2FASignup"
      @cancel="cancel2FASignup"
    />
  </main>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import TwoFAModal from '../components/TwoFAModal.vue'

const auth   = useAuth()
const router = useRouter()

const activeTab = ref('login')

// ── Login ──────────────────────────────────────────────────────────────────
const loginForm        = reactive({ email: '', password: '' })
const loginLoading     = ref(false)
const loginMessage     = ref('')
const loginMessageType = ref('info')

function setLoginMsg(msg, type = 'info') {
  loginMessage.value     = msg
  loginMessageType.value = type
}

async function handleLogin() {
  loginLoading.value = true
  setLoginMsg('Logging in…', 'info')
  try {
    await auth.login(loginForm.email, loginForm.password)
    setLoginMsg('Login successful!', 'success')
    router.replace('/dashboard')
  } catch (err) {
    setLoginMsg(err.message, 'error')
  } finally {
    loginLoading.value = false
  }
}

// ── Signup ─────────────────────────────────────────────────────────────────
const signupForm        = reactive({ first_name: '', last_name: '', username: '', email: '', password: '' })
const signupLoading     = ref(false)
const signupMessage     = ref('')
const signupMessageType = ref('info')
const show2FASignup     = ref(false)
const signupModalRef    = ref(null)
const signupQrCode      = ref('')
const signupManualCode  = ref('')
const signupUserEmail   = ref('')
const passwordFocused   = ref(false)

// ── Live password checks ───────────────────────────────────────────────────
const SPECIAL = /[!@#$%^&*()\-_=+\[\]{};':"\\|,.<>\/?`~]/

const checks = computed(() => {
  const p = signupForm.password
  const spaceIdxs = [...p].reduce((acc, c, i) => (c === ' ' ? [...acc, i] : acc), [])
  const hasTwo    = spaceIdxs.length >= 2
  const noAdj     = hasTwo && !spaceIdxs.some((idx, i) => i > 0 && idx - spaceIdxs[i - 1] === 1)

  return {
    minLen:     p.length >= 16,
    maxLen:     p.length <= 50,
    upper:      /[A-Z]/.test(p),
    digit:      /\d/.test(p),
    special:    SPECIAL.test(p),
    twoSpaces:  hasTwo,
    noAdjacent: noAdj,
  }
})

const allChecksPassed = computed(() => Object.values(checks.value).every(Boolean))

function setSignupMsg(msg, type = 'info') {
  signupMessage.value     = msg
  signupMessageType.value = type
}

function clientValidatePassword() {
  if (!allChecksPassed.value) {
    const failed = []
    if (!checks.value.minLen)     failed.push('at least 16 characters')
    if (!checks.value.maxLen)     failed.push('no more than 50 characters')
    if (!checks.value.upper)      failed.push('at least one capital letter')
    if (!checks.value.digit)      failed.push('at least one digit')
    if (!checks.value.special)    failed.push('at least one special character')
    if (!checks.value.twoSpaces)  failed.push('at least two spaces')
    if (!checks.value.noAdjacent) failed.push('spaces must not be adjacent')
    return 'Password must contain: ' + failed.join('; ')
  }
  return null
}

async function handleSignup() {
  passwordFocused.value = true
  const err = clientValidatePassword()
  if (err) { setSignupMsg(err, 'error'); return }

  signupLoading.value = true
  setSignupMsg('Creating account…', 'info')
  try {
    const result = await auth.signup(signupForm)
    signupQrCode.value     = result.qr_code     || ''
    signupManualCode.value = result.manual_code  || ''
    signupUserEmail.value  = result.user_email   || signupForm.email
    setSignupMsg(result.message, 'info')
    show2FASignup.value = true
  } catch (err) {
    setSignupMsg(err.message, 'error')
  } finally {
    signupLoading.value = false
  }
}

async function verify2FASignup(code) {
  try {
    signupModalRef.value?.setMessage('Verifying code…', 'info')
    await auth.complete2FASignup(code)
    show2FASignup.value = false
    router.replace('/dashboard')
  } catch (err) {
    signupModalRef.value?.setMessage(err.message, 'error')
    throw err
  }
}

function cancel2FASignup() {
  show2FASignup.value = false
  auth.clear2FAState()
  setSignupMsg('', 'info')
}
</script>

<style scoped>
.password-requirements {
  background: #f8f9fc;
  border: 1px solid #dde3ef;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 12px;
  font-size: 0.82rem;
}

.req-title {
  font-weight: 600;
  margin: 0 0 6px;
  color: #333;
}

.password-requirements ul {
  list-style: none;
  padding: 0;
  margin: 0 0 8px;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.req-ok   { color: #2a9d5c; }
.req-fail { color: #c0392b; }

.req-example {
  margin: 0;
  color: #666;
  font-size: 0.78rem;
}

.req-example code {
  background: #eef0f5;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 0.82rem;
}
</style>
