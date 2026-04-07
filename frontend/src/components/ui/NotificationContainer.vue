<template>
  <Teleport to="body">
    <div
      v-if="notifications.length > 0"
      class="fixed top-4 right-4 z-50 space-y-2"
    >
      <TransitionGroup
        name="notification"
        tag="div"
        class="space-y-2"
      >
        <div
          v-for="notification in notifications"
          :key="notification.id"
          :class="notificationClasses(notification.type)"
          class="max-w-sm rounded-lg shadow-lg border p-4 relative animate-in slide-in-from-right-full"
        >
          <div class="flex items-start">
            <div class="flex-shrink-0">
              <component
                :is="notificationIcon(notification.type)"
                class="h-5 w-5"
              />
            </div>
            <div class="ml-3 flex-1">
              <p class="text-sm font-medium">{{ notification.message }}</p>
            </div>
            <div class="ml-4 flex-shrink-0">
              <button
                @click="removeNotification(notification.id)"
                class="inline-flex text-gray-400 hover:text-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 rounded"
              >
                <span class="sr-only">Close</span>
                <svg class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path
                    fill-rule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clip-rule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, h } from 'vue'
import { useNotifications } from '@/composables/useNotifications'
import type { NotificationType } from '@/composables/useNotifications'

const { notifications, removeNotification } = useNotifications()

const notificationClasses = (type: NotificationType) => {
  const baseClasses = 'border backdrop-blur-sm'
  
  const typeClasses = {
    success: 'bg-green-900 bg-opacity-90 border-green-700 text-green-100',
    error: 'bg-red-900 bg-opacity-90 border-red-700 text-red-100',
    warning: 'bg-yellow-900 bg-opacity-90 border-yellow-700 text-yellow-100',
    info: 'bg-blue-900 bg-opacity-90 border-blue-700 text-blue-100'
  }
  
  return `${baseClasses} ${typeClasses[type]}`
}

const notificationIcon = (type: NotificationType) => {
  const icons = {
    success: () => h('svg', {
      class: 'h-5 w-5 text-green-400',
      fill: 'currentColor',
      viewBox: '0 0 20 20'
    }, [
      h('path', {
        'fill-rule': 'evenodd',
        d: 'M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z',
        'clip-rule': 'evenodd'
      })
    ]),
    error: () => h('svg', {
      class: 'h-5 w-5 text-red-400',
      fill: 'currentColor',
      viewBox: '0 0 20 20'
    }, [
      h('path', {
        'fill-rule': 'evenodd',
        d: 'M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z',
        'clip-rule': 'evenodd'
      })
    ]),
    warning: () => h('svg', {
      class: 'h-5 w-5 text-yellow-400',
      fill: 'currentColor',
      viewBox: '0 0 20 20'
    }, [
      h('path', {
        'fill-rule': 'evenodd',
        d: 'M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z',
        'clip-rule': 'evenodd'
      })
    ]),
    info: () => h('svg', {
      class: 'h-5 w-5 text-blue-400',
      fill: 'currentColor',
      viewBox: '0 0 20 20'
    }, [
      h('path', {
        'fill-rule': 'evenodd',
        d: 'M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z',
        'clip-rule': 'evenodd'
      })
    ])
  }
  
  return icons[type]
}
</script>

<style scoped>
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.notification-move {
  transition: transform 0.3s ease;
}

@keyframes slide-in-from-right-full {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.animate-in {
  animation-duration: 0.3s;
  animation-fill-mode: both;
}

.slide-in-from-right-full {
  animation-name: slide-in-from-right-full;
}
</style>
