import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '@/composables/useAuth'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to) {
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/pages/HomePage.vue'),
      meta: { title: 'Ma Liste d\'Anniversaire' },
    },
    {
      path: '/oauth/callback',
      name: 'oauth-callback',
      component: () => import('@/pages/OAuthCallbackPage.vue'),
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/pages/DashboardPage.vue'),
      meta: { title: 'Tableau de bord — Ma Liste d\'Anniversaire', requiresAuth: true },
    },
    {
      path: '/list/:slug',
      name: 'gift-list',
      component: () => import('@/pages/ListPage.vue'),
      meta: { title: 'Liste de cadeaux' },
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/pages/NotFoundPage.vue'),
      meta: { title: 'Page introuvable' },
    },
  ],
})

router.beforeEach(async (to) => {
  if (to.name === 'home') {
    const { init, isAuthenticated } = useAuth()
    await init()
    if (isAuthenticated.value) {
      return { name: 'dashboard' }
    }
  }

  if (to.meta.requiresAuth) {
    const { init, isAuthenticated } = useAuth()
    await init()
    if (!isAuthenticated.value) {
      return { name: 'home' }
    }
  }
})

router.afterEach((to) => {
  const title = to.meta.title as string | undefined
  if (title) document.title = title
})

export default router
