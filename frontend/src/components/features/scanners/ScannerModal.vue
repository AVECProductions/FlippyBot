<template>
  <BaseModal
    :show="show"
    title="Manage Scanner"
    @close="$emit('close')"
  >
    <div v-if="scanner" class="space-y-6">
      <!-- Scanner Details Section -->
      <div class="pb-4 border-b border-gray-800">
        <p class="text-[#F3F4F6] mb-2"><span class="font-medium">Query:</span> {{ scanner.query }}</p>
        <p class="text-[#F3F4F6] mb-2"><span class="font-medium">Category:</span> {{ scanner.category }}</p>
        <p class="text-[#F3F4F6] mb-2">
          <span class="font-medium">Locations: </span> 
          <span v-if="locationNames.length > 0">
            {{ locationNames.join(', ') }}
          </span>
          <span v-else class="text-gray-500 italic">No locations assigned</span>
        </p>
        <p class="text-[#F3F4F6]">
          <span class="font-medium">Status:</span> 
          <span 
            class="px-2 py-1 rounded-full text-xs font-medium ml-2"
            :class="scanner.status === 'running' ? 'bg-green-500 bg-opacity-20 text-green-500' : 'bg-gray-500 bg-opacity-20 text-gray-500'"
          >
            {{ scanner.status }}
          </span>
        </p>
      </div>
      
      <!-- Keywords Section -->
      <div class="pb-4 border-b border-gray-800">
        <div class="flex justify-between items-center mb-2">
          <h4 class="text-md font-semibold text-[#F3F4F6]">Keywords</h4>
        </div>
        
        <div v-if="!keywords || keywords.length === 0" class="text-[#9CA3AF] italic">
          No keywords set. Scanner will match all listings.
        </div>
        <div v-else class="flex flex-wrap gap-2">
          <span 
            v-for="(keyword, index) in keywords" 
            :key="index" 
            class="px-2 py-1 bg-blue-500 bg-opacity-20 text-blue-400 rounded-full text-xs"
          >
            {{ keyword }}
          </span>
        </div>
        <p class="text-xs text-[#9CA3AF] mt-2">
          These keywords are used to filter search results. If any of these keywords are found in a listing title, it will be flagged.
        </p>
      </div>
    </div>
    
    <template #footer>
      <div class="flex space-x-2">
        <BaseButton 
          variant="secondary"
          @click="$emit('edit', scanner)"
        >
          Edit Scanner
        </BaseButton>
        <BaseButton 
          :variant="scanner?.status === 'running' ? 'danger' : 'success'"
          @click="$emit('toggle-status', scanner)"
        >
          {{ scanner?.status === 'running' ? 'Stop Scanner' : 'Start Scanner' }}
        </BaseButton>
        <BaseButton 
          variant="danger"
          @click="$emit('delete', scanner)"
        >
          Delete Scanner
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import type { Scanner } from '@/types'

interface Props {
  show: boolean
  scanner: Scanner | null
  keywords?: string[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  edit: [scanner: Scanner]
  'toggle-status': [scanner: Scanner]
  delete: [scanner: Scanner]
}>()

const locationNames = computed(() => {
  if (props.scanner?.locations_data) {
    return props.scanner.locations_data.map(loc => loc.location_name)
  }
  return []
})
</script>
