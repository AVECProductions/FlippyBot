<template>
  <div class="bg-[#2C2C2E] p-6 rounded-lg shadow-lg max-w-md mx-auto">
    <h2 class="text-xl font-bold mb-4 text-white">Login to FlippyBot</h2>
    
    <div v-if="error" class="bg-red-500 bg-opacity-10 text-red-500 p-3 rounded-md mb-4">
      {{ error }}
    </div>
    
    <form @submit.prevent="handleLogin" class="space-y-4">
      <BaseInput
        v-model="username"
        label="Username"
        type="text"
        placeholder="Enter your username"
        required
      />
      
      <BaseInput
        v-model="password"
        label="Password"
        type="password"
        placeholder="Enter your password"
        required
      />
      
      <BaseButton
        type="submit"
        variant="primary"
        :loading="isLoading"
        loading-text="Logging in..."
        full-width
      >
        Login
      </BaseButton>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/authStore'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

const username = ref('')
const password = ref('')
const router = useRouter()

// Use auth store
const authStore = useAuthStore()
const { isLoading, error } = storeToRefs(authStore)

const handleLogin = async () => {
  const success = await authStore.login(username.value, password.value)
  
  if (success) {
    router.push('/')
  }
}
</script> 