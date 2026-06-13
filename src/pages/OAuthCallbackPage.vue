<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { Loader2 } from 'lucide-vue-next'

const { handleOAuthCallback, error } = useAuth()
const failed = ref(false)

onMounted(async () => {
  const success = await handleOAuthCallback()
  if (!success) {
    failed.value = true
    setTimeout(() => {
      window.location.href = '/'
    }, 3000)
  }
})
</script>

<template>
  <div class="callback-container">
    <div class="callback-card">
      <template v-if="!failed">
        <Loader2 class="spinner" :size="48" />
        <h2>Connexion en cours...</h2>
        <p>Veuillez patienter pendant que nous finalisons votre connexion.</p>
      </template>
      <template v-else>
        <div class="error-icon">!</div>
        <h2>Échec de l'authentification</h2>
        <p>{{ error || 'Une erreur est survenue. Veuillez réessayer.' }}</p>
        <p class="redirect-notice">Redirection vers la page d'accueil...</p>
      </template>
    </div>
  </div>
</template>

<style scoped>
.callback-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--app-bg);
  padding: 1rem;
}

.callback-card {
  background: var(--app-surface);
  border: 1px solid var(--app-border);
  border-radius: 12px;
  padding: 3rem;
  text-align: center;
  max-width: 400px;
  width: 100%;
}

.spinner {
  color: var(--theme-accent);
  animation: spin 1s linear infinite;
  margin-bottom: 1.5rem;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

h2 {
  color: var(--app-text);
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

p {
  color: var(--app-text-muted);
  font-size: 0.95rem;
  line-height: 1.5;
}

.error-icon {
  width: 48px;
  height: 48px;
  background: #ef4444;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  font-weight: bold;
  margin: 0 auto 1.5rem;
}

.redirect-notice {
  margin-top: 1rem;
  font-size: 0.85rem;
}
</style>
