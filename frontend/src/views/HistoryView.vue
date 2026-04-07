<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getScanBatches } from '@/services/api'

const router = useRouter()

const batches = ref<any[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const currentPage = ref(1)
const totalPages = ref(1)
const totalCount = ref(0)
const PAGE_SIZE = 20

const load = async (page = 1) => {
  loading.value = true
  error.value = null
  try {
    const result = await getScanBatches(page, PAGE_SIZE)
    batches.value = result.results || result
    if (result.count !== undefined) {
      totalCount.value = result.count
      totalPages.value = Math.ceil(result.count / PAGE_SIZE)
    }
    currentPage.value = page
  } catch (err: any) {
    error.value = err.message || 'Failed to load history'
  } finally {
    loading.value = false
  }
}

const viewBatch = (scanId: string) => {
  router.push({ name: 'scan-batch', params: { scanId } })
}

const formatDateTime = (iso: string) => {
  try { return new Date(iso).toLocaleString() } catch { return iso }
}

const statusDot = (status: string) => {
  switch (status) {
    case 'completed': return 'bg-green-500'
    case 'in_progress': return 'bg-blue-500'
    case 'failed': return 'bg-red-500'
    case 'pending': return 'bg-yellow-500'
    default: return 'bg-gray-500'
  }
}

onMounted(() => load(1))
</script>

<template>
  <div class="max-w-5xl mx-auto">
    <!-- Header -->
    <div class="flex justify-between items-center mb-8">
      <h2 class="text-xl font-bold uppercase tracking-wide text-white">Scan History</h2>
      <button
        @click="load(currentPage)"
        class="px-3 py-2 rounded border border-gray-600 text-gray-200 font-medium bg-transparent hover:bg-gray-800 hover:border-gray-500 transition-all duration-200"
        :disabled="loading"
      >
        {{ loading ? 'Loading...' : 'Refresh' }}
      </button>
    </div>

    <div v-if="error" class="bg-red-500 bg-opacity-10 text-red-500 p-4 rounded-md mb-4">
      {{ error }}
    </div>

    <!-- Batch list -->
    <div class="bg-[#121212] rounded-lg border border-gray-800">
      <!-- Empty state -->
      <div v-if="!loading && batches.length === 0" class="text-gray-500 text-sm text-center py-16">
        No scan history yet. Run a scan from the Control page.
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading && batches.length === 0" class="divide-y divide-gray-800">
        <div v-for="i in 5" :key="i" class="p-4 animate-pulse flex justify-between">
          <div class="flex items-center space-x-3">
            <div class="w-2 h-2 rounded-full bg-gray-700"></div>
            <div class="h-4 w-40 bg-gray-800 rounded"></div>
          </div>
          <div class="h-4 w-32 bg-gray-800 rounded"></div>
        </div>
      </div>

      <!-- Rows -->
      <div v-if="batches.length > 0" class="divide-y divide-gray-800">
        <div
          v-for="batch in batches"
          :key="batch.scan_id"
          class="flex items-center justify-between p-4 hover:bg-gray-800 transition-colors cursor-pointer"
          @click="viewBatch(batch.scan_id)"
        >
          <!-- Left: status + time + type -->
          <div class="flex items-center space-x-3 min-w-0">
            <div class="w-2 h-2 rounded-full flex-shrink-0" :class="statusDot(batch.analysis_status)"></div>
            <div class="min-w-0">
              <div class="flex items-center space-x-2">
                <span class="text-sm text-gray-200">{{ formatDateTime(batch.started_at) }}</span>
                <span
                  class="px-2 py-0.5 rounded text-xs flex-shrink-0"
                  :class="batch.scan_type === 'single'
                    ? 'bg-green-500 bg-opacity-20 text-green-400'
                    : 'bg-blue-500 bg-opacity-20 text-blue-400'"
                >
                  {{ batch.scan_type === 'single' ? 'Manual' : 'Auto' }}
                </span>
              </div>
              <div v-if="batch.scanner_name" class="text-xs text-gray-500 mt-0.5 truncate">
                {{ batch.scanner_name }}
              </div>
            </div>
          </div>

          <!-- Right: stats -->
          <div class="flex items-center space-x-5 text-xs text-gray-400 flex-shrink-0 ml-4">
            <div class="text-center hidden sm:block">
              <div class="text-white font-medium">{{ batch.total_listings_found ?? '—' }}</div>
              <div class="text-gray-500">found</div>
            </div>
            <div class="text-center">
              <div class="text-green-400 font-medium">{{ batch.new_listings_added ?? '—' }}</div>
              <div class="text-gray-500">new</div>
            </div>
            <div class="text-center">
              <div class="text-yellow-400 font-medium">{{ batch.investigation_marked ?? '—' }}</div>
              <div class="text-gray-500">interesting</div>
            </div>
            <svg class="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="totalPages > 1" class="flex items-center justify-between mt-6 text-sm text-gray-400">
      <span>{{ totalCount }} total scans</span>
      <div class="flex items-center space-x-2">
        <button
          @click="load(currentPage - 1)"
          :disabled="currentPage <= 1 || loading"
          class="px-3 py-1 rounded border border-gray-700 hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          Previous
        </button>
        <span class="text-gray-500">{{ currentPage }} / {{ totalPages }}</span>
        <button
          @click="load(currentPage + 1)"
          :disabled="currentPage >= totalPages || loading"
          class="px-3 py-1 rounded border border-gray-700 hover:bg-gray-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          Next
        </button>
      </div>
    </div>
  </div>
</template>
