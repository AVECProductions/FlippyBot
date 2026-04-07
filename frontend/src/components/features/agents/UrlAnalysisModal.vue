<template>
  <BaseModal
    :show="show"
    title="Analyze Listing"
    size="xl"
    @close="handleClose"
  >
    <div class="space-y-5">
      <!-- URL Input -->
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1.5">Facebook Marketplace URL</label>
        <div class="flex items-end space-x-2">
          <input
            v-model="url"
            type="url"
            placeholder="https://www.facebook.com/marketplace/item/..."
            :disabled="isAnalyzing"
            class="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none disabled:opacity-50"
            @keyup.enter="handleAnalyze"
          />
          <button
            @click="handleAnalyze"
            :disabled="!isValidUrl || isAnalyzing"
            class="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm font-medium rounded transition-colors flex-shrink-0"
          >
            {{ isAnalyzing ? 'Analyzing...' : 'Analyze' }}
          </button>
        </div>
        <p v-if="agentName" class="text-[11px] text-gray-600 mt-1">Agent: {{ agentName }}</p>
      </div>

      <!-- Loading State -->
      <div v-if="isAnalyzing" class="py-8 text-center">
        <div class="inline-flex items-center space-x-3">
          <svg class="animate-spin h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
          </svg>
          <span class="text-sm text-gray-400">{{ loadingMessage }}</span>
        </div>
        <p class="text-[11px] text-gray-600 mt-3">This can take 15-30 seconds</p>
      </div>

      <!-- Error -->
      <div v-if="error" class="text-xs text-red-400 bg-red-500/5 border border-red-500/10 px-4 py-2.5 rounded">
        {{ error }}
      </div>

      <!-- Results -->
      <div v-if="result && !isAnalyzing" class="space-y-4">
        <!-- Recommendation Banner -->
        <div 
          :class="[
            'flex items-center justify-between px-4 py-3 rounded border',
            isNotify 
              ? 'bg-emerald-500/5 border-emerald-500/20' 
              : 'bg-gray-800/50 border-gray-700'
          ]"
        >
          <div class="flex items-center space-x-3">
            <span 
              :class="[
                'text-xs font-semibold uppercase tracking-wider px-2 py-0.5 rounded',
                isNotify ? 'text-emerald-400 bg-emerald-500/10' : 'text-gray-500 bg-gray-700/50'
              ]"
            >
              {{ result.analysis?.recommendation || 'N/A' }}
            </span>
            <span class="text-sm text-gray-300">{{ result.analysis?.summary }}</span>
          </div>
          <span class="text-xs text-gray-500">{{ result.analysis?.confidence }}% confidence</span>
        </div>

        <!-- Listing Info -->
        <div class="grid grid-cols-3 gap-3 text-xs">
          <div class="bg-gray-900/50 border border-gray-800 rounded px-3 py-2">
            <p class="text-gray-600 mb-0.5">Title</p>
            <p class="text-gray-300 truncate">{{ result.title }}</p>
          </div>
          <div class="bg-gray-900/50 border border-gray-800 rounded px-3 py-2">
            <p class="text-gray-600 mb-0.5">Price</p>
            <p class="text-gray-300">{{ result.price }}</p>
          </div>
          <div class="bg-gray-900/50 border border-gray-800 rounded px-3 py-2">
            <p class="text-gray-600 mb-0.5">Location</p>
            <p class="text-gray-300 truncate">{{ result.location }}</p>
          </div>
        </div>

        <!-- Value Assessment -->
        <div v-if="result.analysis?.value_assessment" class="bg-gray-900/50 border border-gray-800 rounded px-4 py-3">
          <p class="text-[11px] text-gray-500 uppercase tracking-wider mb-2">Value Assessment</p>
          <div class="grid grid-cols-3 gap-3 text-xs">
            <div>
              <p class="text-gray-600">Asking</p>
              <p class="text-gray-300">{{ result.analysis.value_assessment.asking_price }}</p>
            </div>
            <div>
              <p class="text-gray-600">Est. Value</p>
              <p class="text-gray-300">{{ result.analysis.value_assessment.estimated_value }}</p>
            </div>
            <div>
              <p class="text-gray-600">Savings</p>
              <p :class="savings > 0 ? 'text-emerald-400' : 'text-gray-400'">
                {{ savings > 0 ? savings + '%' : 'N/A' }}
              </p>
            </div>
          </div>
        </div>

        <!-- Key Takeaways -->
        <div v-if="result.analysis?.key_takeaways" class="grid grid-cols-2 gap-3">
          <div v-if="positives.length > 0" class="bg-gray-900/50 border border-gray-800 rounded px-4 py-3">
            <p class="text-[11px] text-gray-500 uppercase tracking-wider mb-1.5">Positives</p>
            <ul class="text-xs text-gray-400 space-y-1">
              <li v-for="(p, i) in positives" :key="i" class="flex items-start space-x-1.5">
                <span class="text-emerald-500 mt-0.5 flex-shrink-0">+</span>
                <span>{{ p }}</span>
              </li>
            </ul>
          </div>
          <div v-if="negatives.length > 0" class="bg-gray-900/50 border border-gray-800 rounded px-4 py-3">
            <p class="text-[11px] text-gray-500 uppercase tracking-wider mb-1.5">Negatives</p>
            <ul class="text-xs text-gray-400 space-y-1">
              <li v-for="(n, i) in negatives" :key="i" class="flex items-start space-x-1.5">
                <span class="text-red-400 mt-0.5 flex-shrink-0">-</span>
                <span>{{ n }}</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Image Analysis -->
        <div v-if="result.analysis?.image_analysis" class="bg-gray-900/50 border border-gray-800 rounded px-4 py-3">
          <p class="text-[11px] text-gray-500 uppercase tracking-wider mb-1.5">Image Analysis</p>
          <p class="text-xs text-gray-400 leading-relaxed">{{ result.analysis.image_analysis }}</p>
        </div>

        <!-- Description excerpt -->
        <div v-if="result.description" class="bg-gray-900/50 border border-gray-800 rounded px-4 py-3">
          <p class="text-[11px] text-gray-500 uppercase tracking-wider mb-1.5">Description</p>
          <p class="text-xs text-gray-500 leading-relaxed whitespace-pre-line">{{ result.description }}</p>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-between items-center">
        <div>
          <span v-if="result?.listing_id" class="text-[11px] text-gray-600">
            Saved as listing #{{ result.listing_id }}
          </span>
        </div>
        <button
          @click="handleClose"
          class="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
        >
          Close
        </button>
      </div>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { analyzeListingUrl } from '@/services/api'
import BaseModal from '@/components/ui/BaseModal.vue'

const props = defineProps<{
  show: boolean
  agentSlug: string
  agentName?: string
}>()

const emit = defineEmits<{
  close: []
}>()

const url = ref('')
const isAnalyzing = ref(false)
const loadingMessage = ref('Scraping listing...')
const error = ref<string | null>(null)
const result = ref<any>(null)

const isValidUrl = computed(() => {
  return /facebook\.com\/marketplace\/item\/\d+/.test(url.value)
})

const isNotify = computed(() => {
  return result.value?.analysis?.recommendation?.toUpperCase() === 'NOTIFY'
})

const savings = computed(() => {
  return result.value?.analysis?.value_assessment?.savings_percent || 0
})

const positives = computed(() => {
  return result.value?.analysis?.key_takeaways?.positives || []
})

const negatives = computed(() => {
  return result.value?.analysis?.key_takeaways?.negatives || []
})

const handleAnalyze = async () => {
  if (!isValidUrl.value || isAnalyzing.value) return
  
  isAnalyzing.value = true
  error.value = null
  result.value = null
  loadingMessage.value = 'Scraping listing...'
  
  // Update loading message after a few seconds
  const timer = setTimeout(() => {
    loadingMessage.value = 'Running AI analysis...'
  }, 8000)
  
  try {
    result.value = await analyzeListingUrl(props.agentSlug, url.value)
  } catch (err: any) {
    error.value = err.message || 'Analysis failed'
  } finally {
    clearTimeout(timer)
    isAnalyzing.value = false
  }
}

const handleClose = () => {
  emit('close')
}

// Reset state when modal opens
watch(() => props.show, (newShow) => {
  if (newShow) {
    url.value = ''
    error.value = null
    result.value = null
    isAnalyzing.value = false
  }
})
</script>
