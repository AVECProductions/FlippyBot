<template>
  <tr 
    class="border-t border-gray-800 hover:bg-[#2C2C2E] cursor-pointer transition-colors duration-200 bg-[#232323]"
    @click="$emit('click', scanner)"
  >
    <td class="px-4 py-3 pl-8 text-[#F3F4F6] truncate w-[70%]">{{ scanner.query }}</td>
    <td class="px-4 py-3 w-[30%] text-right pr-6">
      <span 
        class="px-3 py-1 rounded-full text-xs font-medium"
        :class="statusClasses"
      >
        {{ scanner.status }}
      </span>
    </td>
  </tr>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Scanner } from '@/types'

interface Props {
  scanner: Scanner
}

const props = defineProps<Props>()

const emit = defineEmits<{
  click: [scanner: Scanner]
}>()

const statusClasses = computed(() => {
  return props.scanner.status === 'running' 
    ? 'bg-green-500 bg-opacity-20 text-green-500' 
    : 'bg-gray-500 bg-opacity-20 text-gray-500'
})
</script>
