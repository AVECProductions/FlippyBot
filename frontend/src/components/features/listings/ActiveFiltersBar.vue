<template>
  <!-- Active Filters Display -->
  <div v-if="hasActiveFilters" class="flex flex-wrap items-center gap-2 mb-4">
    <span class="text-gray-400">Active Filters:</span>

    <div
      v-if="filters.notify_only"
      class="px-2 py-1 bg-green-500 bg-opacity-20 text-green-400 rounded-full text-xs flex items-center"
    >
      Notify Only
      <button @click="$emit('remove-filter', 'notify_only')" class="ml-1 font-bold hover:text-green-300">×</button>
    </div>

    <div
      v-if="filters.interesting_only"
      class="px-2 py-1 bg-yellow-500 bg-opacity-20 text-yellow-400 rounded-full text-xs flex items-center"
    >
      Interesting Only
      <button @click="$emit('remove-filter', 'interesting_only')" class="ml-1 font-bold hover:text-yellow-300">×</button>
    </div>

    <div
      v-if="filters.agent_slug"
      class="px-2 py-1 bg-purple-500 bg-opacity-20 text-purple-400 rounded-full text-xs flex items-center"
    >
      Agent: {{ agentName }}
      <button @click="$emit('remove-filter', 'agent_slug')" class="ml-1 font-bold hover:text-purple-300">×</button>
    </div>

    <div
      v-if="filters.scanner_id !== null && filters.scanner_id !== undefined"
      class="px-2 py-1 bg-blue-500 bg-opacity-20 text-blue-400 rounded-full text-xs flex items-center"
    >
      Scanner: {{ scannerQuery }}
      <button @click="$emit('remove-filter', 'scanner_id')" class="ml-1 font-bold hover:text-blue-300">×</button>
    </div>

    <div
      v-if="filters.search_location"
      class="px-2 py-1 bg-blue-500 bg-opacity-20 text-blue-400 rounded-full text-xs flex items-center"
    >
      Location: {{ filters.search_location }}
      <button @click="$emit('remove-filter', 'search_location')" class="ml-1 font-bold hover:text-blue-300">×</button>
    </div>

    <div
      v-if="filters.min_price !== null && filters.min_price !== undefined"
      class="px-2 py-1 bg-blue-500 bg-opacity-20 text-blue-400 rounded-full text-xs flex items-center"
    >
      Min Price: ${{ filters.min_price }}
      <button @click="$emit('remove-filter', 'min_price')" class="ml-1 font-bold hover:text-blue-300">×</button>
    </div>

    <div
      v-if="filters.max_price !== null && filters.max_price !== undefined"
      class="px-2 py-1 bg-blue-500 bg-opacity-20 text-blue-400 rounded-full text-xs flex items-center"
    >
      Max Price: ${{ filters.max_price }}
      <button @click="$emit('remove-filter', 'max_price')" class="ml-1 font-bold hover:text-blue-300">×</button>
    </div>

    <div
      v-if="filters.max_distance !== null && filters.max_distance !== undefined"
      class="px-2 py-1 bg-blue-500 bg-opacity-20 text-blue-400 rounded-full text-xs flex items-center"
    >
      Max Distance: {{ filters.max_distance }} miles
      <button @click="$emit('remove-filter', 'max_distance')" class="ml-1 font-bold hover:text-blue-300">×</button>
    </div>

    <BaseButton
      @click="$emit('clear-all')"
      variant="ghost"
      size="sm"
      class="border border-gray-600 hover:bg-gray-800"
    >
      Clear All
    </BaseButton>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import type { ListingFilters } from '@/services/api'

interface FilterOptions {
  agents: { slug: string; name: string }[]
  scanners: { id: number; query: string; agent_slug: string }[]
}

interface Props {
  filters: ListingFilters
  filterOptions?: FilterOptions
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'remove-filter': [key: keyof ListingFilters]
  'clear-all': []
}>()

const agentName = computed(() => {
  if (!props.filters.agent_slug || !props.filterOptions) return props.filters.agent_slug
  return props.filterOptions.agents.find(a => a.slug === props.filters.agent_slug)?.name ?? props.filters.agent_slug
})

const scannerQuery = computed(() => {
  if (props.filters.scanner_id === null || props.filters.scanner_id === undefined || !props.filterOptions) {
    return props.filters.scanner_id
  }
  return props.filterOptions.scanners.find(s => s.id === props.filters.scanner_id)?.query ?? `#${props.filters.scanner_id}`
})

const hasActiveFilters = computed(() => {
  return Object.entries(props.filters).some(([, value]) =>
    value !== undefined && value !== null && value !== ''
  )
})
</script>
