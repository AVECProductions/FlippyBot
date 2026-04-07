import { ref, computed, watch } from 'vue'

export interface PaginationOptions {
  initialPage?: number
  initialPageSize?: number
  maxPageSize?: number
  minPageSize?: number
}

export interface PaginationData {
  currentPage: number
  pageSize: number
  totalItems: number
  totalPages: number
  hasNext: boolean
  hasPrevious: boolean
}

export const usePagination = (options: PaginationOptions = {}) => {
  const {
    initialPage = 1,
    initialPageSize = 20,
    maxPageSize = 100,
    minPageSize = 10
  } = options

  // State
  const currentPage = ref(initialPage)
  const pageSize = ref(initialPageSize)
  const totalItems = ref(0)
  const totalPages = ref(0)

  // Computed properties
  const hasNext = computed(() => currentPage.value < totalPages.value)
  const hasPrevious = computed(() => currentPage.value > 1)
  
  const startItem = computed(() => {
    return totalItems.value === 0 ? 0 : (currentPage.value - 1) * pageSize.value + 1
  })
  
  const endItem = computed(() => {
    const end = currentPage.value * pageSize.value
    return Math.min(end, totalItems.value)
  })

  const paginationInfo = computed(() => ({
    currentPage: currentPage.value,
    pageSize: pageSize.value,
    totalItems: totalItems.value,
    totalPages: totalPages.value,
    hasNext: hasNext.value,
    hasPrevious: hasPrevious.value,
    startItem: startItem.value,
    endItem: endItem.value
  }))

  // Page size validation
  const setPageSize = (size: number) => {
    const validSize = Math.max(minPageSize, Math.min(maxPageSize, size))
    pageSize.value = validSize
    
    // Reset to first page when page size changes
    currentPage.value = 1
  }

  // Navigation methods
  const goToPage = (page: number) => {
    if (page >= 1 && page <= totalPages.value) {
      currentPage.value = page
    }
  }

  const nextPage = () => {
    if (hasNext.value) {
      currentPage.value++
    }
  }

  const previousPage = () => {
    if (hasPrevious.value) {
      currentPage.value--
    }
  }

  const firstPage = () => {
    currentPage.value = 1
  }

  const lastPage = () => {
    currentPage.value = totalPages.value
  }

  // Update pagination data from API response
  const updateFromResponse = (response: {
    count?: number
    total_pages?: number
    current_page?: number
    has_next?: boolean
    has_previous?: boolean
  }) => {
    if (typeof response.count === 'number') {
      totalItems.value = response.count
    }
    
    if (typeof response.total_pages === 'number') {
      totalPages.value = response.total_pages
    }
    
    if (typeof response.current_page === 'number') {
      currentPage.value = response.current_page
    }
  }

  // Calculate total pages when total items or page size changes
  watch([totalItems, pageSize], () => {
    totalPages.value = Math.ceil(totalItems.value / pageSize.value)
    
    // Ensure current page is valid
    if (currentPage.value > totalPages.value && totalPages.value > 0) {
      currentPage.value = totalPages.value
    }
  }, { immediate: true })

  // Reset pagination
  const reset = () => {
    currentPage.value = initialPage
    pageSize.value = initialPageSize
    totalItems.value = 0
    totalPages.value = 0
  }

  // Generate page numbers for pagination controls
  const getPageNumbers = (maxVisible: number = 5) => {
    const pages: number[] = []
    const total = totalPages.value
    const current = currentPage.value
    
    if (total <= maxVisible) {
      // Show all pages if total is small
      for (let i = 1; i <= total; i++) {
        pages.push(i)
      }
    } else {
      // Show smart pagination with ellipsis
      const halfVisible = Math.floor(maxVisible / 2)
      let start = Math.max(1, current - halfVisible)
      let end = Math.min(total, current + halfVisible)
      
      // Adjust range if we're near the beginning or end
      if (end - start + 1 < maxVisible) {
        if (start === 1) {
          end = Math.min(total, start + maxVisible - 1)
        } else {
          start = Math.max(1, end - maxVisible + 1)
        }
      }
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
    }
    
    return pages
  }

  return {
    // State
    currentPage,
    pageSize,
    totalItems,
    totalPages,
    
    // Computed
    hasNext,
    hasPrevious,
    startItem,
    endItem,
    paginationInfo,
    
    // Methods
    setPageSize,
    goToPage,
    nextPage,
    previousPage,
    firstPage,
    lastPage,
    updateFromResponse,
    reset,
    getPageNumbers
  }
}
