<script setup lang="ts">
import { useToast } from '@/composables/useToast'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-vue-next'

const { toasts, removeToast } = useToast()

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
}
</script>

<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="['toast', `toast-${toast.type}`]"
        >
          <component :is="icons[toast.type]" :size="18" class="toast-icon" />
          <span class="toast-message">{{ toast.message }}</span>
          <button class="toast-close" @click="removeToast(toast.id)">
            <X :size="16" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #18181b;
  border: 1px solid #27272a;
  border-radius: 10px;
  color: #fafafa;
  font-size: 0.9rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
  pointer-events: auto;
  min-width: 280px;
  max-width: 400px;
}

.toast-success {
  border-color: #22c55e;
}

.toast-success .toast-icon {
  color: #22c55e;
}

.toast-error {
  border-color: #ef4444;
}

.toast-error .toast-icon {
  color: #ef4444;
}

.toast-info {
  border-color: #3b82f6;
}

.toast-info .toast-icon {
  color: #3b82f6;
}

.toast-warning {
  border-color: #f59e0b;
}

.toast-warning .toast-icon {
  color: #f59e0b;
}

.toast-icon {
  flex-shrink: 0;
}

.toast-message {
  flex: 1;
  line-height: 1.4;
}

.toast-close {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
  background: transparent;
  border: none;
  color: #71717a;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.15s;
}

.toast-close:hover {
  background: #27272a;
  color: #fafafa;
}

/* Animations */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(100px);
}

@media (max-width: 480px) {
  .toast-container {
    left: 10px;
    right: 10px;
    top: 10px;
  }

  .toast {
    min-width: auto;
    max-width: none;
  }
}
</style>
