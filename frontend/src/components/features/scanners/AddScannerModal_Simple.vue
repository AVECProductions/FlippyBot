<template>
  <BaseModal
    :show="show"
    title="Add Search Query"
    @close="$emit('close')"
    size="md"
  >
    <form @submit.prevent="handleSubmit" class="space-y-6">
      <!-- Agent Info -->
      <div v-if="agentInfo" class="px-3 py-2.5 border border-gray-800 rounded bg-gray-900/50">
        <p class="text-sm text-gray-300">{{ agentInfo.name }}</p>
        <p v-if="agentInfo.description" class="text-xs text-gray-600 mt-0.5">{{ agentInfo.description }}</p>
      </div>

      <!-- Search Query -->
      <div>
        <div class="flex items-center justify-between mb-1">
          <label class="block text-sm font-medium text-gray-300">What are you searching for? <span class="text-red-400">*</span></label>
          <button
            v-if="agentInfo"
            type="button"
            @click="handleSuggest"
            :disabled="isSuggesting"
            class="text-[11px] text-gray-500 hover:text-gray-300 transition-colors disabled:opacity-50"
          >
            {{ isSuggesting ? 'thinking...' : 'suggest queries' }}
          </button>
        </div>
        <BaseInput 
          v-model="form.query"
          placeholder="e.g., 'twin tip skis', 'ON3P skis 180cm', 'Volkl Mantra'"
          required
          hint="The AI agent will analyze listings matching this search"
        />
        <!-- Suggestions -->
        <div v-if="suggestions.length > 0" class="flex flex-wrap gap-1.5 mt-2">
          <button
            v-for="suggestion in suggestions"
            :key="suggestion"
            type="button"
            @click="useSuggestion(suggestion)"
            class="text-xs px-2.5 py-1 rounded border border-gray-700 text-gray-400 hover:text-gray-200 hover:border-gray-500 bg-gray-900/50 transition-colors"
          >
            {{ suggestion }}
          </button>
        </div>
      </div>
      
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
        <button
          type="button"
          @click="$emit('create-location')"
          class="mt-2 text-xs text-blue-400 hover:text-blue-300"
        >
          + Add New Location
        </button>
      </div>
      
      <!-- Status -->
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">Status</label>
        <select 
          v-model="form.status" 
          class="w-full px-3 py-2 bg-[#1C1C1E] border border-gray-800 rounded-md text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="stopped">Stopped (don't run yet)</option>
          <option value="running">Running (scan automatically)</option>
        </select>
        <p class="text-xs text-gray-500 mt-1">You can change this later</p>
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

      <!-- AI Info -->
      <div class="border border-gray-800 rounded px-4 py-3">
        <p class="text-xs font-medium text-gray-400 mb-1.5">How AI-Driven Search Works</p>
        <ul class="text-xs text-gray-600 space-y-1 list-disc list-inside">
          <li>Listings matching your query are scraped and saved</li>
          <li>The AI agent triages which listings are interesting</li>
          <li>Interesting listings get deep multimodal analysis (text + images)</li>
          <li>You're notified only about the best matches</li>
        </ul>
      </div>
    </form>

    <template #footer>
      <div class="flex justify-end space-x-2">
        <BaseButton 
          @click="$emit('close')" 
          variant="secondary"
        >
          Cancel
        </BaseButton>
        <BaseButton 
          @click="handleSubmit" 
          variant="primary"
          :loading="isCreating"
          loading-text="Creating..."
        >
          Add Query
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useScannerStore } from '@/stores/scannerStore'
import { useAgentStore } from '@/stores/agentStore'
import { suggestAgentQueries } from '@/services/api'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import SearchableMultiSelect from '@/components/ui/SearchableMultiSelect.vue'
import type { AgentType } from '@/types'

interface Props {
  show: boolean
  agentType?: AgentType
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  created: []
  'create-location': []
}>()

const scannerStore = useScannerStore()
const agentStore = useAgentStore()
const { locations, isCreating } = storeToRefs(scannerStore)
const { agents } = storeToRefs(agentStore)

const form = reactive({
  query: '',
  category: '',
  status: 'stopped' as 'running' | 'stopped',
  location_ids: [] as number[],
  notification_emails: [] as string[]
})

const agentInfo = computed(() => {
  if (!props.agentType) return null
  return agents.value.find(a => a.slug === props.agentType || a.type === props.agentType) || null
})

// Query suggestions
const suggestions = ref<string[]>([])
const isSuggesting = ref(false)

const handleSuggest = async () => {
  if (!props.agentType || isSuggesting.value) return
  isSuggesting.value = true
  try {
    const result = await suggestAgentQueries(props.agentType)
    suggestions.value = result.suggestions || []
  } catch (err) {
    console.error('Failed to get suggestions:', err)
  } finally {
    isSuggesting.value = false
  }
}

const useSuggestion = (suggestion: string) => {
  form.query = suggestion
}

const addEmail = () => {
  form.notification_emails.push('')
}

const removeEmail = (index: number) => {
  form.notification_emails.splice(index, 1)
}

const resetForm = () => {
  form.query = ''
  form.category = ''
  form.status = 'stopped'
  form.location_ids = []
  form.notification_emails = []
  suggestions.value = []
}

const handleSubmit = async () => {
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
    
    // Build scanner data (simplified - no filters!)
    const scannerData = {
      query: form.query.trim(),
      category: form.category.trim() || form.query.trim(),
      status: form.status,
      location_ids: form.location_ids,
      notification_emails: validEmails,
      agent_type: props.agentType || 'skis',
      // All filtering is handled by the AI agent - no manual filters!
      product_category: 'ai_beta' as const,
      min_price: null,
      max_price: null,
      max_distance: null,
      category_filters: {}
    }
    
    await scannerStore.createNewScanner(scannerData, []) // No keywords either!
    emit('created')
    resetForm()
  } catch (error) {
    // Error handling is done in the store
    console.error('Failed to create scanner:', error)
  }
}

// Reset form when modal closes
watch(() => props.show, (newShow) => {
  if (!newShow) {
    resetForm()
  }
})
</script>
