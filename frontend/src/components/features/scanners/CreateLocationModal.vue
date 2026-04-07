<template>
  <BaseModal
    :show="show"
    title="Add New Location"
    @close="$emit('close')"
  >
    <form @submit.prevent="handleSubmit" class="space-y-4">
      <BaseInput 
        v-model="form.name"
        label="Location Name"
        placeholder="e.g., Colorado Springs, CO"
        required
      />
      
      <BaseInput 
        v-model="form.marketplace_url_slug"
        label="Facebook Marketplace URL Slug"
        placeholder="e.g., coloradosprings"
        hint="The URL slug from Facebook Marketplace (the part after facebook.com/marketplace/)"
        required
      />
    </form>

    <template #footer>
      <div class="flex justify-end space-x-2">
        <BaseButton 
          @click="$emit('close')" 
          variant="secondary"
        >
          Cancel
        </BaseButton>
        <BaseButton 
          @click="handleSubmit" 
          variant="primary"
          :loading="isCreatingLocation"
          loading-text="Creating..."
          :disabled="!form.name || !form.marketplace_url_slug"
        >
          Create Location
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useScannerStore } from '@/stores/scannerStore'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

interface Props {
  show: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  created: []
}>()

const scannerStore = useScannerStore()
const { isCreatingLocation } = storeToRefs(scannerStore)

const form = reactive({
  name: '',
  marketplace_url_slug: ''
})

const resetForm = () => {
  form.name = ''
  form.marketplace_url_slug = ''
}

const handleSubmit = async () => {
  try {
    await scannerStore.createNewLocation(form)
    emit('created')
    resetForm()
  } catch (error) {
    // Error handling is done in the store
  }
}

// Reset form when modal closes
watch(() => props.show, (newShow) => {
  if (!newShow) {
    resetForm()
  }
})
</script>
