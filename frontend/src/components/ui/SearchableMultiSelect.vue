<template>
  <div class="relative" ref="containerRef">
    <label v-if="label" class="block text-sm font-medium text-gray-300 mb-1">
      {{ label }}
    </label>
    
    <!-- Selected Items Display & Search Input -->
    <div
      class="min-h-[42px] w-full px-3 py-2 bg-[#1C1C1E] border border-gray-800 rounded-md text-gray-300 cursor-text flex flex-wrap gap-1 items-center"
      :class="{ 'ring-1 ring-blue-500 border-blue-500': isOpen }"
      @click="openDropdown"
    >
      <!-- Selected Tags -->
      <span
        v-for="item in selectedItems"
        :key="item.id"
        class="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-600/30 text-blue-300 rounded text-sm"
      >
        {{ item.name }}
        <button
          type="button"
          @click.stop="removeItem(item)"
          class="hover:text-blue-100 transition-colors"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </span>
      
      <!-- Search Input -->
      <input
        ref="inputRef"
        v-model="searchQuery"
        type="text"
        :placeholder="selectedItems.length === 0 ? placeholder : ''"
        class="flex-1 min-w-[100px] bg-transparent border-none outline-none text-gray-300 placeholder-gray-500 text-sm"
        @focus="openDropdown"
        @keydown.escape="closeDropdown"
        @keydown.backspace="handleBackspace"
      />
    </div>
    
    <!-- Dropdown -->
    <Transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="transform scale-95 opacity-0"
      enter-to-class="transform scale-100 opacity-100"
      leave-active-class="transition duration-75 ease-in"
      leave-from-class="transform scale-100 opacity-100"
      leave-to-class="transform scale-95 opacity-0"
    >
      <div
        v-if="isOpen"
        class="absolute z-50 w-full mt-1 bg-[#2C2C2E] border border-gray-700 rounded-md shadow-lg max-h-64 overflow-y-auto"
      >
        <div v-if="filteredOptions.length === 0" class="px-3 py-2 text-gray-500 text-sm">
          {{ searchQuery ? 'No locations found' : 'No locations available' }}
        </div>
        
        <div
          v-for="option in filteredOptions"
          :key="option.id"
          class="px-3 py-2 cursor-pointer transition-colors flex items-center gap-2"
          :class="[
            isSelected(option) 
              ? 'bg-blue-600/20 text-blue-300' 
              : 'text-gray-300 hover:bg-[#3C3C3E]'
          ]"
          @click="toggleOption(option)"
        >
          <div
            class="w-4 h-4 rounded border flex items-center justify-center flex-shrink-0"
            :class="isSelected(option) ? 'bg-blue-600 border-blue-600' : 'border-gray-600'"
          >
            <svg v-if="isSelected(option)" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <span class="truncate">{{ option.name }}</span>
        </div>
      </div>
    </Transition>
    
    <p v-if="hint" class="text-xs text-gray-500 mt-1">{{ hint }}</p>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'

interface Option {
  id: number | string
  name: string
  [key: string]: any
}

interface Props {
  modelValue: (number | string)[]
  options: Option[]
  label?: string
  placeholder?: string
  hint?: string
  maxDisplay?: number
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: 'Search...',
  maxDisplay: 5
})

const emit = defineEmits<{
  'update:modelValue': [(number | string)[]]
}>()

const containerRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLInputElement | null>(null)
const isOpen = ref(false)
const searchQuery = ref('')

const selectedItems = computed(() => {
  return props.options.filter(opt => props.modelValue.includes(opt.id))
})

const filteredOptions = computed(() => {
  let filtered = props.options
  
  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(opt => 
      opt.name.toLowerCase().includes(query)
    )
  }
  
  // Return all filtered options (scrollable dropdown handles overflow)
  return filtered
})

const isSelected = (option: Option) => {
  return props.modelValue.includes(option.id)
}

const toggleOption = (option: Option) => {
  const newValue = [...props.modelValue]
  const index = newValue.indexOf(option.id)
  
  if (index === -1) {
    newValue.push(option.id)
  } else {
    newValue.splice(index, 1)
  }
  
  emit('update:modelValue', newValue)
}

const removeItem = (item: Option) => {
  const newValue = props.modelValue.filter(id => id !== item.id)
  emit('update:modelValue', newValue)
}

const openDropdown = () => {
  isOpen.value = true
  setTimeout(() => inputRef.value?.focus(), 0)
}

const closeDropdown = () => {
  isOpen.value = false
  searchQuery.value = ''
}

const handleBackspace = () => {
  if (searchQuery.value === '' && selectedItems.value.length > 0) {
    // Remove last selected item
    const lastItem = selectedItems.value[selectedItems.value.length - 1]
    removeItem(lastItem)
  }
}

// Close dropdown when clicking outside
const handleClickOutside = (event: MouseEvent) => {
  if (containerRef.value && !containerRef.value.contains(event.target as Node)) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>


