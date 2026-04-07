<template>
  <div class="relative">
    <!-- Context Menu -->
    <div
      v-if="showContextMenu"
      ref="contextMenuRef"
      class="fixed bg-[#2C2C2E] border border-gray-700 rounded-lg shadow-xl py-1 z-50 min-w-[180px]"
      :style="{ top: contextMenuY + 'px', left: contextMenuX + 'px' }"
    >
      <button
        @click="handleAnalyzeWithAI"
        class="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-purple-600/20 hover:text-purple-300 flex items-center"
      >
        <span class="mr-2">🤖</span>
        Analyze with AI
      </button>
      <button
        @click="openInNewTab"
        class="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 flex items-center"
      >
        <span class="mr-2">↗️</span>
        Open Listing
      </button>
    </div>

    <div
      @contextmenu.prevent="handleRightClick"
      @click="handleCardClick"
      class="bg-[#1C1C1E] rounded-lg overflow-hidden shadow-lg flex flex-col hover:bg-[#2C2C2E] transition-colors duration-200 cursor-pointer border border-gray-800"
    >
      <!-- Image Container -->
      <div class="relative w-full aspect-square overflow-hidden">
        <img
          :src="listing.img || 'https://via.placeholder.com/300x200?text=No+Image'"
          :alt="listing.title"
          class="w-full h-full object-cover transition-opacity duration-200 ease-in-out opacity-0"
          @error="handleImageError"
          @load="onImageLoad"
        />

        <!-- Notify Bell Icon -->
        <div
          v-if="aiRecommendation === 'NOTIFY'"
          class="absolute top-1 right-1 w-6 h-6 rounded-full bg-green-600 bg-opacity-90 flex items-center justify-center z-10"
          title="AI recommends: NOTIFY"
        >
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" class="w-3.5 h-3.5 text-white">
            <path d="M5.85 3.5a.75.75 0 00-1.117-1 9.719 9.719 0 00-2.348 4.876.75.75 0 001.479.248A8.219 8.219 0 015.85 3.5zM19.267 2.5a.75.75 0 10-1.118 1 8.22 8.22 0 011.987 4.124.75.75 0 001.48-.248A9.72 9.72 0 0019.267 2.5z" />
            <path fill-rule="evenodd" d="M12 2.25A6.75 6.75 0 005.25 9v.75a8.217 8.217 0 01-2.119 5.52.75.75 0 00.298 1.206c1.544.57 3.16.99 4.831 1.243a3.75 3.75 0 107.48 0 24.583 24.583 0 004.83-1.244.75.75 0 00.298-1.205 8.217 8.217 0 01-2.118-5.52V9A6.75 6.75 0 0012 2.25zM9.75 18c0-.034 0-.067.002-.1a25.05 25.05 0 004.496 0l.002.1a2.25 2.25 0 11-4.5 0z" clip-rule="evenodd" />
          </svg>
        </div>

        <!-- AI Badge if analyzed (IGNORE state) -->
        <div
          v-if="hasAIAnalysis && aiRecommendation !== 'NOTIFY'"
          class="absolute top-1 left-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-gray-600 text-gray-200"
        >
          🤖 {{ aiRecommendation }}
        </div>
      </div>

      <!-- Content Container -->
      <div class="p-2 flex-1 flex flex-col">
        <!-- Price -->
        <div class="text-base font-bold text-white">{{ listing.price }}</div>

        <!-- Title -->
        <h3 class="font-medium text-gray-300 text-sm line-clamp-2 min-h-[2.5rem]">{{ listing.title }}</h3>

        <!-- Location with mileage and distance -->
        <div class="flex flex-col mt-1">
          <div class="flex justify-between items-center">
            <p class="text-xs text-gray-400 truncate mr-2">{{ listing.location }}</p>
            <p v-if="listing.distance !== null && listing.distance !== undefined" class="text-xs text-gray-400 whitespace-nowrap">
              {{ formatDistance(listing.distance) }}
            </p>
          </div>

          <p v-if="listing.description && listing.description.includes('mile')" class="text-xs text-gray-400">
            {{ extractMiles(listing.description) }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Listing } from '@/types/index'

interface Props {
  listing: Listing & { analysis_metadata?: any }
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'analyze-ai': [listing: Listing]
}>()

// Context menu state
const showContextMenu = ref(false)
const contextMenuX = ref(0)
const contextMenuY = ref(0)
const contextMenuRef = ref<HTMLElement | null>(null)

// AI Analysis state — handle both storage formats:
// 1. Scan pipeline stores directly: analysis_metadata.recommendation
// 2. Manual analyze-ai stores nested: analysis_metadata.llm_analysis.recommendation
const getAnalysis = computed(() => {
  const meta = props.listing.analysis_metadata
  return meta?.llm_analysis ?? (meta?.recommendation ? meta : null)
})

const hasAIAnalysis = computed(() => !!getAnalysis.value?.recommendation)

const aiRecommendation = computed(() => getAnalysis.value?.recommendation || '')

// Close context menu when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  if (contextMenuRef.value && !contextMenuRef.value.contains(event.target as Node)) {
    showContextMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

const handleRightClick = (event: MouseEvent) => {
  event.preventDefault()
  showContextMenu.value = true
  contextMenuX.value = event.clientX
  contextMenuY.value = event.clientY
}

const handleCardClick = () => {
  if (showContextMenu.value) {
    showContextMenu.value = false
    return
  }
  emit('analyze-ai', props.listing)
}

const handleAnalyzeWithAI = () => {
  showContextMenu.value = false
  emit('analyze-ai', props.listing)
}

const openInNewTab = () => {
  showContextMenu.value = false
  window.open(props.listing.url, '_blank')
}

const formatDistance = (distance: number): string => {
  if (distance === 0) return 'Local'
  return `${distance.toFixed(1)} miles`
}

const extractMiles = (description: string): string => {
  // Look for patterns like "123K miles" or "12345 miles" in the description
  const milesMatch = description.match(/(\d+\.?\d*[Kk]?\s*miles)/i)
  if (milesMatch) {
    return milesMatch[0]
  }
  return ''
}

const onImageLoad = (event: Event) => {
  const img = event.target as HTMLImageElement
  
  if (img) {
    // Add fade-in effect for smoother loading
    img.style.opacity = '1'
    
    // For very wide or very tall images, adjust the object-fit
    if (img.naturalWidth > 0 && img.naturalHeight > 0) {
      const aspectRatio = img.naturalWidth / img.naturalHeight
      
      // Very wide or very tall images might need contain instead of cover
      if (aspectRatio > 3 || aspectRatio < 0.3) {
        img.classList.add('object-contain', 'p-1')
        img.classList.remove('object-cover')
      }
    }
  }
}

const handleImageError = (event: Event) => {
  // Replace broken image with placeholder
  const imgElement = event.target as HTMLImageElement
  imgElement.src = 'https://via.placeholder.com/300x200?text=No+Image'
  imgElement.classList.add('object-contain', 'p-2')
  imgElement.classList.remove('object-cover')
  
  // Optionally log the error
  console.warn(`Failed to load image for listing: ${props.listing.title}`)
}
</script>

<style scoped>
/* Image transitions */
img {
  opacity: 0;
  transition: opacity 0.3s ease-in-out;
}
</style>
