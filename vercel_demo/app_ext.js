// ── OVERLAY MANAGEMENT ──────────────────────────────────────
function toggleOverlay(id) {
  const el = document.getElementById(id);
  const isOpen = el.style.display === 'block';
  closeOverlays();
  if (!isOpen) {
    el.style.display = 'block';
    renderTopBarData();
  }
}

function closeOverlays() {
  document.querySelectorAll('.topbar-overlay').forEach(ov => {
    if (ov.id !== 'modal-container') ov.style.display = 'none';
  });
}

function renderTopBarData() {
  const alertsBody = document.getElementById('overlay-alerts-body');
  if (alertsBody) {
    alertsBody.innerHTML = IAS_DATA.insights.slice(0, 5).map(i => `
      <div class="dc-card p-3 mb-2" style="background:rgba(255,255,255,0.03);border-radius:6px;border-left:3px solid var(--c-${i.severity === 'HIGH' ? 'red' : 'gold'})">
        <div class="flex justify-b mb-1"><span class="tag gray xs">${i.type}</span><span class="tag ${i.severity === 'HIGH' ? 'red' : 'gold'} xs">${i.severity}</span></div>
        <div style="font-weight:700;font-size:12px">${i.title}</div>
        <div style="font-size:11px;color:var(--c-text2)">${i.desc}</div>
      </div>
    `).join('');
  }

  const tasksBody = document.getElementById('overlay-tasks-body');
  if (tasksBody) {
    tasksBody.innerHTML = IAS_DATA.tasks.slice(0, 5).map(t => `
      <div class="flex items-c gap-3 p-2 mb-1" style="border-bottom:1px solid var(--c-border)">
        <div class="dot-${t.priority === 'High' ? 'red' : 'orange'}"></div>
        <div class="flex-1">
          <div style="font-weight:600;font-size:12px">${t.title}</div>
          <div style="font-size:10px;color:var(--c-text3)">${t.client} &middot; ${t.due}</div>
        </div>
      </div>
    `).join('');
  }
}

// ── LOGIC ENGINE ─────────────────────────────────────────────
function transaction_engine(data) {
  console.log('Sanchay OS: Running Transaction Engine', data);
  const c = IAS_DATA.clients.find(x => x.id === data.clientId);
  if (!c) { console.error('Client not found', data.clientId); return; }

  let holding = c.portfolio.holdings.find(h => h.name === data.asset);
  
  if (data.type === 'BUY') {
    if (!holding) {
      holding = { name: data.asset, type: 'Equity · Custom', value: '₹0', alloc: '0%', return: '0%', drift: '0%', status: 'on-target' };
      c.portfolio.holdings.push(holding);
    }
    const currentVal = parseFloat(holding.value.replace(/[₹,L,Cr]/g, '')) || 0;
    holding.value = '₹' + (currentVal + (data.amount / 100000)).toFixed(1) + 'L';
  } else if (data.type === 'SELL' && holding) {
    const currentVal = parseFloat(holding.value.replace(/[₹,L,Cr]/g, '')) || 0;
    holding.value = '₹' + Math.max(0, currentVal - (data.amount / 100000)).toFixed(1) + 'L';
  }

  // Insert transaction
  IAS_DATA.transactions.unshift({
    id: 'tx' + Date.now(),
    clientId: data.clientId,
    date: 'Today',
    type: data.type,
    security: data.asset,
    amount: '₹' + data.amount.toLocaleString(),
    nav: '—',
    mode: 'Manual',
    status: 'Confirmed'
  });

  console.log('Sanchay OS: Transaction saved. Triggering insights.');
  insight_engine(c.id);
  if (typeof openProfile === 'function') openProfile(c.id);
}

function insight_engine(clientId) {
  const c = IAS_DATA.clients.find(x => x.id === clientId);
  if (!c) return;

  const equity = c.portfolio.equity;
  if (equity > 80) {
    create_alert(c.name, 'High Risk Exposure', 'Equity concentration > 80%');
  }

  c.portfolio.holdings.forEach(h => {
    const alloc = parseFloat(h.alloc) || 0;
    if (alloc > 25) {
      create_alert(c.name, 'Over Concentration', `${h.name} is > 25% of portfolio`);
    }
  });
}

function create_alert(clientName, type, desc) {
  const alert = {
    id: 'i' + Date.now(),
    type: 'RISK_ALERT',
    severity: 'HIGH',
    title: type,
    desc: `${clientName}: ${desc}`,
    clients: 1,
    action: 'Review',
    screen: 's-profile'
  };
  IAS_DATA.insights.unshift(alert);
  task_generator(clientName, type);
  updateNotificationBadge();
}

function updateNotificationBadge() {
  const badge = document.querySelector('#btn-alerts .badge-dot');
  if (!badge) return;
  const highCount = IAS_DATA.insights.filter(i => i.severity === 'HIGH').length;
  badge.style.display = highCount > 0 ? 'block' : 'none';
}

async function task_generator(clientName, alertType) {
  const client = IAS_DATA.clients.find(c => c.name === clientName);
  const clientId = client ? Number(String(client.id).replace(/^c/, '')) : null;

  const task = {
    id: 't' + Date.now(),
    title: `Follow-up: ${alertType}`,
    client: clientName,
    due: 'Tomorrow',
    priority: 'High',
    status: 'Pending',
    type: 'Action'
  };

  IAS_DATA.tasks.unshift(task);

  if (clientId !== null) {
    await apiFetch('/tasks', {
      method: 'POST',
      body: JSON.stringify({
        advisor_id: 1,
        client_id: clientId,
        task_type: task.title,
        priority: 'High',
        due_date: new Date(Date.now() + 24*60*60*1000).toISOString().slice(0,10),
        status: 'Pending'
      })
    });
  }

  if (typeof renderDashboard === 'function') renderDashboard();
}

// ── MODAL CONTROLLER ─────────────────────────────────────────
function openModal(title, contentHtml) {
  const container = document.getElementById('modal-container');
  const body = document.getElementById('modal-body');
  const titleEl = document.getElementById('modal-title');
  
  if (!container || !body || !titleEl) return;
  
  titleEl.textContent = title;
  body.innerHTML = contentHtml;
  container.style.display = 'block';
}

function closeModal() {
  const container = document.getElementById('modal-container');
  if (container) container.style.display = 'none';
}

// Modal Form Handlers
async function handleAddClient(e) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const name = formData.get('name');
  if (!name) return;

  const payload = {
    name,
    email: formData.get('email') || null,
    phone: formData.get('phone') || null,
    advisor_id: 1,
    onboarding_date: new Date().toISOString().slice(0,10)
  };

  const res = await apiFetch('/onboard_client', {
    method: 'POST',
    body: JSON.stringify(payload)
  });

  const newId = res?.client_id ? `c${res.client_id}` : 'c' + (IAS_DATA.clients.length + 100);

  const newClient = {
    id: newId,
    name,
    initials: name.split(' ').map(n=>n[0]).join('').substring(0,2).toUpperCase(),
    aum: '₹0',
    aum_raw: 0,
    phone: payload.phone || '+91 -',
    email: payload.email || '',
    risk: formData.get('risk_profile') || 'Moderate',
    since: new Date().getFullYear().toString(),
    category: 'Retail',
    status: 'Active',
    portfolio: { equity: 0, debt: 0, gold: 0, cash: 0, holdings: [] }
  };

  IAS_DATA.clients.unshift(newClient);

  if (typeof renderClientsTable === 'function') renderClientsTable(document.querySelector('#clients-table tbody'));
  if (typeof renderDashboard === 'function') renderDashboard();
  closeModal();
}

function handleAddHolding(e) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const clientId = GLOBAL_STATE.selected_client?.id;
  if (!clientId) return;
  
  transaction_engine({
    clientId,
    asset: formData.get('asset'),
    type: 'BUY',
    amount: parseFloat(formData.get('units')) * parseFloat(formData.get('buy_price')),
    units: parseFloat(formData.get('units'))
  });
  closeModal();
}

async function handleAddTransaction(e) {
  e.preventDefault();
  const formData = new FormData(e.target);
  const clientId = GLOBAL_STATE.selected_client?.id;
  if (!clientId) return;

  const txn = {
    clientId,
    asset: formData.get('asset'),
    type: formData.get('txn_type'),
    amount: parseFloat(formData.get('amount')),
    units: parseFloat(formData.get('units'))
  };

  transaction_engine(txn);

  await apiFetch('/transactions', {
    method: 'POST',
    body: JSON.stringify({
      client_id: Number(String(clientId).replace(/^c/, '')) || 0,
      asset_id: 1,
      txn_type: txn.type,
      quantity: txn.units || 0,
      price: txn.amount || 0,
      txn_date: new Date().toISOString().slice(0,10)
    })
  });

  closeModal();
}


// ── GOAL WORKFLOW ───────────────────────────────────────────
let currentGoalData = {};

function startGoalWorkflow(clientId = null) {
  const client = clientId ? IAS_DATA.clients.find(c => c.id === clientId) : null;
  currentGoalData = {
    clientId: clientId || '',
    clientName: client ? client.name : '',
    name: '', target: 0, date: '', corpus: 0, sip: 0
  };
  showScreen('s-goal-workflow');

  // Reset all steps
  document.querySelectorAll('.gw-step-content').forEach(c => c.style.display = 'none');

  if (clientId && client) {
    // Client already known — skip Step 1, go straight to goal details
    document.getElementById('gw-content-2').style.display = 'block';
    updateStepUI(2);

    // Show client name as a read-only label in Step 2 header if element exists
    const clientLabel = document.getElementById('gw-selected-client-label');
    if (clientLabel) clientLabel.textContent = 'Client: ' + client.name;
  } else {
    // No client — show Step 1 (select client)
    document.getElementById('gw-content-1').style.display = 'block';
    updateStepUI(1);

    const select = document.getElementById('gw-client-select');
    if (select) {
      select.innerHTML = '<option value="">-- Select Client --</option>' +
        IAS_DATA.clients.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    }
    document.getElementById('gw-new-client-form').style.display = 'none';
    document.getElementById('gw-nc-name').value = '';
  }
}

function updateStepUI(step) {
  document.querySelectorAll('.step-item').forEach((item, idx) => {
    const num = item.querySelector('.step-num');
    if (idx + 1 < step) {
      num.style.background = 'var(--c-green)';
      num.innerHTML = '✓';
    } else if (idx + 1 === step) {
      num.style.background = 'var(--c-gold)';
      num.style.color = '#000';
      num.innerHTML = step;
    } else {
      num.style.background = 'var(--c-border)';
      num.style.color = 'var(--c-text3)';
      num.innerHTML = idx + 1;
    }
  });
}

function handleGoalNext(step) {
  if (step === 1) {
    const select = document.getElementById('gw-client-select');
    const newName = document.getElementById('gw-nc-name').value;
    
    if (newName) {
      currentGoalData.clientName = newName;
      currentGoalData.clientId = 'c' + Date.now();
    } else if (select.value) {
      const c = IAS_DATA.clients.find(x => x.id === select.value);
      currentGoalData.clientId = c.id;
      currentGoalData.clientName = c.name;
    } else {
      alert('Please select a client or enter a new name');
      return;
    }
    
    document.getElementById('gw-content-1').style.display = 'none';
    document.getElementById('gw-content-2').style.display = 'block';
    updateStepUI(2);
  } else if (step === 2) {
    currentGoalData.name = document.getElementById('gw-g-name').value;
    currentGoalData.target = document.getElementById('gw-g-target').value;
    currentGoalData.date = document.getElementById('gw-g-date').value;
    currentGoalData.corpus = document.getElementById('gw-g-corpus').value;
    currentGoalData.sip = document.getElementById('gw-g-sip').value;

    if (!currentGoalData.name) { alert('Please enter goal name'); return; }

    // Summary
    document.getElementById('rv-client-name').textContent = currentGoalData.clientName;
    document.getElementById('rv-goal-name').textContent = currentGoalData.name;
    document.getElementById('rv-target-amt').textContent = '₹' + parseFloat(currentGoalData.target).toLocaleString();
    document.getElementById('rv-target-date').textContent = currentGoalData.date;
    document.getElementById('rv-sip-amt').textContent = '₹' + parseFloat(currentGoalData.sip).toLocaleString() + ' /mo';

    document.getElementById('gw-content-2').style.display = 'none';
    document.getElementById('gw-content-3').style.display = 'block';
    updateStepUI(3);
  }
}

async function handleGoalFinish() {
  const fv = currentGoalData.target;
  const sip = currentGoalData.sip;
  const prob = 85;

  const newGoal = {
    id: 'g' + Date.now(),
    clientId: currentGoalData.clientId,
    client: currentGoalData.clientName,
    name: currentGoalData.name,
    targetAmount: '₹' + Math.round(fv).toLocaleString('en-IN'),
    currentCorpus: '₹' + Math.round(currentGoalData.corpus).toLocaleString('en-IN'),
    targetDate: currentGoalData.date,
    sipRequired: '₹' + Math.round(sip).toLocaleString('en-IN'),
    sipCurrent: '₹' + Math.round(sip).toLocaleString('en-IN'),
    probability: prob,
    status: 'On Track'
  };

  IAS_DATA.goals.unshift(newGoal);
  
  await apiFetch('/goals', {
    method: 'POST',
    body: JSON.stringify({
      client_id: Number(String(currentGoalData.clientId).replace(/^c/, '')) || 0,
      goal_type: newGoal.name,
      target_amount: Number(fv),
      target_date: currentGoalData.date || new Date().toISOString().slice(0,10),
      priority: 'Medium',
      status: 'On Track'
    })
  });
  
  if (GLOBAL_STATE.selected_client && GLOBAL_STATE.selected_client.id === currentGoalData.clientId) {
    if (typeof openProfile === 'function') openProfile(currentGoalData.clientId);
  }
  
  showScreen('s-goals');
  if (typeof renderDashboard === 'function') renderDashboard();
  alert('Goal added successfully!');
}

// ── INIT ─────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Navigation & Step listeners
  document.getElementById('gw-next-1')?.addEventListener('click', () => handleGoalNext(1));
  document.getElementById('gw-next-2')?.addEventListener('click', () => handleGoalNext(2));
  document.getElementById('gw-finish')?.addEventListener('click', handleGoalFinish);
  
  document.getElementById('gw-prev-2')?.addEventListener('click', () => {
    // If client already known (no Step 1 needed), just cancel back to profile
    if (currentGoalData.clientId && !document.getElementById('gw-content-1').dataset.shown) {
      showScreen('s-profile');
      return;
    }
    document.getElementById('gw-content-2').style.display = 'none';
    document.getElementById('gw-content-1').style.display = 'block';
    updateStepUI(1);
  });
  document.getElementById('gw-prev-3')?.addEventListener('click', () => {
    document.getElementById('gw-content-3').style.display = 'none';
    document.getElementById('gw-content-2').style.display = 'block';
    updateStepUI(2);
  });

  document.getElementById('gw-btn-new-client')?.addEventListener('click', () => {
    const form = document.getElementById('gw-new-client-form');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
  });

  // Modal Buttons
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('#btn-open-add-client, #btn-open-add-holding, #btn-open-add-transaction, #btn-close-modal, #btn-open-upload-cas');
    if (!btn) return;

    if (btn.id === 'btn-open-upload-cas') {
      const clientId = GLOBAL_STATE.selected_client?.id;
      if (!clientId) return;
      openModal('Upload CAS Statement', `
        <form id='form-upload-cas' class='flex flex-col gap-4'>
          <div style='padding:40px; border:2px dashed var(--c-border); border-radius:8px; text-align:center; background:rgba(255,255,255,0.02)'>
            <input type='file' id='cas-file-input' accept='.pdf' style='display:none'>
            <label for='cas-file-input' style='cursor:pointer'>
              <svg width='32' height='32' viewBox='0 0 24 24' fill='none' stroke='var(--c-gold)' stroke-width='2' style='margin-bottom:12px'><path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/><polyline points='17 8 12 3 7 8'/><line x1='12' y1='3' x2='12' y2='15'/></svg>
              <div style='font-size:14px; font-weight:600'>Click to select CAS PDF</div>
              <div style='font-size:10px; color:var(--c-text3); margin-top:4px'>Only .pdf files are accepted</div>
            </label>
            <div id='cas-file-name' style='margin-top:12px; font-size:12px; color:var(--c-gold); font-weight:700'></div>
          </div>
          <button type='submit' class='btn btn-primary w-full mt-2' id='btn-submit-cas' disabled>Ingest Statement &rarr;</button>
        </form>
      `);
      
      const input = document.getElementById('cas-file-input');
      const submit = document.getElementById('btn-submit-cas');
      const fileName = document.getElementById('cas-file-name');
      
      input.onchange = (e) => {
        if (e.target.files.length > 0) {
          fileName.textContent = e.target.files[0].name;
          submit.disabled = false;
        }
      };

      document.getElementById('form-upload-cas').onsubmit = (e) => {
        e.preventDefault();
        cas_upload_engine(input.files[0], clientId);
      };

    } else if (btn.id === 'btn-open-add-client') {
      openModal('Add New Client', `
        <form id='form-add-client' class='flex flex-col gap-4'>
          <div><label class='field-label'>Name</label><input class='field-input' name='name' required></div>
          <div><label class='field-label'>Phone</label><input class='field-input' name='phone' required></div>
          <div><label class='field-label'>Email</label><input class='field-input' name='email' required></div>
          <div><label class='field-label'>Risk Profile</label>
            <select class='field-input' name='risk_profile'>
              <option>Aggressive</option><option>Moderate</option><option>Conservative</option>
            </select>
          </div>
          <button type='submit' class='btn btn-primary w-full mt-2'>Create Client</button>
        </form>
      `);
      document.getElementById('form-add-client').onsubmit = handleAddClient;
    } else if (btn.id === 'btn-open-add-holding') {
      openModal('Add Holding', `
        <form id='form-add-holding' class='flex flex-col gap-4'>
          <div><label class='field-label'>Asset</label><input class='field-input' name='asset' required></div>
          <div class='grid-2'>
            <div><label class='field-label'>Units</label><input class='field-input' name='units' type='number' step='0.01' required></div>
            <div><label class='field-label'>Buy Price</label><input class='field-input' name='buy_price' type='number' step='0.01' required></div>
          </div>
          <button type='submit' class='btn btn-primary w-full mt-2'>Add Holding</button>
        </form>
      `);
      document.getElementById('form-add-holding').onsubmit = handleAddHolding;
    } else if (btn.id === 'btn-open-add-transaction') {
      openModal('Add Transaction', `
        <form id='form-add-transaction' class='flex flex-col gap-4'>
          <div><label class='field-label'>Asset</label><input class='field-input' name='asset' required></div>
          <div class='grid-2'>
            <div><label class='field-label'>Type</label>
              <select class='field-input' name='txn_type'><option>BUY</option><option>SELL</option></select>
            </div>
            <div><label class='field-label'>Amount</label><input class='field-input' name='amount' type='number' required></div>
          </div>
          <div><label class='field-label'>Units</label><input class='field-input' name='units' type='number' step='0.01' required></div>
          <button type='submit' class='btn btn-primary w-full mt-2'>Record Transaction</button>
        </form>
      `);
      document.getElementById('form-add-transaction').onsubmit = handleAddTransaction;
    } else if (btn.id === 'btn-close-modal') {
      closeModal();
    }
  });

  // Global Goal Buttons
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('#btn-add-goal-dash, #btn-add-goal-global, #btn-add-goal-profile, #btn-add-goal-header');
    if (btn) {
      e.preventDefault();
      const activeClient = GLOBAL_STATE.selected_client?.id;
      startGoalWorkflow(activeClient);
    }
  });

  renderMarketTicker();
});

// ── CAS INGESTION ENGINE ─────────────────────────────────────
function cas_upload_engine(file, clientId) {
  console.log('Sanchay OS: Starting CAS Ingestion', file.name);
  const casId = 'cas' + Date.now();
  
  IAS_DATA.cas_files.unshift({
    cas_id: casId,
    client_id: clientId,
    file_url: file.name,
    upload_date: new Date().toLocaleDateString(),
    status: 'Processing'
  });

  closeModal();
  alert('CAS Statement Uploaded. Processing transactions...');

  // Step 2: Trigger Parser (Simulation)
  setTimeout(() => cas_parser(casId), 1500);
}

function cas_parser(casId) {
  console.log('Sanchay OS: Running CAS Parser', casId);
  const casRecord = IAS_DATA.cas_files.find(f => f.cas_id === casId);
  if (!casRecord) return;

  // Mock extracted transactions based on rules
  const mockRawData = [
    { scheme_name: 'HDFC Bank Ltd', isin: 'HDFC_BANK', amount: 50000, date: '2023-10-10', line: 'Purchase HDFC Bank - 50000' },
    { scheme_name: 'Reliance Ind.', isin: 'RELIANCE', amount: 30000, date: '2023-10-12', line: 'Purchase Reliance - 30000' },
    { scheme_name: 'HDFC Bank Ltd', isin: 'HDFC_BANK', amount: 10000, date: '2023-10-15', line: 'Redemption HDFC Bank - 10000' }
  ];

  mockRawData.forEach(raw => {
    let type = 'OTHER';
    if (raw.line.includes('Purchase')) type = 'BUY';
    if (raw.line.includes('Redemption')) type = 'SELL';
    if (raw.line.includes('SIP')) type = 'SIP';

    IAS_DATA.raw_transactions.push({
      raw_txn_id: 'rt' + Math.random().toString(36).substr(2, 9),
      cas_id: casId,
      scheme_name: raw.scheme_name,
      isin: raw.isin,
      txn_type: type,
      amount: raw.amount,
      date: raw.date
    });
  });

  casRecord.status = 'Completed';
  console.log('Sanchay OS: CAS Parsing Finished. Transactions stored.');

  // Step 3: Trigger Reconstruction
  portfolio_reconstruction_engine(casRecord.client_id);
}

function portfolio_reconstruction_engine(clientId) {
  console.log('Sanchay OS: Reconstructing Portfolio for', clientId);
  const client = IAS_DATA.clients.find(c => c.id === clientId);
  if (!client) return;

  const clientTxns = IAS_DATA.raw_transactions.filter(t => {
    const cas = IAS_DATA.cas_files.find(f => f.cas_id === t.cas_id);
    return cas && cas.client_id === clientId;
  });

  // Group by ISIN
  const groups = {};
  clientTxns.forEach(t => {
    if (!groups[t.isin]) groups[t.isin] = { units: 0, total_spent: 0, name: t.scheme_name };
    
    // Simulating conversion (amount / 1000 = units for demo)
    const mockUnits = t.amount / 1000;
    if (t.txn_type === 'BUY' || t.txn_type === 'SIP') {
      groups[t.isin].units += mockUnits;
      groups[t.isin].total_spent += t.amount;
    } else if (t.txn_type === 'SELL') {
      groups[t.isin].units -= mockUnits;
    }
  });

  // Update holdings
  Object.keys(groups).forEach(isin => {
    const data = groups[isin];
    let h = client.portfolio.holdings.find(x => x.name === data.name);
    if (!h) {
      h = { name: data.name, type: 'Equity · Ingested', value: '₹0', return: '—', status: 'Active' };
      client.portfolio.holdings.push(h);
    }
    h.units = data.units.toFixed(2);
    h.avg_price = (data.total_spent / data.units).toFixed(2);
    h.isin = isin;
  });

  console.log('Sanchay OS: Portfolio Reconstruction Finished.');
  valuation_engine(clientId);
}

function nav_sync_engine() {
  console.log('Sanchay OS: Syncing NAVs...');
  // Mock update
  IAS_DATA.nav_data.forEach(n => {
    n.nav *= (1 + (Math.random() * 0.02 - 0.01)); // +/- 1%
  });
}

function valuation_engine(clientId) {
  console.log('Sanchay OS: Running Valuation Engine for', clientId);
  const client = IAS_DATA.clients.find(c => c.id === clientId);
  if (!client) return;

  let totalValue = 0;
  client.portfolio.holdings.forEach(h => {
    const navItem = IAS_DATA.nav_data.find(n => n.asset_id === h.isin);
    const nav = navItem ? navItem.nav : 1500; // Fallback
    const currentVal = (h.units || 0) * nav;
    h.value = '₹' + (currentVal / 100000).toFixed(1) + 'L';
    totalValue += currentVal;
  });

  client.aum_raw = totalValue;
  client.aum = '₹' + (totalValue / 10000000).toFixed(2) + ' Cr';
  
  console.log('Sanchay OS: Valuation complete. AUM:', client.aum);
  
  // Refresh UI
  if (typeof openProfile === 'function') openProfile(clientId);
  if (typeof renderDashboard === 'function') renderDashboard();
  
  // QA-05: Insights Trigger
  create_alert(client.name, 'Portfolio Reconstructed', `Ingestion completed for ${client.name}. Total Value: ${client.aum}`);
}

// Helper for Background ticker
function renderMarketTicker() {
  const t = document.getElementById('market-ticker');
  if (!t) return;
  const items = [
    { name: 'NIFTY 50', val: '24,321.05', delta: '+124.50', up: true },
    { name: 'SENSEX', val: '80,123.44', delta: '+450.20', up: true },
    { name: 'HDFC BANK', val: '1,680.40', delta: '-12.30', up: false }
  ];
  t.innerHTML = '<div class="ticker-scroll">' + items.map(i => `
    <div class="ticker-item">
      <span class="ticker-name">${i.name}</span>
      <span class="ticker-val">${i.val}</span>
      <span class="ticker-delta" style="color:${i.up ? 'var(--c-green)' : 'var(--c-red)'}">${i.delta}</span>
    </div>
  `).join('') + '</div>';
}
setInterval(renderMarketTicker, 60000);
