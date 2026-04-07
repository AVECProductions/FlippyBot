import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginUser, logoutUser, getUserProfile, refreshToken } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<{
    name: string
    token: string
  }>({
    name: '',
    token: ''
  })
  
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!user.value.token)
  const username = computed(() => user.value.name || 'User')
  const userInitial = computed(() => username.value.charAt(0).toUpperCase())

  // Actions
  const login = async (username: string, password: string) => {
    isLoading.value = true
    error.value = null
    
    try {
      const response = await loginUser(username, password)
      
      if (response.success && response.token) {
        user.value = {
          name: username,
          token: response.token
        }
        
        // Dispatch event to notify other parts of the app
        window.dispatchEvent(new CustomEvent('auth-event', { 
          detail: { action: 'login', user: user.value } 
        }))
        
        return true
      }
      return false
    } catch (err: any) {
      error.value = err.message || 'Login failed'
      return false
    } finally {
      isLoading.value = false
    }
  }

  const logout = () => {
    // Use API service for logout
    logoutUser()
    
    // Clear user state
    user.value = {
      name: '',
      token: ''
    }
    
    // Clear localStorage (done in API service, but ensure it's clear)
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_name')
    
    // Dispatch event
    window.dispatchEvent(new CustomEvent('auth-event', { 
      detail: { action: 'logout' } 
    }))
  }

  const checkLoginState = () => {
    const token = localStorage.getItem('access_token')
    const name = localStorage.getItem('user_name')
    
    if (token) {
      user.value = {
        name: name || 'User',
        token: token
      }
      console.log('User authenticated from localStorage:', user.value)
    } else {
      user.value = {
        name: '',
        token: ''
      }
      console.log('No authentication found in localStorage')
    }
  }

  const refreshUserToken = async () => {
    try {
      const response = await refreshToken()
      if (response.success && response.token) {
        user.value.token = response.token
        return true
      }
      return false
    } catch (err) {
      console.error('Token refresh failed:', err)
      logout() // Force logout on refresh failure
      return false
    }
  }

  // Initialize auth state from localStorage
  const initialize = () => {
    checkLoginState()
  }

  return {
    // State
    user,
    isLoading,
    error,
    
    // Getters
    isAuthenticated,
    username,
    userInitial,
    
    // Actions
    login,
    logout,
    checkLoginState,
    refreshUserToken,
    initialize
  }
})
