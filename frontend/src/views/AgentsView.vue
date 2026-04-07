<template>
  <div class="max-w-5xl mx-auto">
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-sm font-medium uppercase tracking-widest text-gray-400">Agents</h2>
      </div>
      <div class="flex items-center space-x-2">
        <button
          @click="handleCreateAgent()"
          class="text-xs text-gray-500 hover:text-gray-300 px-3 py-1.5 border border-gray-800 rounded hover:border-gray-700 transition-colors"
        >
          + New Agent
        </button>
      </div>
    </div>
    
    <!-- Status Messages -->
    <div v-if="successMessage || agentSuccessMessage" class="text-xs text-emerald-500/80 bg-emerald-500/5 border border-emerald-500/10 px-4 py-2.5 rounded mb-4">
      {{ successMessage || agentSuccessMessage }}
    </div>
    
    <div v-if="error || agentError" class="text-xs text-red-400/80 bg-red-500/5 border border-red-500/10 px-4 py-2.5 rounded mb-4">
      {{ error || agentError }}
    </div>
    
    <!-- Loading State -->
    <div v-if="isLoading || agentIsLoading" class="text-center py-16">
      <p class="text-xs text-gray-600">Loading...</p>
    </div>
    
    <!-- Agents List -->
    <div v-else>
      <div 
        v-if="displayedAgents.length > 0" 
        class="border border-gray-800/60 rounded-lg overflow-hidden bg-[#0a0a0a]"
      >
        <AgentCard 
          v-for="agentInfo in displayedAgents" 
          :key="agentInfo.slug || agentInfo.type"
          :agent-info="agentInfo"
          :queries="scannersByAgent[agentInfo.slug || agentInfo.type] || []"
          @add-query="handleAddQuery(agentInfo.slug || agentInfo.type)"
          @edit-agent="handleEditAgent(agentInfo)"
          @analyze-url="handleAnalyzeUrl(agentInfo)"
          @delete-agent="handleDeleteAgent(agentInfo)"
          @edit-query="handleEditQuery"
          @delete-query="handleDeleteQuery"
          @toggle-query-status="handleToggleStatus"
        />
      </div>
      
      <!-- Empty state -->
      <div v-else class="text-center py-20">
        <p class="text-sm text-gray-600 mb-4">No agents configured</p>
        <button
          @click="handleCreateAgent()"
          class="text-xs text-gray-500 hover:text-gray-300 px-3 py-1.5 border border-gray-800 rounded hover:border-gray-700 transition-colors"
        >
          + Create Agent
        </button>
      </div>
    </div>
    
    <!-- Agent Editor Modal -->
    <AgentEditorModal
      :show="agentEditorModal.isOpen.value"
      :agent="agentToEdit"
      @close="agentEditorModal.close()"
      @saved="handleAgentSaved"
      @deleted="handleAgentDeleted"
    />
    
    <!-- Add Query Modal -->
    <AddScannerModalSimple
      :show="addQueryModal.isOpen.value"
      :agent-type="selectedAgentType"
      @close="addQueryModal.close()"
      @created="handleQueryCreated"
      @create-location="locationModal.open()"
    />
    
    <!-- Edit Query Modal -->
    <EditScannerModalSimple
      :show="editModal.isOpen.value"
      :scanner="selectedScanner"
      @close="editModal.close()"
      @updated="handleQueryUpdated"
      @deleted="handleQueryDeleted"
    />
    
    <!-- Create Location Modal -->
    <CreateLocationModal 
      :show="locationModal.isOpen.value"
      @close="locationModal.close()"
      @created="handleLocationCreated"
    />
    
    <!-- URL Analysis Modal -->
    <UrlAnalysisModal
      :show="urlAnalysisModal.isOpen.value"
      :agent-slug="selectedAnalysisAgent?.slug || selectedAnalysisAgent?.type || ''"
      :agent-name="selectedAnalysisAgent?.name"
      @close="urlAnalysisModal.close()"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useScannerStore } from '@/stores/scannerStore'
import { useAgentStore } from '@/stores/agentStore'
import { useModal } from '@/composables/useModal'
import AgentCard from '@/components/features/agents/AgentCard.vue'
import AgentEditorModal from '@/components/features/agents/AgentEditorModal.vue'
import UrlAnalysisModal from '@/components/features/agents/UrlAnalysisModal.vue'
import AddScannerModalSimple from '@/components/features/scanners/AddScannerModal_Simple.vue'
import EditScannerModalSimple from '@/components/features/scanners/EditScannerModal_Simple.vue'
import CreateLocationModal from '@/components/features/scanners/CreateLocationModal.vue'
import type { Scanner, AgentInfo, AgentType } from '@/types'

// Stores and composables
const scannerStore = useScannerStore()
const agentStore = useAgentStore()
const addQueryModal = useModal()
const editModal = useModal()
const locationModal = useModal()
const agentEditorModal = useModal()
const urlAnalysisModal = useModal()

// Reactive state from stores
const { 
  scannersByAgent,
  selectedScanner,
  isLoading, 
  error, 
  successMessage 
} = storeToRefs(scannerStore)

const {
  agents,
  isLoading: agentIsLoading,
  error: agentError,
  successMessage: agentSuccessMessage
} = storeToRefs(agentStore)

// Local state
const selectedAgentType = ref<AgentType>('skis')
const agentToEdit = ref<AgentInfo | null>(null)
const selectedAnalysisAgent = ref<AgentInfo | null>(null)

// Computed
const displayedAgents = computed(() => {
  return agents.value
})

// Methods
const handleCreateAgent = () => {
  agentToEdit.value = null
  agentEditorModal.open()
}

const handleEditAgent = async (agentInfo: AgentInfo) => {
  const fullAgent = await agentStore.fetchAgentDetail(agentInfo.slug || agentInfo.type)
  agentToEdit.value = fullAgent
  agentEditorModal.open()
}

const handleAgentSaved = async (agent: AgentInfo) => {
  agentEditorModal.close()
  await agentStore.fetchAgents()
  scannerStore.setSuccessMessage(`Agent "${agent.name}" saved successfully`)
}

const handleAgentDeleted = async (slug: string) => {
  agentEditorModal.close()
  await agentStore.fetchAgents()
  scannerStore.setSuccessMessage('Agent deleted successfully')
}

const handleDeleteAgent = async (agentInfo: AgentInfo) => {
  const queryCount = (scannersByAgent.value[agentInfo.slug || agentInfo.type] || []).length
  const warning = queryCount > 0 ? ` This will also delete its ${queryCount} ${queryCount === 1 ? 'query' : 'queries'}.` : ''
  if (!confirm(`Delete agent "${agentInfo.name}"?${warning}`)) return
  try {
    await agentStore.deleteExistingAgent(agentInfo.slug || agentInfo.type)
    await Promise.all([agentStore.fetchAgents(), scannerStore.fetchScanners()])
    scannerStore.setSuccessMessage(`Agent "${agentInfo.name}" deleted`)
  } catch (err) {
    console.error('Failed to delete agent:', err)
  }
}

const handleAnalyzeUrl = (agentInfo: AgentInfo) => {
  selectedAnalysisAgent.value = agentInfo
  urlAnalysisModal.open()
}

const handleAddQuery = (agentType: AgentType) => {
  selectedAgentType.value = agentType
  addQueryModal.open()
}

const handleEditQuery = (scanner: Scanner) => {
  scannerStore.selectScanner(scanner)
  editModal.open()
}

const handleDeleteQuery = async (scanner: Scanner) => {
  if (confirm(`Delete query "${scanner.query}"?`)) {
    try {
      await scannerStore.deleteExistingScanner(scanner.id)
    } catch (err) {
      console.error('Failed to delete query:', err)
    }
  }
}

const handleToggleStatus = async (scanner: Scanner) => {
  try {
    await scannerStore.toggleStatus(scanner.id, scanner.status)
  } catch (err) {
    console.error('Failed to toggle query status:', err)
  }
}

const handleQueryCreated = () => {
  addQueryModal.close()
  scannerStore.setSuccessMessage('Query created successfully')
}

const handleQueryUpdated = () => {
  editModal.close()
  scannerStore.setSuccessMessage('Query updated successfully')
}

const handleQueryDeleted = () => {
  editModal.close()
  scannerStore.setSuccessMessage('Query deleted successfully')
}

const handleLocationCreated = () => {
  locationModal.close()
  scannerStore.setSuccessMessage('Location created successfully')
}

// Initialize data
onMounted(async () => {
  await Promise.all([
    agentStore.fetchAgents(),
    scannerStore.fetchScanners(),
    scannerStore.fetchLocations(),
  ])
})
</script>
