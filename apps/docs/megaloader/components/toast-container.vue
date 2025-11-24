<template>
  <TransitionGroup name="toast" tag="div" class="toast-container">
    <div 
      v-for="toast in toasts" 
      :key="toast.id" 
      class="toast" 
      :class="toast.type"
    >
      <span class="toast-icon">{{ toast.type === 'success' ? '✓' : '!' }}</span>
      {{ toast.message }}
    </div>
  </TransitionGroup>
</template>

<script setup>
defineProps({
  toasts: {
    type: Array,
    required: true,
  },
});
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  z-index: 100;
  pointer-events: none;
}

.toast {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  background: var(--vp-c-bg);
  border: 1px solid var(--vp-c-divider);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  pointer-events: auto;
  max-width: 350px;
}

.toast.success {
  border-left: 4px solid var(--vp-c-green);
}

.toast.error {
  border-left: 4px solid var(--vp-c-red);
}

.toast-icon {
  font-weight: bold;
}

.toast.success .toast-icon { color: var(--vp-c-green); }
.toast.error .toast-icon { color: var(--vp-c-red); }

/* Toast Transitions */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

@media (max-width: 640px) {
  .toast-container {
    left: 1rem;
    right: 1rem;
    bottom: 1rem;
  }
}
</style>
