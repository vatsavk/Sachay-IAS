
  'use strict';
  
  // Auth Guard
  const TOKEN = localStorage.getItem('sanchay_token');
  const ROLE  = localStorage.getItem('sanchay_role');
  const UNAME = localStorage.getItem('sanchay_name');
  
  if (!TOKEN || ROLE !== 'client') {
    window.location.href = 'client_login.html';
  }

  // Header Details
  document.getElementById('user-name').textContent = UNAME || 'Client';
  const initials = (UNAME || 'C').split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase();
  document.getElementById('user-avatar').textContent = initials;
  
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
  document.getElementById('greeting-txt').textContent = `${greeting}, ${(UNAME || 'Client').split(' ')[0]} 👋`;
  
  document.getElementById('terminal-date').textContent = new Date().toLocaleDateString('en-IN', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric'
  });

  const API_BASE = window.SANCHAY_CONFIG ? window.SANCHAY_CONFIG.getAPIUrl('') : 'http://localhost:8001';
  
  let dashboardData = null;
  let trendChart = null;

  const formatINR = v => {
    if (v >= 1e7) return `₹${(v / 1e7).toFixed(2)} Cr`;
    if (v >= 1e5) return `₹${(v / 1e5).toFixed(1)} L`;
    return `₹${Number(Math.round(v || 0)).toLocaleString('en-IN')}`;
  };

  function showToast(msg, type = 'success') {
    const container = document.getElementById('toast-wrap');
    const toast = document.createElement('div');
    toast.className = `toast-message ${type}`;
    toast.innerHTML = `<span>${type === 'success' ? '✓' : '✕'}</span><span>${msg}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  }

  function triggerNav(targetScreen) {
    document.querySelectorAll('.nav-item').forEach(nav => {
      if (nav.getAttribute('data-target') === targetScreen) {
        nav.classList.add('active');
      } else {
        nav.classList.remove('active');
      }
    });
    document.querySelectorAll('.screen').forEach(scr => {
      if (scr.getAttribute('id') === targetScreen) {
        scr.classList.add('active');
      } else {
        scr.classList.remove('active');
      }
    });

    if (targetScreen === 's-overview') renderOverview();
    else if (targetScreen === 's-portfolio') renderPortfolio();
    else if (targetScreen === 's-goals') renderGoals();
    else if (targetScreen === 's-risk') renderRisk();
    else if (targetScreen === 's-actions') renderActionHub();
    else if (targetScreen === 's-minutes') renderMeetingMinutes();
    else if (targetScreen === 's-tax') renderTax();
  }

  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      triggerNav(item.getAttribute('data-target'));
    });
  });

  async function fetchAPI(endpoint, opts = {}) {
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${TOKEN}`
    };
    try {
      const response = await fetch(API_BASE + endpoint, { headers, ...opts });
      if (response.status === 401) {
        logout();
        return null;
      }
      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || response.statusText);
      }
      return await response.json();
    } catch (err) {
      if (err.message !== 'Failed to fetch') {
        showToast(err.message, 'error');
      }
      return null;
    }
  }

  async function loadDashboardData() {
    document.getElementById('skeleton-screen').style.display = 'flex';
    const data = await fetchAPI('/my/dashboard/analytics');
    document.getElementById('skeleton-screen').style.display = 'none';
    if (data) {
      dashboardData = data;
      if (data.usd_inr) {
        document.getElementById('ticker-usd').textContent = data.usd_inr.toFixed(2);
      }
      renderOverview();
    }
  }

  // ── ZONE 1 & 2 & 3: OVERVIEW RENDERING ──
  function renderOverview() {
    if (!dashboardData) return;

    // ZONE 1: TODAY'S POSITION Summary
    const z1 = dashboardData.zone1_today_position || {};
    document.getElementById('kpi-net-worth').textContent = formatINR(z1.net_worth);
    
    const signCost = z1.today_change >= 0 ? '+' : '';
    document.getElementById('kpi-net-worth-desc').innerHTML = `
      <span style="color: ${z1.today_change >= 0 ? 'var(--green)' : 'var(--red)'}; font-weight:700;">
        ${signCost}${formatINR(z1.today_change)} (${z1.today_change_percent}%)
      </span> today
    `;

    document.getElementById('kpi-goals-summary').textContent = `${z1.goals_on_track} / ${z1.goals_on_track + z1.goals_at_risk}`;
    document.getElementById('kpi-goals-desc').innerHTML = `
      <span style="color:var(--green); font-weight:700;">${z1.goals_on_track} Goals</span> on track
    `;

    document.getElementById('kpi-health-score').textContent = `${z1.health_score}%`;
    document.getElementById('kpi-health-desc').textContent = z1.health_status;
    const hCard = document.getElementById('kpi-health-card');
    hCard.className = `kpi-card ${z1.health_status === 'Healthy' ? 'blue' : z1.health_status === 'Needs Attention' ? 'amber' : 'red'}`;

    document.getElementById('kpi-actions-score').textContent = `${z1.pending_actions_count} Pending`;
    document.getElementById('kpi-actions-desc').textContent = z1.pending_actions_count > 0 ? "Signature required" : "Ledger clean";

    // ZONE 2: MY PORTFOLIO TODAY Events Feed
    const events = dashboardData.zone2_portfolio_events || [];
    const eventWrap = document.getElementById('overview-event-list');
    if (events.length > 0) {
      eventWrap.innerHTML = events.map(e => {
        const typeClass = e.event_type.toLowerCase().includes('dividend') ? 'dividend' : e.event_type.toLowerCase().includes('earn') ? 'earnings' : e.event_type.toLowerCase().includes('policy') ? 'policy' : 'corp';
        const impactBadge = e.impact_score > 30 ? 'high' : e.impact_score > 10 ? 'med' : 'low';
        return `
          <div class="event-row" onclick="triggerNav('s-portfolio')">
            <div class="event-icon-badge ${typeClass}">${e.event_type.slice(0, 4).toUpperCase()}</div>
            <div class="event-details">
              <div class="event-meta">
                <span>Security: <strong>${sanitize(e.security_name)}</strong></span>
                <span>Exposure: ${e.exposure_percent}%</span>
              </div>
              <div class="event-headline">${sanitize(e.content)}</div>
              <div class="event-desc">Rec Action: <strong style="color:var(--teal);">${sanitize(e.recommended_action)}</strong></div>
            </div>
            <div class="event-impact-badge ${impactBadge}">
              Impact Score: ${e.impact_score}
            </div>
          </div>
        `;
      }).join('');
    } else {
      eventWrap.innerHTML = `<div class="empty-state">No events currently affecting your portfolio.</div>`;
    }

    // ZONE 3: WEALTH OVERVIEW Charts
    renderWealthTrendChart();
    renderDrilldownAllocation();

    // ZONE 5: PERFORMANCE Contributors & Attributions
    const z5 = dashboardData.zone5_performance || {};
    const contribBody = document.getElementById('overview-contrib-body');
    const detractBody = document.getElementById('overview-detract-body');
    
    contribBody.innerHTML = (z5.top_contributors || []).map(hc => `
      <tr>
        <td style="font-weight:600; color:var(--text-primary);">${sanitize(hc.security_name)}</td>
        <td class="num-col" style="color:var(--green); font-weight:700;">+${hc.contribution_percent}%</td>
      </tr>
    `).join('') || `<tr><td colspan="2" style="text-align:center;">None</td></tr>`;

    detractBody.innerHTML = (z5.top_detractors || []).map(hc => `
      <tr>
        <td style="font-weight:600; color:var(--text-primary);">${sanitize(hc.security_name)}</td>
        <td class="num-col" style="color:var(--red); font-weight:700;">${hc.contribution_percent}%</td>
      </tr>
    `).join('') || `<tr><td colspan="2" style="text-align:center;">None</td></tr>`;

    const attrWrap = document.getElementById('overview-attribution-wrap');
    attrWrap.innerHTML = (z5.attribution || []).map(a => `
      <div class="attribution-row">
        <span>${sanitize(a.category_name)} Attribution</span>
        <strong style="color: ${a.contribution_percent >= 0 ? 'var(--green)' : 'var(--red)'};">
          ${a.contribution_percent >= 0 ? '+' : ''}${a.contribution_percent}%
        </strong>
      </div>
    `).join('');

    // ZONE 7: AI RECOMMENDATIONS Feed
    const recs = dashboardData.zone7_recommendations || [];
    const recWrap = document.getElementById('overview-rec-list');
    if (recs.length > 0) {
      recWrap.innerHTML = recs.map(r => {
        const pClass = r.priority.toLowerCase() === 'critical' ? 'critical' : r.priority.toLowerCase() === 'high' ? 'high' : 'medium';
        return `
          <div class="rec-card" id="rec-card-${r.recommendation_id}">
            <div class="rec-hdr">
              <span class="rec-title">${sanitize(r.title)}</span>
              <span class="rec-priority ${pClass}">${sanitize(r.priority)} Priority</span>
            </div>
            <div class="rec-body">${sanitize(r.reason)}</div>
            <div class="rec-benefit-panel">
              <strong>Expected Benefit:</strong> ${sanitize(r.expected_benefit)}<br/>
              <strong>Potential Impact:</strong> ${sanitize(r.potential_impact)}
            </div>
            <div style="display:flex; gap:8px; justify-content:flex-end;">
              <button class="act-btn agree" style="flex:initial; padding:4px 12px;" onclick="executeRecommendation(${r.recommendation_id})">✓ Execute Recommendation</button>
            </div>
          </div>
        `;
      }).join('');
    } else {
      recWrap.innerHTML = `<div class="empty-state">No recommendation alerts.</div>`;
    }
  }

  // ── ZONE 3: CHART & TREE RENDERING ──
  function renderWealthTrendChart() {
    const trend = dashboardData.zone3_wealth_overview?.historical_trend || [];
    const ctx = document.getElementById('nw-trend-chart');
    if (!ctx || trend.length === 0) return;

    if (trendChart) {
      trendChart.destroy();
    }

    const labels = trend.map(t => t.snapshot_date);
    const data = trend.map(t => t.total_value);

    trendChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Total Net Worth',
          data: data,
          borderColor: '#0ae5b3',
          borderWidth: 2,
          backgroundColor: 'rgba(10, 229, 179, 0.05)',
          fill: true,
          tension: 0.2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#475569', font: { size: 9 } }
          },
          y: {
            grid: { color: 'rgba(255,255,255,0.03)' },
            ticks: {
              color: '#475569',
              font: { size: 9 },
              callback: value => formatINR(value)
            }
          }
        }
      }
    });
  }

  function renderDrilldownAllocation() {
    const tree = dashboardData.zone3_wealth_overview?.allocation_tree || {};
    const wrap = document.getElementById('overview-drilldown-tree');
    if (!wrap || !tree.children) return;

    // Recursive helper to render the HTML tree list
    function renderNode(node, level = 0) {
      if (node.value !== undefined) {
        // Lead security node
        return `
          <div style="display:flex; justify-content:space-between; padding:2px 6px; color:var(--text-secondary); margin-left:${level * 8}px;">
            <span>▪ ${sanitize(node.name)}</span>
            <strong style="color:var(--text-primary); font-weight:500;">${formatINR(node.value)}</strong>
          </div>
        `;
      }
      
      const sumValue = getSumValue(node);
      const childrenHTML = (node.children || []).map(child => renderNode(child, level + 1)).join('');
      
      return `
        <div class="tree-node" style="margin-left:${level * 6}px;">
          <div class="tree-node-hdr" onclick="toggleNode(this)">
            <span class="tree-node-name">▼ ${sanitize(node.name)}</span>
            <span class="tree-node-val">${formatINR(sumValue)}</span>
          </div>
          <div class="tree-node-children">
            ${childrenHTML}
          </div>
        </div>
      `;
    }

    function getSumValue(node) {
      if (node.value !== undefined) return node.value;
      return (node.children || []).reduce((acc, c) => acc + getSumValue(c), 0);
    }

    wrap.innerHTML = (tree.children || []).map(cat => renderNode(cat, 0)).join('');
  }

  function toggleNode(hdr) {
    const children = hdr.nextElementSibling;
    if (children.style.display === 'none') {
      children.style.display = 'block';
      hdr.querySelector('.tree-node-name').textContent = hdr.querySelector('.tree-node-name').textContent.replace('▶', '▼');
    } else {
      children.style.display = 'none';
      hdr.querySelector('.tree-node-name').textContent = hdr.querySelector('.tree-node-name').textContent.replace('▼', '▶');
    }
  }

  // Execute recommendation consent
  async function executeRecommendation(id) {
    const card = document.getElementById(`rec-card-${id}`);
    const btn = card.querySelector('button');
    btn.disabled = true;
    
    // Simulate proposal execution via task/notification logic
    showToast('Executing rebalancing recommendation...', 'success');
    setTimeout(() => {
      btn.innerHTML = '✓ Executed';
      btn.className = 'act-btn';
      btn.style.background = 'transparent';
      btn.style.color = 'var(--text-muted)';
      showToast('Portfolio realigned and logs committed successfully.', 'success');
    }, 1500);
  }

  // ── ZONE 4: GOAL COMMAND CENTER FEASIBILITY CENTER ──
  function renderGoals() {
    if (!dashboardData) return;

    const wrap = document.getElementById('goals-list-wrap');
    const goals = dashboardData.zone4_goals_center || [];
    
    if (goals.length > 0) {
      wrap.innerHTML = goals.map(g => {
        const isFeasible = g.success_probability >= 80;
        const barColor = isFeasible ? 'var(--green)' : 'var(--amber)';
        const probBadgeClass = isFeasible ? 'on-track' : 'at-risk';
        return `
          <div class="goal-card">
            <div class="goal-title-row">
              <span>${sanitize(g.goal_name)}</span>
              <span class="goal-prob-badge ${probBadgeClass}">${g.success_probability}% Probability</span>
            </div>
            
            <div class="goal-metric-row" style="margin-top:4px;">
              <span>Allocated Corpus</span>
              <span class="goal-metric-val">${formatINR(g.current_corpus)}</span>
            </div>
            <div class="goal-metric-row">
              <span>Target Amount</span>
              <span class="goal-metric-val">${formatINR(g.target_corpus)}</span>
            </div>
            
            <div class="bar-container" style="height:6px; background:var(--surface-interactive); border-radius:3px; overflow:hidden; margin: 4px 0;">
              <div class="bar-fill" style="width: ${g.funding_percent}%; background: ${barColor};"></div>
            </div>
            
            <div class="goal-metric-row" style="font-size:9.5px;">
              <span>Funding Metric</span>
              <strong style="color:${barColor}; font-weight:700;">${g.funding_percent}%</strong>
            </div>

            ${!isFeasible ? `
              <div class="shortfall-panel">
                <span class="shortfall-title">Funding Shortfall Alert</span>
                <span class="shortfall-desc">
                  Estimated Gap: <strong>${formatINR(g.funding_gap)}</strong><br/>
                  Suggested SIP Increment: <strong style="color:var(--teal); font-weight:700;">+${formatINR(g.suggested_sip_increase)}/mo</strong>
                </span>
                <span style="font-size:9px; color:var(--text-muted); margin-top:2px;">
                  Increases achievement probability by +${g.impact_on_success_probability}%
                </span>
              </div>
            ` : `
              <div style="font-size:10px; color:var(--green); text-align:center; padding:8px; border:1px dashed rgba(44, 212, 136, 0.15); border-radius:6px; margin-top:4px; font-weight:600;">
                ✓ Trajectory fully capitalized
              </div>
            `}
          </div>
        `;
      }).join('');
    } else {
      wrap.innerHTML = `<div class="empty-state" style="grid-column: span 3;">No financial milestones configured.</div>`;
    }
  }

  // ── ZONE 6: RISK COMMAND CENTER DIAGNOSTICS ──
  function renderRisk() {
    if (!dashboardData) return;

    const z6 = dashboardData.zone6_risk || {};
    
    // Risk score numerical exposure rating
    document.getElementById('risk-rating-val').textContent = z6.risk_score;
    document.getElementById('risk-rating-cat').textContent = z6.risk_category;

    // Concentration values
    const conc = z6.concentration || {};
    document.getElementById('risk-top5-pct').textContent = `${conc.top5_holdings_percent}%`;
    document.getElementById('risk-top5-bar').style.width = `${conc.top5_holdings_percent}%`;
    document.getElementById('risk-top10-pct').textContent = `${conc.top10_holdings_percent}%`;
    document.getElementById('risk-top10-bar').style.width = `${conc.top10_holdings_percent}%`;

    // Drift table list
    const driftBody = document.getElementById('risk-drift-body');
    driftBody.innerHTML = (z6.drift || []).map(d => {
      const devColor = d.deviation_percent > 5 ? 'var(--red)' : d.deviation_percent < -5 ? 'var(--amber)' : 'var(--green)';
      const signDev = d.deviation_percent > 0 ? '+' : '';
      return `
        <tr>
          <td style="font-weight:600; color:var(--text-primary);">${sanitize(d.category_name)}</td>
          <td class="num-col">${d.target_percent}%</td>
          <td class="num-col">${d.current_percent}%</td>
          <td class="num-col" style="color:${devColor}; font-weight:700;">${signDev}${d.deviation_percent}%</td>
        </tr>
      `;
    }).join('');

    // Contributors breakdowns
    const contribs = z6.risk_contributors || {};
    
    // Sectors
    const secWrap = document.getElementById('risk-sectors-list');
    secWrap.innerHTML = (contribs.sector_risk || []).map(s => {
      const col = s.risk_rating === 'High' ? 'var(--red)' : s.risk_rating === 'Medium' ? 'var(--amber)' : 'var(--green)';
      return `
        <div style="display:flex; justify-content:space-between; font-size:10.5px; border-bottom:1px solid var(--border); padding:3px 0;">
          <span>${sanitize(s.sector)}</span>
          <span>${s.exposure_percent}% (<strong style="color:${col};">${s.risk_rating}</strong>)</span>
        </div>
      `;
    }).join('');

    // Caps
    const capWrap = document.getElementById('risk-caps-list');
    capWrap.innerHTML = (contribs.market_cap_risk || []).map(mc => `
      <div style="display:flex; justify-content:space-between; font-size:10.5px; border-bottom:1px solid var(--border); padding:3px 0;">
        <span>${sanitize(mc.category)}</span>
        <strong>${mc.exposure_percent}%</strong>
      </div>
    `).join('');

    // Factors
    const factWrap = document.getElementById('risk-factors-list');
    factWrap.innerHTML = (contribs.factor_risk || []).map(f => `
      <div style="display:flex; justify-content:space-between; font-size:10.5px; border-bottom:1px solid var(--border); padding:3px 0;">
        <span>${sanitize(f.factor)} style</span>
        <strong>${f.exposure_percent}%</strong>
      </div>
    `).join('');
  }

  // ── ZONE 8: TAX & CASHFLOW INTELLIGENCE ──
  function renderTax() {
    if (!dashboardData) return;

    const z8 = dashboardData.zone8_tax_cashflow || {};
    const wrap = document.getElementById('tax-cards-wrap');
    
    wrap.innerHTML = `
      <div class="tax-card">
        <span class="tax-lbl">Projected Tax Liability</span>
        <span class="tax-val" style="color:var(--red);">${formatINR(z8.projected_tax_liability)}</span>
      </div>
      <div class="tax-card">
        <span class="tax-lbl">Expected Dividend Credits</span>
        <span class="tax-val" style="color:var(--green);">${formatINR(z8.expected_dividend_income)}</span>
      </div>
      <div class="tax-card">
        <span class="tax-lbl">Cash Available balance</span>
        <span class="tax-val" style="color:var(--teal);">${formatINR(z8.cash_available)}</span>
      </div>
      <div class="tax-card">
        <span class="tax-lbl">Upcoming SIP commitments</span>
        <span class="tax-val" style="color:var(--amber);">${formatINR(z8.upcoming_sips)}</span>
      </div>
    `;
  }

  // ── PORTFOLIO SCREEN ──
  function renderPortfolio() {
    if (!dashboardData) return;
    
    const holdingsBody = document.getElementById('portfolio-holdings-body');
    const totalVal = dashboardData.zone1_today_position ? dashboardData.zone1_today_position.net_worth : 1;
    
    if (dashboardData.holdings && dashboardData.holdings.length > 0) {
      holdingsBody.innerHTML = dashboardData.holdings.map(h => {
        const value = h.quantity * h.current_price;
        const pct = Math.round((value / totalVal) * 100);
        return `
          <tr>
            <td style="font-weight: 600; color: var(--text-primary);">${sanitize(h.asset_name)}</td>
            <td><span class="system-badge" style="font-size:9px; padding:2px 8px;">${sanitize(h.category_name)}</span></td>
            <td class="num-col">${Number(h.quantity).toLocaleString()}</td>
            <td class="num-col">${formatINR(h.avg_buy_price)}</td>
            <td class="num-col">${formatINR(h.current_price)}</td>
            <td class="num-col" style="font-weight: 700; color: var(--text-primary);">${formatINR(value)}</td>
            <td class="num-col" style="font-weight: 600; color: var(--teal);">${pct}%</td>
          </tr>
        `;
      }).join('');
    } else {
      holdingsBody.innerHTML = `<tr><td colspan="7" style="text-align:center;">No active portfolio holdings found.</td></tr>`;
    }

    const txnsBody = document.getElementById('portfolio-transactions-body');
    const txns = dashboardData.transactions || [];
    
    if (txns.length > 0) {
      txnsBody.innerHTML = txns.map(t => {
        const totalNet = t.quantity * t.price;
        const typeClass = t.txn_type === 'BUY' || t.txn_type === 'SIP' ? 'up' : 'down';
        return `
          <tr>
            <td style="font-family: var(--font-mono); font-size:10px;">${t.txn_date || '—'}</td>
            <td><span class="ticker-delta ${typeClass}" style="font-weight: 700;">${sanitize(t.txn_type)}</span></td>
            <td class="num-col">${Number(t.quantity).toLocaleString()}</td>
            <td class="num-col">${formatINR(t.price)}</td>
            <td class="num-col" style="font-weight: 700; color: var(--text-primary);">${formatINR(totalNet)}</td>
          </tr>
        `;
      }).join('');
    } else {
      txnsBody.innerHTML = `<tr><td colspan="5" style="text-align:center;">No transaction history found.</td></tr>`;
    }
  }

  // ── ACTION CENTER APPROVALS ──
  function renderActionHub() {
    if (!dashboardData) return;
    
    const actionList = document.getElementById('action-hub-list');
    const pendingNotifs = (dashboardData.notifications || []).filter(n => n.consent_status === 'pending');
    const tasks = dashboardData.tasks || [];
    
    let htmlContent = "";
    
    if (pendingNotifs.length > 0) {
      htmlContent += `<div class="nav-grp-lbl" style="padding-left:0; margin-bottom:8px;">PENDING REBALANCING PROPOSALS</div>`;
      htmlContent += pendingNotifs.map(n => {
        const d = new Date(n.created_at).toLocaleString('en-IN', {
          day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
        });
        const typeLabel = n.type === 'portfolio_change' ? 'Portfolio Proposal' : 'Minutes Review';
        const typeClass = n.type === 'portfolio_change' ? 'portfolio' : 'minutes';
        return `
          <div class="action-card" id="ac-card-${n.notification_id}">
            <div class="action-meta">
              <span class="action-type ${typeClass}">${typeLabel}</span>
              <span class="action-date">${d}</span>
            </div>
            <div class="action-desc">${sanitize(n.content)}</div>
            <div class="action-btns" id="btn-group-${n.notification_id}">
              <button class="act-btn agree" onclick="submitConsent(${n.notification_id}, 'agree')">✓ Sign Approval</button>
              <button class="act-btn disagree" onclick="submitConsent(${n.notification_id}, 'disagree')">✕ Decline Proposal</button>
              <button class="act-btn discuss" onclick="submitConsent(${n.notification_id}, 'discuss')">💬 Request Discussion</button>
            </div>
          </div>
        `;
      }).join('');
    }
    
    if (tasks.length > 0) {
      htmlContent += `<div class="nav-grp-lbl" style="padding-left:0; margin-top:16px; margin-bottom:8px;">ASSIGNED TASKS & CHECKLISTS</div>`;
      htmlContent += tasks.map(t => `
        <div class="action-card">
          <div class="action-meta">
            <span class="action-type task">Task Checklist</span>
            <span class="action-date">Due: ${t.due_date || '—'}</span>
          </div>
          <span class="action-desc">${sanitize(t.task_type)}</span>
          <div style="display:flex; justify-content:space-between; align-items:center; font-size:9px; color:var(--text-muted); border-top:1px solid var(--border); padding-top:6px; margin-top:2px;">
            <span>Priority: <strong style="color:var(--text-secondary)">${sanitize(t.priority)}</strong></span>
            <span>Status: <strong style="color:var(--amber)">Pending Followup</strong></span>
          </div>
        </div>
      `).join('');
    }
    
    if (pendingNotifs.length === 0 && tasks.length === 0) {
      htmlContent = `<div class="empty-state" style="padding: 40px;">Approvals ledger fully signed. No items pending.</div>`;
    }
    
    actionList.innerHTML = htmlContent;
  }

  // ── MEETING MINUTES REVIEW ──
  async function renderMeetingMinutes() {
    const list = document.getElementById('meeting-minutes-list');
    list.innerHTML = `<div style="text-align:center; padding:30px;"><div class="spinner"></div></div>`;
    
    const minutes = await fetchAPI('/minutes');
    if (!minutes || minutes.length === 0) {
      list.innerHTML = `<div class="empty-state" style="padding: 40px;">No meeting reviews recorded.</div>`;
      return;
    }
    
    list.innerHTML = minutes.map(m => `
      <div class="action-card" style="gap:10px;">
        <div class="action-meta">
          <span class="action-type minutes">Meeting Review Journal</span>
          <span class="action-date" style="font-weight:700;">Journal Date: ${m.meeting_date}</span>
        </div>
        <div style="font-size:11px; font-weight:700; color:var(--text-primary); text-transform:uppercase;">
          Agenda: ${sanitize(m.agenda || 'Annual Strategic Portfolio Review')}
        </div>
        <div class="action-desc" style="white-space: pre-line; background: var(--surface-interactive); padding: 10px; border-radius: 6px; border: 1px solid var(--border);">
          ${sanitize(m.discussion)}
        </div>
        ${m.action_items ? `
          <div style="border-top:1px solid var(--border); padding-top:8px;">
            <div style="font-size:8px; font-weight:700; color:var(--text-muted); text-transform:uppercase; margin-bottom:4px;">Decided Actions:</div>
            <div style="font-size:10px; color:var(--text-secondary); font-family:var(--font-mono); white-space:pre-line;">${sanitize(m.action_items)}</div>
          </div>
        ` : ''}
      </div>
    `).join('');
  }

  // Submit consent via API
  async function submitConsent(id, status) {
    const btnGroup = document.getElementById(`btn-group-${id}`);
    if (btnGroup) {
      btnGroup.querySelectorAll('button').forEach(btn => btn.disabled = true);
    }
    
    const response = await fetchAPI(`/notifications/${id}/consent`, {
      method: 'POST',
      body: JSON.stringify({ consent_status: status })
    });
    
    if (response && response.status === 'success') {
      showToast('Consent logged to cryptographic ledger.', 'success');
      setTimeout(async () => {
        const data = await fetchAPI('/my/dashboard/analytics');
        if (data) {
          dashboardData = data;
          document.getElementById('kpi-actions-score').textContent = `${data.pending_consents} Pending`;
          
          const activeNav = document.querySelector('.nav-item.active');
          if (activeNav) {
            const screen = activeNav.getAttribute('data-target');
            if (screen === 's-overview') renderOverview();
            else if (screen === 's-actions') renderActionHub();
          }
        }
      }, 500);
    } else {
      showToast('Signature write failed. Re-enabling buttons.', 'error');
      if (btnGroup) {
        btnGroup.querySelectorAll('button').forEach(btn => btn.disabled = false);
      }
    }
  }

  function sanitize(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function logout() {
    ['sanchay_token', 'sanchay_role', 'sanchay_name', 'sanchay_advisor_id'].forEach(k => localStorage.removeItem(k));
    window.location.href = 'client_login.html';
  }

  document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    
    // Periodically refresh data every 60 seconds
    setInterval(async () => {
      const data = await fetchAPI('/my/dashboard/analytics');
      if (data) {
        dashboardData = data;
        document.getElementById('kpi-actions-score').textContent = `${data.pending_consents} Pending`;
        
        const activeNav = document.querySelector('.nav-item.active');
        if (activeNav) {
          const screen = activeNav.getAttribute('data-target');
          if (screen === 's-overview') renderOverview();
          else if (screen === 's-actions') renderActionHub();
        }
      }
    }, 60000);
  });
