import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { getListings, toggleWatchlist, getFilterOptions } from '@/services/api'
import { useApi } from '@/composables/useApi'
import { usePagination } from '@/composables/usePagination'
import { useNotifications } from '@/composables/useNotifications'
import type { Listing } from '@/types/index'
import type { ListingFilters } from '@/services/api'

export const useListingStore = defineStore('listing', () => {
  // Composables
  const api = useApi()
  const pagination = usePagination({ initialPageSize: 20 })
  const { notifySuccess, notifyError } = useNotifications()
  
  // State
  const listings = ref<Listing[]>([])
  const successMessage = ref<string | null>(null)
  
  // Filter state
  const filters = ref<ListingFilters>({})
  const tempFilters = ref<ListingFilters>({})
  const filtersVisible = ref(false)
  
  // Filter options
  const filterOptions = ref({
    search_locations: [] as string[],
    agents: [] as { slug: string; name: string }[],
    scanners: [] as { id: number; query: string; agent_slug: string }[],
  })

  // Getters
  const isLoading = computed(() => api.isLoading.value)
  const error = computed(() => api.error.value)
  const totalPages = computed(() => pagination.totalPages.value)
  const currentPage = computed(() => pagination.currentPage.value)
  const totalItems = computed(() => pagination.totalItems.value)
  
  const hasActiveFilters = computed(() => {
    return Object.values(filters.value).some(value => 
      value !== undefined && value !== null && value !== ''
    )
  })

  // Actions
  const fetchListings = async () => {
    const data = await api.call(
      () => getListings(pagination.currentPage.value, pagination.pageSize.value, filters.value),
      { showErrorMessage: true }
    )
    
    if (data) {
      listings.value = data.results || []
      pagination.updateFromResponse(data)
    }
  }

  const fetchFilterOptions = async () => {
    const options = await api.call(
      () => getFilterOptions(),
      { silent: true }
    )
    
    if (options) {
      filterOptions.value = options
    }
  }

  const toggleListingWatchlist = async (listing: Listing) => {
    const isAdding = !listing.watchlist
    const message = `Listing ${isAdding ? 'added to' : 'removed from'} watchlist`
    
    const updated = await api.call(
      () => toggleWatchlist(listing.listing_idx, listing.watchlist),
      { 
        showSuccessMessage: true,
        successMessage: message,
        errorMessage: 'Failed to update watchlist'
      }
    )
    
    if (updated) {
      // Update the listing in our local state
      const index = listings.value.findIndex((l: Listing) => l.listing_idx === listing.listing_idx)
      if (index !== -1) {
        listings.value[index].watchlist = isAdding
      }
    }
  }

  const applyFilters = () => {
    // Copy temp filters to active filters
    filters.value = { ...tempFilters.value }
    pagination.firstPage()
    fetchListings()
    filtersVisible.value = false
  }

  const resetFilters = () => {
    filters.value = {}
    tempFilters.value = {}
    pagination.firstPage()
    fetchListings()
  }

  const removeFilter = (key: keyof ListingFilters) => {
    // Create a new object without the specified filter
    const { [key]: _, ...rest } = filters.value
    filters.value = rest
    tempFilters.value = { ...filters.value }
    pagination.firstPage()
    fetchListings()
  }

  const toggleNotifyFilter = () => {
    if (filters.value.notify_only) {
      const { notify_only, ...rest } = filters.value
      filters.value = rest
    } else {
      filters.value = { ...filters.value, notify_only: true }
    }
    tempFilters.value = { ...filters.value }
    pagination.firstPage()
    fetchListings()
  }

  const toggleFiltersVisible = () => {
    filtersVisible.value = !filtersVisible.value
    
    // When showing filters, initialize temp filters with current values
    if (filtersVisible.value) {
      tempFilters.value = { ...filters.value }
    }
  }

  const goToPage = (page: number) => {
    pagination.goToPage(page)
    fetchListings()
  }
  
  const nextPage = () => {
    pagination.nextPage()
    fetchListings()
  }
  
  const prevPage = () => {
    pagination.previousPage()
    fetchListings()
  }

  // Utility actions
  const clearMessages = () => {
    api.clearError()
    successMessage.value = null
  }
  
  // Watch for filter changes to auto-refetch
  watch(filters, () => {
    pagination.firstPage()
    fetchListings()
  }, { deep: true })

  return {
    // State
    listings,
    isLoading,
    error,
    successMessage,
    filters,
    tempFilters,
    filtersVisible,
    filterOptions,
    
    // Pagination (exposed from composable)
    currentPage,
    totalItems,
    totalPages,
    hasNext: pagination.hasNext,
    hasPrevious: pagination.hasPrevious,
    
    // Getters
    hasActiveFilters,
    
    // Actions
    fetchListings,
    fetchFilterOptions,
    toggleListingWatchlist,
    applyFilters,
    resetFilters,
    removeFilter,
    toggleNotifyFilter,
    toggleFiltersVisible,
    nextPage,
    prevPage,
    goToPage,
    clearMessages
  }
})