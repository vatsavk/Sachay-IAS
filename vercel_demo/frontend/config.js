/**
 * SANCHAY Configuration
 * Centralized configuration for frontend environment
 * Loads from environment or uses sensible defaults
 */

const CONFIG = {
  // API Configuration
  api: {
    baseURL: window.location.origin,
    timeout: 10000,
    retryAttempts: 3,
    retryDelay: 1000,
  },

  // UI Configuration
  ui: {
    theme: 'dark',
    refreshInterval: 60000, // 1 minute
    animationsEnabled: true,
  },

  // Data Refresh Configuration
  data: {
    autoRefresh: true,
    refreshIntervalMs: 24 * 60 * 60 * 1000, // 24 hours
    refreshKey: 'sanchay_last_refresh',
    fallbackToLocal: true, // Use local data if API fails
  },

  // Feature Flags
  features: {
    enableAnalytics: true,
    enableNotifications: true,
    enableOfflineMode: true,
  },

  // Logging
  logging: {
    enabled: true,
    level: 'info', // 'debug', 'info', 'warn', 'error'
  },

  // Get API URL
  getAPIUrl(endpoint) {
    const base = this.api.baseURL.replace(/\/$/, '');
    return `${base}${endpoint}`;
  },

  // Get feature status
  isFeatureEnabled(feature) {
    return this.features[feature] === true;
  },

  // Validate configuration
  validate() {
    if (!this.api.baseURL) {
      console.error('[CONFIG] API baseURL is not configured');
      return false;
    }
    return true;
  },
};

// Log configuration on load
if (CONFIG.logging.enabled && CONFIG.logging.level === 'debug') {
  console.log('[CONFIG] Configuration loaded:', CONFIG);
}

// Make CONFIG globally available
window.SANCHAY_CONFIG = CONFIG;
