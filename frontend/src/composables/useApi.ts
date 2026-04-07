import { ref, computed } from 'vue'
import { useNotifications } from './useNotifications'
import type { ApiError } from '@/types'

export interface ApiRequestOptions {
  showSuccessMessage?: boolean
  showErrorMessage?: boolean
  successMessage?: string
  errorMessage?: string
  silent?: boolean
}

export const useApi = () => {
  const { notifySuccess, notifyError } = useNotifications()
  
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastResponse = ref<any>(null)

  const handleApiError = (err: any, options?: ApiRequestOptions): string => {
    let errorMessage = 'An unexpected error occurred'
    
    if (err?.response?.data) {
      const data = err.response.data
      errorMessage = data.detail || data.error || data.message || errorMessage
    } else if (err?.message) {
      errorMessage = err.message
    }

    error.value = errorMessage

    if (!options?.silent && options?.showErrorMessage !== false) {
      const displayMessage = options?.errorMessage || errorMessage
      notifyError(displayMessage)
    }

    return errorMessage
  }

  const handleApiSuccess = (response: any, options?: ApiRequestOptions) => {
    lastResponse.value = response
    error.value = null

    if (options?.showSuccessMessage && options?.successMessage) {
      notifySuccess(options.successMessage)
    }

    return response
  }

  const execute = async <T = any>(
    apiCall: () => Promise<T>,
    options?: ApiRequestOptions
  ): Promise<{ data: T | null; error: string | null; success: boolean }> => {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiCall()
      handleApiSuccess(response, options)
      
      return {
        data: response,
        error: null,
        success: true
      }
    } catch (err: any) {
      const errorMessage = handleApiError(err, options)
      
      return {
        data: null,
        error: errorMessage,
        success: false
      }
    } finally {
      isLoading.value = false
    }
  }

  // Convenience method for API calls with automatic error handling
  const call = async <T = any>(
    apiCall: () => Promise<T>,
    options?: ApiRequestOptions
  ): Promise<T | null> => {
    const result = await execute(apiCall, options)
    return result.success ? result.data : null
  }

  const clearError = () => {
    error.value = null
  }

  const reset = () => {
    isLoading.value = false
    error.value = null
    lastResponse.value = null
  }

  return {
    // State
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),
    lastResponse: computed(() => lastResponse.value),
    hasError: computed(() => !!error.value),
    
    // Methods
    execute,
    call,
    clearError,
    reset,
    handleApiError,
    handleApiSuccess
  }
}

// Global API state for app-wide loading indicators
const globalLoading = ref(false)
const activeRequests = ref(0)

export const useGlobalApi = () => {
  const incrementRequests = () => {
    activeRequests.value++
    globalLoading.value = true
  }

  const decrementRequests = () => {
    activeRequests.value = Math.max(0, activeRequests.value - 1)
    if (activeRequests.value === 0) {
      globalLoading.value = false
    }
  }

  return {
    globalLoading: computed(() => globalLoading.value),
    activeRequests: computed(() => activeRequests.value),
    incrementRequests,
    decrementRequests
  }
}
