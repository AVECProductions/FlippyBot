<template>
  <nav class="fixed top-0 left-0 right-0 z-50 border-b border-gray-800 bg-black w-full">
    <div class="w-full max-w-[95%] mx-auto px-4">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <div class="flex items-center">
          <router-link to="/" class="uppercase tracking-wide text-white font-bold text-xl">FLIPPYBOT</router-link>
          
          <!-- Navigation Links -->
          <div class="hidden md:block ml-10">
            <div class="flex items-baseline space-x-1">
              <router-link
                v-for="link in navLinks"
                :key="link.to"
                v-if="isAuthenticated"
                :to="link.to"
                class="px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200"
                :class="[$route.path === link.to ? 'bg-gray-800 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white']"
              >
                {{ link.label }}
              </router-link>
            </div>
          </div>
        </div>
        
        <!-- Task Status Indicator & Profile Dropdown - Only show on desktop (md and up) -->
        <div class="ml-4 hidden md:flex items-center md:ml-6">
          <!-- Task Status Indicator -->
          <TaskStatusIndicator v-if="isAuthenticated" />
          
          <!-- Not Logged In State -->
          <router-link 
            v-if="!isAuthenticated" 
            to="/login"
            class="bg-transparent border-2 border-gray-600 text-gray-200 px-4 py-2 rounded-md text-sm font-medium hover:bg-gray-800 hover:border-gray-500 transition-all duration-200"
          >
            Login
          </router-link>
          
          <!-- Logged In State: Profile Button with Username -->
          <div v-else class="relative ml-3">
            <button 
              @click="isProfileOpen = !isProfileOpen" 
              class="flex items-center text-sm bg-transparent border border-gray-700 rounded-md px-3 py-2 focus:outline-none"
              id="user-menu-button"
              aria-expanded="false"
              aria-haspopup="true"
            >
              <span class="sr-only">Open user menu</span>
              <div class="flex items-center">
                <div class="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center font-medium text-white mr-2">
                  {{ userInitial }}
                </div>
                <span class="text-white">Hello, {{ username }}</span>
                <svg class="w-4 h-4 ml-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </div>
            </button>
            
            <!-- Profile Dropdown Menu -->
            <div 
              v-if="isProfileOpen" 
              class="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-black ring-1 ring-black ring-opacity-5 focus:outline-none z-50 border border-gray-800"
              role="menu"
              aria-orientation="vertical"
              aria-labelledby="user-menu-button"
              tabindex="-1"
            >
              <div class="block px-4 py-2 text-sm text-gray-300 border-b border-gray-800">
                Signed in as <span class="font-medium">{{ username }}</span>
              </div>
              <a 
                href="#" 
                @click.prevent="handleLogout"
                class="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-800 hover:text-white" 
                role="menuitem" 
                tabindex="-1" 
                id="user-menu-item-2"
              >
                Logout
              </a>
            </div>
          </div>
        </div>
        
        <!-- Mobile Menu Button -->
        <div class="flex items-center md:hidden">
          <button 
            type="button" 
            class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-800 focus:outline-none"
            @click="mobileMenuOpen = !mobileMenuOpen"
          >
            <span class="sr-only">Open main menu</span>
            <!-- Icon when menu is closed -->
            <svg 
              class="h-6 w-6" 
              :class="{'hidden': mobileMenuOpen, 'block': !mobileMenuOpen }"
              stroke="currentColor" 
              fill="none" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <!-- Icon when menu is open -->
            <svg 
              class="h-6 w-6" 
              :class="{'block': mobileMenuOpen, 'hidden': !mobileMenuOpen }"
              stroke="currentColor" 
              fill="none" 
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Flippy status sub-bar (mobile only — desktop has TaskStatusIndicator in nav) -->
    <div v-if="currentTask" class="md:hidden border-t border-blue-500/20 bg-blue-500/5 px-4 py-1">
      <div class="w-full max-w-[95%] mx-auto flex items-center gap-2 text-xs">
        <div class="w-2 h-2 rounded-full bg-blue-500 animate-pulse flex-shrink-0"></div>
        <span class="text-blue-400 font-medium flex-shrink-0">{{ currentTask.step_display }}</span>
        <span v-if="currentTask.progress_message" class="text-gray-500 truncate">{{ currentTask.progress_message }}</span>
        <span class="text-gray-600 ml-auto flex-shrink-0">{{ currentTask.progress_percent }}%</span>
      </div>
    </div>

    <!-- Mobile menu -->
    <div class="md:hidden" :class="{'block': mobileMenuOpen, 'hidden': !mobileMenuOpen}">
      <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3">
        <router-link
          v-for="link in navLinks"
          :key="link.to"
          v-if="isAuthenticated"
          :to="link.to"
          class="block px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:bg-gray-800 hover:text-white"
          :class="[$route.path === link.to ? 'bg-gray-800 text-white' : '']"
          @click="mobileMenuOpen = false"
        >
          {{ link.label }}
        </router-link>
        <div v-if="isAuthenticated" class="border-t border-gray-800 pt-4 pb-3">
          <div class="flex items-center px-5">
            <div class="flex-shrink-0">
              <div class="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">
                {{ userInitial }}
              </div>
            </div>
            <div class="ml-3">
              <div class="text-base font-medium leading-none text-white">{{ username }}</div>
            </div>
          </div>
          <div class="mt-3 px-2 space-y-1">
            <a 
              href="#" 
              @click.prevent="handleLogout"
              class="block px-3 py-2 rounded-md text-base font-medium text-gray-400 hover:text-white hover:bg-gray-800"
            >
              Logout
            </a>
          </div>
        </div>
        <router-link
          v-else
          to="/login"
          class="block px-3 py-2 rounded-md text-base font-medium text-gray-300 hover:bg-gray-800 hover:text-white"
          :class="[$route.path === '/login' ? 'bg-gray-800 text-white' : '']"
          @click="mobileMenuOpen = false"
        >
          Login
        </router-link>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import TaskStatusIndicator from './TaskStatusIndicator.vue'
import { useTaskStatus } from '@/composables/useTaskStatus'

const route = useRoute()
const { isAuthenticated, username, userInitial, logout } = useAuth()
const { currentTask, initialize: initTaskStatus } = useTaskStatus()

const mobileMenuOpen = ref(false)
const isProfileOpen = ref(false)

const navLinks = [
  { to: '/agents', label: 'Agents' },
  { to: '/listings', label: 'Listings' },
  { to: '/history', label: 'History' },
  { to: '/scanner-control', label: 'Control' },
]

const handleLogout = () => {
  logout()
  isProfileOpen.value = false
  mobileMenuOpen.value = false
}

// Close profile dropdown when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  const target = event.target as HTMLElement
  if (isProfileOpen.value && target.closest('#user-menu-button') === null) {
    isProfileOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  initTaskStatus()
})

// Clean up event listeners when component is unmounted
onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
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
