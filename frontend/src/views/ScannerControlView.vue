<template>
  <div class="max-w-5xl mx-auto">
    <!-- Header -->
    <div class="flex justify-between items-center mb-8">
      <h2 class="text-xl font-bold uppercase tracking-wide text-white">Scanner Control</h2>
      <button 
        @click="refreshAll" 
        class="px-3 py-2 rounded border border-gray-600 text-gray-200 font-medium bg-transparent hover:bg-gray-800 hover:border-gray-500 transition-all duration-200"
        :disabled="loading"
      >
        {{ loading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </div>

    <!-- Worker Status Bar -->
    <div class="bg-[#121212] rounded-lg p-4 border border-gray-800 mb-6">
      <div class="flex items-center justify-between flex-wrap gap-3">
        <div class="flex items-center space-x-3">
          <!-- Animated dot -->
          <div class="relative flex items-center justify-center w-4 h-4">
            <div class="w-3 h-3 rounded-full" :class="workerDotClass"></div>
            <div v-if="workerScanning" class="absolute w-3 h-3 rounded-full bg-blue-500 animate-ping opacity-60"></div>
            <div v-else-if="workerWaiting" class="absolute w-3 h-3 rounded-full bg-yellow-500 animate-ping opacity-60"></div>
          </div>
          <span class="text-sm font-medium" :class="workerScanning ? 'text-blue-400' : workerOnline ? 'text-green-400' : 'text-red-400'">
            {{ workerStatusLabel }}
          </span>
          <!-- Pending trigger message -->
          <span v-if="pendingTrigger && !workerScanning" class="text-xs text-yellow-400 animate-pulse">
            — waiting for Flippy to pick up...
          </span>
        </div>
        <div class="flex items-center space-x-4 text-xs text-gray-500">
          <span v-if="workerStatus?.last_scan_at">
            Last scan: {{ formatDateTime(workerStatus.last_scan_at) }}
          </span>
          <span v-if="workerStatus?.auto_enabled && timeUntilNextScan !== null && !workerScanning" class="text-blue-400">
            Next scan in {{ formatCountdown(timeUntilNextScan) }}
          </span>
        </div>
      </div>
    </div>

    <!-- Error/Success Messages -->
    <div v-if="error" class="bg-red-500 bg-opacity-10 text-red-500 p-4 rounded-md mb-4">
      {{ error }}
    </div>

    <div v-if="successMessage" class="bg-green-500 bg-opacity-10 text-green-500 p-4 rounded-md mb-4">
      {{ successMessage }}
    </div>

    <!-- Current Task Status (if running) -->
    <div v-if="currentTask" class="bg-blue-500 bg-opacity-10 border border-blue-500 border-opacity-30 rounded-lg p-4 mb-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center space-x-4">
          <div class="animate-spin">
            <svg class="h-6 w-6 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <div>
            <div class="font-semibold text-white">{{ currentTask.step_display }}</div>
            <div class="text-sm text-gray-400">{{ currentTask.progress_message || 'Processing...' }}</div>
            <div class="text-xs text-gray-500 mt-1">
              Running for {{ formatElapsed(currentTask.elapsed_seconds) }}
            </div>
          </div>
        </div>
        <div class="flex items-center space-x-4">
          <div class="w-32 h-2 bg-gray-700 rounded-full overflow-hidden">
            <div 
              class="h-full bg-blue-500 transition-all duration-300"
              :style="{ width: `${currentTask.progress_percent}%` }"
            ></div>
          </div>
          <span class="text-blue-400 font-medium">{{ currentTask.progress_percent }}%</span>
          <!-- Clear stuck task button (shows if task running > 5 min) -->
          <button
            v-if="currentTask.elapsed_seconds > 60"
            @click="clearStuckTask"
            class="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 text-white rounded transition-colors"
            :title="currentTask.elapsed_seconds > 300 ? 'Task appears stuck. Click to cancel.' : 'Cancel running task'"
          >
            {{ currentTask.elapsed_seconds > 300 ? 'Cancel Stuck Task' : 'Cancel Task' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Mode Selection -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      
      <!-- Manual Mode Card -->
      <div
        class="bg-[#121212] rounded-lg p-6 border-2 transition-all"
        :class="[
          settings?.mode === 'manual' ? 'border-green-500' : 'border-gray-800',
          settings?.mode === 'manual' ? '' : workerStandby ? 'cursor-pointer hover:border-gray-600' : 'cursor-not-allowed opacity-60'
        ]"
        @click="setMode('manual')"
      >
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-full bg-green-500 bg-opacity-20 flex items-center justify-center">
              <svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122"></path>
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-white">Manual Mode</h3>
              <p class="text-xs text-gray-500">For testing & validation</p>
            </div>
          </div>
          <div 
            class="w-4 h-4 rounded-full border-2"
            :class="settings?.mode === 'manual' ? 'bg-green-500 border-green-500' : 'border-gray-600'"
          ></div>
        </div>
        
        <p class="text-sm text-gray-400 mb-4">
          Run single scans to test and validate agent behavior. Review results before running analysis.
        </p>
        
        <!-- Manual Mode Controls -->
        <div v-if="settings?.mode === 'manual'" class="space-y-3 mt-4 pt-4 border-t border-gray-800">
          <button 
            @click.stop="runManualScan" 
            class="w-full px-4 py-3 rounded bg-green-600 text-white hover:bg-green-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            :disabled="actionLoading || !!currentTask"
          >
            <svg v-if="!actionLoading" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <svg v-else class="animate-spin w-5 h-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{{ actionLoading ? 'Running Scan...' : 'Run Single Scan' }}</span>
          </button>
          
          <p v-if="currentTask" class="text-xs text-yellow-500 text-center">
            Please wait for current task to complete
          </p>
          
          <!-- Manual Scan History -->
          <div class="mt-4 pt-4 border-t border-gray-800">
            <h4 class="text-sm font-medium text-gray-400 mb-3">Recent Manual Scans</h4>
            <div class="max-h-48 overflow-y-auto space-y-2">
              <div v-if="manualBatches.length === 0" class="text-gray-500 text-xs text-center py-2">
                No manual scans yet
              </div>
              <div 
                v-for="batch in manualBatches.slice(0, 5)" 
                :key="batch.scan_id"
                class="flex justify-between items-center p-2 rounded bg-[#0D1117] hover:bg-gray-800 transition-colors cursor-pointer"
                @click.stop="viewScanBatch(batch.scan_id)"
              >
                <div class="flex items-center space-x-2">
                  <div 
                    class="w-2 h-2 rounded-full"
                    :class="getStatusDot(batch.analysis_status)"
                  ></div>
                  <span class="text-xs text-gray-300">{{ formatDateTime(batch.started_at) }}</span>
                </div>
                <div class="flex items-center space-x-2 text-xs">
                  <span class="text-gray-400">{{ batch.new_listings_added }} new</span>
                  <svg class="w-3 h-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Auto Mode Card -->
      <div
        class="bg-[#121212] rounded-lg p-6 border-2 transition-all"
        :class="[
          settings?.mode === 'auto' ? 'border-blue-500' : 'border-gray-800',
          settings?.mode === 'auto' ? '' : workerStandby ? 'cursor-pointer hover:border-gray-600' : 'cursor-not-allowed opacity-60'
        ]"
        @click="setMode('auto')"
      >
        <div class="flex items-center justify-between mb-4">
          <div class="flex items-center space-x-3">
            <div class="w-10 h-10 rounded-full bg-blue-500 bg-opacity-20 flex items-center justify-center">
              <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
            </div>
            <div>
              <h3 class="text-lg font-semibold text-white">Automatic Mode</h3>
              <p class="text-xs text-gray-500">Scheduled scanning</p>
            </div>
          </div>
          <div 
            class="w-4 h-4 rounded-full border-2"
            :class="settings?.mode === 'auto' ? 'bg-blue-500 border-blue-500' : 'border-gray-600'"
          ></div>
        </div>
        
        <p class="text-sm text-gray-400 mb-4">
          Automatically scan marketplace at regular intervals. Ideal for production monitoring.
        </p>
        
        <!-- Auto Mode Controls -->
        <div v-if="settings?.mode === 'auto'" class="space-y-4 mt-4 pt-4 border-t border-gray-800" @click.stop>
          <!-- Interval Setting -->
          <div>
            <label class="block text-sm text-gray-400 mb-2">Scan Interval</label>
            <div class="flex items-center space-x-3">
              <input 
                v-model.number="intervalMinutes"
                type="number" 
                min="5" 
                max="120"
                class="flex-1 px-3 py-2 bg-[#1C1C1E] border border-gray-700 rounded text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
                :disabled="settings?.auto_enabled"
              />
              <span class="text-gray-500 text-sm">minutes</span>
            </div>
          </div>
          
          <!-- Status Display -->
          <div v-if="settings?.auto_enabled" class="bg-[#0D1117] rounded p-4 space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-gray-400">Status:</span>
              <span class="text-green-400 font-medium">Running</span>
            </div>
            <div v-if="settings?.last_scan_at" class="flex justify-between text-sm">
              <span class="text-gray-400">Last Scan:</span>
              <span class="text-gray-300">{{ formatDateTime(settings.last_scan_at) }}</span>
            </div>
            <div v-if="settings?.next_scan_at" class="flex justify-between text-sm">
              <span class="text-gray-400">Next Scan:</span>
              <span class="text-blue-400">{{ formatCountdown(settings.time_until_next_scan) }}</span>
            </div>
          </div>
          
          <!-- Toggle Button -->
          <button
            v-if="!settings?.auto_enabled"
            @click.stop="enableAuto"
            class="w-full px-4 py-3 rounded bg-blue-600 text-white hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
            :disabled="actionLoading || !!currentTask || !workerOnline"
            :title="!workerOnline ? 'Flippy must be online to start auto scanning' : ''"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
            <span>Start Auto Scanning</span>
          </button>
          
          <button 
            v-else
            @click.stop="disableAuto" 
            class="w-full px-4 py-3 rounded bg-red-600 text-white hover:bg-red-700 transition-colors duration-200 disabled:opacity-50 flex items-center justify-center space-x-2"
            :disabled="actionLoading"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"></path>
            </svg>
            <span>Stop Auto Scanning</span>
          </button>
          
          <!-- Auto Scan History -->
          <div class="mt-4 pt-4 border-t border-gray-800">
            <h4 class="text-sm font-medium text-gray-400 mb-3">Recent Auto Scans</h4>
            <div class="max-h-48 overflow-y-auto space-y-2">
              <div v-if="autoBatches.length === 0" class="text-gray-500 text-xs text-center py-2">
                No automatic scans yet
              </div>
              <div 
                v-for="batch in autoBatches.slice(0, 5)" 
                :key="batch.scan_id"
                class="flex justify-between items-center p-2 rounded bg-[#0D1117] hover:bg-gray-800 transition-colors cursor-pointer"
                @click.stop="viewScanBatch(batch.scan_id)"
              >
                <div class="flex items-center space-x-2">
                  <div 
                    class="w-2 h-2 rounded-full"
                    :class="getStatusDot(batch.analysis_status)"
                  ></div>
                  <span class="text-xs text-gray-300">{{ formatDateTime(batch.started_at) }}</span>
                </div>
                <div class="flex items-center space-x-2 text-xs">
                  <span class="text-gray-400">{{ batch.new_listings_added }} new</span>
                  <svg class="w-3 h-3 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Link to full history -->
    <div class="text-center mt-2">
      <router-link
        to="/history"
        class="text-sm text-blue-400 hover:text-blue-300 transition-colors"
      >
        View full scan history →
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';

import { useRouter } from 'vue-router';
import {
  getScannerSettings,
  getScannerStatus,
  setScannerMode,
  enableAutoScan,
  disableAutoScan,
  runManualScan as runManualScanApi,
  clearStuckTasks as clearStuckTasksApi,
  type ScannerSettings
} from '@/services/api';
import { useTaskStatus } from '@/composables/useTaskStatus';

const router = useRouter();

// Use centralized task status
const { currentTask, isRunning, notifyTaskStarted, refresh: refreshTaskStatus, initialize: initTaskStatus } = useTaskStatus();

// State
const loading = ref(false);
const actionLoading = ref(false);
const error = ref<string | null>(null);
const successMessage = ref<string | null>(null);

// Data
const settings = ref<ScannerSettings | null>(null);
const intervalMinutes = ref(30);

// Worker status (polled separately from settings)
const workerStatus = ref<any>(null);
const pendingTrigger = ref(false);
let pendingTriggerTimeout: ReturnType<typeof setTimeout> | null = null;

// Computed worker state
const workerOnline = computed(() => workerStatus.value?.running === true);
const workerScanning = computed(() => workerOnline.value && workerStatus.value?.worker?.current_task === 'scanning');
const workerWaiting = computed(() => workerOnline.value && workerStatus.value?.worker?.current_task === 'waiting');
const workerStandby = computed(() => workerOnline.value && !workerScanning.value && !workerWaiting.value);
const workerDotClass = computed(() => {
  if (workerScanning.value) return 'bg-blue-500';
  if (workerWaiting.value) return 'bg-yellow-500';
  if (workerStandby.value) return 'bg-green-500';
  return 'bg-gray-600';
});
const workerStatusLabel = computed(() => {
  if (workerScanning.value) return 'Flippy scanning...';
  if (workerWaiting.value) return 'Flippy waiting...';
  if (workerStandby.value) return 'Flippy standby';
  return 'Flippy offline';
});
const timeUntilNextScan = computed<number | null>(() => {
  const next = workerStatus.value?.next_scan_at;
  if (!next) return null;
  const diff = Math.floor((new Date(next).getTime() - Date.now()) / 1000);
  return diff > 0 ? diff : 0;
});

// Settings polling for auto mode countdown
let settingsInterval: number | null = null;

// Computed filtered batches by scan type
const manualBatches = computed(() => [] as any[]);
const autoBatches = computed(() => [] as any[]);

// Methods
const clearMessages = () => {
  error.value = null;
  successMessage.value = null;
};

const showSuccess = (message: string) => {
  successMessage.value = message;
  error.value = null;
  setTimeout(() => { successMessage.value = null; }, 3000);
};

const showError = (message: string) => {
  error.value = message;
  successMessage.value = null;
};

const refreshAll = async () => {
  loading.value = true;
  try {
    await Promise.all([refreshSettings(), refreshTaskStatus()]);
  } finally {
    loading.value = false;
  }
};

const refreshSettings = async () => {
  try {
    settings.value = await getScannerSettings();
    intervalMinutes.value = settings.value.interval_minutes;
  } catch (err: any) {
    console.error('Error fetching settings:', err);
  }
};

const setMode = async (mode: 'auto' | 'manual') => {
  if (settings.value?.mode === mode) return;
  if (!workerStandby.value) {
    showError('Can only switch modes when Flippy is in standby');
    return;
  }
  
  actionLoading.value = true;
  clearMessages();
  
  try {
    const result = await setScannerMode(mode);
    settings.value = result.settings;
    showSuccess(`Switched to ${mode} mode`);
  } catch (err: any) {
    showError(err.message || 'Failed to change mode');
  } finally {
    actionLoading.value = false;
  }
};

const runManualScan = async () => {
  actionLoading.value = true;
  clearMessages();
  
  try {
    // Notify task started (optimistic update, triggers active polling)
    notifyTaskStarted({
      task_type: 'scan',
      task_type_display: 'Marketplace Scan',
      current_step: 'initializing',
      step_display: 'Initializing',
      progress_message: 'Starting scan...'
    });
    
    const result = await runManualScanApi();
    markTriggered();
    showSuccess(result.message || 'Scan triggered — Flippy will start within 5 seconds');
    await refreshSettings();
  } catch (err: any) {
    showError(err.message || 'Failed to run scan');
    // Refresh task status on error
    await refreshTaskStatus();
  } finally {
    actionLoading.value = false;
  }
};

const enableAuto = async () => {
  actionLoading.value = true;
  clearMessages();
  
  try {
    // Notify task system that a scan will start
    notifyTaskStarted({
      task_type: 'scan',
      task_type_display: 'Marketplace Scan',
      current_step: 'initializing',
      step_display: 'Initializing',
      progress_message: 'Starting auto scan...'
    });
    
    const result = await enableAutoScan(intervalMinutes.value);
    settings.value = result.settings;
    markTriggered();
    showSuccess('Auto scanning enabled — Flippy will start within 5 seconds');
    startSettingsPolling();
  } catch (err: any) {
    showError(err.message || 'Failed to enable auto scan');
    await refreshTaskStatus();
  } finally {
    actionLoading.value = false;
  }
};

const disableAuto = async () => {
  actionLoading.value = true;
  clearMessages();
  
  try {
    const result = await disableAutoScan();
    settings.value = result.settings;
    showSuccess('Auto scanning disabled');
    
    // Stop settings polling
    stopSettingsPolling();
  } catch (err: any) {
    showError(err.message || 'Failed to disable auto scan');
  } finally {
    actionLoading.value = false;
  }
};

const viewScanBatch = (scanId: string) => {
  router.push({ name: 'scan-batch', params: { scanId } });
};

const formatDateTime = (isoString: string): string => {
  try {
    return new Date(isoString).toLocaleString();
  } catch {
    return isoString;
  }
};

const formatCountdown = (seconds: number | null): string => {
  if (!seconds || seconds <= 0) return 'Soon...';
  
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  
  if (mins > 0) {
    return `${mins}m ${secs}s`;
  }
  return `${secs}s`;
};

const formatElapsed = (seconds: number | null): string => {
  if (!seconds) return '0s';
  
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  
  if (mins > 0) {
    return `${mins}m ${secs}s`;
  }
  return `${secs}s`;
};

const clearStuckTask = async () => {
  try {
    await clearStuckTasksApi(true);
    showSuccess('Stuck task cleared');
    await refreshTaskStatus();
  } catch (err: any) {
    showError(err.message || 'Failed to clear stuck task');
  }
};

// Worker status polling — always on, 5s interval
const refreshWorkerStatus = async () => {
  try {
    workerStatus.value = await getScannerStatus();
  } catch {
    // silently ignore — worker may be offline
  }
};

const startSettingsPolling = () => {
  if (settingsInterval) return;
  settingsInterval = window.setInterval(async () => {
    await Promise.all([refreshSettings(), refreshWorkerStatus()]);
  }, 5000);
};

const stopSettingsPolling = () => {
  if (settingsInterval) {
    clearInterval(settingsInterval);
    settingsInterval = null;
  }
};

// Set pending state after triggering — clears when worker picks up or after 30s
const markTriggered = () => {
  pendingTrigger.value = true;
  if (pendingTriggerTimeout) clearTimeout(pendingTriggerTimeout);
  pendingTriggerTimeout = setTimeout(() => { pendingTrigger.value = false; }, 30000);
};

// Clear pending once worker is actually scanning
watch(workerScanning, (scanning) => {
  if (scanning && pendingTrigger.value) {
    pendingTrigger.value = false;
    if (pendingTriggerTimeout) clearTimeout(pendingTriggerTimeout);
  }
});

// Auto-clear orphaned task when Flippy goes offline mid-scan
watch(workerOnline, async (online, wasOnline) => {
  if (wasOnline && !online && currentTask.value) {
    await clearStuckTasksApi(true).catch(() => {});
    await refreshTaskStatus();
  }
});

const getStatusClass = (status: string) => {
  switch (status) {
    case 'pending': return 'bg-yellow-500 bg-opacity-20 text-yellow-400';
    case 'in_progress': return 'bg-blue-500 bg-opacity-20 text-blue-400';
    case 'completed': return 'bg-green-500 bg-opacity-20 text-green-400';
    case 'failed': return 'bg-red-500 bg-opacity-20 text-red-400';
    default: return 'bg-gray-500 bg-opacity-20 text-gray-400';
  }
};

const getStatusDot = (status: string) => {
  switch (status) {
    case 'pending': return 'bg-yellow-500';
    case 'in_progress': return 'bg-blue-500';
    case 'completed': return 'bg-green-500';
    case 'failed': return 'bg-red-500';
    default: return 'bg-gray-500';
  }
};

// Watch for task completion to refresh settings
watch(isRunning, async (running, wasRunning) => {
  if (wasRunning && !running) {
    await refreshSettings();
  }
});

// Lifecycle
onMounted(async () => {
  initTaskStatus();
  await Promise.all([refreshAll(), refreshWorkerStatus()]);
  // Always poll — shows worker online/offline and countdown
  startSettingsPolling();
});

onUnmounted(() => {
  stopSettingsPolling();
  if (pendingTriggerTimeout) clearTimeout(pendingTriggerTimeout);
});
</script>

<style scoped>
.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Custom scrollbar */
.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #1a1a1a;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #4a4a4a;
  border-radius: 3px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #6a6a6a;
}
</style>
