import axios from 'axios';
import type { Scanner, AgentInfo, AgentFormData, GeneratePromptRequest, GeneratePromptResponse, RefinePromptRequest, RefinePromptResponse } from '@/types';

// Environment-based configuration
const isLocalNetwork = () => {
  const hostname = window.location.hostname;
  // Check for localhost, 127.0.0.1, or local network IPs (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
  return hostname === 'localhost' || 
         hostname === '127.0.0.1' ||
         hostname.startsWith('192.168.') ||
         hostname.startsWith('10.') ||
         /^172\.(1[6-9]|2[0-9]|3[0-1])\./.test(hostname);
};

const getApiUrl = () => {
  if (isLocalNetwork()) {
    // For local network access, use the same host but port 8000 for the backend
    const hostname = window.location.hostname;
    return `http://${hostname}:8000/api`;
  } else {
    // Return production API URL
    return 'https://flippy-production-9afd.up.railway.app/api';
  }
};

const getAuthUrl = () => {
  if (isLocalNetwork()) {
    // For local network access, use the same host but port 8000 for the backend
    const hostname = window.location.hostname;
    return `http://${hostname}:8000/auth`;
  } else {
    // Return production API URL
    return 'https://flippy-production-9afd.up.railway.app/auth';
  }
};

// Set dynamic API URLs
const API_URL = getApiUrl();
const AUTH_URL = getAuthUrl();

// Create an axios instance with dynamic baseURL
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Create auth client instance with dynamic baseURL
const authClient = axios.create({
  baseURL: AUTH_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add request interceptor to include the token in all API requests
apiClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;  // Use Bearer format for JWT
    }
    return config;
  },
  error => Promise.reject(error)
);

// Add request interceptor for authClient too
authClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;  // Use Bearer format for JWT
    }
    return config;
  },
  error => Promise.reject(error)
);

// Authentication functions
export const loginUser = async (username: string, password: string) => {
  try {
    const response = await authClient.post('/login/', { username, password });
    const { access, refresh } = response.data;
    
    // Store tokens and username
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    localStorage.setItem('user_name', username);
    
    return { success: true, token: access };
  } catch (error) {
    throw error;
  }
};

export const getUserProfile = async () => {
  // Since we simplified auth, we don't have user profiles anymore
  // Just return basic info from the token or localStorage
  try {
    const token = localStorage.getItem('access_token');
    const username = localStorage.getItem('user_name') || 'User';
    
    if (!token) {
      throw new Error('No authentication token found');
    }
    
    // Return basic user info - we don't have profile endpoints anymore
    return { 
      username: username,
      // You can decode the JWT token here if you need more info
    };
  } catch (error) {
    console.error('Error getting user info:', error);
    return { username: 'User' };
  }
};

export const refreshToken = async () => {
  try {
    const refresh = localStorage.getItem('refresh_token');
    
    if (!refresh) {
      throw new Error('No refresh token found');
    }
    
    const response = await authClient.post('/refresh/', { refresh });
    const { access } = response.data;
    
    // Store new access token
    localStorage.setItem('access_token', access);
    
    return { success: true, token: access };
  } catch (error) {
    // Clear tokens on refresh failure
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    throw error;
  }
};

export const logoutUser = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user_name');
  
  // Dispatch event to notify App.vue about logout
  window.dispatchEvent(new CustomEvent('auth-event', { 
    detail: { action: 'logout' } 
  }));
  
  return { success: true };
};

// Helper function to transform scanner data
const transformScannerData = (data: any) => {
  const transformed = { ...data };
  
  // Convert empty strings to null for numeric fields
  if (transformed.min_price === '' || transformed.min_price === '0') {
    transformed.min_price = null;
  } else if (transformed.min_price) {
    transformed.min_price = parseFloat(transformed.min_price);
  }
  
  if (transformed.max_price === '' || transformed.max_price === '0') {
    transformed.max_price = null;
  } else if (transformed.max_price) {
    transformed.max_price = parseFloat(transformed.max_price);
  }
  
  if (transformed.max_mileage === '' || transformed.max_mileage === '0') {
    transformed.max_mileage = null;
  } else if (transformed.max_mileage) {
    transformed.max_mileage = parseInt(transformed.max_mileage);
  }
  
  if (transformed.max_distance === '' || transformed.max_distance === '0') {
    transformed.max_distance = null;
  } else if (transformed.max_distance) {
    transformed.max_distance = parseInt(transformed.max_distance);
  }
  
  // Transform category_filters - convert empty strings to null for integer fields
  if (transformed.category_filters && typeof transformed.category_filters === 'object') {
    const cleanedFilters: Record<string, any> = {};
    for (const [key, value] of Object.entries(transformed.category_filters)) {
      if (value === '' || value === null || value === undefined) {
        // Skip empty values
        continue;
      }
      // Convert numeric strings to numbers
      if (typeof value === 'string' && !isNaN(Number(value))) {
        cleanedFilters[key] = Number(value);
      } else {
        cleanedFilters[key] = value;
      }
    }
    transformed.category_filters = cleanedFilters;
  }
  
  return transformed;
};

// ═══════════════════════════════════════════════════════════════════════════════
// AGENT API FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * Get all agents (lightweight, no prompts)
 */
export const getAgents = async (): Promise<AgentInfo[]> => {
  try {
    const response = await apiClient.get('/agents/');
    // Map API response to AgentInfo format
    return response.data.map((agent: any) => ({
      ...agent,
      type: agent.slug,  // Map slug to type for backward compatibility
    }));
  } catch (error) {
    console.error('Error fetching agents:', error);
    return [];
  }
};

/**
 * Get a single agent by slug (includes prompts)
 */
export const getAgent = async (slug: string): Promise<AgentInfo | null> => {
  try {
    const response = await apiClient.get(`/agents/${slug}/`);
    return {
      ...response.data,
      type: response.data.slug,
    };
  } catch (error) {
    console.error(`Error fetching agent ${slug}:`, error);
    return null;
  }
};

/**
 * Create a new agent
 */
export const createAgent = async (data: AgentFormData): Promise<AgentInfo | null> => {
  try {
    const response = await apiClient.post('/agents/', data);
    return {
      ...response.data,
      type: response.data.slug,
    };
  } catch (error: any) {
    console.error('Error creating agent:', error.response?.data || error);
    throw new Error(error.response?.data?.detail || JSON.stringify(error.response?.data) || 'Failed to create agent');
  }
};

/**
 * Update an existing agent
 */
export const updateAgent = async (slug: string, data: Partial<AgentFormData>): Promise<AgentInfo | null> => {
  try {
    const response = await apiClient.patch(`/agents/${slug}/`, data);
    return {
      ...response.data,
      type: response.data.slug,
    };
  } catch (error: any) {
    console.error(`Error updating agent ${slug}:`, error.response?.data || error);
    throw new Error(error.response?.data?.detail || JSON.stringify(error.response?.data) || 'Failed to update agent');
  }
};

/**
 * Delete an agent
 */
export const deleteAgent = async (slug: string): Promise<boolean> => {
  try {
    await apiClient.delete(`/agents/${slug}/`);
    return true;
  } catch (error: any) {
    console.error(`Error deleting agent ${slug}:`, error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to delete agent');
  }
};

/**
 * Duplicate an agent
 */
export const duplicateAgent = async (slug: string): Promise<AgentInfo | null> => {
  try {
    const response = await apiClient.post(`/agents/${slug}/duplicate/`);
    return {
      ...response.data,
      type: response.data.slug,
    };
  } catch (error: any) {
    console.error(`Error duplicating agent ${slug}:`, error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to duplicate agent');
  }
};

/**
 * Generate agent prompts using AI
 */
export const generateAgentPrompt = async (data: GeneratePromptRequest): Promise<GeneratePromptResponse> => {
  try {
    const response = await apiClient.post('/agents/generate-prompt/', data);
    return response.data;
  } catch (error: any) {
    console.error('Error generating prompts:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to generate prompts');
  }
};

/**
 * Refine existing agent prompts using AI
 */
export const refineAgentPrompt = async (data: RefinePromptRequest): Promise<RefinePromptResponse> => {
  try {
    const response = await apiClient.post('/agents/refine-prompt/', data);
    return response.data;
  } catch (error: any) {
    console.error('Error refining prompts:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to refine prompts');
  }
};

/**
 * Suggest search queries for an agent based on its prompts.
 */
export const suggestAgentQueries = async (slug: string): Promise<{ suggestions: string[] }> => {
  try {
    const response = await apiClient.get(`/agents/${slug}/suggest-queries/`);
    return response.data;
  } catch (error: any) {
    console.error('Error suggesting queries:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to suggest queries');
  }
};

/**
 * Analyze a single Facebook Marketplace listing URL with a specific agent.
 * Scrapes the listing, runs analysis, saves to DB, and returns the result.
 */
export const analyzeListingUrl = async (slug: string, url: string): Promise<any> => {
  try {
    const response = await apiClient.post(`/agents/${slug}/analyze-url/`, { url }, {
      timeout: 120000  // 2 min timeout - scraping + analysis takes time
    });
    return response.data;
  } catch (error: any) {
    console.error('Error analyzing URL:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to analyze listing');
  }
};

// Scanner API functions
export const getScanners = async (): Promise<Scanner[]> => {
  try {
    console.log('Fetching scanners from:', `${API_URL}/scanners/`);
    const response = await apiClient.get('/scanners/');
    console.log('API response:', response);
    return response.data;
  } catch (error) {
    console.error('Error fetching scanners:', error);
    return [];
  }
};

export const createScanner = async (scannerData: Omit<Scanner, 'id'>): Promise<Scanner | null> => {
  try {
    // Transform the data to handle empty string values
    const transformedData = transformScannerData(scannerData);
    const response = await apiClient.post('/scanners/', transformedData);
    return response.data;
  } catch (error: any) {
    console.error('Error creating scanner:', error.response?.data || error);
    throw new Error(error.response?.data?.detail || 'Failed to create scanner');
  }
};

export const updateScanner = async (id: number, scannerData: Partial<Scanner>): Promise<Scanner | null> => {
  try {
    // Transform the data to handle empty string values
    const transformedData = transformScannerData(scannerData);
    const response = await apiClient.patch(`/scanners/${id}/`, transformedData);
    return response.data;
  } catch (error: any) {
    console.error(`Error updating scanner ${id}:`, error.response?.data || error);
    throw new Error(error.response?.data?.detail || 'Failed to update scanner');
  }
};

export const deleteScanner = async (id: number): Promise<boolean> => {
  try {
    await apiClient.delete(`/scanners/${id}/`);
    return true;
  } catch (error) {
    console.error(`Error deleting scanner ${id}:`, error);
    return false;
  }
};

export const toggleScannerStatus = async (id: number, currentStatus: string): Promise<Scanner | null> => {
  const newStatus = currentStatus === 'running' ? 'stopped' : 'running';
  return updateScanner(id, { status: newStatus });
};

/**
 * Fetches keywords associated with a specific scanner
 * @param scannerId The ID of the scanner to fetch keywords for
 * @returns Array of keyword strings or empty array on error
 */
export const getKeywordsByScanner = async (scannerId: number): Promise<any[]> => {
  try {
    console.log(`Fetching keywords for scanner ${scannerId}`);
    const response = await apiClient.get(`/keywords/by-scanner/?scannerId=${scannerId}`);
    console.log('Keywords response:', response.data);
    return response.data;
  } catch (error: any) {
    console.error('Error fetching keywords:', error.response?.data || error);
    return [];
  }
};

/**
 * Updates keywords in bulk for a specific scanner
 * @param scannerId The ID of the scanner to update keywords for
 * @param keywords Array of keyword strings
 * @returns Updated keywords array or empty array on error
 */
export const updateKeywords = async (scannerId: number, keywords: string[]): Promise<boolean> => {
  try {
    console.log(`Updating keywords for scanner ${scannerId}:`, keywords);
    const response = await apiClient.post(`/keywords/bulk-update/`, {
      scannerId: scannerId,
      keywords: keywords
    });
    console.log('Update keywords response:', response.data);
    return true;
  } catch (error: any) {
    console.error('Error updating keywords:', error.response?.data || error);
    throw new Error(error.response?.data?.detail || 'Failed to update keywords');
  }
};

// Listing API functions
export interface ListingFilters {
  search_location?: string;
  min_price?: number | null;
  max_price?: number | null;
  watchlist?: boolean;
  max_distance?: number | null;
  agent_slug?: string;
  scanner_id?: number | null;
  interesting_only?: boolean;
  notify_only?: boolean;
  page?: number;
  limit?: number;
}

export const getListings = async (page = 1, limit = 20, filters: ListingFilters = {}): Promise<any> => {
  try {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('limit', limit.toString());
    
    if (filters.search_location) params.append('search_location', filters.search_location);
    if (filters.min_price !== null && filters.min_price !== undefined) 
      params.append('min_price', filters.min_price.toString());
    if (filters.max_price !== null && filters.max_price !== undefined) 
      params.append('max_price', filters.max_price.toString());
    if (filters.max_distance !== null && filters.max_distance !== undefined)
      params.append('max_distance', filters.max_distance.toString());
    if (filters.watchlist) params.append('watchlist', 'true');
    if (filters.agent_slug) params.append('agent_slug', filters.agent_slug);
    if (filters.scanner_id !== null && filters.scanner_id !== undefined)
      params.append('scanner_id', filters.scanner_id.toString());
    if (filters.interesting_only) params.append('interesting_only', 'true');
    if (filters.notify_only) params.append('notify_only', 'true');

    console.log('Applying filters:', params.toString());
    
    const response = await apiClient.get('/listings/', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching listings:', error);
    return [];
  }
};

/**
 * Gets filter options for listings
 * @returns Available filter options including queries, categories, and scanner locations
 */
export const getFilterOptions = async (): Promise<{
  search_locations: string[];
  agents: { slug: string; name: string }[];
  scanners: { id: number; query: string; agent_slug: string }[];
}> => {
  try {
    const response = await apiClient.get('/listings/filter_options/');
    return response.data;
  } catch (error) {
    console.error('Error fetching filter options:', error);
    throw error;
  }
};

/**
 * Toggles a listing's watchlist status
 * @param listingId The ID of the listing to toggle
 * @param currentStatus The current watchlist status
 * @returns Updated listing data or null on error
 */
export const toggleWatchlist = async (listingId: string | number, currentStatus: boolean): Promise<any> => {
  try {
    const response = await apiClient.patch(`/listings/${listingId}/`, {
      watchlist: !currentStatus
    });
    return response.data;
  } catch (error) {
    console.error(`Error toggling watchlist for listing ${listingId}:`, error);
    return null;
  }
};

// Location API functions
export const getLocations = async (): Promise<any[]> => {
  try {
    const response = await apiClient.get('/locations/');
    return response.data;
  } catch (error) {
    console.error('Error fetching locations:', error);
    return [];
  }
};

export const createLocation = async (locationData: { name: string; marketplace_url_slug: string }): Promise<any | null> => {
  try {
    const response = await apiClient.post('/locations/', locationData);
    return response.data;
  } catch (error: any) {
    console.error('Error creating location:', error.response?.data || error);
    throw new Error(error.response?.data?.detail || 'Failed to create location');
  }
};

// Scanner Control API functions
export const startScanner = async (interval: number = 20, randomize: boolean = true): Promise<any> => {
  try {
    const response = await apiClient.post('/scanner/start/', {
      interval,
      randomize
    });
    return response.data;
  } catch (error: any) {
    console.error('Error starting scanner:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to start scanner');
  }
};

export const stopScanner = async (): Promise<any> => {
  try {
    const response = await apiClient.post('/scanner/stop/');
    return response.data;
  } catch (error: any) {
    console.error('Error stopping scanner:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to stop scanner');
  }
};

export const getScannerStatus = async (): Promise<any> => {
  try {
    const response = await apiClient.get('/scanner/status/');
    return response.data;
  } catch (error: any) {
    console.error('Error getting scanner status:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to get scanner status');
  }
};

export const runSingleScan = async (randomize: boolean = true): Promise<any> => {
  try {
    const response = await apiClient.post('/scanner/single-run/', {
      randomize
    });
    return response.data;
  } catch (error: any) {
    console.error('Error running single scan:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to run single scan');
  }
};

export const getScanHistory = async (): Promise<any> => {
  try {
    const response = await apiClient.get('/scanner/history/');
    return response.data;
  } catch (error: any) {
    console.error('Error fetching scan history:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to fetch scan history');
  }
};

// Notification API functions
export const testNotifications = async (channels?: string[], sendSample: boolean = false): Promise<any> => {
  try {
    const data: { channels?: string[], send_sample: boolean } = { send_sample: sendSample };
    if (channels) {
      data.channels = channels;
    }
    
    const response = await apiClient.post('/notifications/test/', data);
    return response.data;
  } catch (error: any) {
    console.error('Error testing notifications:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to test notifications');
  }
};

export const getNotificationStatus = async (): Promise<any> => {
  try {
    const response = await apiClient.get('/notifications/status/');
    return response.data;
  } catch (error: any) {
    console.error('Error getting notification status:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to get notification status');
  }
};

export const sendScanNotifications = async (scanId: string): Promise<any> => {
  try {
    const response = await apiClient.post(`/scan-batches/${scanId}/send-notifications/`);
    return response.data;
  } catch (error: any) {
    console.error('Error sending notifications:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to send notifications');
  }
};

// Phase 2: Scan Batch API functions
export const getScanBatches = async (page = 1, limit = 10): Promise<any> => {
  try {
    const response = await apiClient.get('/scan-batches/', {
      params: { page, limit }
    });
    return response.data;
  } catch (error: any) {
    console.error('Error fetching scan batches:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to fetch scan batches');
  }
};

export const getScanBatch = async (scanId: string): Promise<any> => {
  try {
    const response = await apiClient.get(`/scan-batches/${scanId}/`);
    return response.data;
  } catch (error: any) {
    console.error('Error fetching scan batch:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to fetch scan batch');
  }
};

export const getScanBatchListings = async (scanId: string, page = 1, limit = 20, filter = 'all'): Promise<any> => {
  try {
    const response = await apiClient.get(`/scan-batches/${scanId}/listings/`, {
      params: { page, limit, filter }
    });
    return response.data;
  } catch (error: any) {
    console.error('Error fetching scan batch listings:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to fetch scan batch listings');
  }
};

// Run detailed analysis on a scan batch
export const runDetailedAnalysis = async (scanId: string): Promise<any> => {
  try {
    const response = await apiClient.post(`/scan-batches/${scanId}/analyze/`);
    return response.data;
  } catch (error: any) {
    console.error('Error running detailed analysis:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to run detailed analysis');
  }
};

export const resetAnalysisStatus = async (scanId: string): Promise<any> => {
  try {
    const response = await apiClient.post(`/scan-batches/${scanId}/reset-analysis/`);
    return response.data;
  } catch (error: any) {
    console.error('Error resetting analysis status:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to reset analysis status');
  }
};

// AI Analysis API functions
export const analyzeListing = async (listingId: number, force: boolean = false): Promise<any> => {
  try {
    const params = force ? { force: 'true' } : {};
    const response = await apiClient.post(`/listings/${listingId}/analyze-ai/`, {}, { params });
    return response.data;
  } catch (error: any) {
    console.error('Error analyzing listing with AI:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to analyze listing with AI');
  }
};

export const getAIAnalysis = async (listingId: number): Promise<any> => {
  try {
    const response = await apiClient.get(`/listings/${listingId}/ai-analysis/`);
    return response.data;
  } catch (error: any) {
    console.error('Error fetching AI analysis:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to fetch AI analysis');
  }
};

// Manual AI Analysis Control (New Architecture)

export const toggleInvestigationStatus = async (
  listingId: number,
  needsInvestigation: boolean
): Promise<any> => {
  try {
    const response = await apiClient.post('/listings/toggle-investigation/', {
      listing_id: listingId,
      needs_investigation: needsInvestigation
    });
    return response.data;
  } catch (error: any) {
    console.error('Error toggling investigation status:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to toggle investigation status');
  }
};

export const runDeepAnalysis = async (
  listingIds: number[],
  scanBatchId?: string
): Promise<any> => {
  try {
    const response = await apiClient.post('/listings/deep-analysis/', {
      listing_ids: listingIds,
      scan_batch_id: scanBatchId
    });
    return response.data;
  } catch (error: any) {
    console.error('Error running deep analysis:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to run deep analysis');
  }
};

export const rerunTriage = async (
  scanBatchId: string
): Promise<any> => {
  try {
    const response = await apiClient.post(`/scan-batches/${scanBatchId}/rerun-triage/`);
    return response.data;
  } catch (error: any) {
    console.error('Error re-running triage:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to re-run triage');
  }
};

// ═══════════════════════════════════════════════════════════════════════════════
// TASK STATUS & SCANNER SETTINGS API
// ═══════════════════════════════════════════════════════════════════════════════

export interface SystemTask {
  id: number;
  task_type: string;
  task_type_display: string;
  status: string;
  status_display: string;
  current_step: string;
  step_display: string;
  progress_percent: number;
  progress_message: string;
  started_at: string;
  completed_at: string | null;
  elapsed_seconds: number;
  scan_batch_id: string | null;
  details: Record<string, any>;
}

export interface ScannerSettings {
  id: number;
  mode: 'auto' | 'manual';
  mode_display: string;
  auto_enabled: boolean;
  interval_minutes: number;
  randomize_order: boolean;
  last_scan_at: string | null;
  next_scan_at: string | null;
  auto_process_pid: number | null;
  can_run_manual: boolean;
  can_enable_auto: boolean;
  time_until_next_scan: number | null;
  // Schedule window
  schedule_enabled: boolean;
  schedule_start: string;   // "HH:MM:SS"
  schedule_end: string;     // "HH:MM:SS"
  schedule_timezone: string;
  schedule_active: boolean; // computed: is current time inside the window?
}

/**
 * Get the currently running task (if any)
 */
export const getCurrentTask = async (): Promise<{ busy: boolean; task: SystemTask | null }> => {
  try {
    const response = await apiClient.get('/task/current/');
    return response.data;
  } catch (error: any) {
    console.error('Error getting current task:', error.response?.data || error);
    return { busy: false, task: null };
  }
};

/**
 * Get recent task history
 */
export const getTaskHistory = async (limit: number = 10): Promise<{ tasks: SystemTask[] }> => {
  try {
    const response = await apiClient.get('/task/history/', { params: { limit } });
    return response.data;
  } catch (error: any) {
    console.error('Error getting task history:', error.response?.data || error);
    return { tasks: [] };
  }
};

/**
 * Get scanner settings
 */
export const getScannerSettings = async (): Promise<ScannerSettings> => {
  try {
    const response = await apiClient.get('/settings/');
    return response.data;
  } catch (error: any) {
    console.error('Error getting scanner settings:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to get scanner settings');
  }
};

/**
 * Update scanner settings
 */
export const updateScannerSettings = async (
  settings: Partial<Pick<ScannerSettings, 'interval_minutes' | 'randomize_order' | 'schedule_enabled' | 'schedule_start' | 'schedule_end' | 'schedule_timezone'>>
): Promise<ScannerSettings> => {
  try {
    const response = await apiClient.post('/settings/update/', settings);
    return response.data;
  } catch (error: any) {
    console.error('Error updating scanner settings:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to update scanner settings');
  }
};

/**
 * Set scanner mode (auto or manual)
 */
export const setScannerMode = async (mode: 'auto' | 'manual'): Promise<any> => {
  try {
    const response = await apiClient.post('/settings/mode/', { mode });
    return response.data;
  } catch (error: any) {
    console.error('Error setting scanner mode:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to set scanner mode');
  }
};

/**
 * Enable automatic scanning
 */
export const enableAutoScan = async (interval_minutes?: number): Promise<any> => {
  try {
    const data = interval_minutes ? { interval_minutes } : {};
    const response = await apiClient.post('/settings/auto/enable/', data);
    return response.data;
  } catch (error: any) {
    console.error('Error enabling auto scan:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to enable auto scan');
  }
};

/**
 * Disable automatic scanning
 */
export const disableAutoScan = async (): Promise<any> => {
  try {
    const response = await apiClient.post('/settings/auto/disable/');
    return response.data;
  } catch (error: any) {
    console.error('Error disabling auto scan:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to disable auto scan');
  }
};

/**
 * Run a manual scan (with task tracking)
 */
export const runManualScan = async (): Promise<any> => {
  try {
    const response = await apiClient.post('/manual-scan/');
    return response.data;
  } catch (error: any) {
    console.error('Error running manual scan:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to run manual scan');
  }
};

/**
 * Clear stuck/stale tasks
 */
export const clearStuckTasks = async (force: boolean = false): Promise<any> => {
  try {
    const response = await apiClient.post('/task/clear/', { force });
    return response.data;
  } catch (error: any) {
    console.error('Error clearing stuck tasks:', error.response?.data || error);
    throw new Error(error.response?.data?.error || 'Failed to clear stuck tasks');
  }
};