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
          <div class="form-group">
            <label for="signup-password">Password:</label>
            <input
              id="signup-password"
              v-model="signupForm.password"
              type="password"
              required
              minlength="6"
              autocomplete="new-password"
            />
          </div>
          <button type="submit" class="btn btn-primary" :disabled="signupLoading">
            {{ signupLoading ? 'Creating account…' : 'Sign Up' }}
          </button>
          <div v-if="signupMessage" :class="['message', signupMessageType]">{{ signupMessage }}</div>
        </form>
      </div>
    </div>

    <!-- 2FA Signup Modal — shows QR code for authenticator app scan -->
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
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth.js'
import TwoFAModal from '../components/TwoFAModal.vue'

const auth   = useAuth()
const router = useRouter()

const activeTab = ref('login')

// ── Login state ────────────────────────────────────────────────────────────
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
    const result = await auth.login(loginForm.email, loginForm.password)
    setLoginMsg('Login successful!', 'success')
    router.replace('/dashboard')
  } catch (err) {
    setLoginMsg(err.message, 'error')
  } finally {
    loginLoading.value = false
  }
}

// ── Signup state ───────────────────────────────────────────────────────────
const signupForm        = reactive({ first_name: '', last_name: '', username: '', email: '', password: '' })
const signupLoading     = ref(false)
const signupMessage     = ref('')
const signupMessageType = ref('info')
const show2FASignup     = ref(false)
const signupModalRef    = ref(null)
const signupQrCode      = ref('')
const signupManualCode  = ref('')
const signupUserEmail   = ref('')

function setSignupMsg(msg, type = 'info') {
  signupMessage.value     = msg
  signupMessageType.value = type
}

async function handleSignup() {
  signupLoading.value = true
  setSignupMsg('Creating account…', 'info')
  try {
    const result = await auth.signup(signupForm)
    signupQrCode.value     = result.qr_code    || ''
    signupManualCode.value = result.manual_code || ''
    signupUserEmail.value  = result.user_email  || signupForm.email
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
