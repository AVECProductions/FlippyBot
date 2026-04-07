<template>
  <BaseModal
    :show="show"
    :title="isEditing ? 'Edit Agent' : 'Create Agent'"
    size="xl"
    @close="$emit('close')"
  >
    <div class="space-y-6">
      <!-- AI Builder Section -->
      <div class="bg-purple-900/20 border border-purple-500/30 rounded-lg p-4">
        <h4 class="text-sm font-semibold text-purple-300 mb-2">AI Prompt Builder</h4>
        <p class="text-xs text-gray-400 mb-3">
          Describe what you want this agent to look for and AI will generate the prompts for you.
        </p>
        <div class="flex items-end space-x-2">
          <textarea
            ref="aiTextarea"
            v-model="aiDescription"
            :placeholder="isEditing ? 'Describe changes you want...' : 'e.g. Find undervalued vintage guitars on marketplace...'"
            class="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none resize-none overflow-y-auto"
            style="min-height: 38px; max-height: 150px;"
            rows="1"
            @input="autoResize"
            @keydown.enter.exact.prevent="handleAIGenerate"
          ></textarea>
          <button
            @click="handleAIGenerate"
            :disabled="!aiDescription.trim() || isGenerating"
            class="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm font-medium rounded transition-colors flex items-center space-x-1 flex-shrink-0"
          >
            <svg v-if="isGenerating" class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
            </svg>
            <span>{{ isEditing ? 'Refine' : 'Generate' }}</span>
          </button>
        </div>
        <p v-if="aiChangeSummary" class="mt-2 text-xs text-purple-300">{{ aiChangeSummary }}</p>
      </div>

      <!-- Basic Info -->
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Agent Name</label>
        <input
          v-model="form.name"
          type="text"
          placeholder="e.g. Vintage Guitar Specialist"
          class="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
        />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <!-- Slug -->
        <div>
          <label class="block text-xs font-medium text-gray-400 mb-1">Slug (URL identifier)</label>
          <input
            v-model="form.slug"
            type="text"
            placeholder="e.g. vintage-guitars"
            :disabled="isEditing"
            class="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none disabled:opacity-50"
          />
        </div>

        <!-- Enabled -->
        <div class="flex items-end">
          <label class="flex items-center space-x-2 cursor-pointer">
            <input
              v-model="form.enabled"
              type="checkbox"
              class="w-4 h-4 rounded border-gray-600 text-blue-600 focus:ring-blue-500 bg-gray-900"
            />
            <span class="text-sm text-gray-300">Agent Enabled</span>
          </label>
        </div>
      </div>

      <!-- Description -->
      <div>
        <label class="block text-xs font-medium text-gray-400 mb-1">Description</label>
        <input
          v-model="form.description"
          type="text"
          placeholder="Brief description shown on the agent card"
          class="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-white placeholder-gray-500 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
        />
      </div>

      <!-- Prompt Tabs -->
      <div>
        <div class="flex border-b border-gray-700 mb-3">
          <button
            @click="activeTab = 'triage'"
            :class="[
              'px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px',
              activeTab === 'triage'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            ]"
          >
            Triage Prompt (Pass 1)
          </button>
          <button
            @click="activeTab = 'analysis'"
            :class="[
              'px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px',
              activeTab === 'analysis'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            ]"
          >
            Analysis Prompt (Pass 2)
          </button>
        </div>

        <!-- Triage Prompt -->
        <div v-show="activeTab === 'triage'">
          <p class="text-xs text-gray-500 mb-2">
            System prompt for quick scanning (title + price + location only). Must tell the AI to respond with JSON array.
          </p>
          <textarea
            v-model="form.triage_prompt"
            rows="12"
            placeholder="You are a specialist conducting a quick triage of marketplace listings..."
            class="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none font-mono resize-y"
          ></textarea>
        </div>

        <!-- Analysis Prompt -->
        <div v-show="activeTab === 'analysis'">
          <p class="text-xs text-gray-500 mb-2">
            System prompt for deep analysis (full description + images). Must tell the AI to respond with JSON.
          </p>
          <textarea
            v-model="form.analysis_prompt"
            rows="12"
            placeholder="You are a specialist performing deep analysis of marketplace listings..."
            class="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none font-mono resize-y"
          ></textarea>
        </div>
      </div>

      <!-- Error -->
      <div v-if="localError" class="bg-red-500/10 border border-red-500/30 text-red-400 text-sm p-3 rounded">
        {{ localError }}
      </div>
    </div>

    <template #footer>
      <div class="flex justify-between items-center">
        <div>
          <button
            v-if="isEditing"
            @click="handleDelete"
            class="px-4 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded transition-colors"
          >
            Delete Agent
          </button>
        </div>
        <div class="flex space-x-3">
          <button
            @click="$emit('close')"
            class="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            @click="handleSave"
            :disabled="isSaving || !isValid"
            class="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm font-medium rounded transition-colors"
          >
            {{ isSaving ? 'Saving...' : (isEditing ? 'Save Changes' : 'Create Agent') }}
          </button>
        </div>
      </div>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAgentStore } from '@/stores/agentStore'
import BaseModal from '@/components/ui/BaseModal.vue'
import type { AgentInfo } from '@/types'

const props = defineProps<{
  show: boolean
  agent?: AgentInfo | null
}>()

const emit = defineEmits<{
  close: []
  saved: [agent: AgentInfo]
  deleted: [slug: string]
}>()

const agentStore = useAgentStore()

// Template refs
const aiTextarea = ref<HTMLTextAreaElement | null>(null)

// Local state
const activeTab = ref<'triage' | 'analysis'>('triage')
const aiDescription = ref('')
const aiChangeSummary = ref('')
const localError = ref<string | null>(null)
const isSaving = ref(false)
const isGenerating = ref(false)

const form = ref({
  name: '',
  slug: '',
  description: '',
  icon: '',
  triage_prompt: '',
  analysis_prompt: '',
  triage_model: 'gemini-2.5-pro',
  analysis_model: 'gemini-2.5-pro',
  enabled: true,
})

// Computed
const isEditing = computed(() => !!props.agent?.id)

const isValid = computed(() => {
  return form.value.name.trim() &&
         form.value.slug.trim() &&
         form.value.triage_prompt.trim() &&
         form.value.analysis_prompt.trim()
})

// Auto-resize the AI description textarea
function autoResize() {
  const el = aiTextarea.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 150) + 'px'
}

// Watch for agent changes (when opening edit)
watch(() => props.agent, (newAgent) => {
  if (newAgent) {
    form.value = {
      name: newAgent.name || '',
      slug: newAgent.slug || newAgent.type || '',
      description: newAgent.description || '',
      icon: newAgent.icon || '',
      triage_prompt: newAgent.triage_prompt || '',
      analysis_prompt: newAgent.analysis_prompt || '',
      triage_model: newAgent.triage_model || 'gemini-2.5-pro',
      analysis_model: newAgent.analysis_model || 'gemini-2.5-pro',
      enabled: newAgent.enabled ?? true,
    }
  } else {
    resetForm()
  }
  aiDescription.value = ''
  aiChangeSummary.value = ''
  localError.value = null
  activeTab.value = 'triage'
  if (aiTextarea.value) aiTextarea.value.style.height = 'auto'
}, { immediate: true })

// Watch show to reset on open
watch(() => props.show, (newShow) => {
  if (newShow && !props.agent) {
    resetForm()
  }
})

function resetForm() {
  form.value = {
    name: '',
    slug: '',
    description: '',
    icon: '',
    triage_prompt: '',
    analysis_prompt: '',
    triage_model: 'gemini-2.5-pro',
    analysis_model: 'gemini-2.5-pro',
    enabled: true,
  }
}

// Auto-generate slug from name
watch(() => form.value.name, (newName) => {
  if (!isEditing.value && newName) {
    form.value.slug = newName
      .toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')
  }
})

async function handleAIGenerate() {
  if (!aiDescription.value.trim()) return
  
  isGenerating.value = true
  localError.value = null
  aiChangeSummary.value = ''
  
  try {
    if (isEditing.value && form.value.triage_prompt && form.value.analysis_prompt) {
      // Refine existing prompts
      const result = await agentStore.refinePrompts(
        form.value.triage_prompt,
        form.value.analysis_prompt,
        aiDescription.value
      )
      if (result) {
        form.value.triage_prompt = result.triage_prompt
        form.value.analysis_prompt = result.analysis_prompt
        aiChangeSummary.value = result.changes_summary || 'Prompts refined successfully'
      }
    } else {
      // Generate new prompts
      const result = await agentStore.generatePrompts(aiDescription.value)
      if (result) {
        form.value.name = form.value.name || result.suggested_name
        form.value.slug = form.value.slug || result.suggested_slug
        form.value.description = form.value.description || result.suggested_description
        form.value.triage_prompt = result.triage_prompt
        form.value.analysis_prompt = result.analysis_prompt
        aiChangeSummary.value = 'Prompts generated! Review and edit below, then save.'
      }
    }
  } catch (err: any) {
    localError.value = err.message || 'Failed to generate prompts'
  } finally {
    isGenerating.value = false
  }
}

async function handleSave() {
  if (!isValid.value) return
  
  isSaving.value = true
  localError.value = null
  
  try {
    if (isEditing.value) {
      const updated = await agentStore.updateExistingAgent(props.agent!.slug || props.agent!.type, form.value)
      if (updated) {
        emit('saved', updated)
      }
    } else {
      const created = await agentStore.createNewAgent(form.value)
      if (created) {
        emit('saved', created)
      }
    }
  } catch (err: any) {
    localError.value = err.message || 'Failed to save agent'
  } finally {
    isSaving.value = false
  }
}

async function handleDelete() {
  if (!props.agent) return
  
  const slug = props.agent.slug || props.agent.type
  if (!confirm(`Are you sure you want to delete "${props.agent.name}"? This cannot be undone.`)) return
  
  isSaving.value = true
  localError.value = null
  
  try {
    await agentStore.deleteExistingAgent(slug)
    emit('deleted', slug)
  } catch (err: any) {
    localError.value = err.message || 'Failed to delete agent'
  } finally {
    isSaving.value = false
  }
}
</script>
