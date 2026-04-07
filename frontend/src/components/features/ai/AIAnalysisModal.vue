<template>
  <BaseModal
    :show="show"
    title="🤖 AI Deal Analysis"
    @close="$emit('close')"
    size="xl"
  >
    <div class="space-y-6">
      <!-- Loading State -->
      <div v-if="isAnalyzing" class="text-center py-12">
        <div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-purple-500 border-t-transparent"></div>
        <p class="text-gray-400 mt-4">Analyzing listing with AI...</p>
        <p class="text-gray-500 text-sm mt-2">Evaluating images, price, and market value</p>
      </div>
      
      <!-- Error State -->
      <div v-else-if="error" class="text-center py-8">
        <div class="text-red-400 text-5xl mb-4">⚠️</div>
        <p class="text-red-400 font-medium">Analysis Failed</p>
        <p class="text-gray-400 text-sm mt-2">{{ error }}</p>
        <button
          @click="retryAnalysis"
          class="mt-4 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
        >
          Retry Analysis
        </button>
      </div>
      
      <!-- Analysis Result -->
      <div v-else-if="analysisResult" class="space-y-6">
        <!-- Header: Listing Info + Verdict Side by Side -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <!-- Listing Info Card -->
          <div class="p-4 bg-[#1C1C1E] rounded-lg border border-gray-800">
            <div class="flex gap-4">
              <div class="w-24 h-24 flex-shrink-0 rounded-lg overflow-hidden bg-gray-800">
                <img 
                  v-if="listing?.img"
                  :src="listing.img"
                  :alt="listing.title"
                  class="w-full h-full object-cover"
                />
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="text-white font-medium line-clamp-2">{{ listing?.title }}</h3>
                <p class="text-green-400 font-bold text-lg">{{ listing?.price }}</p>
                <p class="text-gray-400 text-sm">{{ listing?.location }}</p>
                <a 
                  :href="listing?.url" 
                  target="_blank"
                  class="text-blue-400 text-sm hover:text-blue-300"
                >
                  View Original →
                </a>
              </div>
            </div>
          </div>
          
          <!-- Verdict Card -->
          <div 
            class="p-4 rounded-lg border-2 flex flex-col justify-center"
            :class="analysisResult.recommendation === 'NOTIFY' 
              ? 'bg-green-900/20 border-green-500' 
              : 'bg-gray-800 border-gray-600'"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center">
                <span class="text-4xl mr-3">
                  {{ analysisResult.recommendation === 'NOTIFY' ? '✅' : '❌' }}
                </span>
                <div>
                  <p class="text-xl font-bold" :class="analysisResult.recommendation === 'NOTIFY' ? 'text-green-400' : 'text-gray-400'">
                    {{ analysisResult.recommendation === 'NOTIFY' ? 'GOOD DEAL' : 'PASS' }}
                  </p>
                  <p class="text-gray-400 text-sm">{{ analysisResult.confidence }}% confidence</p>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Section 1: Item Identification -->
        <div class="p-4 bg-[#1C1C1E] rounded-lg border border-gray-800">
          <h4 class="text-white font-semibold mb-3 flex items-center">
            <span class="mr-2 text-lg">🏷️</span>
            What This Item Is
          </h4>
          <p class="text-gray-300 mb-3">{{ analysisResult.item_identification?.description || 'Item identification pending...' }}</p>
          
          <!-- Item Details Grid -->
          <div v-if="analysisResult.item_identification" class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div v-if="analysisResult.item_identification.brand" class="p-2 bg-gray-800 rounded text-center">
              <p class="text-gray-500 text-xs uppercase">Brand</p>
              <p class="text-white font-medium">{{ analysisResult.item_identification.brand }}</p>
            </div>
            <div v-if="analysisResult.item_identification.model" class="p-2 bg-gray-800 rounded text-center">
              <p class="text-gray-500 text-xs uppercase">Model</p>
              <p class="text-white font-medium">{{ analysisResult.item_identification.model }}</p>
            </div>
            <div v-if="analysisResult.item_identification.year" class="p-2 bg-gray-800 rounded text-center">
              <p class="text-gray-500 text-xs uppercase">Year</p>
              <p class="text-white font-medium">{{ analysisResult.item_identification.year }}</p>
            </div>
            <div v-if="analysisResult.item_identification.size" class="p-2 bg-gray-800 rounded text-center">
              <p class="text-gray-500 text-xs uppercase">Size</p>
              <p class="text-white font-medium">{{ analysisResult.item_identification.size }}</p>
            </div>
            <div v-if="analysisResult.item_identification.condition" class="p-2 bg-gray-800 rounded text-center">
              <p class="text-gray-500 text-xs uppercase">Condition</p>
              <p class="text-white font-medium">{{ analysisResult.item_identification.condition }}</p>
            </div>
            <div v-if="analysisResult.item_identification.included_accessories" class="p-2 bg-gray-800 rounded text-center col-span-2">
              <p class="text-gray-500 text-xs uppercase">Includes</p>
              <p class="text-white font-medium">{{ analysisResult.item_identification.included_accessories }}</p>
            </div>
          </div>
        </div>
        
        <!-- Section 2: Value Assessment -->
        <div class="p-4 bg-[#1C1C1E] rounded-lg border border-gray-800">
          <h4 class="text-white font-semibold mb-3 flex items-center">
            <span class="mr-2 text-lg">💰</span>
            Value Assessment
          </h4>
          <div class="grid grid-cols-3 gap-4 mb-3">
            <div class="text-center p-3 bg-gray-800 rounded-lg">
              <p class="text-gray-500 text-xs uppercase mb-1">Listed Price</p>
              <p class="text-xl font-bold text-white">{{ listing?.price }}</p>
            </div>
            <div class="text-center p-3 bg-gray-800 rounded-lg">
              <p class="text-gray-500 text-xs uppercase mb-1">Estimated Value</p>
              <p class="text-xl font-bold text-blue-400">{{ analysisResult.value_assessment?.estimated_value || 'N/A' }}</p>
            </div>
            <div class="text-center p-3 rounded-lg" :class="getSavingsClass">
              <p class="text-gray-500 text-xs uppercase mb-1">Potential Savings</p>
              <p class="text-xl font-bold" :class="analysisResult.value_assessment?.savings_percent > 0 ? 'text-green-400' : 'text-gray-400'">
                {{ analysisResult.value_assessment?.savings_percent ? `${analysisResult.value_assessment.savings_percent}%` : 'N/A' }}
              </p>
            </div>
          </div>
          <p class="text-gray-300 text-sm">{{ analysisResult.value_assessment?.explanation || 'Value assessment pending...' }}</p>
        </div>
        
        <!-- Section 3: Key Takeaways (Why It's a Good/Bad Deal) -->
        <div class="p-4 bg-[#1C1C1E] rounded-lg border border-gray-800">
          <h4 class="text-white font-semibold mb-3 flex items-center">
            <span class="mr-2 text-lg">🎯</span>
            Key Takeaways
          </h4>
          <p class="text-gray-300 mb-4">{{ analysisResult.summary }}</p>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <!-- Positive Points -->
            <div v-if="analysisResult.key_takeaways?.positives?.length" class="p-3 bg-green-900/10 rounded-lg border border-green-800/50">
              <p class="text-green-400 font-medium mb-2 flex items-center text-sm">
                <span class="mr-2">✨</span>
                Why This Is Good
              </p>
              <ul class="text-gray-300 text-sm space-y-1">
                <li v-for="(point, i) in analysisResult.key_takeaways.positives" :key="i" class="flex items-start">
                  <span class="text-green-400 mr-2">+</span>
                  {{ point }}
                </li>
              </ul>
            </div>
            
            <!-- Negative Points -->
            <div v-if="analysisResult.key_takeaways?.negatives?.length" class="p-3 bg-red-900/10 rounded-lg border border-red-800/50">
              <p class="text-red-400 font-medium mb-2 flex items-center text-sm">
                <span class="mr-2">⚠️</span>
                Concerns
              </p>
              <ul class="text-gray-300 text-sm space-y-1">
                <li v-for="(point, i) in analysisResult.key_takeaways.negatives" :key="i" class="flex items-start">
                  <span class="text-red-400 mr-2">-</span>
                  {{ point }}
                </li>
              </ul>
            </div>
          </div>
        </div>
        
        <!-- Section 4: Notes & Considerations -->
        <div class="p-4 bg-[#1C1C1E] rounded-lg border border-gray-800">
          <h4 class="text-white font-semibold mb-3 flex items-center">
            <span class="mr-2 text-lg">📝</span>
            Notes & Considerations
          </h4>
          
          <!-- Condition Details -->
          <div v-if="analysisResult.notes?.condition_details" class="mb-4">
            <p class="text-blue-400 font-medium text-sm mb-1">Condition Details</p>
            <p class="text-gray-300 text-sm">{{ analysisResult.notes.condition_details }}</p>
          </div>
          
          <!-- Things to Look Out For -->
          <div v-if="analysisResult.notes?.things_to_check?.length" class="mb-4">
            <p class="text-yellow-400 font-medium text-sm mb-2">Things to Check When Viewing</p>
            <ul class="text-gray-300 text-sm space-y-1">
              <li v-for="(item, i) in analysisResult.notes.things_to_check" :key="i" class="flex items-start">
                <span class="text-yellow-400 mr-2">•</span>
                {{ item }}
              </li>
            </ul>
          </div>
          
          <!-- Things to Consider -->
          <div v-if="analysisResult.notes?.considerations?.length" class="mb-4">
            <p class="text-purple-400 font-medium text-sm mb-2">Things to Consider</p>
            <ul class="text-gray-300 text-sm space-y-1">
              <li v-for="(item, i) in analysisResult.notes.considerations" :key="i" class="flex items-start">
                <span class="text-purple-400 mr-2">•</span>
                {{ item }}
              </li>
            </ul>
          </div>
          
          <!-- Red Flags -->
          <div v-if="analysisResult.notes?.red_flags?.length">
            <p class="text-red-400 font-medium text-sm mb-2">Red Flags</p>
            <ul class="text-gray-300 text-sm space-y-1">
              <li v-for="(flag, i) in analysisResult.notes.red_flags" :key="i" class="flex items-start">
                <span class="text-red-400 mr-2">🚩</span>
                {{ flag }}
              </li>
            </ul>
          </div>
        </div>
        
        <!-- Section 5: Image Analysis -->
        <div v-if="analysisResult.image_analysis" class="p-4 bg-[#1C1C1E] rounded-lg border border-gray-800">
          <h4 class="text-white font-semibold mb-3 flex items-center">
            <span class="mr-2 text-lg">📷</span>
            Image Analysis
          </h4>
          <p class="text-gray-300 text-sm">{{ analysisResult.image_analysis }}</p>
        </div>
        
        <!-- Mock Data Warning -->
        <div v-if="analysisResult.is_mock" class="p-3 bg-yellow-900/20 border border-yellow-600/50 rounded-lg">
          <p class="text-yellow-400 text-sm flex items-center">
            <span class="mr-2">⚠️</span>
            <strong class="mr-1">Development Mode:</strong>
            This is mock data. Connect to the LLM service for real analysis.
          </p>
        </div>
      </div>
      
      <!-- Initial State (no analysis yet) -->
      <div v-else class="text-center py-10">
        <div class="text-5xl mb-4">🤖</div>
        <p class="text-gray-300 font-medium mb-2">No AI analysis yet</p>
        <p class="text-gray-500 text-sm">Click "Analyze with AI" below to run a deep analysis on this listing.</p>
      </div>
    </div>

    <template #footer>
      <div class="flex justify-between items-center w-full">
        <!-- Left: Open Listing button -->
        <a
          v-if="listing?.url"
          :href="listing.url"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center px-3 py-1.5 rounded-lg text-sm bg-gray-700 hover:bg-gray-600 text-gray-200 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="w-4 h-4 mr-1.5">
            <path fill-rule="evenodd" d="M4.25 5.5a.75.75 0 00-.75.75v8.5c0 .414.336.75.75.75h8.5a.75.75 0 00.75-.75v-4a.75.75 0 011.5 0v4A2.25 2.25 0 0112.75 17h-8.5A2.25 2.25 0 012 14.75v-8.5A2.25 2.25 0 014.25 4h5a.75.75 0 010 1.5h-5z" clip-rule="evenodd" />
            <path fill-rule="evenodd" d="M6.194 12.753a.75.75 0 001.06.053L16.5 4.44v2.81a.75.75 0 001.5 0v-4.5a.75.75 0 00-.75-.75h-4.5a.75.75 0 000 1.5h2.553l-9.056 8.194a.75.75 0 00-.053 1.06z" clip-rule="evenodd" />
          </svg>
          Open Listing
        </a>
        <div v-else></div>

        <!-- Right: Action buttons -->
        <div class="flex space-x-2">
          <BaseButton
            v-if="!analysisResult && !isAnalyzing"
            @click="runAnalysis()"
            variant="primary"
          >
            🤖 Analyze with AI
          </BaseButton>
          <BaseButton
            v-if="analysisResult && analysisResult.recommendation === 'NOTIFY'"
            @click="sendNotification"
            variant="primary"
            :disabled="notificationSent || isSendingNotification"
            :loading="isSendingNotification"
          >
            {{ notificationSent ? '✓ Notification Sent' : '📧 Send Notification' }}
          </BaseButton>
          <BaseButton
            v-if="analysisResult"
            @click="retryAnalysis"
            variant="secondary"
          >
            🔄 Re-analyze
          </BaseButton>
          <BaseButton
            @click="$emit('close')"
            variant="secondary"
          >
            Close
          </BaseButton>
        </div>
      </div>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import { analyzeListing } from '@/services/api'
import type { Listing } from '@/types/index'

interface Props {
  show: boolean
  listing: (Listing & { analysis_metadata?: any }) | null
}

interface AIAnalysisResult {
  recommendation: 'NOTIFY' | 'IGNORE'
  confidence: number
  summary: string
  
  // Item Identification
  item_identification?: {
    description: string
    brand?: string
    model?: string
    year?: string
    size?: string
    condition?: string
    included_accessories?: string
  }
  
  // Value Assessment
  value_assessment?: {
    estimated_value: string
    savings_percent?: number
    explanation: string
  }
  
  // Key Takeaways
  key_takeaways?: {
    positives: string[]
    negatives: string[]
  }
  
  // Notes & Considerations
  notes?: {
    condition_details?: string
    things_to_check?: string[]
    considerations?: string[]
    red_flags?: string[]
  }
  
  // Image Analysis
  image_analysis?: string
  
  // Legacy fields for backwards compatibility
  reasoning?: {
    image_analysis?: string
    price_assessment?: string
    condition_notes?: string
    red_flags?: string[]
    positive_indicators?: string[]
  }
  extracted_details?: {
    brand?: string
    model?: string
    length_cm?: number
    bindings_included?: boolean
    condition?: string
  }
  
  notification_sent?: boolean
  is_mock?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  analyzed: [listing: Listing, result: AIAnalysisResult]
}>()

const isAnalyzing = ref(false)
const isSendingNotification = ref(false)
const error = ref<string | null>(null)
const analysisResult = ref<AIAnalysisResult | null>(null)
const notificationSent = ref(false)

// Computed for savings styling
const getSavingsClass = computed(() => {
  const savings = analysisResult.value?.value_assessment?.savings_percent || 0
  if (savings > 20) return 'bg-green-900/30'
  if (savings > 0) return 'bg-green-900/10'
  return 'bg-gray-800'
})

// Resolve analysis from listing — handle both storage formats:
// 1. Scan pipeline stores directly: analysis_metadata.recommendation
// 2. Manual analyze-ai stores nested: analysis_metadata.llm_analysis.recommendation
const resolveAnalysis = (listing: typeof props.listing) => {
  const meta = listing?.analysis_metadata
  return meta?.llm_analysis ?? (meta?.recommendation ? meta : null)
}

// Watch for listing changes — load existing analysis if available
watch(() => props.listing, (newListing) => {
  const analysis = resolveAnalysis(newListing)
  if (analysis) {
    analysisResult.value = analysis
    notificationSent.value = newListing?.analysis_metadata?.notification_sent || false
  } else {
    analysisResult.value = null
  }
}, { immediate: true })

// Reset state when modal closes
watch(() => props.show, (isVisible) => {
  if (!isVisible) {
    analysisResult.value = null
    error.value = null
    notificationSent.value = false
  }
})

const runAnalysis = async (force: boolean = false) => {
  if (!props.listing) return
  
  isAnalyzing.value = true
  error.value = null
  
  try {
    console.log('🤖 Starting AI analysis for listing:', props.listing.listing_idx, force ? '(forced)' : '')
    const result = await analyzeListing(props.listing.listing_idx, force)
    console.log('✅ AI analysis complete:', {
      recommendation: result.recommendation,
      confidence: result.confidence,
      brand: result.item_identification?.brand,
      model: result.item_identification?.model
    })
    
    analysisResult.value = result
    emit('analyzed', props.listing, result)
    
    // Check if notification was already sent
    if (result.notification_sent) {
      notificationSent.value = true
    }
  } catch (err: any) {
    console.error('❌ AI analysis failed:', err)
    error.value = err.message || 'Failed to analyze listing'
  } finally {
    isAnalyzing.value = false
  }
}

const retryAnalysis = () => {
  // Clear previous result and re-run with force=true to bypass cache
  analysisResult.value = null
  runAnalysis(true)
}

const sendNotification = async () => {
  if (!props.listing || notificationSent.value) return
  
  isSendingNotification.value = true
  
  try {
    // TODO: Call API to send notification
    // await sendAINotification(props.listing.listing_idx)
    notificationSent.value = true
  } catch (err) {
    console.error('Failed to send notification:', err)
  } finally {
    isSendingNotification.value = false
  }
}
</script>
