<template>
  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex flex-wrap justify-between items-start gap-3 mb-6">
      <div>
        <h2 class="text-xl font-bold text-white">Scan Results</h2>
        <p class="text-gray-500 text-sm" v-if="scanBatch">
          {{ formatDateTime(scanBatch.started_at) }} · {{ scanBatch.scan_type === 'single' ? 'Manual' : 'Auto' }} scan
        </p>
      </div>
      <div class="flex items-center space-x-3">
        <!-- Re-run Actions (lowkey dropdown) -->
        <div class="relative" v-if="scanBatch">
          <button 
            @click="showActionsMenu = !showActionsMenu"
            class="px-3 py-2 text-sm text-gray-400 hover:text-white flex items-center"
          >
            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"></path>
            </svg>
            Actions
          </button>
          <div 
            v-if="showActionsMenu"
            class="absolute right-0 mt-1 w-48 bg-[#1C1C1E] border border-gray-700 rounded-lg shadow-xl z-50"
          >
            <button
              @click="rerunTriage(); showActionsMenu = false"
              :disabled="isRerunningTriage"
              class="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 flex items-center"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              {{ isRerunningTriage ? 'Running...' : 'Re-run Triage' }}
            </button>
            <button
              @click="resetAnalysis(); showActionsMenu = false"
              :disabled="analysisLoading"
              class="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 flex items-center"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
              Reset Analysis
            </button>
            <button
              @click="sendNotifications(); showActionsMenu = false"
              :disabled="isSendingNotifications || notifyCount === 0"
              class="w-full px-4 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 flex items-center"
              :class="{ 'opacity-50 cursor-not-allowed': notifyCount === 0 }"
            >
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
              </svg>
              {{ isSendingNotifications ? 'Sending...' : `Send Notifications (${notifyCount})` }}
            </button>
          </div>
        </div>
        <button 
          @click="refreshData" 
          class="px-3 py-2 rounded border border-gray-700 text-gray-300 text-sm hover:bg-gray-800 transition-colors"
          :disabled="loading"
        >
          {{ loading ? 'Loading...' : 'Refresh' }}
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div v-if="error" class="bg-red-500/10 text-red-400 p-4 rounded-lg mb-4 text-sm">
      {{ error }}
    </div>
    <div v-if="successMessage" class="bg-green-500/10 text-green-400 p-4 rounded-lg mb-4 text-sm">
      {{ successMessage }}
    </div>

    <!-- Loading State -->
    <div v-if="loading && !scanBatch" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      <p class="text-gray-400 mt-3">Loading scan results...</p>
    </div>

    <!-- Filters -->
    <div v-if="scanBatch" class="flex flex-wrap items-center gap-2 mb-6">
      <button
        v-for="filter in listingFilters"
        :key="filter.key"
        @click="applyFilter(filter.key)"
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          activeFilter === filter.key
            ? filter.color || 'bg-blue-600 text-white'
            : 'bg-[#1C1C1E] text-gray-400 hover:text-white hover:bg-gray-800'
        ]"
      >
        {{ filter.label }}
        <span v-if="filter.count !== undefined" class="ml-1 opacity-70">({{ filter.count }})</span>
      </button>
    </div>

    <!-- Bulk Actions (for interesting listings ready for Pass 2) -->
    <div v-if="activeFilter === 'interesting' && interestingListings.length > 0" 
      class="bg-gradient-to-r from-yellow-900/20 to-purple-900/20 border border-yellow-800/30 rounded-lg p-4 mb-6">
      <div class="flex flex-col md:flex-row md:justify-between md:items-center gap-4">
        <div>
          <h3 class="text-white font-medium">Ready for Deep Analysis (Pass 2)</h3>
          <p class="text-sm text-gray-400">
            These {{ interestingListings.length }} listings were flagged as interesting. Select which ones to analyze in detail.
          </p>
        </div>
        <div class="flex items-center space-x-3">
          <div class="flex items-center space-x-2 text-sm">
            <span class="text-white font-medium">{{ selectedCount }}</span>
            <span class="text-gray-400">selected</span>
            <button @click="selectAllInteresting" class="text-blue-400 hover:text-blue-300 ml-2">Select All</button>
            <button v-if="selectedCount > 0" @click="deselectAll" class="text-gray-400 hover:text-gray-300">Clear</button>
          </div>
          <button
            @click="analyzeSelectedListings"
            :disabled="selectedCount === 0 || isAnalyzingSelected"
            class="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm font-medium rounded-lg transition-colors flex items-center"
          >
            <svg v-if="!isAnalyzingSelected" class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
            <div v-else class="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            {{ isAnalyzingSelected ? 'Running Pass 2...' : 'Run Pass 2 Analysis' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Listings -->
    <div v-if="listingsLoading" class="text-center py-12">
      <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
    </div>

    <div v-else-if="filteredListings.length === 0" class="text-center py-12">
      <p class="text-gray-500">No listings found</p>
    </div>

    <div v-else class="space-y-4">
      <div
        v-for="listing in filteredListings"
        :key="listing.listing_idx"
        class="bg-[#121212] rounded-lg border border-gray-800 overflow-hidden hover:border-gray-700 transition-colors"
      >
        <!-- Listing Card -->
        <div class="p-4">
          <div class="flex gap-4">
            <!-- Checkbox (for interesting filter) -->
            <div v-if="activeFilter === 'interesting'" class="flex-shrink-0 pt-1">
              <input
                type="checkbox"
                :checked="selectedListingIds.has(listing.listing_idx)"
                @change="toggleSelection(listing.listing_idx)"
                class="w-5 h-5 rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-blue-500 cursor-pointer"
              />
            </div>

            <!-- Image -->
            <div 
              class="flex-shrink-0 w-28 h-28 bg-gray-900 rounded-lg overflow-hidden cursor-pointer"
              @click="toggleExpanded(listing.listing_idx)"
            >
              <img
                v-if="listing.img"
                :src="listing.img"
                :alt="listing.title"
                class="w-full h-full object-cover"
                @error="($event.target as HTMLImageElement).style.display = 'none'"
              />
              <div v-else class="w-full h-full flex items-center justify-center text-gray-600">
                <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                </svg>
              </div>
            </div>

            <!-- Content -->
            <div class="flex-1 min-w-0">
              <!-- Title & Price Row -->
              <div class="flex justify-between items-start gap-4 mb-2">
                <h3 
                  class="text-white font-medium cursor-pointer hover:text-blue-400 transition-colors line-clamp-2"
                  @click="toggleExpanded(listing.listing_idx)"
                >
                  {{ listing.title }}
                </h3>
                <span class="text-green-400 font-bold text-lg flex-shrink-0">{{ listing.price }}</span>
              </div>

              <!-- Location & Date -->
              <div class="flex items-center text-sm text-gray-500 mb-3">
                <span>{{ listing.location }}</span>
                <span class="mx-2">·</span>
                <span>{{ formatDateTime(listing.created_at) }}</span>
              </div>

              <!-- Status Badges -->
              <div class="flex flex-wrap items-center gap-2">
                <!-- Pass 2: Deep Analysis Result (takes priority) -->
                <template v-if="hasDeepAnalysis(listing)">
                  <span
                    class="inline-flex items-center px-3 py-1 rounded-md text-xs font-bold"
                    :class="listing.analysis_metadata.recommendation === 'NOTIFY' 
                      ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                      : 'bg-red-500/20 text-red-400 border border-red-500/30'"
                  >
                    {{ listing.analysis_metadata.recommendation === 'NOTIFY' ? '✅' : '❌' }}
                    {{ listing.analysis_metadata.recommendation }}
                    ({{ listing.analysis_metadata.confidence || 0 }}%)
                  </span>
                </template>
                
                <!-- Pass 1: Triage Result (only show if no deep analysis) -->
                <template v-else>
                  <span
                    v-if="listing.triage_interesting === true"
                    class="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-yellow-500/20 text-yellow-400 border border-yellow-500/30"
                  >
                    🟡 Interesting ({{ listing.triage_confidence || 0 }}%)
                  </span>
                  <span
                    v-else-if="listing.triage_interesting === false"
                    class="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-gray-700/50 text-gray-400"
                  >
                    Skipped
                  </span>
                  <span
                    v-else
                    class="inline-flex items-center px-3 py-1 rounded-md text-xs font-medium bg-gray-800 text-gray-500"
                  >
                    Not Triaged
                  </span>
                </template>
              </div>

              <!-- AI Reasoning (Triage or Summary) -->
              <div v-if="!isExpanded(listing.listing_idx)" class="mt-3">
                <!-- Deep Analysis Summary -->
                <p
                  v-if="hasDeepAnalysis(listing) && listing.analysis_metadata.summary"
                  class="text-sm text-gray-300 line-clamp-2 border-l-2 border-green-500 pl-3"
                >
                  {{ listing.analysis_metadata.summary }}
                </p>
                <!-- Triage Reason -->
                <p
                  v-else-if="listing.triage_reason"
                  class="text-sm text-gray-400 line-clamp-2 border-l-2 pl-3"
                  :class="listing.triage_interesting ? 'border-yellow-500' : 'border-gray-600'"
                >
                  <span class="text-gray-500">AI Triage:</span> {{ listing.triage_reason }}
                </p>
              </div>
            </div>

            <!-- Expand Arrow -->
            <div class="flex-shrink-0 self-center">
              <button
                @click="toggleExpanded(listing.listing_idx)"
                class="p-2 text-gray-500 hover:text-white transition-colors"
              >
                <svg 
                  class="w-5 h-5 transition-transform" 
                  :class="{ 'rotate-180': isExpanded(listing.listing_idx) }"
                  fill="none" stroke="currentColor" viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Expanded Details -->
        <div v-if="isExpanded(listing.listing_idx)" class="border-t border-gray-800 p-4 bg-[#0D1117]">
          <!-- Quick Actions -->
          <div class="flex items-center justify-between mb-4">
            <a
              :href="listing.url"
              target="_blank"
              class="text-blue-400 hover:text-blue-300 text-sm font-medium flex items-center"
            >
              View Original Listing
              <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path>
              </svg>
            </a>
            <button
              v-if="hasDeepAnalysis(listing)"
              @click="reanalyze(listing)"
              :disabled="reanalyzingId === listing.listing_idx"
              class="text-sm text-gray-400 hover:text-purple-400 flex items-center transition-colors"
            >
              <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
              {{ reanalyzingId === listing.listing_idx ? 'Analyzing...' : 'Re-analyze' }}
            </button>
          </div>

          <!-- PASS 1 ONLY: Triage Results (no deep analysis yet) -->
          <div v-if="!hasDeepAnalysis(listing)" class="space-y-4">
            <!-- Triage Status Card -->
            <div 
              class="rounded-lg p-4 border-l-4"
              :class="listing.triage_interesting 
                ? 'bg-yellow-500/10 border-yellow-500' 
                : 'bg-gray-800/50 border-gray-600'"
            >
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center space-x-3">
                  <span class="text-2xl">{{ listing.triage_interesting ? '🟡' : '⚪' }}</span>
                  <div>
                    <div class="text-lg font-bold" :class="listing.triage_interesting ? 'text-yellow-400' : 'text-gray-400'">
                      {{ listing.triage_interesting ? 'Marked Interesting' : 'Skipped by AI' }}
                    </div>
                    <div class="text-sm text-gray-500">
                      Pass 1 Triage · {{ listing.triage_confidence || 0 }}% confidence
                    </div>
                  </div>
                </div>
              </div>
              <p v-if="listing.triage_reason" class="text-sm text-gray-300 mt-3">
                {{ listing.triage_reason }}
              </p>
            </div>

            <!-- Run Deep Analysis CTA -->
            <div class="bg-purple-900/20 border border-purple-800/50 rounded-lg p-4 text-center">
              <p class="text-gray-400 mb-3">
                {{ listing.triage_interesting 
                  ? 'This listing is marked for deep analysis. Run Pass 2 to get detailed insights.' 
                  : 'AI skipped this listing during triage. You can still run a deep analysis manually.' 
                }}
              </p>
              <button
                @click="reanalyze(listing)"
                :disabled="reanalyzingId === listing.listing_idx"
                class="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 text-white text-sm font-medium rounded-lg transition-colors inline-flex items-center"
              >
                <svg v-if="reanalyzingId !== listing.listing_idx" class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                </svg>
                <div v-else class="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                {{ reanalyzingId === listing.listing_idx ? 'Running Deep Analysis...' : 'Run Deep Analysis (Pass 2)' }}
              </button>
            </div>
          </div>

          <!-- PASS 2: Deep Analysis Results -->
          <div v-else class="space-y-4">
            
            <!-- Recommendation Header -->
            <div 
              class="rounded-lg p-4 border-l-4"
              :class="listing.analysis_metadata.recommendation === 'NOTIFY' 
                ? 'bg-green-500/10 border-green-500' 
                : 'bg-gray-800 border-gray-600'"
            >
              <div class="flex items-center justify-between mb-2">
                <div class="flex items-center space-x-3">
                  <span class="text-2xl">
                    {{ listing.analysis_metadata.recommendation === 'NOTIFY' ? '✅' : '❌' }}
                  </span>
                  <div>
                    <div 
                      class="text-lg font-bold"
                      :class="listing.analysis_metadata.recommendation === 'NOTIFY' ? 'text-green-400' : 'text-gray-400'"
                    >
                      {{ listing.analysis_metadata.recommendation }}
                    </div>
                    <div class="text-sm text-gray-500">{{ listing.analysis_metadata.confidence }}% confidence</div>
                  </div>
                </div>
                <div class="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div 
                    class="h-full rounded-full"
                    :class="listing.analysis_metadata.recommendation === 'NOTIFY' ? 'bg-green-500' : 'bg-gray-500'"
                    :style="{ width: `${listing.analysis_metadata.confidence || 0}%` }"
                  ></div>
                </div>
              </div>
              <p v-if="listing.analysis_metadata.summary" class="text-sm text-gray-300">
                {{ listing.analysis_metadata.summary }}
              </p>
            </div>

            <!-- Item Details -->
            <div v-if="listing.analysis_metadata.item_identification" class="bg-gray-800/50 rounded-lg p-4">
              <h4 class="text-sm font-medium text-gray-400 mb-3 flex items-center">
                <span class="mr-2">🏷️</span> Item Details
              </h4>
              <div class="grid grid-cols-2 md:grid-cols-3 gap-x-6 gap-y-2">
                <div v-if="listing.analysis_metadata.item_identification.brand" class="text-sm">
                  <span class="text-gray-500">Brand:</span>
                  <span class="text-white ml-2">{{ listing.analysis_metadata.item_identification.brand }}</span>
                </div>
                <div v-if="listing.analysis_metadata.item_identification.model" class="text-sm">
                  <span class="text-gray-500">Model:</span>
                  <span class="text-white ml-2">{{ listing.analysis_metadata.item_identification.model }}</span>
                </div>
                <div v-if="listing.analysis_metadata.item_identification.year" class="text-sm">
                  <span class="text-gray-500">Year:</span>
                  <span class="text-white ml-2">{{ listing.analysis_metadata.item_identification.year }}</span>
                </div>
                <div v-if="listing.analysis_metadata.item_identification.size" class="text-sm">
                  <span class="text-gray-500">Size:</span>
                  <span class="text-white ml-2">{{ listing.analysis_metadata.item_identification.size }}</span>
                </div>
                <div v-if="listing.analysis_metadata.item_identification.condition" class="text-sm">
                  <span class="text-gray-500">Condition:</span>
                  <span class="text-white ml-2">{{ listing.analysis_metadata.item_identification.condition }}</span>
                </div>
                <div v-if="listing.analysis_metadata.item_identification.includes" class="text-sm">
                  <span class="text-gray-500">Includes:</span>
                  <span class="text-white ml-2">{{ listing.analysis_metadata.item_identification.includes }}</span>
                </div>
              </div>
            </div>

            <!-- Value Assessment -->
            <div v-if="listing.analysis_metadata.value_assessment" class="bg-gray-800/50 rounded-lg p-4">
              <h4 class="text-sm font-medium text-gray-400 mb-3 flex items-center">
                <span class="mr-2">💰</span> Value Assessment
              </h4>
              <div class="grid grid-cols-3 gap-4 mb-3">
                <div class="text-center bg-gray-900/50 rounded-lg p-3">
                  <div class="text-xs text-gray-500 uppercase mb-1">Listed Price</div>
                  <div class="text-lg font-bold text-white">{{ listing.price }}</div>
                </div>
                <div class="text-center bg-gray-900/50 rounded-lg p-3">
                  <div class="text-xs text-gray-500 uppercase mb-1">Est. Value</div>
                  <div class="text-lg font-bold text-green-400">
                    {{ listing.analysis_metadata.value_assessment.estimated_value || 'N/A' }}
                  </div>
                </div>
                <div class="text-center bg-gray-900/50 rounded-lg p-3">
                  <div class="text-xs text-gray-500 uppercase mb-1">Savings</div>
                  <div class="text-lg font-bold text-yellow-400">
                    {{ listing.analysis_metadata.value_assessment.potential_savings || 'N/A' }}
                  </div>
                </div>
              </div>
              <p v-if="listing.analysis_metadata.value_assessment.assessment" class="text-sm text-gray-400">
                {{ listing.analysis_metadata.value_assessment.assessment }}
              </p>
            </div>

            <!-- Key Takeaways -->
            <div v-if="listing.analysis_metadata.key_takeaways" class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <!-- Pros -->
              <div v-if="listing.analysis_metadata.key_takeaways.pros?.length" class="bg-green-900/20 rounded-lg p-4 border border-green-800/50">
                <h4 class="text-sm font-medium text-green-400 mb-2">Why This Is Good</h4>
                <ul class="space-y-1">
                  <li v-for="(pro, idx) in listing.analysis_metadata.key_takeaways.pros" :key="idx" class="text-sm text-gray-300 flex">
                    <span class="text-green-400 mr-2">+</span>
                    {{ pro }}
                  </li>
                </ul>
              </div>
              <!-- Cons -->
              <div v-if="listing.analysis_metadata.key_takeaways.cons?.length" class="bg-red-900/20 rounded-lg p-4 border border-red-800/50">
                <h4 class="text-sm font-medium text-red-400 mb-2">Concerns</h4>
                <ul class="space-y-1">
                  <li v-for="(con, idx) in listing.analysis_metadata.key_takeaways.cons" :key="idx" class="text-sm text-gray-300 flex">
                    <span class="text-red-400 mr-2">-</span>
                    {{ con }}
                  </li>
                </ul>
              </div>
            </div>

            <!-- AI Notes -->
            <div v-if="listing.analysis_metadata.notes && typeof listing.analysis_metadata.notes === 'string'" class="bg-gray-800/50 rounded-lg p-4">
              <h4 class="text-sm font-medium text-gray-400 mb-2 flex items-center">
                <span class="mr-2">📝</span> AI Notes
              </h4>
              <p class="text-sm text-gray-300">{{ listing.analysis_metadata.notes }}</p>
            </div>
            
            <!-- AI Notes (Object format) -->
            <div v-else-if="listing.analysis_metadata.notes && typeof listing.analysis_metadata.notes === 'object'" class="bg-gray-800/50 rounded-lg p-4">
              <h4 class="text-sm font-medium text-gray-400 mb-2 flex items-center">
                <span class="mr-2">📝</span> AI Notes
              </h4>
              <div class="space-y-2 text-sm">
                <div v-if="listing.analysis_metadata.notes.condition_details">
                  <span class="text-gray-500">Condition:</span>
                  <span class="text-gray-300 ml-2">{{ listing.analysis_metadata.notes.condition_details }}</span>
                </div>
                <div v-if="listing.analysis_metadata.notes.things_to_check?.length">
                  <span class="text-gray-500">Things to Check:</span>
                  <ul class="mt-1 ml-4 space-y-1">
                    <li v-for="(item, idx) in listing.analysis_metadata.notes.things_to_check" :key="idx" class="text-gray-300">
                      • {{ item }}
                    </li>
                  </ul>
                </div>
                <div v-if="listing.analysis_metadata.notes.considerations?.length">
                  <span class="text-gray-500">Considerations:</span>
                  <ul class="mt-1 ml-4 space-y-1">
                    <li v-for="(item, idx) in listing.analysis_metadata.notes.considerations" :key="idx" class="text-gray-300">
                      • {{ item }}
                    </li>
                  </ul>
                </div>
                <div v-if="listing.analysis_metadata.notes.red_flags?.length">
                  <span class="text-red-400">Red Flags:</span>
                  <ul class="mt-1 ml-4 space-y-1">
                    <li v-for="(item, idx) in listing.analysis_metadata.notes.red_flags" :key="idx" class="text-red-300">
                      • {{ item }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <!-- Raw Data (collapsible, for debugging) -->
          <details v-if="listing.analysis_metadata" class="mt-4">
            <summary class="text-xs text-gray-600 cursor-pointer hover:text-gray-400">View Raw JSON Data</summary>
            <pre class="mt-2 text-xs text-gray-500 bg-gray-900 rounded p-3 overflow-x-auto max-h-48">{{ JSON.stringify(listing.analysis_metadata, null, 2) }}</pre>
          </details>
        </div>
      </div>
    </div>

    <!-- Pagination -->
    <div v-if="listingsPagination && listingsPagination.total_pages > 1" class="mt-6 flex justify-center">
      <div class="flex space-x-2">
        <button
          v-for="page in getVisiblePages()"
          :key="page"
          @click="loadListings(page, activeFilter)"
          :class="[
            'px-3 py-1 rounded text-sm',
            page === currentPage
              ? 'bg-blue-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          ]"
        >
          {{ page }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import {
  getScanBatch,
  getScanBatchListings,
  resetAnalysisStatus,
  runDeepAnalysis,
  rerunTriage as rerunTriageAPI,
  sendScanNotifications
} from '@/services/api';
import { formatDateTimeMST } from '@/utils/datetime';

const route = useRoute();
const scanId = route.params.scanId as string;

// State
const loading = ref(false);
const listingsLoading = ref(false);
const analysisLoading = ref(false);
const error = ref<string | null>(null);
const successMessage = ref<string | null>(null);
const showActionsMenu = ref(false);

// Data
const scanBatch = ref<any>(null);
const listings = ref<any[]>([]);
const listingsPagination = ref<any>(null);
const totalCounts = ref<any>({ all: 0, interesting: 0, analyzed: 0 });
const currentPage = ref(1);
const activeFilter = ref('all');

// Expanded state
const expandedListingId = ref<number | null>(null);

// Selection state
const selectedListingIds = ref<Set<number>>(new Set());
const isAnalyzingSelected = ref(false);
const isRerunningTriage = ref(false);
const isSendingNotifications = ref(false);
const reanalyzingId = ref<number | null>(null);

// Helpers
const hasDeepAnalysis = (listing: any) => {
  return listing.analysis_metadata?.recommendation && 
    ['NOTIFY', 'PASS', 'IGNORE'].includes(listing.analysis_metadata.recommendation);
};

// Computed
const filteredListings = computed(() => listings.value);

const interestingListings = computed(() => 
  listings.value.filter(l => l.triage_interesting)
);

const selectedCount = computed(() => selectedListingIds.value.size);

// Count listings with deep analysis
const deepAnalyzedCount = computed(() => 
  listings.value.filter(l => hasDeepAnalysis(l)).length
);

// Count NOTIFY recommendations
const notifyCount = computed(() => 
  listings.value.filter(l => l.analysis_metadata?.recommendation === 'NOTIFY').length
);

const listingFilters = computed(() => [
  { key: 'all', label: 'All', count: totalCounts.value.all },
  { key: 'interesting', label: 'Interesting', count: totalCounts.value.interesting || 0, color: 'bg-yellow-600 text-white' },
  { key: 'skipped', label: 'Skipped', count: totalCounts.value.skipped || 0 },
  { key: 'notify', label: 'Notified', count: totalCounts.value.notify || 0, color: 'bg-emerald-600 text-white' },
]);

// Methods
const isExpanded = (id: number) => expandedListingId.value === id;
const toggleExpanded = (id: number) => {
  expandedListingId.value = expandedListingId.value === id ? null : id;
};

const toggleSelection = (id: number) => {
  const newSet = new Set(selectedListingIds.value);
  if (newSet.has(id)) {
    newSet.delete(id);
  } else {
    newSet.add(id);
  }
  selectedListingIds.value = newSet;
};

const selectAllInteresting = () => {
  const newSet = new Set(selectedListingIds.value);
  interestingListings.value.forEach(l => newSet.add(l.listing_idx));
  selectedListingIds.value = newSet;
};

const deselectAll = () => {
  selectedListingIds.value = new Set();
};

const showSuccess = (msg: string) => {
  successMessage.value = msg;
  error.value = null;
  setTimeout(() => successMessage.value = null, 3000);
};

const showError = (msg: string) => {
  error.value = msg;
  successMessage.value = null;
  setTimeout(() => error.value = null, 5000);
};

const formatDateTime = formatDateTimeMST;

const loadScanBatch = async () => {
  try {
    loading.value = true;
    scanBatch.value = await getScanBatch(scanId);
  } catch (err: any) {
    showError(err.message || 'Failed to load scan batch');
  } finally {
    loading.value = false;
  }
};

const loadListings = async (page = 1, filter = 'all') => {
  try {
    listingsLoading.value = true;
    const data = await getScanBatchListings(scanId, page, 20, filter);
    listings.value = data.results || data;
    
    if (data.count) {
      listingsPagination.value = {
        total_pages: Math.ceil(data.count / 20),
        current_page: page,
        total_count: data.count
      };
    }
    
    if (data.total_counts) {
      totalCounts.value = data.total_counts;
    }
    
    currentPage.value = page;
    activeFilter.value = filter;
  } catch (err: any) {
    showError(err.message || 'Failed to load listings');
  } finally {
    listingsLoading.value = false;
  }
};

const applyFilter = async (filterKey: string) => {
  currentPage.value = 1;
  await loadListings(1, filterKey);
};

const refreshData = async () => {
  await Promise.all([loadScanBatch(), loadListings(currentPage.value, activeFilter.value)]);
};

const rerunTriage = async () => {
  try {
    isRerunningTriage.value = true;
    const result = await rerunTriageAPI(scanId);
    showSuccess(result.message || 'Triage re-run complete');
    await refreshData();
  } catch (err: any) {
    showError(err.message || 'Failed to re-run triage');
  } finally {
    isRerunningTriage.value = false;
  }
};

const resetAnalysis = async () => {
  try {
    analysisLoading.value = true;
    await resetAnalysisStatus(scanId);
    showSuccess('Analysis status reset');
    await refreshData();
  } catch (err: any) {
    showError(err.message || 'Failed to reset analysis');
  } finally {
    analysisLoading.value = false;
  }
};

const sendNotifications = async () => {
  try {
    isSendingNotifications.value = true;
    const result = await sendScanNotifications(scanId);
    if (result.success) {
      showSuccess(result.message || `Sent ${result.sent} notification(s)`);
    } else {
      showError(result.error || 'Failed to send notifications');
    }
  } catch (err: any) {
    showError(err.message || 'Failed to send notifications');
  } finally {
    isSendingNotifications.value = false;
  }
};

const analyzeSelectedListings = async () => {
  if (selectedCount.value === 0) return;
  
  try {
    isAnalyzingSelected.value = true;
    const listingIds = Array.from(selectedListingIds.value);
    const result = await runDeepAnalysis(listingIds, scanId);
    
    if (result.success) {
      showSuccess(`Analyzed ${result.analyzed} listings`);
      deselectAll();
      await loadListings(currentPage.value, activeFilter.value);
    } else {
      showError(result.error || 'Analysis failed');
    }
  } catch (err: any) {
    showError(err.message || 'Failed to analyze listings');
  } finally {
    isAnalyzingSelected.value = false;
  }
};

const reanalyze = async (listing: any) => {
  try {
    reanalyzingId.value = listing.listing_idx;
    const result = await runDeepAnalysis([listing.listing_idx], scanId);
    
    if (result.success) {
      showSuccess('Analysis complete');
      await loadListings(currentPage.value, activeFilter.value);
    } else {
      showError(result.error || 'Analysis failed');
    }
  } catch (err: any) {
    showError(err.message || 'Failed to analyze listing');
  } finally {
    reanalyzingId.value = null;
  }
};

const getVisiblePages = () => {
  if (!listingsPagination.value) return [];
  const total = listingsPagination.value.total_pages;
  const current = currentPage.value;
  const pages = [];
  const start = Math.max(1, current - 2);
  const end = Math.min(total, current + 2);
  for (let i = start; i <= end; i++) pages.push(i);
  return pages;
};

onMounted(refreshData);
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.animate-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
