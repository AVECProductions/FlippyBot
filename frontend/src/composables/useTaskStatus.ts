/**
 * Centralized task status management.
 * 
 * This composable provides a single source of truth for the current system task.
 * It uses smart polling - only polling when a task is known to be running.
 * 
 * Usage:
 *   const { currentTask, isRunning, startPolling, stopPolling, notifyTaskStarted } = useTaskStatus();
 */
import { ref, computed, readonly } from 'vue';
import { getCurrentTask, type SystemTask } from '@/services/api';

// Singleton state - shared across all component instances
const currentTask = ref<SystemTask | null>(null);
const isPolling = ref(false);
const lastCheck = ref<Date | null>(null);
const pollInterval = ref<ReturnType<typeof setInterval> | null>(null);
const errorCount = ref(0);

// Configuration
const POLL_INTERVAL_ACTIVE = 2000;  // 2s when task is running
const POLL_INTERVAL_IDLE = 30000;   // 30s idle check (in case we missed something)
const MAX_ERRORS = 3;               // Stop polling after consecutive errors

/**
 * Fetch the current task status from the server
 */
async function fetchTaskStatus(): Promise<boolean> {
  try {
    const response = await getCurrentTask();
    const wasRunning = currentTask.value !== null;
    
    if (response.busy && response.task) {
      currentTask.value = response.task;
      errorCount.value = 0;
      return true; // Task is running
    } else {
      currentTask.value = null;
      errorCount.value = 0;
      return false; // No task running
    }
  } catch (err) {
    errorCount.value++;
    console.warn('Task status check failed:', err);
    
    // After too many errors, assume no task is running
    if (errorCount.value >= MAX_ERRORS) {
      currentTask.value = null;
      return false;
    }
    
    // Keep previous state on error
    return currentTask.value !== null;
  } finally {
    lastCheck.value = new Date();
  }
}

/**
 * Start active polling (when we know or suspect a task is running)
 */
function startActivePolling() {
  if (pollInterval.value) {
    clearInterval(pollInterval.value);
  }
  
  isPolling.value = true;
  
  // Immediate check
  fetchTaskStatus().then((taskRunning) => {
    if (!taskRunning) {
      // Task completed, switch to idle mode
      switchToIdlePolling();
    }
  });
  
  // Poll every 2s while task is active
  pollInterval.value = setInterval(async () => {
    const taskRunning = await fetchTaskStatus();
    
    if (!taskRunning) {
      // Task completed, switch to idle mode
      switchToIdlePolling();
    }
  }, POLL_INTERVAL_ACTIVE);
}

/**
 * Switch to idle polling (occasional checks)
 */
function switchToIdlePolling() {
  if (pollInterval.value) {
    clearInterval(pollInterval.value);
  }
  
  isPolling.value = false;
  
  // Occasional check in case we missed a task start
  pollInterval.value = setInterval(async () => {
    const taskRunning = await fetchTaskStatus();
    
    if (taskRunning) {
      // Task started, switch to active polling
      startActivePolling();
    }
  }, POLL_INTERVAL_IDLE);
}

/**
 * Stop all polling
 */
function stopPolling() {
  if (pollInterval.value) {
    clearInterval(pollInterval.value);
    pollInterval.value = null;
  }
  isPolling.value = false;
}

/**
 * Notify that a task was just started (triggers active polling)
 */
function notifyTaskStarted(task?: Partial<SystemTask>) {
  // Optimistically set task state if provided
  if (task) {
    currentTask.value = {
      id: 0,
      task_type: task.task_type || 'scan',
      task_type_display: task.task_type_display || 'Task',
      status: 'running',
      status_display: 'Running',
      current_step: task.current_step || 'initializing',
      step_display: task.step_display || 'Initializing',
      progress_percent: task.progress_percent || 0,
      progress_message: task.progress_message || 'Starting...',
      started_at: new Date().toISOString(),
      elapsed_seconds: 0,
      ...task
    } as SystemTask;
  }
  
  // Start active polling
  startActivePolling();
}

/**
 * Force a refresh of task status
 */
async function refresh(): Promise<void> {
  const taskRunning = await fetchTaskStatus();
  
  if (taskRunning && !isPolling.value) {
    startActivePolling();
  } else if (!taskRunning && isPolling.value) {
    switchToIdlePolling();
  }
}

/**
 * Initialize the task status system
 */
function initialize() {
  // Do an initial check
  fetchTaskStatus().then((taskRunning) => {
    if (taskRunning) {
      startActivePolling();
    } else {
      switchToIdlePolling();
    }
  });
}

// Composable function
export function useTaskStatus() {
  return {
    // State (readonly to prevent external mutation)
    currentTask: readonly(currentTask),
    isPolling: readonly(isPolling),
    lastCheck: readonly(lastCheck),
    
    // Computed
    isRunning: computed(() => currentTask.value !== null),
    isBusy: computed(() => currentTask.value !== null),
    
    // Actions
    notifyTaskStarted,
    refresh,
    stopPolling,
    initialize,
    
    // For debugging
    _startActivePolling: startActivePolling,
  };
}

// Export singleton for direct access if needed
export const taskStatus = {
  currentTask,
  isPolling,
  notifyTaskStarted,
  refresh,
  stopPolling,
  initialize,
};
