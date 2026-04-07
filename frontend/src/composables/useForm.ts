import { ref, reactive, computed } from 'vue'
import { useNotifications } from './useNotifications'

export interface FormField {
  value: any
  error: string | null
  touched: boolean
  required?: boolean
  validator?: (value: any) => string | null
}

export interface FormOptions {
  validateOnChange?: boolean
  validateOnBlur?: boolean
  showSuccessMessage?: boolean
  successMessage?: string
}

export const useForm = <T extends Record<string, any>>(
  initialData: T,
  options: FormOptions = {}
) => {
  const { notifySuccess, notifyError } = useNotifications()
  
  const {
    validateOnChange = true,
    validateOnBlur = true,
    showSuccessMessage = false,
    successMessage = 'Form submitted successfully'
  } = options

  // Create reactive form data
  const formData = reactive<T>({ ...initialData })
  
  // Create fields with validation state
  const fields = reactive<Record<keyof T, FormField>>(
    Object.keys(initialData).reduce((acc, key) => {
      acc[key as keyof T] = {
        value: initialData[key],
        error: null,
        touched: false
      }
      return acc
    }, {} as Record<keyof T, FormField>)
  )

  // Form state
  const isSubmitting = ref(false)
  const submitAttempted = ref(false)

  // Computed properties
  const hasErrors = computed(() => 
    Object.values(fields).some(field => field.error !== null)
  )

  const isValid = computed(() => 
    !hasErrors.value && Object.values(fields).every(field => field.touched || !field.required)
  )

  const isDirty = computed(() => 
    Object.keys(formData).some(key => 
      formData[key] !== initialData[key]
    )
  )

  // Validation rules
  const validators = reactive<Partial<Record<keyof T, (value: any) => string | null>>>({})

  // Set validator for a field
  const setValidator = (field: keyof T, validator: (value: any) => string | null) => {
    validators[field] = validator
  }

  // Validate a single field
  const validateField = (fieldName: keyof T) => {
    const field = fields[fieldName]
    const value = formData[fieldName]
    
    // Check required
    if (field.required && (value === null || value === undefined || value === '')) {
      field.error = `${String(fieldName)} is required`
      return false
    }

    // Check custom validator
    if (validators[fieldName]) {
      const validationResult = validators[fieldName]!(value)
      field.error = validationResult
      return validationResult === null
    }

    field.error = null
    return true
  }

  // Validate all fields
  const validateForm = () => {
    let isFormValid = true
    
    Object.keys(fields).forEach(key => {
      const fieldName = key as keyof T
      if (!validateField(fieldName)) {
        isFormValid = false
      }
    })
    
    return isFormValid
  }

  // Handle field changes
  const updateField = (fieldName: keyof T, value: any) => {
    formData[fieldName] = value
    fields[fieldName].value = value
    fields[fieldName].touched = true

    if (validateOnChange) {
      validateField(fieldName)
    }
  }

  // Handle field blur
  const handleBlur = (fieldName: keyof T) => {
    fields[fieldName].touched = true
    
    if (validateOnBlur) {
      validateField(fieldName)
    }
  }

  // Reset form
  const reset = () => {
    Object.keys(formData).forEach(key => {
      const fieldName = key as keyof T
      formData[fieldName] = initialData[fieldName]
      fields[fieldName].value = initialData[fieldName]
      fields[fieldName].error = null
      fields[fieldName].touched = false
    })
    
    isSubmitting.value = false
    submitAttempted.value = false
  }

  // Submit form
  const submit = async (submitFn: (data: T) => Promise<any>) => {
    submitAttempted.value = true
    
    if (!validateForm()) {
      notifyError('Please fix the form errors before submitting')
      return { success: false, data: null }
    }

    isSubmitting.value = true

    try {
      const result = await submitFn(formData)
      
      if (showSuccessMessage) {
        notifySuccess(successMessage)
      }
      
      return { success: true, data: result }
    } catch (error: any) {
      const errorMessage = error?.response?.data?.message || error?.message || 'Submission failed'
      notifyError(errorMessage)
      
      return { success: false, data: null, error: errorMessage }
    } finally {
      isSubmitting.value = false
    }
  }

  // Set field as required
  const setRequired = (fieldName: keyof T, required = true) => {
    fields[fieldName].required = required
  }

  // Get field error
  const getFieldError = (fieldName: keyof T) => {
    const field = fields[fieldName]
    return field.touched || submitAttempted.value ? field.error : null
  }

  // Check if field has error
  const hasFieldError = (fieldName: keyof T) => {
    return !!getFieldError(fieldName)
  }

  return {
    // Form data
    formData,
    fields,
    
    // State
    isSubmitting,
    submitAttempted,
    
    // Computed
    hasErrors,
    isValid,
    isDirty,
    
    // Methods
    setValidator,
    validateField,
    validateForm,
    updateField,
    handleBlur,
    reset,
    submit,
    setRequired,
    getFieldError,
    hasFieldError
  }
}

// Common validators
export const validators = {
  required: (message = 'This field is required') => 
    (value: any) => {
      if (value === null || value === undefined || value === '') {
        return message
      }
      return null
    },

  email: (message = 'Please enter a valid email address') => 
    (value: string) => {
      if (!value) return null // Let required validator handle empty values
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      return emailRegex.test(value) ? null : message
    },

  minLength: (min: number, message?: string) => 
    (value: string) => {
      if (!value) return null
      const actualMessage = message || `Must be at least ${min} characters`
      return value.length >= min ? null : actualMessage
    },

  maxLength: (max: number, message?: string) => 
    (value: string) => {
      if (!value) return null
      const actualMessage = message || `Must be no more than ${max} characters`
      return value.length <= max ? null : actualMessage
    },

  numeric: (message = 'Must be a number') => 
    (value: any) => {
      if (!value) return null
      return !isNaN(Number(value)) ? null : message
    },

  pattern: (regex: RegExp, message = 'Invalid format') => 
    (value: string) => {
      if (!value) return null
      return regex.test(value) ? null : message
    }
}
