<script setup lang="ts">
import { RouterView } from 'vue-router'
import { onMounted, onErrorCaptured } from 'vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import NotificationContainer from '@/components/ui/NotificationContainer.vue'
import { useAuth } from '@/composables/useAuth'
import { useNotifications } from '@/composables/useNotifications'

const { initialize } = useAuth()
const { notifyError } = useNotifications()

onMounted(() => {
  // Initialize auth state when app mounts
  initialize()
  
  // Global error handler for unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason)
    notifyError('An unexpected error occurred. Please try again.')
    event.preventDefault()
  })
  
  // Global error handler for JavaScript errors
  window.addEventListener('error', (event) => {
    console.error('Global error:', event.error)
    notifyError('An unexpected error occurred. Please refresh the page.')
  })
})

// Vue error boundary
onErrorCaptured((error, instance, info) => {
  console.error('Vue error captured:', { error, instance, info })
  notifyError('A component error occurred. Please try again.')
  return false // Prevent error from propagating
})
</script>

<template>
  <div id="app" class="flex flex-col min-h-screen bg-[#1C1C1E] text-gray-100 w-full">
    <!-- Navigation Header -->
    <AppHeader />

    <!-- Main Content -->
    <main class="flex-grow w-full pt-16">
      <div class="w-full max-w-[95%] mx-auto px-4 py-6">
        <RouterView />
      </div>
    </main>
    
    <!-- Global Notification Container -->
    <NotificationContainer />
  </div>
</template>

<style>
/* Global CSS reset */
body, html {
  margin: 0;
  padding: 0;
  width: 100vw;
  min-height: 100vh;
  overflow-x: hidden;
  background-color: black;
}

/* Remove the width constraint from #app */
#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  width: 100vw;
}

/* Remove default link styles */
a {
  text-decoration: none;
  color: inherit;
}

/* Dropdown animation */
@keyframes dropdownFade {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

#user-menu-button + div {
  animation: dropdownFade 0.2s ease;
}
</style>
