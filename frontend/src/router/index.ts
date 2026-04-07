import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import HomeView from '../views/HomeView.vue'
import AgentsView from '../views/AgentsView.vue'
import ListingsView from '../views/ListingsView.vue'
import LoginView from '../views/LoginView.vue'
import ScannerControlView from '../views/ScannerControlView.vue'
import ScanBatchView from '../views/ScanBatchView.vue'
import HistoryView from '../views/HistoryView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/agents',
    name: 'agents',
    component: AgentsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/scanners',
    redirect: '/agents'
  },
  {
    path: '/listings',
    name: 'listings',
    component: ListingsView,
    meta: { requiresAuth: true }
  },
  {
    path: '/history',
    name: 'history',
    component: HistoryView,
    meta: { requiresAuth: true }
  },
  {
    path: '/scanner-control',
    name: 'scanner-control',
    component: ScannerControlView,
    meta: { requiresAuth: true }
  },
  {
    path: '/scan-batch/:scanId',
    name: 'scan-batch',
    component: ScanBatchView,
    meta: { requiresAuth: true }
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation guard to check authentication
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  
  // Initialize auth state if needed
  authStore.checkLoginState()
  
  if (requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login if authentication is required but user is not authenticated
    next({
      path: '/login',
      query: { redirect: to.fullPath } // Save intended destination
    })
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    // Redirect to intended destination or home if user is already logged in
    const redirect = to.query.redirect as string || '/'
    next(redirect)
  } else {
    next()
  }
})

export default router
