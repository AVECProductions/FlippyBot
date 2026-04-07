<template>
  <div class="border-b border-gray-800/60 last:border-b-0">
    <!-- Agent Row (always visible) -->
    <div
      class="flex items-start gap-3 px-4 py-4 cursor-pointer select-none transition-colors hover:bg-white/[0.02]"
      @click="toggleExpanded"
    >
      <!-- Expand Chevron -->
      <svg
        class="w-4 h-4 text-gray-500 transition-transform duration-200 flex-shrink-0 mt-0.5"
        :class="{ 'rotate-90': isExpanded }"
        fill="none" stroke="currentColor" viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5l7 7-7 7" />
      </svg>

      <!-- Agent info: stacks vertically on mobile -->
      <div class="flex-1 min-w-0">
        <!-- Row 1: status dot + name -->
        <div class="flex items-center gap-2 flex-wrap">
          <div
            :class="[
              'w-1.5 h-1.5 rounded-full flex-shrink-0',
              agentInfo.enabled ? 'bg-emerald-400' : 'bg-gray-600'
            ]"
          />
          <span class="text-sm font-medium text-gray-200">{{ agentInfo.name }}</span>
          <span
            v-if="runningCount > 0"
            class="text-[10px] tracking-wide uppercase text-emerald-500/80"
          >
            {{ runningCount }} running
          </span>
        </div>
        <!-- Row 2: query count -->
        <div class="flex items-center gap-2 mt-1 flex-wrap">
          <span class="text-xs text-gray-600">
            {{ queries.length }} {{ queries.length === 1 ? 'query' : 'queries' }}
          </span>
        </div>
      </div>

      <!-- Right side actions (stop propagation so clicks don't toggle) -->
      <div class="flex items-center gap-1 flex-shrink-0" @click.stop>
        <button
          @click="$emit('edit-agent')"
          class="p-2 text-gray-600 hover:text-gray-300 rounded transition-colors"
          title="Edit agent"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </button>
        <button
          v-if="agentInfo.enabled"
          @click="$emit('add-query')"
          class="p-2 text-gray-600 hover:text-gray-300 rounded transition-colors"
          title="Add query"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4v16m8-8H4" />
          </svg>
        </button>
        <button
          @click="$emit('delete-agent')"
          class="p-2 text-gray-700 hover:text-red-500 rounded transition-colors"
          title="Delete agent"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Expanded Content -->
    <div v-if="isExpanded">
      <!-- Agent meta (subtle) -->
      <div class="px-4 py-2.5 flex flex-wrap items-start gap-x-4 gap-y-1 text-[11px] text-gray-600 bg-white/[0.01]">
        <span v-if="agentInfo.description" class="text-gray-500 w-full">{{ agentInfo.description }}</span>
        <span v-if="agentInfo.triage_model">triage: {{ agentInfo.triage_model }}</span>
        <span v-if="agentInfo.analysis_model">analysis: {{ agentInfo.analysis_model }}</span>
        <span v-if="!agentInfo.enabled" class="text-yellow-600">disabled</span>
      </div>

      <!-- Queries -->
      <div v-if="agentInfo.enabled" class="ml-6 mr-4 mb-3 mt-1 border-l border-gray-800/50">
        <div v-if="queries.length === 0" class="pl-4 py-4">
          <p class="text-xs text-gray-700">No queries</p>
        </div>
        <div v-else>
          <QueryRow
            v-for="query in queries"
            :key="query.id"
            :query="query"
            @edit="$emit('edit-query', query)"
            @delete="$emit('delete-query', query)"
            @toggle-status="$emit('toggle-query-status', query)"
          />
        </div>
      </div>
      <div v-else class="ml-6 mr-4 mb-3 mt-1 pl-4 py-4 border-l border-gray-800/50">
        <p class="text-xs text-gray-700">Agent is disabled</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import QueryRow from './QueryRow.vue'
import type { AgentInfo, Scanner } from '@/types'

const props = defineProps<{
  agentInfo: AgentInfo
  queries: Scanner[]
}>()

defineEmits<{
  'add-query': []
  'edit-agent': []
  'analyze-url': []
  'delete-agent': []
  'edit-query': [query: Scanner]
  'delete-query': [query: Scanner]
  'toggle-query-status': [query: Scanner]
}>()

const isExpanded = ref(false)

const runningCount = computed(() => 
  props.queries.filter(q => q.status === 'running').length
)

const toggleExpanded = () => {
  isExpanded.value = !isExpanded.value
}
</script>
