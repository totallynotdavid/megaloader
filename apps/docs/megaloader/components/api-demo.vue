<template>
  <div class="api-demo">
    <div class="input-group">
      <input 
        id="url-input" 
        v-model="url" 
        type="url" 
        placeholder="https://pixeldrain.com/u/..."
        @keyup.enter="startDownload" 
        :disabled="isDownloading"
      />
      <button 
        class="download-btn" 
        @click="startDownload" 
        :disabled="!url.trim() || isDownloading"
      >
        <span v-if="isDownloading" class="spinner"></span>
        {{ isDownloading ? 'Processing...' : 'Download' }}
      </button>
    </div>
    
    <div class="demo-limits">
      Demo limits: Max 4MB file size • Max 50 files
    </div>

    <ToastContainer :toasts="toasts" />
  </div>
</template>

<script setup>
import { ref } from "vue";
import ToastContainer from "./toast-container.vue";

const props = defineProps({
  apiUrl: {
    type: String,
    default: import.meta.env.VITE_API_URL || "http://localhost:8000",
  },
});

const url = ref("");
const isDownloading = ref(false);
const toasts = ref([]);
let toastId = 0;

const showToast = (message, type = "info") => {
  const id = toastId++;
  toasts.value.push({ id, message, type });
  setTimeout(() => {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }, 5000);
};

const startDownload = async () => {
  if (!url.value.trim() || isDownloading.value) return;

  isDownloading.value = true;

  try {
    const endpoint = `${props.apiUrl.replace(/\/$/, "")}/download`;

    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        url: url.value.trim(),
      }),
    });

    const contentType = response.headers.get("content-type");

    if (response.ok) {
      if (contentType?.includes("application/json")) {
        const data = await response.json();
        if (data.exceeds_limit) {
          showToast(data.message || "File too large for demo server", "error");
        } else {
          showToast("Request successful", "success");
        }
      } else {
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);

        // Try to get filename from Content-Disposition header
        const contentDisposition = response.headers.get("content-disposition");
        let filename = "download.zip";

        if (contentDisposition) {
          // Handle both filename="name" and filename*=UTF-8''name formats
          const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
          const matches = filenameRegex.exec(contentDisposition);
          if (matches != null && matches[1]) {
            filename = matches[1].replace(/['"]/g, "");
          }
        }

        const a = document.createElement("a");
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(downloadUrl);
        document.body.removeChild(a);

        showToast(`Downloaded ${filename} successfully!`, "success");
        url.value = ""; // Clear input on success
      }
    } else {
      let errorMessage = "Download failed";
      try {
        const data = await response.json();
        errorMessage = data.detail || errorMessage;
      } catch (e) {
        // Ignore JSON parse error
      }
      showToast(errorMessage, "error");
    }
  } catch (err) {
    console.error(err);
    showToast("Failed to connect to download service", "error");
  } finally {
    isDownloading.value = false;
  }
};
</script>

<style scoped>
.api-demo {
  margin: 1rem 0;
  position: relative;
}

.input-group {
  display: flex;
  gap: 0.5rem;
}

#url-input {
  flex: 1;
  padding: 0.6rem 1rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  font-size: 0.9rem;
  background: var(--vp-c-bg-alt);
  color: var(--vp-c-text-1);
  transition: border-color 0.2s, box-shadow 0.2s;
  font-family: var(--vp-font-family-mono);
}

#url-input:focus {
  outline: none;
  border-color: var(--vp-c-brand);
  box-shadow: 0 0 0 2px var(--vp-c-brand-dimm);
}

#url-input:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.download-btn {
  padding: 0.6rem 1.2rem;
  background: var(--vp-c-brand);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  white-space: nowrap;
}

.download-btn:hover:not(:disabled) {
  filter: brightness(0.9);
}

.download-btn:disabled {
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-3);
  cursor: not-allowed;
}

.spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s linear infinite;
}

.demo-limits {
  margin-top: 0.5rem;
  font-size: 0.8rem;
  color: var(--vp-c-text-2);
  text-align: right;
}

@media (max-width: 640px) {
  .input-group {
    flex-direction: column;
  }
}
</style>
