<template>
  <BaseModal
    :show="show"
    title="Scanner Details"
    size="lg"
    @close="$emit('close')"
  >
    <div v-if="scanner" class="space-y-6">
      <!-- Scanner Details Section -->
      <div class="pb-4 border-b border-gray-800">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Query</label>
            <p class="text-white">{{ scanner.query }}</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Custom Label</label>
            <p class="text-white">{{ scanner.category || 'No label' }}</p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Product Category</label>
            <span 
              class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
              :class="getCategoryBadgeClass(scanner.product_category)"
            >
              {{ getCategoryLabel(scanner.product_category) }}
            </span>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-300 mb-1">Status</label>
            <span 
              class="px-2 py-1 rounded-full text-xs font-medium"
              :class="scanner.status === 'running' ? 'bg-green-500 bg-opacity-20 text-green-500' : 'bg-gray-500 bg-opacity-20 text-gray-500'"
            >
              {{ scanner.status }}
            </span>
          </div>
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-gray-300 mb-1">Locations</label>
            <p class="text-white">
              <span v-if="locationNames.length > 0">
                {{ locationNames.join(', ') }}
              </span>
              <span v-else class="text-gray-500 italic">No locations assigned</span>
            </p>
          </div>
        </div>
      </div>
      
      <!-- Universal Filters Section -->
      <div class="pb-4 border-b border-gray-800">
        <h4 class="text-sm font-semibold text-gray-200 mb-3 flex items-center">
          <span class="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
          Universal Filters
        </h4>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-1">Min Price</label>
            <p class="text-white">
              <span v-if="scanner.min_price">${{ Number(scanner.min_price).toLocaleString() }}</span>
              <span v-else class="text-gray-500 italic">No minimum</span>
            </p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-1">Max Price</label>
            <p class="text-white">
              <span v-if="scanner.max_price">${{ Number(scanner.max_price).toLocaleString() }}</span>
              <span v-else class="text-gray-500 italic">No limit</span>
            </p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-1">Max Distance</label>
            <p class="text-white">
              <span v-if="scanner.max_distance">{{ scanner.max_distance }} miles</span>
              <span v-else class="text-gray-500 italic">No limit</span>
            </p>
          </div>
        </div>
        <p class="text-xs text-gray-400 mt-2">
          Universal filters apply to all product categories.
        </p>
      </div>
      
      <!-- Category-Specific Filters Section -->
      <div v-if="hasCategoryFilters" class="pb-4 border-b border-gray-800">
        <h4 class="text-sm font-semibold text-gray-200 mb-3 flex items-center">
          <span class="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
          {{ getCategoryLabel(scanner.product_category) }} Filters
        </h4>
        
        <!-- Vehicle Filters -->
        <div v-if="scanner.product_category === 'vehicles'" class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-1">Max Mileage</label>
            <p class="text-white">
              <span v-if="getCategoryFilter('max_mileage') || scanner.max_mileage">
                {{ Number(getCategoryFilter('max_mileage') || scanner.max_mileage).toLocaleString() }} miles
              </span>
              <span v-else class="text-gray-500 italic">No limit</span>
            </p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-1">Min Year</label>
            <p class="text-white">
              <span v-if="getCategoryFilter('min_year')">{{ getCategoryFilter('min_year') }}</span>
              <span v-else class="text-gray-500 italic">Any</span>
            </p>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-400 mb-1">Max Year</label>
            <p class="text-white">
              <span v-if="getCategoryFilter('max_year')">{{ getCategoryFilter('max_year') }}</span>
              <span v-else class="text-gray-500 italic">Any</span>
            </p>
          </div>
        </div>
        
        <!-- Ski Filters -->
        <div v-else-if="scanner.product_category === 'skis'" class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-400 mb-1">Length Range</label>
              <p class="text-white">
                <span v-if="getCategoryFilter('min_length_cm') || getCategoryFilter('max_length_cm')">
                  {{ getCategoryFilter('min_length_cm') || '?' }} - {{ getCategoryFilter('max_length_cm') || '?' }} cm
                </span>
                <span v-else class="text-gray-500 italic">Any length</span>
              </p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-400 mb-1">Waist Width</label>
              <p class="text-white">
                <span v-if="getCategoryFilter('width_mm')">{{ getCategoryFilter('width_mm') }} mm</span>
                <span v-else class="text-gray-500 italic">Any width</span>
              </p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-400 mb-1">Ski Type</label>
              <p class="text-white">
                <span v-if="getCategoryFilter('ski_type') && getCategoryFilter('ski_type') !== 'Any'">
                  {{ getCategoryFilter('ski_type') }}
                </span>
                <span v-else class="text-gray-500 italic">Any type</span>
              </p>
            </div>
          </div>
          <div v-if="preferredBrands.length > 0">
            <label class="block text-sm font-medium text-gray-400 mb-2">Preferred Brands</label>
            <div class="flex flex-wrap gap-2">
              <span 
                v-for="brand in preferredBrands" 
                :key="brand" 
                class="px-2 py-1 bg-purple-500 bg-opacity-20 text-purple-400 rounded-full text-xs"
              >
                {{ brand }}
              </span>
            </div>
          </div>
        </div>
        
        <p class="text-xs text-gray-400 mt-3">
          Category-specific filters help narrow down results for {{ getCategoryLabel(scanner.product_category).toLowerCase() }}.
        </p>
      </div>
      
      <!-- No Category Filters Message for General -->
      <div v-else-if="scanner.product_category === 'general'" class="pb-4 border-b border-gray-800">
        <h4 class="text-sm font-semibold text-gray-200 mb-3 flex items-center">
          <span class="w-2 h-2 bg-gray-500 rounded-full mr-2"></span>
          Category Filters
        </h4>
        <p class="text-gray-500 italic text-sm">
          General category has no specific filters. Only universal filters (price, distance) apply.
        </p>
      </div>
      
      <!-- Notification Emails Section -->
      <div class="pb-4 border-b border-gray-800">
        <div class="flex justify-between items-center mb-2">
          <h4 class="text-md font-semibold text-white flex items-center">
            <span class="mr-2">📧</span> Notification Emails
          </h4>
          <BaseButton 
            @click="toggleEmailEditing" 
            variant="ghost"
            size="sm"
          >
            {{ isEditingEmails ? 'Cancel' : 'Edit Emails' }}
          </BaseButton>
        </div>
        
        <!-- Email editing view -->
        <div v-if="isEditingEmails" class="space-y-4">
          <div class="space-y-2">
            <div v-for="(email, index) in localEmails" :key="`email-${index}`" class="flex items-center">
              <BaseInput 
                v-model="localEmails[index]" 
                placeholder="email@example.com"
                type="email"
                class="flex-grow"
              />
              <BaseButton 
                @click="removeEmail(index)" 
                variant="danger"
                size="sm"
                class="ml-2"
              >
                Remove
              </BaseButton>
            </div>
            <BaseButton 
              @click="addEmail" 
              variant="secondary"
              size="sm"
              full-width
            >
              + Add Email
            </BaseButton>
          </div>
          <div class="flex justify-end space-x-2">
            <BaseButton 
              @click="cancelEmailEditing" 
              variant="secondary"
              size="sm"
            >
              Cancel
            </BaseButton>
            <BaseButton 
              @click="saveEmails" 
              variant="primary"
              size="sm"
              :loading="isSavingEmails"
              loading-text="Saving..."
            >
              Save Emails
            </BaseButton>
          </div>
        </div>
        
        <!-- Email display view -->
        <div v-else>
          <div v-if="!scanner?.notification_emails || scanner.notification_emails.length === 0" class="text-gray-400 italic">
            No notification emails set. Using default from environment.
          </div>
          <div v-else class="flex flex-wrap gap-2">
            <span 
              v-for="(email, index) in scanner.notification_emails" 
              :key="index" 
              class="px-2 py-1 bg-green-500 bg-opacity-20 text-green-400 rounded-full text-xs"
            >
              {{ email }}
            </span>
          </div>
          <p class="text-xs text-gray-400 mt-2">
            AI deal alerts will be sent to these email addresses when this scanner finds good deals.
          </p>
        </div>
      </div>
      
      <!-- Keywords Section -->
      <div class="pb-4 border-b border-gray-800">
        <div class="flex justify-between items-center mb-2">
          <h4 class="text-md font-semibold text-white">Keywords</h4>
          <BaseButton 
            @click="toggleKeywordEditing" 
            variant="ghost"
            size="sm"
          >
            {{ isEditingKeywords ? 'Cancel' : 'Edit Keywords' }}
          </BaseButton>
        </div>
        
        <!-- Keywords editing view -->
        <div v-if="isEditingKeywords" class="space-y-4">
          <div class="space-y-2">
            <div v-for="(keyword, index) in localKeywords" :key="`keyword-${index}`" class="flex items-center">
              <BaseInput 
                v-model="localKeywords[index]" 
                placeholder="Enter keyword"
                class="flex-grow"
              />
              <BaseButton 
                @click="removeKeyword(index)" 
                variant="danger"
                size="sm"
                class="ml-2"
              >
                Remove
              </BaseButton>
            </div>
            <BaseButton 
              @click="addKeyword" 
              variant="secondary"
              size="sm"
              full-width
            >
              + Add Keyword
            </BaseButton>
          </div>
          <div class="flex justify-end space-x-2">
            <BaseButton 
              @click="cancelKeywordEditing" 
              variant="secondary"
              size="sm"
            >
              Cancel
            </BaseButton>
            <BaseButton 
              @click="saveKeywords" 
              variant="primary"
              size="sm"
              :loading="isSavingKeywords"
              loading-text="Saving..."
            >
              Save Keywords
            </BaseButton>
          </div>
        </div>
        
        <!-- Keywords display view -->
        <div v-else>
          <div v-if="!keywords || keywords.length === 0" class="text-gray-400 italic">
            No keywords set. Scanner will match all listings.
          </div>
          <div v-else class="flex flex-wrap gap-2">
            <span 
              v-for="(keyword, index) in keywords" 
              :key="index" 
              class="px-2 py-1 bg-blue-500 bg-opacity-20 text-blue-400 rounded-full text-xs"
            >
              {{ keyword }}
            </span>
          </div>
          <p class="text-xs text-gray-400 mt-2">
            These keywords are used to filter search results. If any of these keywords are found in a listing title, it will be flagged.
          </p>
        </div>
      </div>
    </div>
    
    <template #footer>
      <div class="flex space-x-2">
        <BaseButton 
          @click="$emit('edit', scanner)"
          variant="secondary"
        >
          Edit Scanner
        </BaseButton>
        <BaseButton 
          :variant="scanner?.status === 'running' ? 'danger' : 'success'"
          @click="handleToggleStatus"
        >
          {{ scanner?.status === 'running' ? 'Stop Scanner' : 'Start Scanner' }}
        </BaseButton>
        <BaseButton 
          variant="danger"
          @click="handleDelete"
        >
          Delete Scanner
        </BaseButton>
      </div>
    </template>
  </BaseModal>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useScannerStore } from '@/stores/scannerStore'
import BaseModal from '@/components/ui/BaseModal.vue'
import BaseInput from '@/components/ui/BaseInput.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import type { Scanner, ProductCategory } from '@/types'

interface Props {
  show: boolean
  scanner: Scanner | null
  keywords?: string[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  edit: [scanner: Scanner]
  updated: []
  deleted: []
  'status-toggled': [status: string]
}>()

const scannerStore = useScannerStore()
const { isSavingKeywords } = storeToRefs(scannerStore)

const isEditingKeywords = ref(false)
const localKeywords = ref<string[]>([])

// Email editing state
const isEditingEmails = ref(false)
const localEmails = ref<string[]>([])
const isSavingEmails = ref(false)

const CATEGORY_LABELS: Record<ProductCategory, string> = {
  vehicles: '🚗 Vehicles',
  skis: '⛷️ Skis',
  general: '📦 General'
}

const getCategoryLabel = (category?: string): string => {
  return CATEGORY_LABELS[(category as ProductCategory) || 'general'] || '📦 General'
}

const getCategoryBadgeClass = (category?: string): string => {
  switch (category) {
    case 'vehicles':
      return 'bg-blue-500 bg-opacity-20 text-blue-400'
    case 'skis':
      return 'bg-purple-500 bg-opacity-20 text-purple-400'
    default:
      return 'bg-gray-500 bg-opacity-20 text-gray-400'
  }
}

const getCategoryFilter = (key: string): any => {
  return props.scanner?.category_filters?.[key]
}

const hasCategoryFilters = computed(() => {
  const category = props.scanner?.product_category
  if (category === 'general') return false
  if (category === 'vehicles') {
    return getCategoryFilter('max_mileage') || props.scanner?.max_mileage || 
           getCategoryFilter('min_year') || getCategoryFilter('max_year')
  }
  if (category === 'skis') {
    return getCategoryFilter('min_length_cm') || getCategoryFilter('max_length_cm') ||
           getCategoryFilter('width_mm') || getCategoryFilter('ski_type') ||
           (getCategoryFilter('preferred_brands')?.length > 0)
  }
  return false
})

const preferredBrands = computed(() => {
  const brands = getCategoryFilter('preferred_brands')
  return Array.isArray(brands) ? brands : []
})

const locationNames = computed(() => {
  if (props.scanner?.locations_data) {
    return props.scanner.locations_data.map(loc => loc.location_name)
  }
  return []
})

const toggleKeywordEditing = () => {
  if (!isEditingKeywords.value) {
    localKeywords.value = [...(props.keywords || [])]
  }
  isEditingKeywords.value = !isEditingKeywords.value
}

const cancelKeywordEditing = () => {
  isEditingKeywords.value = false
  localKeywords.value = []
}

const addKeyword = () => {
  localKeywords.value.push('')
}

const removeKeyword = (index: number) => {
  localKeywords.value.splice(index, 1)
}

const saveKeywords = async () => {
  if (!props.scanner) return
  
  try {
    await scannerStore.saveKeywordsForScanner(props.scanner.id, localKeywords.value)
    isEditingKeywords.value = false
    emit('updated')
  } catch (error) {
    // Error handling is done in the store
  }
}

// Email editing functions
const toggleEmailEditing = () => {
  if (!isEditingEmails.value) {
    localEmails.value = [...(props.scanner?.notification_emails || [])]
  }
  isEditingEmails.value = !isEditingEmails.value
}

const cancelEmailEditing = () => {
  isEditingEmails.value = false
  localEmails.value = []
}

const addEmail = () => {
  localEmails.value.push('')
}

const removeEmail = (index: number) => {
  localEmails.value.splice(index, 1)
}

const saveEmails = async () => {
  if (!props.scanner) return
  
  isSavingEmails.value = true
  try {
    // Filter out empty emails and validate format
    const validEmails = localEmails.value
      .map(e => e.trim().toLowerCase())
      .filter(e => e && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e))
    
    await scannerStore.updateScanner(props.scanner.id, {
      notification_emails: validEmails
    })
    isEditingEmails.value = false
    emit('updated')
  } catch (error) {
    console.error('Error saving emails:', error)
  } finally {
    isSavingEmails.value = false
  }
}

const handleToggleStatus = async () => {
  if (!props.scanner) return
  
  try {
    await scannerStore.toggleStatus(props.scanner.id, props.scanner.status)
    emit('status-toggled', props.scanner.status === 'running' ? 'stopped' : 'running')
  } catch (error) {
    // Error handling is done in the store
  }
}

const handleDelete = async () => {
  if (!props.scanner) return
  
  if (confirm('Are you sure you want to delete this scanner?')) {
    try {
      await scannerStore.deleteExistingScanner(props.scanner.id)
      emit('deleted')
    } catch (error) {
      // Error handling is done in the store
    }
  }
}

// Reset editing state when modal closes
watch(() => props.show, (newShow) => {
  if (!newShow) {
    isEditingKeywords.value = false
    localKeywords.value = []
    isEditingEmails.value = false
    localEmails.value = []
  }
})
</script>
