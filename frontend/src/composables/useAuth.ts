import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/authStore'
import { useRouter, useRoute } from 'vue-router'

export const useAuth = () => {
  const authStore = useAuthStore()
  const router = useRouter()
  const route = useRoute()

  // Reactive refs from store
  const { 
    user, 
    isLoading, 
    error, 
    isAuthenticated, 
    username, 
    userInitial 
  } = storeToRefs(authStore)

  // Actions
  const login = async (username: string, password: string) => {
    const success = await authStore.login(username, password)
    if (success) {
      // Redirect to intended destination or default to listings
      const redirect = route.query.redirect as string || '/listings'
      router.push(redirect)
    }
    return success
  }

  const logout = () => {
    authStore.logout()
    router.push('/')
  }

  const initialize = () => {
    authStore.initialize()
  }

  const checkAuthState = () => {
    authStore.checkLoginState()
  }

  return {
    // Reactive state
    user,
    isLoading,
    error,
    isAuthenticated,
    username,
    userInitial,
    
    // Actions
    login,
    logout,
    initialize,
    checkAuthState
  }
}
