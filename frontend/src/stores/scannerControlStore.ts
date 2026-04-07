import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useScannerControlStore = defineStore('scannerControl', () => {
  // State
  const isControlPanelOpen = ref(false)
  const selectedScannerId = ref<number | null>(null)
  
  // Actions
  const openControlPanel = (scannerId?: number) => {
    isControlPanelOpen.value = true
    if (scannerId) {
      selectedScannerId.value = scannerId
    }
  }
  
  const closeControlPanel = () => {
    isControlPanelOpen.value = false
    selectedScannerId.value = null
  }
  
  const selectScanner = (scannerId: number) => {
    selectedScannerId.value = scannerId
  }
  
  return {
    // State
    isControlPanelOpen,
    selectedScannerId,
    
    // Actions
    openControlPanel,
    closeControlPanel,
    selectScanner
  }
})