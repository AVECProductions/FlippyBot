import { ref } from 'vue'

export type NotificationType = 'success' | 'error' | 'info' | 'warning'

interface Notification {
  id: string
  type: NotificationType
  message: string
  timeout?: number
}

const notifications = ref<Notification[]>([])

export const useNotifications = () => {
  
  const addNotification = (
    type: NotificationType, 
    message: string, 
    timeout: number = 3000
  ) => {
    const id = Date.now().toString()
    
    notifications.value.push({
      id,
      type,
      message,
      timeout
    })

    // Auto-remove notification after timeout
    if (timeout > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, timeout)
    }

    return id
  }

  const removeNotification = (id: string) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }

  const clearAllNotifications = () => {
    notifications.value = []
  }

  // Convenience methods
  const notifySuccess = (message: string, timeout?: number) => 
    addNotification('success', message, timeout)
  
  const notifyError = (message: string, timeout?: number) => 
    addNotification('error', message, timeout)
  
  const notifyInfo = (message: string, timeout?: number) => 
    addNotification('info', message, timeout)
  
  const notifyWarning = (message: string, timeout?: number) => 
    addNotification('warning', message, timeout)

  return {
    notifications,
    addNotification,
    removeNotification,
    clearAllNotifications,
    notifySuccess,
    notifyError,
    notifyInfo,
    notifyWarning
  }
}
