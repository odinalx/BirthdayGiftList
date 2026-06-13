import { ref, computed } from 'vue'
import { api, type User } from '@/services/api'

const user = ref<User | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)
let initPromise: Promise<void> | null = null
let sessionExpiredListenerAttached = false

export function useAuth() {
  const isAuthenticated = computed(() => !!user.value)

  async function init() {
    if (initPromise) return initPromise
    initPromise = doInit()
    return initPromise
  }

  async function doInit() {
    const params = new URLSearchParams(window.location.search)
    const authError = params.get('error')

    if (authError) {
      error.value = params.get('message') || 'Échec de l\'authentification'
      window.history.replaceState({}, '', window.location.pathname)
      isLoading.value = false
      return
    }

    try {
      const session = await api.checkSession()
      if (session.authenticated && session.user) {
        user.value = session.user
      }
    } catch {
      console.error('Vérification de session échouée')
    }

    isLoading.value = false
  }

  async function handleOAuthCallback(): Promise<boolean> {
    isLoading.value = true

    try {
      const session = await api.checkSession()

      if (session.authenticated && session.user) {
        user.value = session.user
        window.location.href = '/dashboard'
        return true
      } else {
        error.value = 'Échec de l\'authentification'
        isLoading.value = false
        return false
      }
    } catch (e) {
      console.error('Échec du callback OAuth:', e)
      error.value = 'Échec de l\'authentification'
      isLoading.value = false
      return false
    }
  }

  function loginWithGoogle() {
    window.location.href = api.getGoogleLoginUrl()
  }

  async function logout() {
    try {
      await api.logout()
    } catch {
      console.error('Échec de la déconnexion')
    }
    user.value = null
  }

  async function refreshUser() {
    try {
      const session = await api.checkSession()
      if (session.authenticated && session.user) {
        user.value = session.user
      }
    } catch {
      console.error('Échec du rafraîchissement de l\'utilisateur')
    }
  }

  function clearError() {
    error.value = null
  }

  function handleSessionExpired() {
    user.value = null
    error.value = 'Votre session a expiré. Veuillez vous reconnecter.'
    if (window.location.pathname !== '/' && !window.location.pathname.startsWith('/oauth')) {
      window.location.href = '/'
    }
  }

  function setupSessionExpiredListener() {
    if (sessionExpiredListenerAttached) return
    sessionExpiredListenerAttached = true
    window.addEventListener('auth:session-expired', handleSessionExpired)
  }

  setupSessionExpiredListener()

  return {
    user,
    isAuthenticated,
    isLoading,
    error,
    init,
    handleOAuthCallback,
    loginWithGoogle,
    logout,
    refreshUser,
    clearError,
  }
}
