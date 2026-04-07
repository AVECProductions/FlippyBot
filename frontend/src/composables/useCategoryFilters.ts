/**
 * Composable for managing category-specific filters in scanner creation/editing
 */
import { ref, computed, watch } from 'vue'
import type { ProductCategory, CategorySchema, CategoryFilterField } from '@/types'

// Category schemas - mirrors backend CATEGORY_FILTER_SCHEMAS
const CATEGORY_SCHEMAS: Record<ProductCategory, CategorySchema> = {
  vehicles: {
    fields: [
      {
        name: 'max_mileage',
        type: 'integer',
        label: 'Max Mileage',
        placeholder: 'e.g., 100000',
        hint: 'Maximum odometer reading',
        validation: { min: 0, max: 500000 }
      },
      {
        name: 'min_year',
        type: 'integer',
        label: 'Min Year',
        placeholder: 'e.g., 2015',
        hint: 'Oldest model year',
        validation: { min: 1980, max: 2030 }
      },
      {
        name: 'max_year',
        type: 'integer',
        label: 'Max Year',
        placeholder: 'e.g., 2024',
        hint: 'Newest model year',
        validation: { min: 1980, max: 2030 }
      },
    ],
    keywords: [],
    listing_type: 'vehicle'
  },
  
  skis: {
    fields: [
      {
        name: 'min_length_cm',
        type: 'integer',
        label: 'Min Length (cm)',
        placeholder: 'e.g., 170',
        hint: 'Minimum ski length',
        validation: { min: 100, max: 210 }
      },
      {
        name: 'max_length_cm',
        type: 'integer',
        label: 'Max Length (cm)',
        placeholder: 'e.g., 180',
        hint: 'Maximum ski length',
        validation: { min: 100, max: 210 }
      },
      {
        name: 'width_mm',
        type: 'integer',
        label: 'Waist Width (mm)',
        placeholder: 'e.g., 95',
        hint: 'Ski waist width',
        validation: { min: 60, max: 140 }
      },
      {
        name: 'preferred_brands',
        type: 'multi_select',
        label: 'Preferred Brands',
        options: ['Volkl', 'Rossignol', 'Salomon', 'Atomic', 'Head', 'K2', 'Nordica', 'Blizzard', 'Line', 'Faction'],
        hint: 'Select preferred brands (optional)'
      },
      {
        name: 'ski_type',
        type: 'select',
        label: 'Ski Type',
        options: ['Any', 'All-Mountain', 'Powder', 'Carving', 'Park', 'Touring'],
        hint: 'Type of skiing'
      },
    ],
    keywords: [],
    listing_type: 'ski_equipment'
  },
  
  general: {
    fields: [],
    keywords: [],
    listing_type: 'general'
  },
  
  ai_beta: {
    fields: [],  // No filters for AI - it uses the LLM to evaluate
    keywords: [],
    listing_type: 'ai_analyzed'
  }
}

export function useCategoryFilters() {
  const selectedCategory = ref<ProductCategory>('general')
  const categoryFilters = ref<Record<string, any>>({})
  
  const availableCategories = computed(() => Object.keys(CATEGORY_SCHEMAS) as ProductCategory[])
  
  const currentSchema = computed(() => CATEGORY_SCHEMAS[selectedCategory.value])
  
  const categoryFields = computed(() => currentSchema.value.fields)
  
  // Reset category filters when category changes
  watch(selectedCategory, () => {
    categoryFilters.value = {}
  })
  
  const setCategory = (category: ProductCategory) => {
    selectedCategory.value = category
  }
  
  const setCategoryFilter = (fieldName: string, value: any) => {
    categoryFilters.value[fieldName] = value
  }
  
  const getCategoryFilter = (fieldName: string) => {
    return categoryFilters.value[fieldName]
  }
  
  const loadExistingFilters = (category: ProductCategory, filters: Record<string, any>) => {
    selectedCategory.value = category
    categoryFilters.value = { ...filters }
  }
  
  const validateFilters = (): { valid: boolean; errors: string[] } => {
    const errors: string[] = []
    
    for (const field of categoryFields.value) {
      const value = categoryFilters.value[field.name]
      
      if (field.validation?.required && !value) {
        errors.push(`${field.label} is required`)
      }
      
      if (value && field.type === 'integer') {
        const numValue = Number(value)
        if (isNaN(numValue)) {
          errors.push(`${field.label} must be a number`)
        }
        if (field.validation?.min !== undefined && numValue < field.validation.min) {
          errors.push(`${field.label} must be at least ${field.validation.min}`)
        }
        if (field.validation?.max !== undefined && numValue > field.validation.max) {
          errors.push(`${field.label} must be at most ${field.validation.max}`)
        }
      }
    }
    
    return { valid: errors.length === 0, errors }
  }
  
  return {
    selectedCategory,
    categoryFilters,
    availableCategories,
    currentSchema,
    categoryFields,
    setCategory,
    setCategoryFilter,
    getCategoryFilter,
    loadExistingFilters,
    validateFilters
  }
}

