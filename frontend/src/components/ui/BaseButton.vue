<template>
  <button
    :type="type"
    :disabled="disabled || loading"
    :class="buttonClasses"
    @click="$emit('click', $event)"
  >
    <slot v-if="!loading" />
    <span v-else class="flex items-center">
      <svg class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      {{ loadingText || 'Loading...' }}
    </span>
  </button>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  loadingText?: string
  type?: 'button' | 'submit' | 'reset'
  fullWidth?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  disabled: false,
  loading: false,
  fullWidth: false
})

defineEmits<{
  click: [event: MouseEvent]
}>()

const buttonClasses = computed(() => {
  const baseClasses = [
    'inline-flex items-center justify-center font-medium rounded transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-black',
    props.disabled || props.loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
  ]

  // Size classes
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base'
  }

  // Variant classes
  const variantClasses = {
    primary: 'bg-blue-500 text-white border border-blue-500 hover:bg-blue-600 focus:ring-blue-500',
    secondary: 'bg-transparent text-gray-200 border border-gray-600 hover:bg-gray-800 hover:border-gray-500 focus:ring-gray-500',
    danger: 'bg-transparent text-red-500 border border-red-500 hover:bg-red-500 hover:bg-opacity-10 focus:ring-red-500',
    success: 'bg-transparent text-green-500 border border-green-500 hover:bg-green-500 hover:bg-opacity-10 focus:ring-green-500',
    ghost: 'bg-transparent text-gray-300 border-0 hover:bg-gray-800 focus:ring-gray-500'
  }

  // Width classes
  const widthClasses = props.fullWidth ? 'w-full' : ''

  return [
    ...baseClasses,
    sizeClasses[props.size],
    variantClasses[props.variant],
    widthClasses
  ].join(' ')
})
</script>
