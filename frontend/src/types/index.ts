export interface Listing {
  listing_idx: number;
  price: string;
  title: string;
  location: string;
  description: string | null;
  distance: number;
  url: string;
  img: string | null;
  query: string;
  search_title: string;
  watchlist: boolean;
  scanner_id: number;
  search_location: string;
  created_at: string;
  analysis_metadata?: Record<string, any>;
  investigation_completed?: boolean;
  investigation_result?: string;
  triage_interesting?: boolean;
  triage_confidence?: number;
  triage_reason?: string;
}

export type ProductCategory = 'general' | 'ai_beta' | string;

export type AgentType = string;  // Now dynamic - any slug string

export interface AgentInfo {
  id?: number;
  type: AgentType;      // Alias for slug (backward compat)
  slug?: string;        // The actual slug from DB
  name: string;
  description: string;
  enabled: boolean;
  triage_model?: string;
  analysis_model?: string;
  triage_prompt?: string;
  analysis_prompt?: string;
  icon: string;
  scanner_count?: number;
  created_at?: string;
  updated_at?: string;
}

export interface AgentFormData {
  name: string;
  slug: string;
  description: string;
  icon: string;
  triage_prompt: string;
  analysis_prompt: string;
  triage_model: string;
  analysis_model: string;
  enabled: boolean;
}

export interface GeneratePromptRequest {
  description: string;
}

export interface GeneratePromptResponse {
  suggested_name: string;
  suggested_slug: string;
  suggested_icon: string;
  suggested_description: string;
  triage_prompt: string;
  analysis_prompt: string;
  token_usage?: Record<string, number>;
}

export interface RefinePromptRequest {
  current_triage_prompt: string;
  current_analysis_prompt: string;
  feedback: string;
}

export interface RefinePromptResponse {
  triage_prompt: string;
  analysis_prompt: string;
  changes_summary: string;
  token_usage?: Record<string, number>;
}

export interface CategoryFilterField {
  name: string;
  type: 'integer' | 'text' | 'select' | 'multi_select';
  label: string;
  placeholder?: string;
  hint?: string;
  options?: string[];
  validation?: {
    min?: number;
    max?: number;
    required?: boolean;
  };
}

export interface CategorySchema {
  fields: CategoryFilterField[];
  keywords: string[];
  listing_type: string;
}

export interface Scanner {
  id: number;
  category: string;              // User's custom label
  product_category: ProductCategory;  // System category for filtering
  agent_type: AgentType;         // Legacy agent type string
  agent?: number;                // Agent FK (database ID)
  agent_slug?: string;           // Agent slug (preferred identifier)
  query: string;
  town?: string; // Optional for backward compatibility
  status: 'running' | 'stopped';
  location_ids?: number[];
  locations_data?: LocationMapping[];
  
  // Universal filters
  min_price?: number | null;
  max_price?: number | null;
  max_distance?: number | null;
  
  // Category-specific filters (JSON)
  category_filters?: Record<string, any>;
  
  // Notification settings
  notification_emails?: string[];
  
  // Deprecated fields (kept for backward compatibility)
  max_mileage?: number | null;
  
  created_at: string;
}

export interface AgentWithQueries {
  agent: AgentInfo;
  queries: Scanner[];
}

export interface LocationMapping {
  id: number;
  location: number;
  location_name: string;
  scanner: number;
}

export interface Location {
  id: number;
  name: string;
  marketplace_url_slug: string;
}

export interface Keyword {
  id: number;
  keyword: string;
  filterID: number;
}

export interface ScannerFormData {
  query: string;
  category: string;
  product_category?: ProductCategory;
  agent_type?: AgentType;
  agent_slug?: string;
  status: 'running' | 'stopped';
  location_ids: number[];
  
  // Notification settings
  notification_emails?: string[];
  
  // Universal filters (optional - AI handles filtering)
  min_price?: number | null;
  max_price?: number | null;
  max_distance?: number | null;
  
  // Category-specific filters
  category_filters?: Record<string, any>;
  
  // Deprecated (kept for compatibility)
  max_mileage?: number | null;
}

export interface LocationFormData {
  name: string;
  marketplace_url_slug: string;
}

// API Response types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  error?: string;
  message?: string;
  [key: string]: any;
} 