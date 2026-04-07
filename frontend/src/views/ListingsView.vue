<template>
  <div class="w-full relative">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-xl font-bold uppercase tracking-wide text-white">Listings</h2>
      <div class="flex space-x-2">
        <BaseButton
          @click="toggleNotifyFilter"
          :variant="filters.notify_only ? 'primary' : 'secondary'"
          class="flex items-center"
        >
          <span class="mr-1 text-sm" :class="filters.notify_only ? 'text-white' : 'text-gray-400'">●</span>
          Notify
        </BaseButton>
        <BaseButton 
          @click="toggleFiltersVisible" 
          :variant="filtersVisible ? 'primary' : 'secondary'"
          class="flex items-center"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Filters
        </BaseButton>
      </div>
    </div>
    
    <!-- Filters Sidebar -->
    <ListingFilters 
      :show="filtersVisible"
      :filters="filters"
      :filter-options="filterOptions"
      @close="toggleFiltersVisible"
      @apply="handleApplyFilters"
      @reset="resetFilters"
    />
    
    <!-- Status Messages -->
    <div v-if="successMessage" class="bg-green-500 bg-opacity-10 text-green-500 p-4 rounded-md mb-4">
      {{ successMessage }}
    </div>
    
    <div v-if="error" class="bg-red-500 bg-opacity-10 text-red-500 p-4 rounded-md mb-4">
      {{ error }}
    </div>
    
    <!-- Active Filters Display -->
    <ActiveFiltersBar
      :filters="filters"
      :filter-options="filterOptions"
      @remove-filter="removeFilter"
      @clear-all="resetFilters"
    />
    
    <!-- Loading State -->
    <div v-if="isLoading" class="text-center py-8">
      <p class="text-gray-400">Loading listings...</p>
    </div>
    
    <!-- Empty State -->
    <div v-else-if="listings.length === 0" class="text-center py-8 text-gray-400">
      No listings found.
    </div>
    
    <!-- Listings Grid -->
    <div v-else class="grid grid-cols-3 sm:grid-cols-5 lg:grid-cols-8 gap-3">
      <ListingCard
        v-for="listing in listings"
        :key="listing.listing_idx"
        :listing="listing"
        @analyze-ai="openAIAnalysis"
      />
    </div>
    
    <!-- AI Analysis Modal -->
    <AIAnalysisModal
      :show="showAIModal"
      :listing="selectedListingForAI"
      @close="closeAIModal"
      @analyzed="handleAIAnalyzed"
    />
    
    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex justify-center mt-6 space-x-2">
      <BaseButton 
        @click="prevPage" 
        :disabled="currentPage === 1"
        variant="secondary"
      >
        Previous
      </BaseButton>
      
      <span class="px-3 py-2 text-gray-300 flex items-center">{{ currentPage }} / {{ totalPages }}</span>
      
      <BaseButton 
        @click="nextPage" 
        :disabled="currentPage === totalPages"
        variant="secondary"
      >
        Next
      </BaseButton>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { onMounted, onUnmounted } from 'vue'
import { useListingStore } from '@/stores/listingStore'
import BaseButton from '@/components/ui/BaseButton.vue'
import ListingCard from '@/components/features/listings/ListingCard.vue'
import ListingFilters from '@/components/features/listings/ListingFilters.vue'
import ActiveFiltersBar from '@/components/features/listings/ActiveFiltersBar.vue'
import AIAnalysisModal from '@/components/features/ai/AIAnalysisModal.vue'
import type { Listing } from '@/types/index'
import type { ListingFilters as IListingFilters } from '@/services/api'

// Store and composables
const listingStore = useListingStore()

// AI Analysis Modal state
const showAIModal = ref(false)
const selectedListingForAI = ref<Listing | null>(null)

const openAIAnalysis = (listing: Listing) => {
  selectedListingForAI.value = listing
  showAIModal.value = true
}

const closeAIModal = () => {
  showAIModal.value = false
  selectedListingForAI.value = null
}

const handleAIAnalyzed = (listing: Listing, result: any) => {
  // Update the listing with the analysis result
  console.log('✅ AI Analysis complete:', listing.title, result.recommendation)
  
  // Find and update the listing in our local state
  const index = listings.value.findIndex(l => l.listing_idx === listing.listing_idx)
  if (index !== -1) {
    listings.value[index] = {
      ...listings.value[index],
      analysis_metadata: {
        ...listings.value[index].analysis_metadata,
        llm_analysis: result
      }
    }
  }
}

// Reactive state from store
const { 
  listings,
  currentPage,
  totalPages,
  isLoading,
  error,
  successMessage,
  filters,
  filtersVisible,
  filterOptions
} = storeToRefs(listingStore)

// Methods
const toggleNotifyFilter = () => {
  listingStore.toggleNotifyFilter()
}

const toggleFiltersVisible = () => {
  listingStore.toggleFiltersVisible()
}

const handleApplyFilters = (newFilters: IListingFilters) => {
  listingStore.tempFilters = newFilters
  listingStore.applyFilters()
}

const resetFilters = () => {
  listingStore.resetFilters()
}

const removeFilter = (key: keyof IListingFilters) => {
  listingStore.removeFilter(key)
}

const nextPage = () => {
  listingStore.nextPage()
}

const prevPage = () => {
  listingStore.prevPage()
}

// Add keydown event to close filter panel with Escape key
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && filtersVisible.value) {
    listingStore.toggleFiltersVisible()
  }
}

// Lifecycle
onMounted(() => {
  // Fetch filter options first
  listingStore.fetchFilterOptions()
  
  // Then fetch listings
  listingStore.fetchListings()
  
  // Add event listener for Escape key
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})
</script>