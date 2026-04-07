import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { 
  getScanners, 
  createScanner, 
  updateScanner, 
  deleteScanner, 
  toggleScannerStatus,
  getKeywordsByScanner,
  updateKeywords,
  getLocations,
  createLocation
} from '@/services/api'
import type { Scanner } from '@/types'

export const useScannerStore = defineStore('scanner', () => {
  // State
  const scanners = ref<Scanner[]>([])
  const locations = ref<any[]>([])
  const selectedScanner = ref<Scanner | null>(null)
  const keywords = ref<string[]>([])
  
  const isLoading = ref(false)
  const isCreating = ref(false)
  const isUpdating = ref(false)
  const isDeleting = ref(false)
  const isSavingKeywords = ref(false)
  const isCreatingLocation = ref(false)
  
  const error = ref<string | null>(null)
  const successMessage = ref<string | null>(null)

  // Getters
  const groupedScanners = computed(() => {
    const grouped: Record<string, Record<string, Scanner[]>> = {}
    
    scanners.value.forEach(scanner => {
      // If scanner has locations_data, use those locations
      if (scanner.locations_data && scanner.locations_data.length > 0) {
        scanner.locations_data.forEach((locationMapping: any) => {
          const town = locationMapping.location_name
          const category = scanner.category || 'Uncategorized'
          
          if (!grouped[town]) {
            grouped[town] = {}
          }
          
          if (!grouped[town][category]) {
            grouped[town][category] = []
          }
          
          // Check if scanner is already in this town's category
          const alreadyExists = grouped[town][category].some(s => s.id === scanner.id)
          if (!alreadyExists) {
            grouped[town][category].push(scanner)
          }
        })
      } 
      // Fallback to town field for backward compatibility
      else if (scanner.town) {
        const town = scanner.town
        const category = scanner.category || 'Uncategorized'
        
        if (!grouped[town]) {
          grouped[town] = {}
        }
        
        if (!grouped[town][category]) {
          grouped[town][category] = []
        }
        
        grouped[town][category].push(scanner)
      }
      // If no location data at all, put in "Unknown" group
      else {
        const town = 'Unknown'
        const category = scanner.category || 'Uncategorized'
        
        if (!grouped[town]) {
          grouped[town] = {}
        }
        
        if (!grouped[town][category]) {
          grouped[town][category] = []
        }
        
        grouped[town][category].push(scanner)
      }
    })
    
    return grouped
  })

  // Group scanners by agent type/slug (dynamic - supports user-created agents)
  const scannersByAgent = computed(() => {
    const grouped: Record<string, Scanner[]> = {}
    
    scanners.value.forEach(scanner => {
      // Use agent_slug if available, fall back to agent_type
      const agentKey = scanner.agent_slug || scanner.agent_type || 'skis'
      if (!grouped[agentKey]) {
        grouped[agentKey] = []
      }
      grouped[agentKey].push(scanner)
    })
    
    return grouped
  })

  const selectedScannerLocations = computed(() => {
    if (selectedScanner.value?.locations_data) {
      return selectedScanner.value.locations_data
    }
    return []
  })

  // Actions
  const fetchScanners = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      scanners.value = await getScanners()
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch scanners'
    } finally {
      isLoading.value = false
    }
  }

  const fetchLocations = async () => {
    try {
      locations.value = await getLocations()
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch locations'
    }
  }

  const createNewScanner = async (scannerData: any, keywords: string[] = []) => {
    isCreating.value = true
    error.value = null
    
    try {
      const created = await createScanner(scannerData)
      if (created) {
        // If scanner created successfully, add any keywords
        const filteredKeywords = keywords.filter(k => k.trim() !== '')
        if (filteredKeywords.length > 0) {
          await updateKeywords(created.id, filteredKeywords)
        }
        
        successMessage.value = 'Scanner created successfully'
        await fetchScanners()
        return created
      }
      return null
    } catch (err: any) {
      error.value = err.message || 'Failed to create scanner'
      throw err
    } finally {
      isCreating.value = false
    }
  }

  const updateExistingScanner = async (id: number, scannerData: Partial<Scanner>) => {
    isUpdating.value = true
    error.value = null
    
    try {
      const updated = await updateScanner(id, scannerData)
      if (updated) {
        successMessage.value = 'Scanner updated successfully'
        await fetchScanners()
        
        // Update selectedScanner if it was the one being updated
        if (selectedScanner.value?.id === id) {
          selectedScanner.value = scanners.value.find(s => s.id === id) || null
        }
        
        return updated
      }
      return null
    } catch (err: any) {
      error.value = err.message || 'Failed to update scanner'
      throw err
    } finally {
      isUpdating.value = false
    }
  }

  const toggleStatus = async (id: number, currentStatus: string) => {
    try {
      const updated = await toggleScannerStatus(id, currentStatus)
      if (updated) {
        successMessage.value = `Scanner ${updated.status === 'running' ? 'started' : 'stopped'} successfully`
        await fetchScanners()
        
        // Update selectedScanner if it was the one being updated
        if (selectedScanner.value?.id === id) {
          selectedScanner.value = scanners.value.find(s => s.id === id) || null
        }
        
        return updated
      }
      return null
    } catch (err: any) {
      error.value = err.message || 'Failed to toggle scanner status'
      throw err
    }
  }

  const deleteExistingScanner = async (id: number) => {
    isDeleting.value = true
    error.value = null
    
    try {
      const success = await deleteScanner(id)
      if (success) {
        successMessage.value = 'Scanner deleted successfully'
        await fetchScanners()
        
        // Clear selectedScanner if it was the one being deleted
        if (selectedScanner.value?.id === id) {
          selectedScanner.value = null
        }
        
        return true
      }
      return false
    } catch (err: any) {
      error.value = err.message || 'Failed to delete scanner'
      throw err
    } finally {
      isDeleting.value = false
    }
  }

  const selectScanner = async (scanner: Scanner) => {
    selectedScanner.value = scanner
    await fetchKeywordsForScanner(scanner.id)
  }

  const clearSelectedScanner = () => {
    selectedScanner.value = null
    keywords.value = []
  }

  const fetchKeywordsForScanner = async (scannerId: number) => {
    try {
      const keywordData = await getKeywordsByScanner(scannerId)
      
      if (Array.isArray(keywordData)) {
        keywords.value = keywordData.map((k: any) => k.keyword || '').filter(k => k.trim() !== '')
      } else {
        keywords.value = []
      }
    } catch (err: any) {
      console.error('Failed to fetch keywords:', err)
      keywords.value = []
    }
  }

  const saveKeywordsForScanner = async (scannerId: number, keywordList: string[]) => {
    isSavingKeywords.value = true
    error.value = null
    
    try {
      const filteredKeywords = keywordList.filter(k => k.trim() !== '')
      await updateKeywords(scannerId, filteredKeywords)
      
      successMessage.value = 'Keywords updated successfully'
      keywords.value = [...filteredKeywords]
    } catch (err: any) {
      error.value = err.message || 'Failed to update keywords'
      throw err
    } finally {
      isSavingKeywords.value = false
    }
  }

  const createNewLocation = async (locationData: { name: string; marketplace_url_slug: string }) => {
    isCreatingLocation.value = true
    error.value = null
    
    try {
      const created = await createLocation(locationData)
      if (created) {
        successMessage.value = 'Location created successfully'
        await fetchLocations()
        return created
      }
      return null
    } catch (err: any) {
      error.value = err.message || 'Failed to create location'
      throw err
    } finally {
      isCreatingLocation.value = false
    }
  }

  // Utility actions
  const clearMessages = () => {
    error.value = null
    successMessage.value = null
  }

  const setSuccessMessage = (message: string) => {
    successMessage.value = message
    setTimeout(() => {
      successMessage.value = null
    }, 3000)
  }

  const setError = (message: string) => {
    error.value = message
    setTimeout(() => {
      error.value = null
    }, 3000)
  }

  return {
    // State
    scanners,
    locations,
    selectedScanner,
    keywords,
    isLoading,
    isCreating,
    isUpdating,
    isDeleting,
    isSavingKeywords,
    isCreatingLocation,
    error,
    successMessage,
    
    // Getters
    groupedScanners,
    scannersByAgent,
    selectedScannerLocations,
    
    // Actions
    fetchScanners,
    fetchLocations,
    createNewScanner,
    updateExistingScanner,
    toggleStatus,
    deleteExistingScanner,
    selectScanner,
    clearSelectedScanner,
    fetchKeywordsForScanner,
    saveKeywordsForScanner,
    createNewLocation,
    clearMessages,
    setSuccessMessage,
    setError
  }
})
