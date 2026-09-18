/**
 * SANCHAY OS - Main Application Engine v2.0
 * Financial Advisory Operating System
 * Initialization, API communication, and state management
 */

'use strict';

// ═══════════════════════════════════════════════════════════════════
// GLOBAL ERROR HANDLER
// ═══════════════════════════════════════════════════════════════════

window.onerror = function(msg, url, line, col, error) {
  console.error(`[ERROR] ${msg} at ${url}:${line}:${col}`, error);
  const el = document.createElement('div');
  el.style = 'position:fixed;top:0;left:0;background:#d32f2f;color:white;z-index:999999;padding:20px;font-size:14px;font-family:monospace;box-shadow:0 2px 8px rgba(0,0,0,0.3)';
  el.innerHTML = `<strong>ERROR:</strong> ${msg}<br><small>${url}:${line}</small>`;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 5000);
  return false;
};

// ═══════════════════════════════════════════════════════════════════
// GLOBAL STATE MANAGEMENT
// ═══════════════════════════════════════════════════════════════════

const GLOBAL_STATE = {
  currentUser: null,
  selectedClient: null,
  isOffline: false,
  lastSyncTime: null,
  
  setUser(user) {
    this.currentUser = user;
    localStorage.setItem('sanchay_current_user', JSON.stringify(user));
  },
  
  getUser() {
    if (this.currentUser) return this.currentUser;
    const stored = localStorage.getItem('sanchay_current_user');
    return stored ? JSON.parse(stored) : null;
  },
  
  setSelectedClient(client) {
    this.selectedClient = client;
    localStorage.setItem('sanchay_selected_client', JSON.stringify(client));
  },
  
  getSelectedClient() {
    if (this.selectedClient) return this.selectedClient;
    const stored = localStorage.getItem('sanchay_selected_client');
    return stored ? JSON.parse(stored) : null;
  },
};

// ═══════════════════════════════════════════════════════════════════
// API COMMUNICATION LAYER
// ═══════════════════════════════════════════════════════════════════

async function apiFetch(endpoint, options = {}) {
  const config = window.SANCHAY_CONFIG;
  
  if (!config || !config.validate()) {
    console.error('[API] Configuration validation failed');
    return null;
  }
  
  const url = config.getAPIUrl(endpoint);
  const method = options.method || 'GET';
  
  // Add Auth Headers
  const token = localStorage.getItem('sanchay_token');
  const headers = options.headers || { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const body = options.body || null;
  
  try {
    console.log(`[API] ${method} ${endpoint}`);
    
    const response = await fetch(url, {
      method,
      headers,
      body: body ? JSON.stringify(body) : null,
      timeout: config.api.timeout,
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`[API] ✓ Success: ${endpoint}`, data);
    GLOBAL_STATE.lastSyncTime = new Date();
    GLOBAL_STATE.isOffline = false;
    return data;
    
  } catch (error) {
    console.warn(`[API] ✗ Failed: ${endpoint} - ${error.message}`);
    GLOBAL_STATE.isOffline = true;
    
    if (config.data.fallbackToLocal) {
      console.log(`[API] Falling back to local data`);
    }
    
    return null;
  }
}

// ═══════════════════════════════════════════════════════════════════
// DATA SYNC LOGIC
// ═══════════════════════════════════════════════════════════════════

function shouldRefresh() {
  const config = window.SANCHAY_CONFIG;
  const lastRefresh = localStorage.getItem(config.data.refreshKey);
  
  if (!lastRefresh) return true;
  
  const timeSinceRefresh = Date.now() - parseInt(lastRefresh);
  return timeSinceRefresh > config.data.refreshIntervalMs;
}

function markRefreshed() {
  const config = window.SANCHAY_CONFIG;
  const now = Date.now().toString();
  localStorage.setItem(config.data.refreshKey, now);
  
  const el = document.getElementById('last-refresh-time');
  if (el) {
    el.textContent = '✓ Updated: ' + new Date().toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit'
    });
  }
}

async function syncFromAPI(forceRefresh = false) {
  console.log('[SYNC] Starting data synchronization...');
  
  const endpoints = [
    '/dashboard',
    '/clients',
    '/tasks',
    '/goals',
    '/transactions',
    '/reports',
    '/compliance',
    '/team'
  ];
  
  // Always fetch from API (don't use cached data)
  const results = await Promise.allSettled(
    endpoints.map(endpoint => apiFetch(endpoint))
  );
  
  const syncData = {};
  endpoints.forEach((endpoint, index) => {
    const result = results[index];
    const key = endpoint.substring(1); // Remove leading slash
    
    // If API failed, use cached data only as fallback
    if (result.status === 'fulfilled' && result.value) {
      syncData[key] = result.value;
    } else {
      // Fallback to cached data only if API failed
      const cached = localStorage.getItem(`sanchay_${key}`);
      syncData[key] = cached ? JSON.parse(cached) : null;
    }
  });
  
  // Store all synced data separately by endpoint
  Object.keys(syncData).forEach(key => {
    if (syncData[key]) {
      localStorage.setItem(`sanchay_${key}`, JSON.stringify(syncData[key]));
    }
  });
  
  markRefreshed();
  
  console.log('[SYNC] ✓ Synchronization completed', syncData);
  
  // Update UI with fresh data
  updateUIWithData(syncData);
  
  return syncData;
}

// Update UI with fresh data from API
function updateUIWithData(syncData) {
  if (!syncData) return;
  
  // Update clients table
  if (syncData.clients && Array.isArray(syncData.clients)) {
    const clientsTable = document.getElementById('clients-table');
    if (clientsTable) {
      updateClientsTable(syncData.clients);
    }
  }
  
  // Update dashboard with fresh data
  if (syncData.dashboard) {
    updateDashboard(syncData.dashboard);
  }
  
  console.log('[UI] Updated with fresh data from API');
}

// ═══════════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════════

async function initializeApp() {
  console.log('[APP] Initializing SANCHAY OS v2.0...');
  
  // Verify config is loaded
  if (typeof window.SANCHAY_CONFIG === 'undefined') {
    console.error('[APP] Configuration not loaded. Ensure config.js is loaded first.');
    return false;
  }
  
  // Validate configuration
  if (!window.SANCHAY_CONFIG.validate()) {
    console.error('[APP] Configuration validation failed');
    return false;
  }
  
  // Initialize state
  const user = GLOBAL_STATE.getUser() || {
    name: localStorage.getItem('sanchay_name') || 'Dr. Arvind Sharma',
    role: localStorage.getItem('sanchay_role') || 'Lead Advisor'
  };
  
  GLOBAL_STATE.setUser(user);

  // Auth Guard
  const token = localStorage.getItem('sanchay_token');
  const isLoginPage = window.location.pathname.includes('login.html');
  
  if (!token && !isLoginPage) {
    console.warn('[APP] No active session. Redirecting to login.');
    window.location.href = 'frontend/advisor_login.html';
    return false;
  }
  if (token && isLoginPage) {
    window.location.href = localStorage.getItem('sanchay_role') === 'client' ? 'client_portal.html' : 'index.html';
    return true;
  }
  
  // Health check
  const health = await apiFetch('/health');
  if (health) {
    console.log('[APP] ✓ API Server is reachable');
    GLOBAL_STATE.isOffline = false;
  } else {
    console.warn('[APP] ⚠ API Server is offline, using local data fallback');
    GLOBAL_STATE.isOffline = true;
  }
  
  // ALWAYS sync fresh data from API (don't skip on startup)
  console.log('[APP] Fetching fresh data from API...');
  await syncFromAPI(true); // Force refresh on init
  
  console.log('[APP] ✓ SANCHAY OS initialized successfully');
  return true;
}

// ═══════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════

function showScreen(screenId) {
  // Hide all screens
  document.querySelectorAll('.screen').forEach(screen => {
    screen.classList.remove('active');
  });
  
  // Show selected screen
  const screen = document.getElementById(screenId);
  if (screen) {
    screen.classList.add('active');
    console.log(`[UI] Showing screen: ${screenId}`);
  }
}

function closeOverlays() {
  document.querySelectorAll('.topbar-overlay').forEach(overlay => {
    overlay.style.display = 'none';
  });
}

async function refreshDataFromAPI() {
  """Manually refresh data from API (call this after creating/updating records)"""
  console.log('[REFRESH] Force refresh data from API');
  localStorage.removeItem('sanchay_last_refresh'); // Force refresh
  await syncFromAPI(true);
}

function updateClientsTable(clients) {
  """Update clients table with data from API"""
  const tbody = document.querySelector('#clients-table tbody');
  if (!tbody) return;
  
  tbody.innerHTML = '';
  
  if (!Array.isArray(clients) || clients.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:#999">No clients found</td></tr>';
    return;
  }
  
  clients.forEach(client => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${client.name || 'N/A'}</td>
      <td>${client.phone || 'N/A'}</td>
      <td><span class="tag">Medium</span></td>
      <td>₹${client.net_worth ? (client.net_worth/10000000).toFixed(1) : '0'} Cr</td>
      <td><span class="tag green">Good</span></td>
      <td>High</td>
      <td>Today</td>
      <td><button class="btn btn-ghost btn-xs">View</button></td>
    `;
    tbody.appendChild(row);
  });
}

function updateDashboard(dashboard) {
  """Update dashboard with fresh data"""
  if (!dashboard) return;
  
  const dashAum = document.getElementById('dash-aum');
  const dashClients = document.getElementById('dash-clients-count');
  
  if (dashAum && dashboard.total_aum) {
    dashAum.textContent = dashboard.total_aum;
  }
  
  if (dashClients && dashboard.total_clients) {
    dashClients.textContent = dashboard.total_clients;
  }
}

function logInfo(message, data = null) {
  const config = window.SANCHAY_CONFIG;
  if (config && config.logging.enabled) {
    console.log(`[INFO] ${message}`, data || '');
  }
}

function logWarn(message, data = null) {
  const config = window.SANCHAY_CONFIG;
  if (config && config.logging.enabled) {
    console.warn(`[WARN] ${message}`, data || '');
  }
}

function logError(message, data = null) {
  const config = window.SANCHAY_CONFIG;
  if (config && config.logging.enabled) {
    console.error(`[ERROR] ${message}`, data || '');
  }
}

// ═══════════════════════════════════════════════════════════════════
// APP STARTUP
// ═══════════════════════════════════════════════════════════════════

console.log('[APP] app.js module loaded');

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  // DOM already loaded
  initializeApp();
}

// Make key functions globally available
window.showScreen = showScreen;
window.closeOverlays = closeOverlays;
window.apiFetch = apiFetch;
window.syncFromAPI = syncFromAPI;
window.refreshDataFromAPI = refreshDataFromAPI;
window.GLOBAL_STATE = GLOBAL_STATE;

window.logout = function() {
  localStorage.removeItem('sanchay_token');
  localStorage.removeItem('sanchay_role');
  localStorage.removeItem('sanchay_name');
  localStorage.removeItem('sanchay_advisor_id');
  window.location.href = 'advisor_login.html';
};

// Client creation helper - call this after user adds a client
async function createClientAndRefresh(clientData) {
  """Create client via API and refresh data"""
  try {
    console.log('[CLIENT] Creating client...', clientData);
    
    const response = await apiFetch('/clients', {
      method: 'POST',
      body: clientData
    });
    
    if (response && response.client_id) {
      console.log('[CLIENT] ✓ Client created successfully:', response);
      
      // Wait a moment for database to commit
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Refresh all data from API
      await refreshDataFromAPI();
      
      console.log('[CLIENT] ✓ Data refreshed');
      return response;
    } else {
      console.error('[CLIENT] ✗ Failed to create client');
      return null;
    }
  } catch (error) {
    console.error('[CLIENT] ✗ Error creating client:', error);
    return null;
  }
}

// Make this globally available too
window.createClientAndRefresh = createClientAndRefresh;
