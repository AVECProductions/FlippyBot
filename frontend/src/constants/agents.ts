/**
 * Agent utilities - agents are fetched from the API via agentStore.
 * This file provides a fallback lookup for components that need agent info by slug.
 */
import type { AgentInfo, AgentType } from '@/types'

export const getAgentInfo = (agentType: AgentType): AgentInfo => {
  return {
    type: agentType,
    slug: agentType,
    name: agentType,
    description: '',
    enabled: false,
    icon: ''
  }
}
