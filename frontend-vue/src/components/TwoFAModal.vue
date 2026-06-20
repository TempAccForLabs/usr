<template>
  <div class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-box">
      <h3>{{ title }}</h3>
      <p>{{ description }}</p>
      <p v-if="userEmail"><strong>Account:</strong> {{ userEmail }}</p>

      <div class="form-group" style="margin-top:16px">
        <label :for="inputId">2FA Code:</label>
        <input
          :id="inputId"
          v-model="code"
          type="text"
          inputmode="numeric"
          maxlength="6"
          placeholder="123456"
          class="modal-code-input"
          autocomplete="one-time-code"
          @keyup.enter="submit"
        />
      </div>

      <div class="btn-group" style="margin-top:16px">
        <button class="btn btn-primary" style="flex:1" :disabled="loading" @click="submit">
          {{ loading ? 'Verifying…' : 'Verify' }}
        </button>
        <button class="btn btn-secondary" style="flex:1" @click="$emit('cancel')">Cancel</button>
      </div>

      <div v-if="message" :class="['message', messageType]" style="margin-top:12px">
        {{ message }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  title: { type: String, default: '2FA Verification Required' },
  description: { type: String, default: 'Enter the 6-digit code (use the debug endpoint to get the current code).' },
  userEmail: { type: String, default: '' },
  inputId: { type: String, default: 'twofa-code' },
})

const emit = defineEmits(['submit', 'cancel'])

const code = ref('')
const loading = ref(false)
const message = ref('')
const messageType = ref('info')

function setMessage(msg, type = 'info') {
  message.value = msg
  messageType.value = type
}

async function submit() {
  if (!code.value || code.value.length !== 6) {
    setMessage('Please enter a valid 6-digit code.', 'error')
    return
  }
  loading.value = true
  message.value = ''
  try {
    await emit('submit', code.value)
  } finally {
    loading.value = false
  }
}

// Expose so parent can show errors
defineExpose({ setMessage, code })
</script>
