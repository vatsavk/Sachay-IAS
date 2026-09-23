// SANCHAY IAS — ADVISOR OS · APP ENGINE v2.0
window.onerror = function(msg, url, line, col, error) {
  console.error('Sanchay OS Error:', msg, url, line);
  const el = document.createElement('div');
  el.style = 'position:fixed;top:0;left:0;background:red;color:white;z-index:999999;padding:20px;font-size:20px';
  el.innerText = 'ERROR: ' + msg + ' at ' + url + ':' + line;
  document.body.appendChild(el);
  return false;
};
const SANCHAY_API_BASE = 'http://localhost:8001';
const REFRESH_KEY = 'sanchay_last_refresh';
const REFRESH_MS = 24 * 60 * 60 * 1000; // 24 hours
console.log('[Sanchay OS] app.js parsed and executing top-level code');

async function apiFetch(endpoint, options = {}) {
  try {
    const res = await fetch(`${SANCHAY_API_BASE}${endpoint}`, {
      method: options.method || 'GET',
      headers: options.headers || { 'Content-Type': 'application/json' },
      body: options.body || null
    });
    if (!res.ok) throw new Error(`${res.status}`);
    const data = await res.json();
    console.log(`[API] Success: ${endpoint}`, data);
    return data;
  } catch (err) {
    console.warn(`[API] Failure: ${endpoint} - falling back to local data.`, err);
    return null; // Silent fallback to data.js
  }
}

function shouldRefresh() {
  const last = localStorage.getItem(REFRESH_KEY);
  return !last || (Date.now() - parseInt(last)) > REFRESH_MS;
}

function markRefreshed() {
  localStorage.setItem(REFRESH_KEY, Date.now().toString());
  const el = document.getElementById('last-refresh-time');
  if (el) el.textContent = 'Updated: ' + new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
}

async function syncFromAPI() {
  // Run all API fetches in parallel — silent fallback if server is offline
  const [dash, clients, tasks, goals, tx, insights, compliance, reports, team] = await Promise.allSettled([
    apiFetch('/dashboard'), apiFetch('/clients'), apiFetch('/tasks'), apiFetch('/goals'),
    apiFetch('/transactions'), apiFetch('/insights'),
    apiFetch('/compliance'), apiFetch('/reports'), apiFetch('/team')
  ]);

  if (dash.status === 'fulfilled' && dash.value) {
    const d = dash.value;
    IAS_DATA.totalAUM = d.total_aum >= 10000000 
      ? `₹${(d.total_aum / 10000000).toFixed(1)} Cr` 
      : `₹${(d.total_aum / 100000).toFixed(1)} L`;
    IAS_DATA.totalClients = d.client_count;
    IAS_DATA.atRisk = d.at_risk_goals || 0;
  }

  if (clients.value && Array.isArray(clients.value) && clients.value.length > 0) {
    IAS_DATA.clients = clients.value.map(c => ({
      id: String(c.client_id),
      name: c.client_name || c.name || 'Client',
      initials: (c.client_name || c.name || 'C').split(' ').map(n => n[0]).join('').substring(0,2).toUpperCase(),
      email: c.client_email || c.email || '',
      phone: c.phone || '',
      aum: c.total_value ? `₹${(c.total_value/10000000).toFixed(1)} Cr` : (c.aum || '₹0'),
      aum_raw: c.total_value || c.aum_raw || 0,
      risk: c.risk || 'Moderate',
      health: c.health || 75,
      engagement: c.engagement || 50,
      lastContact: c.last_contact || '—',
      status: c.status || 'Active',
      category: c.category || 'Retail',
      since: c.onboarding_date || new Date().getFullYear().toString(),
      portfolio: c.portfolio || { equity: 50, debt: 30, gold: 10, cash: 10, holdings: [] }
    }));
  }

  if (tasks.value && Array.isArray(tasks.value)) {
    IAS_DATA.tasks = tasks.value.map(t => ({
      id: t.task_id, title: t.task_type || 'Task',
      client: (IAS_DATA.clients.find(c => String(c.id) === String(t.client_id)) || {}).name || 'Unknown',
      due: t.due_date || 'TBD', priority: t.priority || 'Medium',
      status: t.status || 'Pending', type: t.task_type || 'Action'
    }));
  }

  if (goals.value && Array.isArray(goals.value) && goals.value.length > 0) {
    IAS_DATA.goals = goals.value.map(g => ({
      id: g.goal_id, clientId: String(g.client_id),
      client: (IAS_DATA.clients.find(c => String(c.id) === String(g.client_id)) || {}).name || 'Unknown',
      name: g.goal_type || 'Goal',
      targetAmount: `₹${Number(g.target_amount || 0).toLocaleString('en-IN')}`,
      currentCorpus: '—', targetDate: g.target_date || '—',
      sipRequired: '—', sipCurrent: '—',
      probability: g.status === 'On Track' ? 80 : 58,
      status: g.status || 'On Track'
    }));
  }

  if (tx.value && Array.isArray(tx.value)) {
    IAS_DATA.transactions = tx.value.map(t => ({
      id: t.txn_id, clientId: String(t.client_id),
      date: t.txn_date || '—', type: t.txn_type || 'BUY',
      security: t.asset_name || String(t.asset_id),
      amount: `₹${Number((t.quantity || 0) * (t.price || 0)).toLocaleString('en-IN')}`,
      status: 'Confirmed'
    }));
  }

  if (insights.value && insights.value.recommendations) {
    const apiInsights = (insights.value.recommendations || []).map(r => ({
      id: 'api_' + r.recommendation_id, type: 'RECOMMENDATION',
      severity: r.risk_score > 70 ? 'HIGH' : 'MEDIUM',
      title: `Scenario: ${r.scenario_type || 'Advisory'}`,
      desc: `Expected return: ${r.expected_return || 0}% | Risk score: ${r.risk_score || 0}`,
      clients: 1, action: 'Review', client: r.client_name
    }));
    if (apiInsights.length > 0) IAS_DATA.insights = [...apiInsights, ...IAS_DATA.insights].slice(0, 10);
  }

  if (compliance.value && Array.isArray(compliance.value) && compliance.value.length > 0) {
    IAS_DATA.compliance = compliance.value.map(c => ({
      id: c.log_id, title: c.action || 'Audit Entry',
      entity_type: c.entity_type || 'LOG', client: c.entity_type || 'System',
      due: c.timestamp ? c.timestamp.split('T')[0] : '—',
      status: 'Logged', owner: c.performed_by_name || 'System'
    }));
  }

  if (reports.value && Array.isArray(reports.value) && reports.value.length > 0) {
    IAS_DATA.reports = reports.value.map(r => ({
      id: r.report_id,
      client_id: r.client_id,
      type: r.report_type, freq: 'On-Demand',
      last: r.generated_at ? r.generated_at.split('T')[0] : '—',
      client: r.client_name || 'All Clients', status: 'Ready',
      url: r.report_data ? (JSON.parse(r.report_data).url || null) : null
    }));
  }

  if (team.value && Array.isArray(team.value) && team.value.length > 0) {
    IAS_DATA.team = team.value.map(t => ({
      id: 'u' + t.advisor_id, name: t.name, role: 'Advisor',
      clients: t.client_count || 0,
      aum: t.aum_managed > 0 ? `₹${(t.aum_managed/10000000).toFixed(1)} Cr` : '—',
      tasks: t.pending_tasks || 0,
      initials: (t.name || 'A').split(' ').map(n => n[0]).join('').substring(0,2).toUpperCase(),
      status: t.status || 'Active'
    }));
  }

  // Force re-render of all screens with new data
  if (window.RE_RENDER_ALL) {
    window.RE_RENDER_ALL();
  }

  markRefreshed();
}


async function loadClientsFromAPI() {
  const clients = await apiFetch('/clients');
  
  if (Array.isArray(clients) && clients.length > 0) {
    console.log('Processing', clients.length, 'clients');
    IAS_DATA.clients = clients.map(c => ({
      id: c.client_id,
      name: c.client_name || c.name,
      email: c.client_email || c.email,
      phone: c.phone || '',
      aum: c.total_value ? `₹${Number(c.total_value).toLocaleString()}` : c.aum,
      aum_raw: c.total_value || c.aum_raw || 0,
      initials: (c.client_name || c.name || 'C').split(' ').map(n=>n[0]).join('').substring(0,2).toUpperCase(),
      risk: c.risk || 'Moderate',
      health: c.health || 75,
      engagement: c.engagement || 50,
      lastContact: c.last_contact || '—',
      nextAction: c.next_action || 'Review',
      status: c.status || 'Active',
      portfolio: c.portfolio || { equity: 0, debt: 0, gold: 0, cash: 0, holdings: [] },
      advisor_id: c.advisor_id,
      category: c.category || 'Retail',
      since: c.onboarding_date || c.since || new Date().getFullYear().toString()
    }));
    console.log('IAS_DATA.clients updated:', IAS_DATA.clients.length, 'clients');
    renderClientsTable(document.querySelector('#clients-table tbody'));
    renderDashboard();
  } else {
    console.warn('No clients returned from API');
  }
}

async function loadTasksFromAPI() {
  console.log('Loading tasks from API...');
  const tasks = await apiFetch('/tasks');
  console.log('loadTasksFromAPI result:', tasks);
  
  if (Array.isArray(tasks)) {
    console.log('Processing', tasks.length, 'tasks');
    IAS_DATA.tasks = tasks.map(t => ({
      id: t.task_id,
      title: t.task_type || 'Task',
      client: (IAS_DATA.clients.find(c => String(c.id) === String(t.client_id)) || {}).name || 'Unknown',
      due: t.due_date || 'TBD',
      priority: t.priority || 'Medium',
      status: t.status || 'Pending',
      type: t.task_type || 'Action'
    }));
    console.log('IAS_DATA.tasks updated:', IAS_DATA.tasks.length, 'tasks');
    renderTasksScreen();
  } else {
    console.warn('No tasks returned from API');
  }
}

async function loadGoalsFromAPI() {
  console.log('Loading goals from API...');
  const goals = await apiFetch('/goals');
  console.log('loadGoalsFromAPI result:', goals);
  
  if (Array.isArray(goals) && goals.length > 0) {
    console.log('Processing', goals.length, 'goals');
    console.log('Sample raw goal:', goals[0]);
    
    IAS_DATA.goals = goals.map(g => {
      const transformed = {
        id: g.goal_id,
        clientId: g.client_id,
        client: (IAS_DATA.clients.find(c => String(c.id) === String(g.client_id)) || {}).name || 'Unknown',
        name: g.goal_type || 'Goal',
        targetAmount: `Rs ${Number(g.target_amount).toLocaleString()}`,
        currentCorpus: 'Rs 0',
        targetDate: g.target_date || 'N/A',
        sipRequired: 'Rs 0',
        avg_return: 12,
        probability: g.status === 'On Track' ? 80 : 58,
        status: g.status || 'On Track'
      };
      return transformed;
    });
    console.log('IAS_DATA.goals updated:', IAS_DATA.goals.length, 'goals');
    console.log('Sample transformed goal:', IAS_DATA.goals[0]);
    renderDashboard();
  } else {
    console.warn('No goals from API, keeping data.js defaults');
    // Don't clear goals - keep the defaults from data.js
  }
}

async function loadTransactionsFromAPI() {
  console.log('Loading transactions from API...');
  const tx = await apiFetch('/transactions');
  console.log('loadTransactionsFromAPI result:', tx);
  
  if (Array.isArray(tx)) {
    console.log('Processing', tx.length, 'transactions');
    IAS_DATA.transactions = tx.map(t => ({
      id: t.txn_id,
      clientId: t.client_id,
      date: t.txn_date || 'Today',
      type: t.txn_type || 'Purchase',
      security: t.asset_id || 'Unknown',
      amount: `Rs ${Number(t.quantity * t.price).toLocaleString()}`,
      status: 'Confirmed'
    }));
    console.log('IAS_DATA.transactions updated:', IAS_DATA.transactions.length, 'transactions');
  } else {
    console.warn('No transactions returned from API');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  init().catch(err => console.error('Sanchay init error:', err));
});

let isInitializing = false;
async function init() {
  if (isInitializing) return;
  isInitializing = true;

  try {
    const featureRes = await fetch(API_BASE + '/features', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    });
    if (featureRes.ok) {
      const features = await featureRes.json();
      if (!features.FEATURE_CLIENT_PORTAL_ENABLED) {
        const portalBtn = document.querySelector('button[data-screen="s-client-portal"]');
        if (portalBtn) portalBtn.style.display = 'none';
      }
    }
  } catch (e) {
    console.error('Failed to fetch features', e);
  }

  const renderSteps = [
    { name: 'Navigation', fn: setupNavigation },
    { name: 'Toggles', fn: setupToggles },
    { name: 'Dashboard', fn: renderDashboard },
    { name: 'Clients', fn: () => renderClientsTable(document.querySelector('#clients-table tbody')) },
    { name: 'Tasks', fn: renderTasksScreen },
    { name: 'Goals', fn: renderGoalsScreen },
    { name: 'Reviews', fn: renderReviewsScreen },
    { name: 'Insights', fn: renderInsightsScreen },
    { name: 'Compliance', fn: renderComplianceScreen },
    { name: 'Reports', fn: renderReportsScreen },
    { name: 'Team', fn: renderTeamScreen },
    { name: 'Branding', fn: renderBranding }
  ];

  // Global Re-render
  window.RE_RENDER_ALL = () => {
    console.log('[Sanchay OS] Global Refresh Started...');
    renderSteps.forEach(step => {
      try {
        console.log(`[Refresh] ${step.name}`);
        step.fn();
      } catch (e) {
        console.error(`[Refresh] Failed ${step.name}:`, e);
      }
    });
    console.log('[Sanchay OS] Global Refresh Complete.');
  };

  // Initial render
  for (const step of renderSteps) {
    try {
      step.fn();
    } catch (e) {
      console.error(`[Init] Failed ${step.name}:`, e);
    }
  }

  const pb = document.getElementById('profile-back');
  if (pb) pb.addEventListener('click', () => showScreen('s-clients'));
  
  // Show dashboard by default
  showScreen('s-dashboard');

  // Background Sync
  if (shouldRefresh()) {
    syncFromAPI().then(() => {
      console.log('Sanchay OS: API Sync Success.');
      window.RE_RENDER_ALL();
    }).catch(err => {
      console.error('Sanchay OS: Sync error:', err);
    });
  } else {
    markRefreshed();
  }

  isInitializing = false;
}


function renderBranding() {
  const nameEl = document.getElementById('user-name');
  const initEl = document.getElementById('user-initials');
  if (nameEl) nameEl.textContent = GLOBAL_STATE.current_user.name;
  if (initEl) initEl.textContent = GLOBAL_STATE.current_user.initials;
}

// ── TABS ─────────────────────────────────────────────────────
function setupTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const parent = document.getElementById('profile-tab-content');
      const targetId = 'ptab-' + btn.dataset.ptab;
      
      if (parent) {
        parent.querySelectorAll('[id^="ptab-"]').forEach(p => p.style.display = 'none');
        const target = document.getElementById(targetId);
        if (target) target.style.display = 'block';
      }
      
      btn.closest('.tabs').querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      
      if (btn.dataset.ptab === 'portfolio') {
        renderAllocationChart(GLOBAL_STATE.selected_client);
      }
      if (btn.dataset.ptab === 'analysis') {
        renderAdvancedAnalytics(GLOBAL_STATE.selected_client?.id);
      }
    });
  });
}

// ── DASHBOARD ───────────────────────────────────────────────
function renderDashboard() {
  const aumEl = document.getElementById('dash-aum');
  const cntEl = document.getElementById('dash-clients-count');
  if (aumEl) aumEl.textContent = IAS_DATA.totalAUM;
  if (cntEl) cntEl.textContent = IAS_DATA.clients ? IAS_DATA.clients.length : IAS_DATA.totalClients;
  
  const pendingTasks = (IAS_DATA.tasks || []).filter(t => t.status === 'Pending').length;
  document.getElementById('dash-tasks-due').textContent = pendingTasks;

  const alertsTbl = document.querySelector('#dash-alerts-table tbody');
  if (alertsTbl && IAS_DATA.insights) {
    try {
      alertsTbl.innerHTML = IAS_DATA.insights.slice(0, 5).map(ins => `
        <tr>
          <td>${ins.clients || 'All'} Clients</td>
          <td><span class="tag gray">${(ins.type || 'SIGNAL').replace(/_/g, ' ')}</span></td>
          <td style="font-weight:600">${ins.title}</td>
          <td><span class="tag ${ins.severity === 'HIGH' ? 'red' : 'orange'}">${ins.severity || 'MEDIUM'}</span></td>
        </tr>
      `).join('');
    } catch (e) {
      console.error('Error rendering dashboard alerts:', e);
      alertsTbl.innerHTML = '<tr><td colspan="4">Error loading alerts</td></tr>';
    }
  }

  const tbl = document.querySelector('#dash-clients tbody');
  if (tbl && IAS_DATA.clients) {
    renderClientsRows(tbl, IAS_DATA.clients.slice(0, 5));
  }
}

// ── NAVIGATION & UI ──────────────────────────────────────────
function showScreen(id) {
  console.log(`[Sanchay OS] Navigation: Showing ${id}`);
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.body.dataset.screen = id;
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.screen === id);
  });
  if (id === 's-profile') {
    const navProfile = document.getElementById('nav-profile');
    if (navProfile) navProfile.style.display = 'flex';
  }
}

function setupNavigation() {
  console.log('[Sanchay OS] setupNavigation executing...');
  document.querySelectorAll('[data-screen]').forEach(btn => {
    if (btn.tagName.toLowerCase() === 'body') return;
    btn.addEventListener('click', (e) => {
      console.log('[Sanchay OS] Clicked nav-btn:', btn.dataset.screen);
      e.preventDefault();
      const screenId = btn.dataset.screen;
      if (screenId) showScreen(screenId);
    });
  });

  // Debug global clicks
  document.addEventListener('click', (e) => {
    console.log('[Sanchay OS] Global click on:', e.target.tagName, e.target.className);
  });

  // Client Search (Global delegation or direct)
  const bindSearch = () => {
    const input = document.getElementById('client-search-input');
    if (input && !input.dataset.bound) {
      input.dataset.bound = 'true';
      input.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const filtered = (IAS_DATA.clients || []).filter(c => 
          c.name.toLowerCase().includes(term) || 
          (c.phone && c.phone.includes(term))
        );
        renderClientsRows(document.querySelector('#clients-table tbody'), filtered);
      });
    }
  };
  bindSearch();
  // Re-bind on screen change just in case
  document.addEventListener('click', (e) => {
    if (e.target.dataset.screen === 's-clients') setTimeout(bindSearch, 100);
  });
}

function setupToggles() {
  document.getElementById('sidebar-toggle')?.addEventListener('click', () => {
    document.getElementById('app').classList.toggle('sidebar-hidden');
  });
  
  document.getElementById('rail-toggle')?.addEventListener('click', () => {
    document.getElementById('app').classList.toggle('rail-hidden');
  });

  // Topbar Overlays
  document.getElementById('btn-alerts')?.addEventListener('click', () => toggleOverlay('overlay-alerts'));
  document.getElementById('btn-topbar-tasks')?.addEventListener('click', () => toggleOverlay('overlay-tasks'));
}

// ── DATA RENDERING ───────────────────────────────────────────
function renderClientsTable(tbody) {
  if (!tbody || !IAS_DATA.clients) return;
  renderClientsRows(tbody, IAS_DATA.clients);
}

function renderClientsRows(tbody, clients) {
  tbody.innerHTML = clients.map(c => {
    const h = c.health || 75;
    const eng = c.engagement || 50;
    const healthClass = h >= 80 ? '' : h >= 60 ? 'warn' : 'crit';
    const engClass = eng >= 60 ? '' : eng >= 35 ? 'warn' : 'crit';
    return `
    <tr onclick="openProfile('${c.id}')" style='cursor:pointer'>
      <td>
        <div class='flex items-c gap-3'>
          <div class='user-avatar xs'>${c.initials}</div>
          <div class='flex flex-col'>
            <span style='font-weight:700;color:var(--c-text1)'>${c.name}</span>
            <span style='font-size:10px;color:var(--c-text3)'>${c.category || 'Retail'} &middot; Since ${c.since}</span>
          </div>
        </div>
      </td>
      <td class='num'>${c.phone || '—'}</td>
      <td><span class='tag ${c.risk === 'Aggressive' ? 'red' : c.risk === 'Conservative' ? 'blue' : 'orange'}'>${c.risk}</span></td>
      <td class='num' style='font-weight:700'>${c.aum}</td>
      <td>
        <div class='health-bar-wrap'>
          <div class='health-bar'><div class='health-bar-fill ${healthClass}' style='width:${h}%'></div></div>
          <span class='health-num'>${h}</span>
        </div>
      </td>
      <td><div class='flex items-c gap-2'><span class='eng-dot ${engClass}'></span><span style='font-size:11px;color:var(--c-text2)'>${eng}</span></div></td>
      <td class='num' style='font-size:11px'>${c.lastContact || '—'}</td>
      <td class='right'><button class='btn btn-ghost btn-xs row-action' onclick='event.stopPropagation();openProfile("${c.id}")'>Profile</button></td>
    </tr>`;
  }).join('');
}

function renderTasksScreen() {
  console.log('Sanchay OS: Rendering Tasks Screen');
  const tbody = document.querySelector('#tasks-table tbody');
  if (!tbody) { console.warn('Tasks tbody not found'); return; }
  try {
    const data = IAS_DATA.tasks || [];
    if (data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:40px;color:var(--c-text3)">No pending tasks</td></tr>';
      return;
    }
    tbody.innerHTML = data.map(t => `
      <tr>
        <td style="font-weight:600">${t.title || 'Untitled'}</td>
        <td>${t.client || 'General'}</td>
        <td><span class="tag gray">${t.type || 'Action'}</span></td>
        <td class="num">${t.due || '—'}</td>
        <td><span class="tag ${t.priority === 'High' ? 'red' : 'orange'}">${t.priority || 'Medium'}</span></td>
        <td><span class="tag ${t.status === 'Pending' ? 'orange' : 'green'}">${t.status || 'Pending'}</span></td>
        <td class="right"><button class="btn btn-ghost btn-xs">Edit</button></td>
      </tr>
    `).join('');
  } catch (e) {
    console.error('Error rendering tasks:', e);
  }
}

function renderEventsScreen() {
  console.log('Sanchay OS: Rendering Events Screen');
  const body = document.getElementById('events-body');
  if (!body) return;
  if (!IAS_DATA.events || IAS_DATA.events.length === 0) {
    body.innerHTML = '<div class="p-4 t3">No lab reports or events available.</div>';
    return;
  }
  body.innerHTML = IAS_DATA.events.map(e => `
    <div class="card">
    </div>
  `).join('');
}

function renderRail() {
  const body = document.getElementById('rail-body');
  if (!body || !IAS_DATA.decisions) return;
  const urgentCount = IAS_DATA.decisions.filter(d => d.urgency === 'high').length;
  const badge = document.getElementById('rail-badge');
  if (badge) badge.textContent = urgentCount + ' URGENT';
  
  body.innerHTML = IAS_DATA.decisions.map(d => `
    <div class="decision-card" style="border-top-color: var(--c-${d.urgency === 'high' ? 'red' : 'gold'})">
      <div class="dc-type" style="background:var(--c-${d.urgency === 'high' ? 'red' : 'gold'}-bg);color:var(--c-${d.urgency === 'high' ? 'red' : 'gold'})">${d.type}</div>
      <div class="dc-title">${d.title}</div>
      <div class="dc-desc">${d.desc}</div>
      <div class="dc-entity">${d.entity}</div>
      <button class="dc-btn">${d.action}</button>
    </div>
  `).join('');
}

// ── CLIENT PROFILE & CHARTS ──────────────────────────────────
let allocationChart = null;

function renderAllocationChart(client) {
  const ctx = document.getElementById('profile-allocation-chart');
  if (!ctx || !client) return;

  if (allocationChart) allocationChart.destroy();

  const data = [client.portfolio.equity, client.portfolio.debt, client.portfolio.gold, client.portfolio.cash];
  const labels = ['Equity', 'Debt', 'Gold', 'Cash'];

  allocationChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: ['#C8A96E', '#3B9EFF', '#F5962B', '#2FBD7E'],
        borderWidth: 0,
        hoverOffset: 4
      }]
    },
    options: {
      cutout: '70%',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#E2E8F0', font: { size: 10 } } }
      }
    }
  });
}

function openProfile(id) {
  const c = IAS_DATA.clients.find(x => x.id === id);
  if (!c) return;
  GLOBAL_STATE.selected_client = c;
  
  document.getElementById('profile-name').textContent = c.name;
  document.getElementById('profile-meta').textContent = (c.category || 'HNI') + ' · ' + c.risk + ' · Since ' + c.since;

  const info = document.getElementById('profile-client-info');
  if (info) {
    info.innerHTML = `
      <div class="kv"><span class="kv-key">Name</span><span class="kv-val">${c.name}</span></div>
      <div class="kv"><span class="kv-key">Phone</span><span class="kv-val">${c.phone || '—'}</span></div>
      <div class="kv"><span class="kv-key">Risk Profile</span><span class="kv-val">${c.risk}</span></div>
      <div class="kv"><span class="kv-key">Category</span><span class="kv-val">${c.category || '—'}</span></div>
    `;
  }
  document.getElementById('profile-total-value').textContent = c.aum;

  // Holdings
  const hbody = document.querySelector('#profile-holdings-table tbody');
  if (hbody) {
    hbody.innerHTML = (c.portfolio.holdings || []).map(h => `
      <tr>
        <td style="font-weight:600">${h.name}</td>
        <td class="num">${h.units || '—'}</td>
        <td class="num">₹${h.avg_price || '—'}</td>
        <td class="num">${h.value}</td>
        <td style="color:var(--c-green)">${h.return}</td>
      </tr>
    `).join('');
  }

  // Transactions
  const txbody = document.querySelector('#profile-transactions-table tbody');
  if (txbody) {
    txbody.innerHTML = (IAS_DATA.transactions || []).filter(t => t.clientId === id).map(t => `
      <tr>
        <td style="font-weight:600">${t.security}</td>
        <td><span class="tag gray">${t.type}</span></td>
        <td class="num">${t.amount}</td>
        <td class="num">${t.date}</td>
        <td><span class="tag green">Confirmed</span></td>
      </tr>
    `).join('');
  }

  // Goals
  const gbody = document.querySelector('#profile-goals-table tbody');
  if (gbody) {
    const cgoals = (IAS_DATA.goals || []).filter(g => g.clientId === id);
    gbody.innerHTML = cgoals.map(g => `
      <tr>
        <td style="font-weight:600">${g.name}</td>
        <td class="num">${g.targetAmount}</td>
        <td class="num">${g.currentCorpus}</td>
        <td style="color:${g.probability > 70 ? 'var(--c-green)' : 'var(--c-red)'}">${g.probability}%</td>
        <td><span class="tag ${g.status === 'On Track' ? 'green' : 'orange'}">${g.status}</span></td>
      </tr>
    `).join('');
  }

  // Tasks
  const taskbody = document.querySelector('#profile-tasks-table tbody');
  if (taskbody) {
    const ctasks = (IAS_DATA.tasks || []).filter(t => t.client === c.name);
    taskbody.innerHTML = ctasks.map(t => `
      <tr>
        <td>${t.title}</td>
        <td><span class="tag gray">${t.type}</span></td>
        <td class="num">${t.due}</td>
        <td><span class="tag ${t.status === 'Done' ? 'green' : 'orange'}">${t.status}</span></td>
      </tr>
    `).join('');
  }

  showScreen('s-profile');
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.nav-btn[data-screen="s-profile"]').forEach(b => b.classList.add('active'));
}

// ── OTHER SCREENS ───────────────────────────────────────────
function renderInsightsScreen() {
  console.log('Sanchay OS: Rendering Insights Screen');
  const body = document.getElementById('insights-body');
  if (!body) {
    console.warn('Insights body element not found');
    return;
  }
  if (!IAS_DATA.insights || IAS_DATA.insights.length === 0) {
    body.innerHTML = '<div class="empty-state"><div class="empty-icon">📡</div><div class="empty-title">No signals yet</div><div class="empty-sub">Intelligence signals will appear here after portfolio analysis.</div></div>';
    return;
  }
  try {
  body.innerHTML = IAS_DATA.insights.map(i => `
    <div class="insight-card sev-${(i.severity || 'MEDIUM').toLowerCase()}">
      <div class="insight-header">
        <span class="tag gray">${(i.type || '').replace(/_/g,' ')}</span>
        <span class="tag ${i.severity === 'HIGH' ? 'red' : i.severity === 'LOW' ? 'green' : 'orange'}">${i.severity}</span>
      </div>
      <div class="insight-title">${i.title}</div>
      <div class="insight-desc">${i.desc}</div>
      <div class="insight-footer">
        <span class="insight-clients">Affects ${i.clients || 'All'} client${(i.clients || 2) > 1 ? 's' : ''}</span>
        <button class="btn btn-ghost btn-xs">${i.action}</button>
      </div>
    </div>
  `).join('');
  } catch (e) {
    console.error('Error rendering insights:', e);
    body.innerHTML = '<div class="empty-state">Error rendering insights</div>';
  }
}

function renderGoalsScreen() {
  const tbody = document.querySelector('#goals-table tbody');
  if (!tbody) return;
  if (!IAS_DATA.goals || !Array.isArray(IAS_DATA.goals) || IAS_DATA.goals.length === 0) {
    tbody.innerHTML = '<tr><td colspan="10" class="empty-cell">No goals found. Add a goal to get started.</td></tr>';
    return;
  }
  tbody.innerHTML = IAS_DATA.goals.map(g => `
    <tr>
      <td><strong>${g.client}</strong></td>
      <td>${g.name}</td>
      <td class="num">${g.targetAmount}</td>
      <td class="num">${g.currentCorpus}</td>
      <td class="num">${g.targetDate}</td>
      <td class="num">${g.sipRequired}</td>
      <td class="num">${g.sipCurrent}</td>
      <td><span style="font-weight:700;color:${g.probability > 75 ? 'var(--c-green)' : 'var(--c-orange)'}">${g.probability}%</span></td>
      <td><span class="tag ${g.status === 'On Track' ? 'green' : g.status === 'Ahead' ? 'blue' : 'red'}">${g.status}</span></td>
      <td><button class="btn btn-ghost btn-xs">Adjust SIP</button></td>
    </tr>
  `).join('');
}

function renderReportsScreen() {
  console.log('Sanchay OS: Rendering Reports Screen');
  const tbody = document.querySelector('#reports-table tbody');
  if (!tbody) {
    console.warn('Reports table tbody not found');
    return;
  }
  if (!IAS_DATA.reports || IAS_DATA.reports.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:var(--c-text3)">No reports available</td></tr>';
    return;
  }
  try {
  tbody.innerHTML = IAS_DATA.reports.map(r => `
    <tr>
      <td style='font-weight:600'>${r.type}</td>
      <td style='color:var(--c-text2)'>${r.client || 'All Clients'}</td>
      <td style='color:var(--c-text2)'>${r.freq}</td>
      <td class='num'>${r.last}</td>
      <td><span class='tag ${r.status === 'Ready' ? 'green' : 'gray'}'>${r.status || 'READY'}</span></td>
      <td>
        ${r.url ? `<a href="${SANCHAY_API_BASE}${r.url}" target="_blank" class='btn btn-ghost btn-xs'>Download</a>` : `<button class='btn btn-ghost btn-xs' onclick="generatePdfReport(${r.client_id}, '${r.type}')">Generate</button>`}
      </td>
    </tr>
  `).join('');
  } catch (e) {
    console.error('Error rendering reports:', e);
    tbody.innerHTML = '<tr><td colspan="6">Error loading reports</td></tr>';
  }
}

async function generatePdfReport(clientId, reportType) {
  try {
    const res = await apiFetch(`/reports?client_id=${clientId}&report_type=${reportType}`, { method: 'POST' });
    if (res && res.url) {
      alert("Report generated successfully!");
      window.open(SANCHAY_API_BASE + res.url, '_blank');
      if (shouldRefresh()) syncFromAPI();
    }
  } catch (err) {
    alert("Error generating report: " + err.message);
  }
}

function filterInsights(severity) {
  const body = document.getElementById('insights-body');
  if (!body) return;
  const filtered = severity === 'ALL'
    ? IAS_DATA.insights
    : (IAS_DATA.insights || []).filter(i => i.severity === severity);
  const tmp = { insights: filtered };
  const orig = IAS_DATA.insights;
  IAS_DATA.insights = filtered;
  renderInsightsScreen();
  IAS_DATA.insights = orig;
}

function renderComplianceScreen() {
  const tbody = document.querySelector('#compliance-table tbody');
  if (!tbody || !IAS_DATA.compliance) return;
  const data = IAS_DATA.compliance || [];
  // Update stat counters
  const pending = data.filter(c => c.status === 'Pending').length;
  const inProg = data.filter(c => c.status === 'In Progress').length;
  const completed = data.filter(c => c.status === 'Completed').length;
  const today = new Date().toISOString().split('T')[0];
  const overdue = data.filter(c => c.status !== 'Completed' && c.due && c.due < today).length;
  const pendEl = document.getElementById('comp-pending'); if (pendEl) pendEl.textContent = pending;
  const inPEl = document.getElementById('comp-in-progress'); if (inPEl) inPEl.textContent = inProg;
  const compEl = document.getElementById('comp-completed'); if (compEl) compEl.textContent = completed;
  const overEl = document.getElementById('comp-overdue'); if (overEl) overEl.textContent = overdue;
  tbody.innerHTML = data.map(c => `
    <tr>
      <td style='font-weight:600'>${c.title}</td>
      <td><span class='tag gray'>${c.entity_type || 'LOG'}</span></td>
      <td>${c.client || 'All Clients'}</td>
      <td class='num'>${c.due || '—'}</td>
      <td>${c.owner || '—'}</td>
      <td><span class='tag ${c.status === 'Completed' ? 'green' : c.status === 'In Progress' ? 'blue' : 'orange'}'>${c.status}</span></td>
    </tr>
  `).join('');
}

function renderRevenueScreen() {
  const tbody = document.getElementById('revenue-table');
  if (!tbody || !IAS_DATA.revenue) return;
  tbody.innerHTML = (IAS_DATA.revenue || []).map(r => `
    <tr>
      <td><div style="font-weight:600">${r.client}</div></td>
      <td class="num">${r.aum}</td>
      <td class="num" style="color:var(--c-green);font-weight:700">${r.trail}</td>
      <td><span class="tag gold">${r.tier}</span></td>
      <td><button class="btn btn-ghost btn-xs">Forecast</button></td>
    </tr>
  `).join('');
}

function renderTeamScreen() {
  const tbody = document.getElementById('team-table');
  if (!tbody || !IAS_DATA.team) return;
  tbody.innerHTML = (IAS_DATA.team || []).map(t => `
    <tr>
      <td><div class="flex items-c gap-2"><div class="user-avatar xs">${t.initials}</div><strong>${t.name}</strong></div></td>
      <td style="color:var(--c-text2)">${t.role}</td>
      <td class="num">${t.clients}</td>
      <td class="num">${t.aum}</td>
      <td class="num">${t.tasks}</td>
      <td><span class="tag green">${t.status}</span></td>
      <td><button class="btn btn-ghost btn-xs">Manage</button></td>
    </tr>
  `).join('');
}

function renderReviewsScreen() {
  const body = document.querySelector('#s-reviews .screen-body');
  if (!body) return;
  body.innerHTML = `
    <div class="grid-4 mb-4">
      <div class="card"><div class="card-header"><span class="card-title">Pending Reviews</span></div><div class="card-body"><div class="stat-value num">4</div></div></div>
      <div class="card"><div class="card-header"><span class="card-title">Completed (QTD)</span></div><div class="card-body"><div class="stat-value num">12</div></div></div>
    </div>
    <div class="card">
      <div class="card-header"><span class="card-title">Recent Client Feedback</span></div>
      <div style="overflow:hidden">
        <table class="data-table">
          <thead><tr><th>Client</th><th>Date</th><th>Rating</th><th>Notes</th></tr></thead>
          <tbody>
            ${(IAS_DATA.reviews || []).map(r => `
              <tr>
                <td><strong>${r.client}</strong></td>
                <td>${r.date}</td>
                <td><span style="color:var(--c-gold)">★★★★★</span> ${r.rating}</td>
                <td style="font-size:11px;color:var(--c-text2)">${r.notes}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderCommCenter() {
  console.log('Sanchay OS: Rendering Comm Center');
}

// ── ADVANCED ANALYTICS RENDERING ─────────────────────────────
function renderAdvancedAnalytics(clientId) {
  console.log('Sanchay OS: Rendering Advanced Analytics for', clientId);
  const data = IAS_DATA.analytics;
  if (!data) return;

  // 1. Risk Gauge
  drawGauge(document.getElementById('risk-gauge'), data.risk.volatility, 30, 'Volatility');
  document.getElementById('risk-vol').textContent = data.risk.volatility + '%';
  document.getElementById('risk-dd').textContent = data.risk.maxDrawdown + '%';

  // 2. Overlap Matrix
  drawMatrix(document.getElementById('overlap-matrix'), data.overlap);

  // 3. Sector Exposure
  drawSectorChart(document.getElementById('sector-chart'), data.sector.current);

  // 4. Optimization
  drawOptimizationChart(document.getElementById('opt-chart'), data.optimization);
  document.getElementById('opt-score').textContent = data.optimization.score + '/100';

  // 5. Recommendations
  renderRecommendations(document.getElementById('recommendation-list'), data.recommendations);
}

function renderPracticeIntelligence() {
  console.log('Sanchay OS: Rendering Practice Intelligence');
  const data = IAS_DATA.analytics;
  if (!data || !data.risk) return;

  drawGauge(document.getElementById('dash-risk-gauge'), data.risk.volatility, 30, 'Avg Vol');
  drawSectorChart(document.getElementById('dash-sector-chart'), data.sector.current);
  
  const recList = document.getElementById('dash-recs-list');
  if (recList) {
    recList.innerHTML = (data.recommendations || []).slice(0, 2).map(r => `
      <div class="p-2 flex justify-b items-c" style="background:var(--c-surface2);border-radius:6px;border-left:3px solid var(--c-${r.impact === 'HIGH' ? 'red' : 'gold'})">
        <span style="font-size:11px;font-weight:600">${r.title}</span>
        <button class="btn btn-ghost btn-xs" onclick="showScreen('s-insights')">Fix</button>
      </div>
    `).join('');
  }
}

// ── CHART HELPERS ────────────────────────────────────────────
function drawGauge(el, value, max, label) {
  if (!el) return;
  if (typeof Chart === 'undefined') {
    el.parentElement.innerHTML = '<div style="color:var(--c-text3);font-size:10px;text-align:center;padding-top:40px">Chart library not loaded</div>';
    return;
  }
  new Chart(el, {
    type: 'doughnut',
    data: {
      datasets: [{
        data: [value, max - value],
        backgroundColor: ['#C8A96E', 'rgba(255,255,255,0.05)'],
        borderWidth: 0,
        circumference: 180,
        rotation: 270,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '80%',
      plugins: { tooltip: { enabled: false }, legend: { display: false } }
    }
  });
}

function drawSectorChart(el, sectors) {
  if (!el) return;
  if (typeof Chart === 'undefined') {
    el.parentElement.innerHTML = '<div style="color:var(--c-text3);font-size:10px;text-align:center;padding-top:40px">Data visualization unavailable</div>';
    return;
  }
  new Chart(el, {
    type: 'bar',
    data: {
      labels: sectors.map(s => s.name),
      datasets: [
        { label: 'Current', data: sectors.map(s => s.value), backgroundColor: '#C8A96E' },
        { label: 'Benchmark', data: sectors.map(s => s.benchmark), backgroundColor: 'rgba(255,255,255,0.1)' }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: { 
        x: { grid: { display:false }, ticks: { color: '#4A5878', font: { size: 10 } } },
        y: { grid: { display:false }, ticks: { color: '#F0F4FF', font: { size: 10 } } }
      }
    }
  });
}

function drawOptimizationChart(el, opt) {
  if (!el) return;
  if (typeof Chart === 'undefined') {
    el.parentElement.innerHTML = '<div style="color:var(--c-text3);font-size:10px;text-align:center;padding-top:40px">Optimization data unavailable</div>';
    return;
  }
  new Chart(el, {
    type: 'radar',
    data: {
      labels: ['Equity', 'Debt', 'Gold', 'Cash'],
      datasets: [
        { label: 'Current', data: opt.currentAlloc, borderColor: 'rgba(255,255,255,0.2)', backgroundColor: 'transparent' },
        { label: 'Optimized', data: opt.optimizedAlloc, borderColor: '#C8A96E', backgroundColor: 'rgba(200,169,110,0.2)' }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        r: { 
          grid: { color: 'rgba(255,255,255,0.05)' },
          angleLines: { color: 'rgba(255,255,255,0.05)' },
          pointLabels: { color: '#F0F4FF', font: { size: 10 } },
          ticks: { display: false }
        }
      }
    }
  });
}

function drawMatrix(el, data) {
  if (!el) return;
  if (typeof Chart === 'undefined') {
    el.parentElement.innerHTML = '<div style="color:var(--c-text3);font-size:10px;text-align:center;padding-top:40px">Overlap matrix unavailable</div>';
    return;
  }
  const bubbleData = [];
  data.matrix.forEach((row, rIdx) => {
    row.forEach((val, cIdx) => {
      bubbleData.push({ x: cIdx, y: rIdx, r: val * 10, v: val });
    });
  });

  new Chart(el, {
    type: 'bubble',
    data: {
      datasets: [{
        data: bubbleData,
        backgroundColor: (ctx) => {
          const v = ctx.raw ? ctx.raw.v : 0;
          return v > 0.5 ? 'rgba(240,78,35,0.7)' : 'rgba(47,189,126,0.7)';
        }
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { min: -1, max: 4, grid: { display:false }, ticks: { display: false } },
        y: { min: -1, max: 4, grid: { display:false }, ticks: { display: false } }
      }
    }
  });
}

function renderRecommendations(el, recs) {
  if (!el) return;
  el.innerHTML = recs.map(r => `
    <div class="rec-card">
      <div class="rec-impact" style="background:var(--c-${r.impact === 'HIGH' ? 'red' : 'gold'}-bg);color:var(--c-${r.impact === 'HIGH' ? 'red' : 'gold'})">${r.impact} IMPACT</div>
      <div style="font-weight:700;font-size:13px;color:var(--c-text1);margin-bottom:4px">${r.title}</div>
      <div style="font-size:11px;color:var(--c-text2);margin-bottom:12px">${r.desc}</div>
      <button class="btn btn-primary btn-xs w-full">Execute Strategy</button>
    </div>
  `).join('');
}
