<template>
  <div class="flex items-center justify-between pl-4 pr-2 py-2.5 transition-colors hover:bg-white/[0.02] group">
    <!-- Left: query info -->
    <div class="flex items-center space-x-3 min-w-0 flex-1">
      <!-- Status dot -->
      <div 
        :class="[
          'w-1.5 h-1.5 rounded-full flex-shrink-0',
          query.status === 'running' ? 'bg-emerald-400' : 'bg-gray-700'
        ]"
      />

      <!-- Query text -->
      <span class="text-sm text-gray-400 truncate">{{ query.query }}</span>

      <!-- Category pill -->
      <span 
        v-if="query.category" 
        class="text-[10px] text-gray-600 px-1.5 py-0.5 border border-gray-800 rounded flex-shrink-0"
      >
        {{ query.category }}
      </span>

      <!-- Locations -->
      <span 
        v-if="locationNames" 
        class="text-[11px] text-gray-700 truncate flex-shrink-0 max-w-[200px]"
      >
        {{ locationNames }}
      </span>
    </div>

    <!-- Right: actions -->
    <div class="flex items-center space-x-1 flex-shrink-0 ml-4 opacity-0 group-hover:opacity-100 transition-opacity">
      <!-- Toggle status -->
      <button
        @click="$emit('toggle-status')"
        :class="[
          'px-2 py-1 rounded text-[10px] font-medium tracking-wide uppercase transition-colors',
          query.status === 'running'
            ? 'text-emerald-500 hover:bg-emerald-500/10'
            : 'text-gray-600 hover:bg-gray-800 hover:text-gray-400'
        ]"
      >
        {{ query.status === 'running' ? 'Running' : 'Stopped' }}
      </button>

      <!-- Edit -->
      <button
        @click="$emit('edit')"
        class="p-1.5 text-gray-700 hover:text-gray-400 rounded transition-colors"
        title="Edit query"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      </button>

      <!-- Delete -->
      <button
        @click="$emit('delete')"
        class="p-1.5 text-gray-700 hover:text-red-500 rounded transition-colors"
        title="Delete query"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Scanner } from '@/types'

const props = defineProps<{
  query: Scanner
}>()

defineEmits<{
  'edit': []
  'delete': []
  'toggle-status': []
}>()

const locationNames = computed(() => {
  if (!props.query.locations_data || props.query.locations_data.length === 0) {
    return ''
  }
  return props.query.locations_data.map(l => l.location_name).join(', ')
})
</script>
