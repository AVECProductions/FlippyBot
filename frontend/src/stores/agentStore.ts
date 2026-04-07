import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getAgents,
  getAgent,
  createAgent,
  updateAgent,
  deleteAgent,
  duplicateAgent,
  generateAgentPrompt,
  refineAgentPrompt,
} from '@/services/api'
import type { AgentInfo, AgentFormData, GeneratePromptResponse, RefinePromptResponse } from '@/types'

export const useAgentStore = defineStore('agent', () => {
  // State
  const agents = ref<AgentInfo[]>([])
  const selectedAgent = ref<AgentInfo | null>(null)
  
  const isLoading = ref(false)
  const isSaving = ref(false)
  const isGenerating = ref(false)
  
  const error = ref<string | null>(null)
  const successMessage = ref<string | null>(null)

  // Getters
  const enabledAgents = computed(() => {
    return agents.value.filter(a => a.enabled)
  })

  const agentsBySlug = computed(() => {
    const map: Record<string, AgentInfo> = {}
    agents.value.forEach(a => {
      map[a.slug || a.type] = a
    })
    return map
  })

  // Actions
  const fetchAgents = async () => {
    isLoading.value = true
    error.value = null
    
    try {
      agents.value = await getAgents()
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch agents'
    } finally {
      isLoading.value = false
    }
  }

  const fetchAgentDetail = async (slug: string) => {
    isLoading.value = true
    error.value = null
    
    try {
      const agent = await getAgent(slug)
      if (agent) {
        selectedAgent.value = agent
        // Also update in the agents list
        const idx = agents.value.findIndex(a => (a.slug || a.type) === slug)
        if (idx >= 0) {
          agents.value[idx] = agent
        }
      }
      return agent
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch agent detail'
      return null
    } finally {
      isLoading.value = false
    }
  }

  const createNewAgent = async (data: AgentFormData) => {
    isSaving.value = true
    error.value = null
    
    try {
      const created = await createAgent(data)
      if (created) {
        agents.value.push(created)
        setSuccessMessage('Agent created successfully')
        return created
      }
      return null
    } catch (err: any) {
      error.value = err.message || 'Failed to create agent'
      throw err
    } finally {
      isSaving.value = false
    }
  }

  const updateExistingAgent = async (slug: string, data: Partial<AgentFormData>) => {
    isSaving.value = true
    error.value = null
    
    try {
      const updated = await updateAgent(slug, data)
      if (updated) {
        const idx = agents.value.findIndex(a => (a.slug || a.type) === slug)
        if (idx >= 0) {
          agents.value[idx] = updated
        }
        if (selectedAgent.value && (selectedAgent.value.slug || selectedAgent.value.type) === slug) {
          selectedAgent.value = updated
        }
        setSuccessMessage('Agent updated successfully')
        return updated
      }
      return null
    } catch (err: any) {
      error.value = err.message || 'Failed to update agent'
      throw err
    } finally {
      isSaving.value = false
    }
  }

  const deleteExistingAgent = async (slug: string) => {
    isSaving.value = true
    error.value = null
    
    try {
      await deleteAgent(slug)
      agents.value = agents.value.filter(a => (a.slug || a.type) !== slug)
      if (selectedAgent.value && (selectedAgent.value.slug || selectedAgent.value.type) === slug) {
        selectedAgent.value = null
      }
      setSuccessMessage('Agent deleted successfully')
      return true
    } catch (err: any) {
      error.value = err.message || 'Failed to delete agent'
      throw err
    } finally {
      isSaving.value = false
    }
  }

  const duplicateExistingAgent = async (slug: string) => {
    isSaving.value = true
    error.value = null
    
    try {
      const duplicated = await duplicateAgent(slug)
      if (duplicated) {
        agents.value.push(duplicated)
        setSuccessMessage('Agent duplicated successfully')
        return duplicated
      }
      return null
    } catch (err: any) {
      error.value = err.message || 'Failed to duplicate agent'
      throw err
    } finally {
      isSaving.value = false
    }
  }

  const generatePrompts = async (description: string): Promise<GeneratePromptResponse | null> => {
    isGenerating.value = true
    error.value = null
    
    try {
      const result = await generateAgentPrompt({ description })
      return result
    } catch (err: any) {
      error.value = err.message || 'Failed to generate prompts'
      throw err
    } finally {
      isGenerating.value = false
    }
  }

  const refinePrompts = async (
    currentTriagePrompt: string,
    currentAnalysisPrompt: string,
    feedback: string
  ): Promise<RefinePromptResponse | null> => {
    isGenerating.value = true
    error.value = null
    
    try {
      const result = await refineAgentPrompt({
        current_triage_prompt: currentTriagePrompt,
        current_analysis_prompt: currentAnalysisPrompt,
        feedback,
      })
      return result
    } catch (err: any) {
      error.value = err.message || 'Failed to refine prompts'
      throw err
    } finally {
      isGenerating.value = false
    }
  }

  // Utility
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
    }, 5000)
  }

  const clearMessages = () => {
    error.value = null
    successMessage.value = null
  }

  return {
    // State
    agents,
    selectedAgent,
    isLoading,
    isSaving,
    isGenerating,
    error,
    successMessage,
    
    // Getters
    enabledAgents,
    agentsBySlug,
    
    // Actions
    fetchAgents,
    fetchAgentDetail,
    createNewAgent,
    updateExistingAgent,
    deleteExistingAgent,
    duplicateExistingAgent,
    generatePrompts,
    refinePrompts,
    clearMessages,
    setSuccessMessage,
    setError,
  }
})
