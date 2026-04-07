<template>
  <!-- Filters Sidebar -->
  <div
    v-if="show"
    class="fixed inset-y-0 right-0 w-80 bg-black shadow-lg transform transition-transform duration-300 ease-in-out z-50 flex flex-col border-l border-gray-800"
    :class="{ 'translate-x-0': show, 'translate-x-full': !show }"
  >
    <!-- Filters Header -->
    <div class="p-4 border-b border-gray-800 flex justify-between items-center">
      <h3 class="text-lg font-semibold uppercase tracking-wide text-white">Filters</h3>
      <BaseButton
        @click="$emit('close')"
        variant="ghost"
        size="sm"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
        </svg>
      </BaseButton>
    </div>

    <!-- Scrollable Filters Content -->
    <div class="flex-1 overflow-y-auto p-4 space-y-6">

      <!-- Notify Only -->
      <div>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            v-model="localFilters.notify_only"
            class="form-checkbox h-5 w-5 text-green-500 rounded bg-[#1C1C1E] border-gray-800 focus:ring-green-500"
          />
          <span class="text-sm font-medium text-gray-300">Notify Only</span>
        </label>
        <p class="text-xs text-gray-500 mt-1 ml-7">Listings the deep analysis rated as great deals</p>
      </div>

      <!-- Interesting Only -->
      <div>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            v-model="localFilters.interesting_only"
            class="form-checkbox h-5 w-5 text-yellow-500 rounded bg-[#1C1C1E] border-gray-800 focus:ring-yellow-500"
          />
          <span class="text-sm font-medium text-gray-300">Interesting Only</span>
        </label>
        <p class="text-xs text-gray-500 mt-1 ml-7">Listings flagged by the AI triage pass</p>
      </div>

      <!-- Agent Filter -->
      <div>
        <label for="agentFilter" class="block text-sm font-medium text-gray-300 mb-2">Agent</label>
        <select
          id="agentFilter"
          v-model="localFilters.agent_slug"
          @change="onAgentChange"
          class="w-full px-3 py-2 bg-[#1C1C1E] border border-gray-800 rounded-md text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All Agents</option>
          <option v-for="agent in filterOptions.agents" :key="agent.slug" :value="agent.slug">
            {{ agent.name }}
          </option>
        </select>
      </div>

      <!-- Scanner Filter (cascades from agent) -->
      <div>
        <label for="scannerFilter" class="block text-sm font-medium text-gray-300 mb-2">Scanner</label>
        <select
          id="scannerFilter"
          v-model="localFilters.scanner_id"
          class="w-full px-3 py-2 bg-[#1C1C1E] border border-gray-800 rounded-md text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
          :disabled="filteredScanners.length === 0"
        >
          <option :value="null">All Scanners</option>
          <option v-for="scanner in filteredScanners" :key="scanner.id" :value="scanner.id">
            {{ scanner.query }}
          </option>
        </select>
      </div>

      <!-- Search Location Filter -->
      <div>
        <label for="searchLocationFilter" class="block text-sm font-medium text-gray-300 mb-2">Search Location</label>
        <select
          id="searchLocationFilter"
          v-model="localFilters.search_location"
          class="w-full px-3 py-2 bg-[#1C1C1E] border border-gray-800 rounded-md text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          <option value="">All Locations</option>
          <option v-for="location in filterOptions.search_locations" :key="location" :value="location">{{ location }}</option>
        </select>
      </div>

      <!-- Price Range Filter -->
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">Price Range</label>
        <div class="flex space-x-2">
          <div class="w-1/2">
            <BaseInput
              v-model.number="localFilters.min_price"
              type="number"
              placeholder="Min"
            />
          </div>
          <div class="w-1/2">
            <BaseInput
              v-model.number="localFilters.max_price"
              type="number"
              placeholder="Max"
            />
          </div>
        </div>
      </div>

      <!-- Max Distance Filter -->
      <div>
        <label for="distanceFilter" class="block text-sm font-medium text-gray-300 mb-2">Max Distance (miles)</label>
        <BaseInput
          id="distanceFilter"
          v-model.number="localFilters.max_distance"
          type="number"
          placeholder="Enter maximum distance"
        />
      </div>

    </div>

    <!-- Filter Actions -->
    <div class="p-4 border-t border-gray-800 flex justify-between">
      <BaseButton
        @click="$emit('reset')"
        variant="secondary"
      >
        Reset
      </BaseButton>
      <BaseButton
        @click="applyFilters"
        variant="primary"
      >
        Apply Filters
      </BaseButton>
    </div>
  </div>

  <!-- Modal Backdrop -->
  <div
    v-if="show"
    @click="$emit('close')"
    class="fixed inset-0 bg-black bg-opacity-50 z-40"
  ></div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import type { ListingFilters } from '@/services/api'

interface FilterOptions {
  search_locations: string[]
  agents: { slug: string; name: string }[]
  scanners: { id: number; query: string; agent_slug: string }[]
}

interface Props {
  show: boolean
  filters: ListingFilters
  filterOptions: FilterOptions
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  apply: [filters: ListingFilters]
  reset: []
}>()

const localFilters = ref<ListingFilters>({})

// Scanners filtered by selected agent
const filteredScanners = computed(() => {
  const slug = localFilters.value.agent_slug
  if (!slug) return props.filterOptions.scanners
  return props.filterOptions.scanners.filter(s => s.agent_slug === slug)
})

const onAgentChange = () => {
  // Clear scanner selection when agent changes
  localFilters.value.scanner_id = null
}

const applyFilters = () => {
  emit('apply', { ...localFilters.value })
}

// Initialize local filters when modal opens
watch(() => props.show, (newShow) => {
  if (newShow) {
    localFilters.value = { ...props.filters }
  }
})

// Initialize on mount
localFilters.value = { ...props.filters }
</script>

<style scoped>
.transform {
  transition-property: transform;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 300ms;
}
</style>
