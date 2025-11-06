<template>
  <div id="demo-app">
    <div class="demo-container">
      <div class="test-indicator">Demo</div>

      <div class="input-section">
        <div class="input-group">
          <label for="url-input">Enter a URL to check compatibility:</label>
          <div class="url-input-container">
            <span class="url-icon">🔗</span>
            <input
              id="url-input"
              :value="url"
              type="url"
              placeholder="https://pixeldrain.com/u/example"
              @input="handleInput"
            />
          </div>
        </div>
      </div>

      <div class="result-section">
        <div v-if="result" class="result" :class="resultClass">
          <div v-if="result.supported && result.plugin" class="success">
            <span class="success-icon">✅</span>
            <span>Supported by</span>
            <span class="plugin-badge">{{ result.plugin }}</span>
            <div class="domain">{{ result.domain }}</div>
            <button
              class="download-btn"
              @click="startDownload"
              :disabled="isDownloading"
            >
              <span v-if="isDownloading" class="loading-spinner">⏳</span>
              <span v-else>⬇️</span>
              {{ isDownloading ? 'Downloading...' : 'Download' }}
            </button>
          </div>
          <div v-else class="error">
            <span class="error-icon">❌</span>
            <span>Not supported</span>
            <div class="domain">{{ result.domain }}</div>
          </div>
        </div>

        <div v-if="downloadResult" class="download-result" :class="downloadResultClass">
          <div v-if="downloadResult.success" class="download-success">
            <span class="success-icon">🎉</span>
            <span>{{ downloadResult.message }}</span>
          </div>
          <div v-else class="download-error">
            <span class="error-icon">❌</span>
            <span>{{ downloadResult.error }}</span>
          </div>
        </div>

        <div v-if="error" class="error-message">
          ⚠️ {{ error }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const url = ref('')
const result = ref(null)
const error = ref('')
const isDownloading = ref(false)
const downloadResult = ref(null)

const resultClass = computed(() => {
  if (!result.value) return {}
  return {
    'result-success': result.value.supported,
    'result-error': !result.value.supported
  }
})

const downloadResultClass = computed(() => {
  if (!downloadResult.value) return {}
  return {
    'download-success': downloadResult.value.success,
    'download-error': !downloadResult.value.success
  }
})

function debounce(func, delay) {
  let timeoutId
  return (...args) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => func.apply(null, args), delay)
  }
}

const handleInput = (event) => {
  url.value = event.target.value
  validateUrl()
}

const validateUrl = debounce(async () => {
  if (!url.value.trim()) {
    result.value = null
    error.value = ''
    return
  }

  error.value = ''
  result.value = null

  try {
    const response = await fetch(`http://localhost:8000/api/validate-url?url=${encodeURIComponent(url.value.trim())}`)
    const data = await response.json()

    if (response.ok) {
      result.value = {
        supported: data.supported,
        plugin: data.plugin,
        domain: data.domain
      }
    } else {
      error.value = data.detail || 'Validation failed'
    }
  } catch (err) {
    error.value = 'Failed to connect to validation service'
  }
}, 300)

const startDownload = async () => {
  if (!url.value.trim() || isDownloading.value) return

  isDownloading.value = true
  downloadResult.value = null
  error.value = ''

  try {
    const response = await fetch('http://localhost:8000/api/download', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: url.value.trim()
      })
    })

    const data = await response.json()

    if (response.ok) {
      downloadResult.value = {
        success: true,
        message: data.message
      }
    } else {
      downloadResult.value = {
        success: false,
        error: data.detail || 'Download failed'
      }
    }
  } catch (err) {
    downloadResult.value = {
      success: false,
      error: 'Failed to connect to download service'
    }
  } finally {
    isDownloading.value = false
  }
}
</script>

<style scoped>
.demo-container {
  max-width: 700px;
  margin: 2rem auto;
  padding: 2.5rem;
  border: 2px solid var(--vp-c-border);
  border-radius: 12px;
  background: var(--vp-c-bg-soft);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
}

.demo-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--vp-c-brand), var(--vp-c-brand-light));
}

.input-section {
  margin-bottom: 2rem;
}

.input-group {
  margin-bottom: 1.5rem;
}

.input-group label {
  display: block;
  margin-bottom: 0.75rem;
  font-weight: 600;
  font-size: 1.1rem;
  color: var(--vp-c-text-1);
}

.url-input-container {
  position: relative;
}

#url-input {
  width: 100%;
  padding: 1rem 1rem 1rem 3rem;
  border: 2px solid var(--vp-c-border);
  border-radius: 8px;
  font-size: 1rem;
  background: var(--vp-c-bg);
  color: var(--vp-c-text);
  transition: all 0.2s ease;
  font-family: var(--vp-font-family-mono);
}

#url-input::placeholder {
  color: var(--vp-c-text-3);
  font-family: var(--vp-font-family-base);
}

#url-input:focus {
  outline: none;
  border-color: var(--vp-c-brand);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  background: var(--vp-c-bg);
}

.url-icon {
  position: absolute;
  left: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--vp-c-text-3);
  font-size: 1.2rem;
  pointer-events: none;
}

.result-section {
  margin-top: 2rem;
}

.result {
  padding: 1.5rem;
  border-radius: 8px;
  margin-top: 1rem;
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}

.result-success {
  background: linear-gradient(135deg, var(--vp-c-success-bg), rgba(34, 197, 94, 0.1));
  border-color: var(--vp-c-success-border);
  color: var(--vp-c-success-text);
}

.result-error {
  background: linear-gradient(135deg, var(--vp-c-danger-bg), rgba(239, 68, 68, 0.1));
  border-color: var(--vp-c-danger-border);
  color: var(--vp-c-danger-text);
}

.success-icon, .error-icon {
  font-size: 1.5rem;
  margin-right: 0.5rem;
}

.success, .error {
  font-weight: 600;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
}

.plugin-badge {
  display: inline-block;
  background: var(--vp-c-brand);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  margin-left: 0.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.domain {
  margin-top: 0.75rem;
  font-size: 0.9rem;
  opacity: 0.8;
  font-family: var(--vp-font-family-mono);
  background: var(--vp-c-bg);
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid var(--vp-c-border);
}

.download-btn {
  margin-top: 1rem;
  padding: 0.75rem 1.5rem;
  background: linear-gradient(135deg, var(--vp-c-brand-1), var(--vp-c-brand-2));
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.download-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.download-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.download-result {
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
  border: 1px solid transparent;
}

.download-success {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05));
  border-color: rgba(34, 197, 94, 0.3);
  color: var(--vp-c-text-1);
}

.download-error {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05));
  border-color: rgba(239, 68, 68, 0.3);
  color: var(--vp-c-text-1);
}

.error-message {
  background: linear-gradient(135deg, var(--vp-c-danger-bg), rgba(239, 68, 68, 0.1));
  border: 1px solid var(--vp-c-danger-border);
  color: var(--vp-c-danger-text);
  padding: 1rem;
  border-radius: 8px;
  margin-top: 1rem;
  font-weight: 500;
}

.test-indicator {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: var(--vp-c-brand);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  opacity: 0.8;
}

@media (max-width: 768px) {
  .demo-container {
    margin: 1rem;
    padding: 1.5rem;
  }

  #url-input {
    padding: 0.875rem 0.875rem 0.875rem 2.5rem;
  }

  .url-icon {
    left: 0.625rem;
  }
}
</style>