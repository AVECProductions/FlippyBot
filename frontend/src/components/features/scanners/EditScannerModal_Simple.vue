<template>
  <BaseModal
    :show="show"
    title="Edit Search Query"
    @close="$emit('close')"
    size="md"
  >
    <form v-if="scanner" @submit.prevent="handleSubmit" class="space-y-6">
      <!-- Agent Info Banner -->
      <div v-if="agentInfo" class="bg-gradient-to-r from-blue-900/30 to-purple-900/30 p-4 rounded-lg border border-gray-700">
        <div class="flex items-center space-x-3">
          <span class="text-3xl">{{ agentInfo.icon }}</span>
          <div>
            <h4 class="text-sm font-semibold text-white">{{ agentInfo.name }}</h4>
            <p class="text-xs text-gray-400">{{ agentInfo.description }}</p>
          </div>
        </div>
      </div>

      <!-- Search Query -->
      <BaseInput 
        v-model="form.query"
        label="What are you searching for?"
        placeholder="e.g., 'twin tip skis', 'ON3P skis 180cm'"
        required
        hint="The AI agent will analyze listings matching this search"
      />
      
      <!-- Custom Label (Optional) -->
      <BaseInput 
        v-model="form.category"
        label="Custom Label (Optional)"
        placeholder="e.g., 'Freestyle Skis', 'Powder Skis'"
        hint="Your own label to organize this query"
      />
      
      <!-- Locations -->
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          Where to search? *
        </label>
        <SearchableMultiSelect
          v-model="form.location_ids"
          :options="locations"
          placeholder="Select locations..."
          hint="Choose one or more locations to search"
          :max-display="5"
        />
      </div>
      
      <!-- Status -->
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">Status</label>
        <select 
          v-model="form.status" 
          class="w-full px-3 py-2 bg-[#1C1C1E] border border-gray-800 rounded-md text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="stopped">Stopped</option>
          <option value="running">Running</option>
        </select>
      </div>
      
      <!-- Notification Emails -->
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          Notification Emails (Optional)
        </label>
        <div class="space-y-2">
          <div v-for="(email, index) in form.notification_emails" :key="`email-${index}`" class="flex items-center space-x-2">
            <input 
              v-model="form.notification_emails[index]"
              type="email"
              placeholder="email@example.com"
              class="flex-1 px-3 py-2 bg-[#1C1C1E] border border-gray-800 rounded-md text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <button 
              type="button"
              @click="removeEmail(index)"
              class="px-3 py-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-md transition-colors"
            >
              Remove
            </button>
          </div>
          <button 
            type="button"
            @click="addEmail"
            class="w-full px-3 py-2 text-sm text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 border border-dashed border-gray-700 rounded-md transition-colors"
          >
            + Add Email
          </button>
        </div>
        <p class="text-xs text-gray-500 mt-1">
          AI deal alerts will be sent to these emails. Leave empty to use default.
        </p>
      </div>
    </form>

    <template #footer>
      <div class="flex justify-between">
        <BaseButton 
          @click="handleDelete" 
          variant="danger"
          :loading="isDeleting"
        >
          Delete Query
        </BaseButton>
        <div class="flex space-x-2">
          <BaseButton 
            @click="$emit('close')" 
            variant="secondary"
          >
            Cancel
          </BaseButton>
          <BaseButton 
            @click="handleSubmit" 
            variant="primary"
            :loading="isUpdating"
            loading-text="Saving..."
          >
            Save Changes
          </BaseButton>
        </div>
      </div>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useScannerStore } from '@/stores/scannerStore'
import { getAgentInfo } from '@/constants/agents'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import SearchableMultiSelect from '@/components/ui/SearchableMultiSelect.vue'
import type { Scanner } from '@/types'

interface Props {
  show: boolean
  scanner: Scanner | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  updated: []
  deleted: []
}>()

const scannerStore = useScannerStore()
const { locations, isUpdating, isDeleting } = storeToRefs(scannerStore)

const form = reactive({
  query: '',
  category: '',
  status: 'stopped' as 'running' | 'stopped',
  location_ids: [] as number[],
  notification_emails: [] as string[]
})

const agentInfo = computed(() => {
  return props.scanner?.agent_type ? getAgentInfo(props.scanner.agent_type) : null
})

const initializeForm = () => {
  if (props.scanner) {
    console.log('Initializing form with scanner:', props.scanner)
    console.log('Scanner locations_data:', props.scanner.locations_data)
    
    form.query = props.scanner.query
    form.category = props.scanner.category
    form.status = props.scanner.status as 'running' | 'stopped'
    
    // Extract location IDs from locations_data (API returns objects, not just IDs)
    if (props.scanner.locations_data && props.scanner.locations_data.length > 0) {
      form.location_ids = props.scanner.locations_data.map(loc => loc.location)
      console.log('Extracted location_ids from locations_data:', form.location_ids)
    } else if (props.scanner.location_ids) {
      form.location_ids = props.scanner.location_ids
      console.log('Using location_ids directly:', form.location_ids)
    } else {
      form.location_ids = []
      console.log('No locations found')
    }
    
    // Initialize notification emails
    form.notification_emails = [...(props.scanner.notification_emails || [])]
    console.log('Initialized notification_emails:', form.notification_emails)
    console.log('Available locations from store:', locations.value)
  }
}

const addEmail = () => {
  form.notification_emails.push('')
}

const removeEmail = (index: number) => {
  form.notification_emails.splice(index, 1)
}

const handleSubmit = async () => {
  if (!props.scanner) return
  
  // Validation
  if (!form.query.trim()) {
    scannerStore.setError('Please enter a search query')
    return
  }
  
  if (form.location_ids.length === 0) {
    scannerStore.setError('Please select at least one location')
    return
  }
  
  try {
    // Filter and validate notification emails
    const validEmails = form.notification_emails
      .map(e => e.trim().toLowerCase())
      .filter(e => e && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e))
    
    // Build update data (simplified - no filters!)
    const updateData = {
      query: form.query.trim(),
      category: form.category.trim() || form.query.trim(),
      status: form.status,
      location_ids: form.location_ids,
      notification_emails: validEmails,
      // Keep existing agent_type, don't change it
      product_category: 'ai_beta' as const,
      min_price: null,
      max_price: null,
      max_distance: null,
      category_filters: {}
    }
    
    await scannerStore.updateExistingScanner(props.scanner.id, updateData)
    emit('updated')
  } catch (error) {
    console.error('Failed to update scanner:', error)
  }
}

const handleDelete = async () => {
  if (!props.scanner) return
  
  if (confirm(`Are you sure you want to delete the query "${props.scanner.query}"?`)) {
    try {
      await scannerStore.deleteExistingScanner(props.scanner.id)
      emit('deleted')
    } catch (error) {
      console.error('Failed to delete scanner:', error)
    }
  }
}

// Initialize form when scanner changes
watch(() => props.scanner, (newScanner) => {
  console.log('Scanner prop changed:', newScanner)
  initializeForm()
}, { immediate: true })

// Initialize form when modal opens
watch(() => props.show, (newShow) => {
  console.log('Modal show changed:', newShow, 'Scanner:', props.scanner)
  if (newShow) {
    // Ensure locations are loaded
    if (locations.value.length === 0) {
      console.log('Fetching locations...')
      scannerStore.fetchLocations()
    }
    initializeForm()
  }
})
</script>
