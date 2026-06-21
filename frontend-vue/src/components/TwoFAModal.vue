<template>
  <div class="modal-overlay" @click.self="$emit('cancel')">
    <div class="modal-box">
      <h3>{{ title }}</h3>

      <div v-if="qrCode" class="qr-section">
        <p class="qr-instructions">
          Open <strong>Google Authenticator</strong> or <strong>Authy</strong> on your phone,
          tap <em>Add account</em>, then scan this QR code:
        </p>
        <div class="qr-wrapper">
          <img :src="qrCode" alt="2FA QR Code" class="qr-image" />
        </div>
        <details class="manual-entry">
          <summary>Can't scan? Enter the code manually</summary>
          <p class="manual-code">{{ manualCode }}</p>
          <p class="manual-hint">Type this key into your authenticator app manually.</p>
        </details>
      </div>

      <p v-if="!qrCode && description" class="modal-description">{{ description }}</p>
      <p v-if="userEmail" class="modal-account"><strong>Account:</strong> {{ userEmail }}</p>

      <div class="form-group" style="margin-top:16px">
        <label :for="inputId">
          {{ qrCode ? 'Enter the 6-digit code from your authenticator app:' : '2FA Code:' }}
        </label>
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
  title:       { type: String, default: '2FA Verification' },
  description: { type: String, default: '' },
  userEmail:   { type: String, default: '' },
  inputId:     { type: String, default: 'twofa-code' },
  qrCode:      { type: String, default: '' },
  manualCode:  { type: String, default: '' },
})

const emit = defineEmits(['submit', 'cancel'])

const code        = ref('')
const loading     = ref(false)
const message     = ref('')
const messageType = ref('info')

function setMessage(msg, type = 'info') {
  message.value     = msg
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

defineExpose({ setMessage, code })
</script>

<style scoped>
.qr-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.qr-instructions {
  text-align: center;
  font-size: 0.9rem;
  color: #444;
  margin: 0;
}

.qr-wrapper {
  background: #fff;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid #ddd;
  display: inline-block;
}

.qr-image {
  display: block;
  width: 200px;
  height: 200px;
}

.manual-entry {
  width: 100%;
  font-size: 0.85rem;
  color: #555;
  cursor: pointer;
}

.manual-entry summary {
  text-align: center;
  color: #4a6fa5;
  user-select: none;
}

.manual-code {
  font-family: monospace;
  font-size: 1rem;
  letter-spacing: 0.15em;
  text-align: center;
  background: #f4f4f4;
  border-radius: 4px;
  padding: 6px 10px;
  margin: 6px 0 2px;
  word-break: break-all;
}

.manual-hint {
  text-align: center;
  font-size: 0.78rem;
  color: #888;
  margin: 0;
}

.modal-description {
  font-size: 0.9rem;
  color: #555;
  margin-bottom: 4px;
}

.modal-account {
  font-size: 0.85rem;
  color: #555;
  margin: 0;
}
</style>
