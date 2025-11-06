<template>
  <div id="demo-app">
    <div class="demo-container">
      <div class="input-section">
        <div class="input-group">
          <input id="url-input" v-model="url" type="url" placeholder="https://example.com/content"
            @keyup.enter="startDownload" />
          <button class="download-btn" @click="startDownload" :disabled="!url.trim() || isDownloading">
            <span v-if="isDownloading" class="spinner"></span>
            {{ isDownloading ? 'Downloading...' : 'Download' }}
          </button>
        </div>
      </div>

      <div v-if="error" class="message error">
        {{ error }}
      </div>

      <div v-if="downloadResult" class="message" :class="downloadResult.success ? 'success' : 'error'">
        {{ downloadResult.message || downloadResult.error }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const url = ref('')
const error = ref('')
const isDownloading = ref(false)
const downloadResult = ref(null)

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

    if (response.ok) {
      const contentType = response.headers.get('content-type')

      if (contentType && contentType.includes('application/json')) {
        // Handle preview response for large files
        const data = await response.json()
        if (data.exceeds_limit) {
          downloadResult.value = {
            success: false,
            error: data.message
          }
        } else {
          downloadResult.value = {
            success: false,
            error: 'Unexpected response format'
          }
        }
      } else {
        // Handle file download
        const blob = await response.blob()
        const downloadUrl = window.URL.createObjectURL(blob)

        // Try to get filename from Content-Disposition header
        const contentDisposition = response.headers.get('content-disposition')
        let filename = 'download.zip'
        if (contentDisposition) {
          const matches = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
          if (matches && matches[1]) {
            filename = matches[1].replace(/['"]/g, '')
          }
        }

        const a = document.createElement('a')
        a.href = downloadUrl
        a.download = filename
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(downloadUrl)
        document.body.removeChild(a)

        downloadResult.value = {
          success: true,
          message: 'Download completed successfully!'
        }
      }
    } else {
      const data = await response.json()
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
  width: 100%;
  margin: 2rem 0;
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

.input-section {
  margin-bottom: 2rem;
}

.input-group {
  display: flex;
  gap: 1rem;
  align-items: stretch;
}

#url-input {
  flex: 1;
  padding: 1rem 1.5rem;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  font-size: 1rem;
  background: #fafbfc;
  transition: all 0.2s ease;
  font-family: ui-monospace, 'SFMono-Regular', monospace;
}

#url-input:focus {
  outline: none;
  border-color: #007acc;
  background: white;
  box-shadow: 0 0 0 3px rgba(0, 122, 204, 0.1);
}

#url-input::placeholder {
  color: #8b949e;
}

.download-btn {
  padding: 1rem 2rem;
  background: #007acc;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  white-space: nowrap;
}

.download-btn:hover:not(:disabled) {
  background: #005999;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 122, 204, 0.3);
}

.download-btn:disabled {
  background: #8b949e;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

.message {
  padding: 1rem 1.5rem;
  border-radius: 8px;
  margin-top: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-weight: 500;
}

.message.success {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #166534;
}

.message.error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}

@media (max-width: 640px) {
  .demo-container {
    margin: 2rem 1rem;
    padding: 2rem;
  }

  .input-group {
    flex-direction: column;
  }

  .download-btn {
    justify-content: center;
  }
}
</style>