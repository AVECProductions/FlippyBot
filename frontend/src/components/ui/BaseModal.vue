<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center"
        @click.self="handleBackdropClick"
      >
        <!-- Backdrop -->
        <div class="fixed inset-0 bg-black bg-opacity-50 transition-opacity"></div>
        
        <!-- Modal -->
        <div 
          :class="modalClasses"
          role="dialog"
          aria-modal="true"
          :aria-labelledby="titleId"
        >
          <!-- Header -->
          <div v-if="$slots.header || title" class="flex items-center justify-between p-4 sm:p-6 border-b border-gray-800">
            <slot name="header">
              <h3 :id="titleId" class="text-lg font-bold text-white">{{ title }}</h3>
            </slot>
            <button
              v-if="showCloseButton"
              @click="close"
              class="text-gray-400 hover:text-white transition-colors duration-200"
              aria-label="Close modal"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="p-4 sm:p-6">
            <slot />
          </div>

          <!-- Footer -->
          <div v-if="$slots.footer" class="p-4 sm:p-6 border-t border-gray-800">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, nextTick, watch } from 'vue'

interface Props {
  show: boolean
  title?: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  showCloseButton?: boolean
  closeOnBackdropClick?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  showCloseButton: true,
  closeOnBackdropClick: true
})

const emit = defineEmits<{
  close: []
  'update:show': [value: boolean]
}>()

const titleId = computed(() => `modal-title-${Math.random().toString(36).substr(2, 9)}`)

const modalClasses = computed(() => {
  const baseClasses = [
    'relative bg-black rounded-lg shadow-lg border border-gray-800 max-h-[90vh] overflow-y-auto'
  ]

  const sizeClasses = {
    sm: 'max-w-md w-full mx-4',
    md: 'max-w-lg w-full mx-4',
    lg: 'max-w-2xl w-full mx-4',
    xl: 'max-w-4xl w-full mx-4'
  }

  return [
    ...baseClasses,
    sizeClasses[props.size]
  ].join(' ')
})

const close = () => {
  emit('close')
  emit('update:show', false)
}

const handleBackdropClick = () => {
  if (props.closeOnBackdropClick) {
    close()
  }
}

// Handle escape key
const handleEscapeKey = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.show) {
    close()
  }
}

// Add/remove escape key listener
watch(() => props.show, (newShow) => {
  if (newShow) {
    nextTick(() => {
      document.addEventListener('keydown', handleEscapeKey)
    })
  } else {
    document.removeEventListener('keydown', handleEscapeKey)
  }
})
</script>

<style scoped>
.modal-enter-active, .modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-active .relative,
.modal-leave-active .relative {
  transition: transform 0.3s ease;
}

.modal-enter-from, .modal-leave-to {
  opacity: 0;
}

.modal-enter-from .relative,
.modal-leave-to .relative {
  transform: scale(0.9) translateY(-10px);
}
</style>
