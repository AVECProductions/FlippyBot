<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { getScanBatches, getScanners } from '@/services/api'

const { isAuthenticated } = useAuth()
const router = useRouter()

// Dashboard state
const recentBatches = ref<any[]>([])
const scanners = ref<any[]>([])
const loading = ref(false)

const activeScannerCount = computed(() =>
  scanners.value.filter(s => s.status === 'running').length
)

const lastBatch = computed(() => recentBatches.value[0] ?? null)

const loadDashboard = async () => {
  loading.value = true
  try {
    const [batchResult, scannerResult] = await Promise.all([
      getScanBatches(1, 6),
      getScanners()
    ])
    recentBatches.value = batchResult.results || batchResult
    scanners.value = scannerResult
  } catch (err) {
    console.error('Dashboard load error:', err)
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
    case 'in_progress': return 'bg-blue-500 animate-pulse'
    case 'failed': return 'bg-red-500'
    case 'pending': return 'bg-yellow-500'
    default: return 'bg-gray-500'
  }
}

onMounted(() => {
  if (isAuthenticated.value) loadDashboard()

  // Landing page mobile scroll animations
  if (!isAuthenticated.value && window.innerWidth < 768) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in')
          observer.unobserve(entry.target)
        }
      })
    }, { threshold: 0.1 })
    document.querySelectorAll('.mobile-animate').forEach(el => observer.observe(el))
  }
})
</script>

<template>
  <!-- ── LANDING PAGE (not logged in) ──────────────────────────── -->
  <div
    v-if="!isAuthenticated"
    class="landing-container bg-black flex flex-col items-center justify-center"
  >
    <div class="text-center px-4">
      <h1 class="text-4xl sm:text-5xl font-bold uppercase tracking-wide text-blue-400 mb-2">
        FLIPPYBOT
      </h1>
      <p class="text-gray-400 text-lg mb-8 max-w-md mx-auto">
        Stop scrolling, find deals.
      </p>
      <div class="flex justify-center">
        <router-link
          to="/login"
          class="px-10 py-4 rounded-md bg-transparent border-2 border-gray-600 text-gray-200 font-medium text-lg hover:bg-gray-800 hover:border-gray-500 transition-all duration-200 shadow-lg hover:shadow-xl"
        >
          ACCESS
        </router-link>
      </div>
    </div>
  </div>

  <!-- ── DASHBOARD (logged in) ──────────────────────────────────── -->
  <div v-else class="max-w-5xl mx-auto">
    <div class="flex justify-between items-center mb-8">
      <h2 class="text-xl font-bold uppercase tracking-wide text-white">Dashboard</h2>
      <button
        @click="loadDashboard"
        class="px-3 py-2 rounded border border-gray-600 text-gray-200 font-medium bg-transparent hover:bg-gray-800 hover:border-gray-500 transition-all duration-200"
        :disabled="loading"
      >
        {{ loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </div>

    <!-- Stats row -->
    <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-8">
      <div class="bg-[#121212] rounded-lg p-4 border border-gray-800">
        <div class="text-2xl font-bold text-blue-400">{{ activeScannerCount }}</div>
        <div class="text-xs text-gray-500 mt-1 uppercase tracking-wide">Active Scanners</div>
      </div>
      <div class="bg-[#121212] rounded-lg p-4 border border-gray-800">
        <div class="text-2xl font-bold text-white">{{ recentBatches.length > 0 ? recentBatches[0].new_listings_added ?? '—' : '—' }}</div>
        <div class="text-xs text-gray-500 mt-1 uppercase tracking-wide">New in Last Scan</div>
      </div>
      <div class="bg-[#121212] rounded-lg p-4 border border-gray-800 col-span-2 sm:col-span-1">
        <div class="text-2xl font-bold text-yellow-400">{{ recentBatches.length > 0 ? recentBatches[0].investigation_marked ?? '—' : '—' }}</div>
        <div class="text-xs text-gray-500 mt-1 uppercase tracking-wide">Interesting in Last Scan</div>
      </div>
    </div>

    <!-- Quick nav -->
    <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
      <router-link
        v-for="link in [
          { to: '/agents', label: 'Agents', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
          { to: '/listings', label: 'Listings', icon: 'M4 6h16M4 10h16M4 14h16M4 18h16' },
          { to: '/history', label: 'History', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
          { to: '/scanner-control', label: 'Control', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
        ]"
        :key="link.to"
        :to="link.to"
        class="bg-[#121212] border border-gray-800 rounded-lg p-4 flex flex-col items-center justify-center space-y-2 hover:bg-gray-800 hover:border-gray-600 transition-all duration-200 text-center"
      >
        <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="link.icon" />
        </svg>
        <span class="text-sm text-gray-300 font-medium">{{ link.label }}</span>
      </router-link>
    </div>

    <!-- Recent scan batches -->
    <div class="bg-[#121212] rounded-lg border border-gray-800">
      <div class="flex justify-between items-center px-5 py-4 border-b border-gray-800">
        <h3 class="text-sm font-semibold text-white uppercase tracking-wide">Recent Scans</h3>
        <router-link to="/history" class="text-xs text-blue-400 hover:text-blue-300 transition-colors">
          View all →
        </router-link>
      </div>

      <div v-if="loading && recentBatches.length === 0" class="divide-y divide-gray-800">
        <div v-for="i in 4" :key="i" class="p-4 animate-pulse flex justify-between">
          <div class="flex items-center space-x-3">
            <div class="w-2 h-2 rounded-full bg-gray-700"></div>
            <div class="h-4 w-36 bg-gray-800 rounded"></div>
          </div>
          <div class="h-4 w-24 bg-gray-800 rounded"></div>
        </div>
      </div>

      <div v-else-if="recentBatches.length === 0" class="text-gray-500 text-sm text-center py-10">
        No scans yet. Head to Control to run your first scan.
      </div>

      <div v-else class="divide-y divide-gray-800">
        <div
          v-for="batch in recentBatches"
          :key="batch.scan_id"
          class="flex items-center justify-between px-5 py-3 hover:bg-gray-800 transition-colors cursor-pointer"
          @click="viewBatch(batch.scan_id)"
        >
          <div class="flex items-center space-x-3">
            <div class="w-2 h-2 rounded-full flex-shrink-0" :class="statusDot(batch.analysis_status)"></div>
            <div>
              <span class="text-sm text-gray-200">{{ formatDateTime(batch.started_at) }}</span>
              <span
                class="ml-2 px-1.5 py-0.5 rounded text-xs"
                :class="batch.scan_type === 'single'
                  ? 'bg-green-500 bg-opacity-20 text-green-400'
                  : 'bg-blue-500 bg-opacity-20 text-blue-400'"
              >
                {{ batch.scan_type === 'single' ? 'Manual' : 'Auto' }}
              </span>
            </div>
          </div>
          <div class="flex items-center space-x-4 text-xs text-gray-400 flex-shrink-0">
            <span class="text-green-400">+{{ batch.new_listings_added ?? 0 }} new</span>
            <span class="text-yellow-400 hidden sm:inline">{{ batch.investigation_marked ?? 0 }} interesting</span>
            <svg class="w-3.5 h-3.5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.landing-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  overflow: hidden;
}

@media (max-width: 767px) {
  .mobile-animate {
    opacity: 0;
    transform: translateX(-30px);
    transition: opacity 0.8s ease-out, transform 0.8s ease-out;
  }
  .animate-in {
    opacity: 1;
    transform: translateX(0);
  }
}
</style>
