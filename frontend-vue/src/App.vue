<template>
  <div class="container">
    <header>
      <h1>USR Authentication</h1>
      <div class="auth-status">
        <span v-if="auth.state.userEmail && isAuthenticated" class="user-email-display">
          {{ auth.state.userEmail }}
        </span>
        <button v-if="isAuthenticated" class="btn btn-secondary" style="width:auto" @click="handleLogout">
          Logout
        </button>
      </div>
    </header>
    <router-view />
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from './composables/useAuth.js'

const auth = useAuth()
const { isAuthenticated, logout } = auth
const router = useRouter()

function handleLogout() {
  logout()
  router.replace('/')
}

// Guard: redirect based on auth state whenever it changes
watch(
  isAuthenticated,
  (authed) => {
    if (authed && router.currentRoute.value.name === 'auth') {
      router.replace('/dashboard')
    } else if (!authed && router.currentRoute.value.name === 'dashboard') {
      router.replace('/')
    }
  },
  { immediate: true }
)
</script>
