<template>
  <div v-if="currentTask" class="task-indicator">
    <div class="task-content">
      <!-- Spinner -->
      <div class="spinner">
        <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      </div>
      
      <!-- Task Info -->
      <div class="task-info">
        <span class="task-step">{{ currentTask.step_display }}</span>
        <span v-if="currentTask.progress_message" class="task-message">{{ currentTask.progress_message }}</span>
      </div>
      
      <!-- Progress Bar -->
      <div class="progress-bar-container">
        <div 
          class="progress-bar" 
          :style="{ width: `${currentTask.progress_percent}%` }"
        ></div>
      </div>
      <span class="progress-text">{{ currentTask.progress_percent }}%</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
import { useTaskStatus } from '@/composables/useTaskStatus';

// Use the centralized task status (no local polling)
const { currentTask, initialize } = useTaskStatus();

// Initialize polling on first mount (idempotent)
onMounted(() => {
  initialize();
});
</script>

<style scoped>
.task-indicator {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  padding: 8px 12px;
  margin-right: 16px;
}

.task-content {
  display: flex;
  align-items: center;
  gap: 10px;
}

.spinner {
  color: #3b82f6;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 120px;
}

.task-step {
  font-size: 12px;
  font-weight: 600;
  color: #3b82f6;
}

.task-message {
  font-size: 10px;
  color: #9ca3af;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.progress-bar-container {
  width: 60px;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: #3b82f6;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 11px;
  color: #6b7280;
  min-width: 30px;
}
</style>
