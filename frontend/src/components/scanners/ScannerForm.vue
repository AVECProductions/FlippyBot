<template>
  <div class="bg-[#2C2C2E] p-4 sm:p-6 rounded-lg shadow-lg">
    <h3 class="text-lg font-bold mb-4 text-white">
      {{ isEditing ? 'Edit Scanner' : 'Add New Scanner' }}
    </h3>
    
    <form @submit.prevent="handleSubmit" class="space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <BaseInput
          v-model="form.category"
          label="Category"
          placeholder="Enter category"
          required
        />
        
        <BaseInput
          v-model="form.query"
          label="Query"
          placeholder="Enter search query"
          required
        />
        
        <BaseInput
          v-model="form.town"
          label="Town"
          placeholder="Enter town"
          required
        />
        
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-1">Status</label>
          <select 
            v-model="form.status" 
            class="w-full px-3 py-2 bg-[#1C1C1E] border border-gray-800 rounded-md text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
            required
          >
            <option value="running">Running</option>
            <option value="stopped">Stopped</option>
          </select>
        </div>
      </div>
      
      <div class="flex flex-col sm:flex-row justify-end space-y-2 sm:space-y-0 sm:space-x-2 pt-4">
        <BaseButton 
          type="button" 
          @click="$emit('cancel')" 
          variant="secondary"
        >
          Cancel
        </BaseButton>
        <BaseButton 
          type="submit" 
          variant="primary"
          :loading="isSubmitting"
          :loading-text="isEditing ? 'Updating...' : 'Adding...'"
        >
          {{ isEditing ? 'Update' : 'Add' }}
        </BaseButton>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import type { Scanner } from '@/types'

const props = defineProps<{
  scanner?: Scanner
  isEditing: boolean
}>()

const emit = defineEmits<{
  submit: [scanner: Omit<Scanner, 'id'> | Partial<Scanner>]
  cancel: []
}>()

const isSubmitting = ref(false)

const form = reactive({
  category: '',
  query: '',
  town: '',
  status: 'stopped'
})

onMounted(() => {
  if (props.scanner && props.isEditing) {
    form.category = props.scanner.category
    form.query = props.scanner.query
    form.town = props.scanner.town
    form.status = props.scanner.status
  }
})

const handleSubmit = async () => {
  isSubmitting.value = true
  
  try {
    emit('submit', { ...form })
  } finally {
    isSubmitting.value = false
  }
}
</script> 