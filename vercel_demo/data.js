// SANCHAY OS — SEED / FALLBACK DATA
// Used when API is offline. Refreshed from API once daily.
'use strict';

var GLOBAL_STATE = {
  state: {
    current_user: { name: 'Dr. Arvind Sharma', initials: 'AS', role: 'Lead Advisor' },
    selected_client: null,
  },
  get current_user() { return this.state.current_user; },
  get selected_client() { return this.state.selected_client; },
  set selected_client(val) { this.state.selected_client = val; }
};

var IAS_DATA = {
  advisor: 'Dr. Arvind Sharma',
  initials: 'AS',
  role: 'Lead Advisor',
  totalAUM: '₹145.2 Cr',
  totalClients: 8,
  atRisk: 2,

  decisions: [
    { id: 'd1', type: 'RISK_ALERT', urgency: 'high', title: 'Sector Allocation Drift', desc: 'Rahul Desai has 35% exposure to Financials vs 25% target.', entity: 'Portfolio: Rahul Core', action: 'Generate Rebalance Proposal' },
    { id: 'd2', type: 'ENGAGEMENT_ALERT', urgency: 'high', title: 'Client Inactive — 45 Days', desc: 'No logged communication with Gupta Family Trust.', entity: 'Client: Gupta Family Trust', action: 'Send WhatsApp Update' },
    { id: 'd3', type: 'EVENT_IMPACT', urgency: 'medium', title: 'RBI Rate Pause Impact', desc: 'MPC paused rates. 12 debt portfolios require duration review.', entity: 'Macro Event', action: 'Analyze Impact' }
  ],

  clients: [
    {
      id: 'c1', name: 'Rahul Desai', initials: 'RD',
      aum: '₹4.2 Cr', aum_raw: 42000000,
      risk: 'Aggressive', health: 88, engagement: 45,
      lastContact: '2024-04-20', nextAction: 'Q3 Review',
      status: 'Active', category: 'HNI',
      email: 'rahul.desai@email.com', phone: '+91 98765 43210',
      since: 'Jan 2019',
      portfolio: {
        equity: 67, debt: 20, gold: 8, cash: 5,
        holdings: [
          { name: 'HDFC Bank', type: 'Equity · Large Cap', value: '₹52.8L', alloc: '12.6%', return: '+14.2%', units: 3142, avg_price: 1680, isin: 'HDFCBANK' },
          { name: 'Reliance Ind.', type: 'Equity · Large Cap', value: '₹41.2L', alloc: '9.8%', return: '+11.5%', units: 1681, avg_price: 2450, isin: 'RELIANCE' },
          { name: 'Nippon Liquid', type: 'Debt · Liquid Fund', value: '₹50.4L', alloc: '12.0%', return: '+6.8%', units: 1768, avg_price: 2850, isin: 'NIPPON_LIQUID' }
        ]
      }
    },
    {
      id: 'c2', name: 'Gupta Family Trust', initials: 'GF',
      aum: '₹45.8 Cr', aum_raw: 458000000,
      risk: 'Moderate', health: 72, engagement: 20,
      lastContact: '2024-03-01', nextAction: 'Quarterly Review',
      status: 'Active', category: 'UHNI',
      email: 'gupta.trust@email.com', phone: '+91 98100 11223',
      since: 'Mar 2016',
      portfolio: { equity: 45, debt: 45, gold: 5, cash: 5, holdings: [] }
    },
    {
      id: 'c3', name: 'Meera Iyer', initials: 'MI',
      aum: '₹1.8 Cr', aum_raw: 18000000,
      risk: 'Moderate', health: 80, engagement: 78,
      lastContact: '2024-05-01', nextAction: 'SIP Review',
      status: 'Active', category: 'Affluent',
      email: 'meera.iyer@email.com', phone: '+91 90000 55566',
      since: 'Jun 2021',
      portfolio: { equity: 50, debt: 35, gold: 10, cash: 5, holdings: [] }
    },
    {
      id: 'c4', name: 'Vikram Singh', initials: 'VS',
      aum: '₹8.5 Cr', aum_raw: 85000000,
      risk: 'Aggressive', health: 91, engagement: 82,
      lastContact: '2024-05-05', nextAction: 'Portfolio Expansion',
      status: 'Active', category: 'HNI',
      email: 'vikram.singh@email.com', phone: '+91 99887 76655',
      since: 'Sep 2018',
      portfolio: { equity: 75, debt: 15, gold: 7, cash: 3, holdings: [] }
    },
    {
      id: 'c5', name: 'Anita Sharma', initials: 'AS',
      aum: '₹2.1 Cr', aum_raw: 21000000,
      risk: 'Conservative', health: 85, engagement: 60,
      lastContact: '2024-04-28', nextAction: 'Debt Review',
      status: 'Active', category: 'Affluent',
      email: 'anita.sharma@email.com', phone: '+91 98110 22334',
      since: 'Jan 2022',
      portfolio: { equity: 20, debt: 65, gold: 10, cash: 5, holdings: [] }
    },
    {
      id: 'c6', name: 'Sunil Varma', initials: 'SV',
      aum: '₹6.3 Cr', aum_raw: 63000000,
      risk: 'Moderate', health: 76, engagement: 55,
      lastContact: '2024-04-15', nextAction: 'KYC Renewal',
      status: 'Active', category: 'HNI',
      email: 'sunil.varma@email.com', phone: '+91 99001 33445',
      since: 'Nov 2017',
      portfolio: { equity: 50, debt: 30, gold: 12, cash: 8, holdings: [] }
    },
    {
      id: 'c7', name: 'Priya Mehta', initials: 'PM',
      aum: '₹3.2 Cr', aum_raw: 32000000,
      risk: 'Moderate', health: 83, engagement: 70,
      lastContact: '2024-05-03', nextAction: 'Goal Planning',
      status: 'Active', category: 'Affluent',
      email: 'priya.mehta@email.com', phone: '+91 98500 44556',
      since: 'Apr 2020',
      portfolio: { equity: 55, debt: 30, gold: 10, cash: 5, holdings: [] }
    },
    {
      id: 'c8', name: 'Rajesh Khanna', initials: 'RK',
      aum: '₹22.4 Cr', aum_raw: 224000000,
      risk: 'Aggressive', health: 94, engagement: 88,
      lastContact: '2024-05-07', nextAction: 'Expansion Review',
      status: 'Active', category: 'UHNI',
      email: 'rajesh.khanna@email.com', phone: '+91 98200 55667',
      since: 'May 2015',
      portfolio: { equity: 72, debt: 18, gold: 7, cash: 3, holdings: [] }
    }
  ],

  insights: [
    { id: 'i1', type: 'PORTFOLIO_IMBALANCE', severity: 'HIGH', title: 'Equity Concentration Risk', desc: '3 Portfolios have equity >65% vs target 55%. Rebalancing required.', clients: 3, action: 'Review & Rebalance' },
    { id: 'i2', type: 'GOAL_RISK', severity: 'HIGH', title: 'Goal Shortfall — 2 Clients', desc: 'Gupta Trust and Sunil Varma are underfunded relative to targets.', clients: 2, action: 'Review Goals' },
    { id: 'i3', type: 'ENGAGEMENT_DROP', severity: 'MEDIUM', title: 'Low Engagement Alert', desc: 'Gupta Family Trust engagement dropped to 20/100. Last contact 45+ days ago.', clients: 1, action: 'Schedule Meeting' },
    { id: 'i4', type: 'DRIFT_ALERT', severity: 'MEDIUM', title: 'Sector Drift — Financials', desc: 'Rahul Desai has 35% in Financials vs 25% benchmark. Trim recommended.', clients: 1, action: 'Generate Proposal' },
    { id: 'i5', type: 'NAV_UPDATE', severity: 'LOW', title: 'MF NAV Updated', desc: 'AMFI NAV refresh complete. 8 holdings revalued. AUM delta: +₹12.4L.', clients: 8, action: 'View Changes' }
  ],

  events: [
    { id: 'e1', date: 'May 10, 2026', type: 'MACRO', title: 'RBI MPC Rate Decision — Pause', impact: 'HIGH', affected: '12 Debt Portfolios', desc: 'Repo rate held at 6.5%. NAV bump expected in longer-duration debt funds. Review duration exposure.' },
    { id: 'e2', date: 'May 08, 2026', type: 'MARKET', title: 'NIFTY 50 Hits All-Time High', impact: 'MEDIUM', affected: '6 Equity-Heavy Portfolios', desc: 'NIFTY touched 24,400. Clients with >65% equity near concentration risk thresholds.' },
    { id: 'e3', date: 'May 05, 2026', type: 'REGULATORY', title: 'SEBI Circular: MF Categorisation Update', impact: 'MEDIUM', affected: 'All MF Holdings', desc: 'SEBI revised fund categorisation norms. 3 holdings may need reclassification.' },
    { id: 'e4', date: 'Apr 30, 2026', type: 'ECONOMIC', title: 'India GDP Growth: 7.2% Q4 FY26', impact: 'LOW', affected: 'All Clients', desc: 'Strong GDP print supports equity allocation thesis. No immediate action required.' },
    { id: 'e5', date: 'Apr 25, 2026', type: 'FX', title: 'USD/INR Weakens to 84.5', impact: 'MEDIUM', affected: '2 International Portfolios', desc: 'Rupee depreciation affects international fund valuations. Monitor hedging.' }
  ],

  tasks: [
    { id: 't1', title: 'Tax-Loss Harvesting — Gupta Family', client: 'Gupta Family Trust', due: '2026-05-12', priority: 'High', status: 'Pending', type: 'Action' },
    { id: 't2', title: 'KYC Renewal — Sunil Varma', client: 'Sunil Varma', due: '2026-05-15', priority: 'High', status: 'Pending', type: 'Compliance' },
    { id: 't3', title: 'Q1 Review — Meera Iyer', client: 'Meera Iyer', due: '2026-05-18', priority: 'Medium', status: 'Pending', type: 'Review' },
    { id: 't4', title: 'SIP Step-Up — Rahul Desai', client: 'Rahul Desai', due: '2026-05-20', priority: 'Medium', status: 'In Progress', type: 'Action' },
    { id: 't5', title: 'Risk Profile Update — Anita Sharma', client: 'Anita Sharma', due: '2026-05-25', priority: 'Low', status: 'Pending', type: 'Compliance' }
  ],

  goals: [
    { id: 'g1', clientId: 'c1', client: 'Rahul Desai', name: 'Retirement Corpus', targetAmount: '₹10 Cr', currentCorpus: '₹4.2 Cr', targetDate: '2035', sipRequired: '₹1.5L', sipCurrent: '₹1L', probability: 82, status: 'On Track' },
    { id: 'g2', clientId: 'c2', client: 'Gupta Family Trust', name: 'Succession Corpus', targetAmount: '₹100 Cr', currentCorpus: '₹45.8 Cr', targetDate: '2040', sipRequired: '₹8L', sipCurrent: '₹8L', probability: 65, status: 'At Risk' },
    { id: 'g3', clientId: 'c3', client: 'Meera Iyer', name: 'Child Education', targetAmount: '₹75L', currentCorpus: '₹22L', targetDate: '2032', sipRequired: '₹45K', sipCurrent: '₹40K', probability: 71, status: 'On Track' },
    { id: 'g4', clientId: 'c4', client: 'Vikram Singh', name: 'Business Expansion', targetAmount: '₹25 Cr', currentCorpus: '₹8.5 Cr', targetDate: '2030', sipRequired: '₹3L', sipCurrent: '₹3.5L', probability: 89, status: 'Ahead' },
    { id: 'g5', clientId: 'c5', client: 'Anita Sharma', name: 'Retirement', targetAmount: '₹5 Cr', currentCorpus: '₹2.1 Cr', targetDate: '2038', sipRequired: '₹35K', sipCurrent: '₹30K', probability: 74, status: 'On Track' },
    { id: 'g6', clientId: 'c6', client: 'Sunil Varma', name: 'Property Purchase', targetAmount: '₹3 Cr', currentCorpus: '₹1.8 Cr', targetDate: '2027', sipRequired: '₹2L', sipCurrent: '₹80K', probability: 48, status: 'At Risk' }
  ],

  transactions: [
    { id: 'tx1', clientId: 'c1', date: '2026-05-08', type: 'BUY', security: 'HDFC Bank', amount: '₹5,00,000', status: 'Confirmed' },
    { id: 'tx2', clientId: 'c1', date: '2026-04-15', type: 'SELL', security: 'Reliance Ind.', amount: '₹2,40,000', status: 'Confirmed' },
    { id: 'tx3', clientId: 'c4', date: '2026-05-05', type: 'SIP', security: 'Parag Parikh Flexi Cap', amount: '₹1,00,000', status: 'Confirmed' }
  ],

  revenue: [
    { client: 'Gupta Family Trust', aum: '₹45.8 Cr', trail: '₹24.9L/yr', tier: 'Platinum' },
    { client: 'Rajesh Khanna', aum: '₹22.4 Cr', trail: '₹12.2L/yr', tier: 'Platinum' },
    { client: 'Vikram Singh', aum: '₹8.5 Cr', trail: '₹4.6L/yr', tier: 'Gold' },
    { client: 'Sunil Varma', aum: '₹6.3 Cr', trail: '₹3.4L/yr', tier: 'Gold' },
    { client: 'Rahul Desai', aum: '₹4.2 Cr', trail: '₹2.3L/yr', tier: 'Silver' },
    { client: 'Priya Mehta', aum: '₹3.2 Cr', trail: '₹1.7L/yr', tier: 'Silver' },
    { client: 'Anita Sharma', aum: '₹2.1 Cr', trail: '₹1.1L/yr', tier: 'Silver' },
    { client: 'Meera Iyer', aum: '₹1.8 Cr', trail: '₹98K/yr', tier: 'Silver' }
  ],

  team: [
    { id: 'u1', name: 'Dr. Arvind Sharma', role: 'Lead Advisor', clients: 5, aum: '₹85.2 Cr', tasks: 3, initials: 'AS', status: 'Active' },
    { id: 'u2', name: 'Meera Kapoor', role: 'Associate Advisor', clients: 2, aum: '₹38.6 Cr', tasks: 2, initials: 'MK', status: 'Active' },
    { id: 'u3', name: 'Rajesh Kumar', role: 'Operations Manager', clients: 0, aum: '—', tasks: 5, initials: 'RK', status: 'Active' }
  ],

  compliance: [
    { id: 'comp1', title: 'Annual AML Audit', due: '2026-05-30', status: 'In Progress', owner: 'Rajesh Kumar', entity_type: 'AUDIT', client: 'All Clients' },
    { id: 'comp2', title: 'PMLA Disclosure Q1', due: '2026-05-25', status: 'Pending', owner: 'Dr. Arvind Sharma', entity_type: 'REGULATORY', client: 'All Clients' },
    { id: 'comp3', title: 'KYC Renewal — Sunil Varma', due: '2026-05-15', status: 'Pending', owner: 'Dr. Arvind Sharma', entity_type: 'KYC', client: 'Sunil Varma' },
    { id: 'comp4', title: 'IPV Verification — Priya Mehta', due: '2026-06-01', status: 'Completed', owner: 'Meera Kapoor', entity_type: 'IPV', client: 'Priya Mehta' },
    { id: 'comp5', title: 'Nominee Update — Rahul Desai', due: '2026-05-20', status: 'Pending', owner: 'Meera Kapoor', entity_type: 'PROFILE', client: 'Rahul Desai' }
  ],

  reports: [
    { type: 'Quarterly Performance Review', freq: 'Quarterly', last: '2026-04-01', client: 'All Clients', status: 'Ready' },
    { type: 'Capital Gains Statement', freq: 'Annual', last: '2026-04-15', client: 'All Clients', status: 'Ready' },
    { type: 'Portfolio Allocation Audit', freq: 'On-Demand', last: '2026-04-25', client: 'Rahul Desai', status: 'Ready' },
    { type: 'Risk Profile Summary', freq: 'Quarterly', last: '2026-03-31', client: 'Vikram Singh', status: 'Archived' },
    { type: 'SIP Performance Report', freq: 'Monthly', last: '2026-05-01', client: 'Meera Iyer', status: 'Ready' }
  ],

  reviews: [
    { client: 'Rahul Desai', date: '2026-04-12', rating: 'Excellent', notes: 'Discussed Q1 results and rebalancing strategy.' },
    { client: 'Gupta Family', date: '2026-03-15', rating: 'Good', notes: 'Strategy sync for family estate and succession planning.' },
    { client: 'Vikram Singh', date: '2026-04-28', rating: 'Excellent', notes: 'Business expansion corpus on track. Portfolio ahead of target.' }
  ],

  cas_files: [],
  raw_transactions: [],

  nav_data: [
    { asset_id: 'HDFCBANK', nav: 1680.40, date: '2026-05-10' },
    { asset_id: 'RELIANCE', nav: 2450.15, date: '2026-05-10' },
    { asset_id: 'INFY', nav: 1523.60, date: '2026-05-10' },
    { asset_id: 'TCS', nav: 3812.75, date: '2026-05-10' },
    { asset_id: 'NIPPON_LIQUID', nav: 2850.10, date: '2026-05-10' }
  ],

  analytics: {
    risk: { volatility: 14.5, maxDrawdown: -12.2, sharpeRatio: 1.8,
      heatmap: [[0.8,-0.2,1.5,-0.5],[1.2,0.4,-0.8,2.1],[-0.4,1.8,0.6,-1.2],[0.5,-0.3,1.1,0.9]]
    },
    overlap: {
      matrix: [[1.0,0.45,0.12,0.08],[0.45,1.0,0.15,0.05],[0.12,0.15,1.0,0.32],[0.08,0.05,0.32,1.0]],
      descriptions: ['HDFC Bank','Reliance Ind.','Nippon Liquid','SBI Small Cap']
    },
    sector: {
      current: [
        { name: 'Financials', value: 35, benchmark: 25 },
        { name: 'Energy', value: 20, benchmark: 15 },
        { name: 'IT', value: 15, benchmark: 20 },
        { name: 'FMCG', value: 10, benchmark: 12 },
        { name: 'Debt/Cash', value: 20, benchmark: 28 }
      ]
    },
    optimization: {
      score: 84,
      currentAlloc: [67, 20, 8, 5],
      optimizedAlloc: [55, 30, 10, 5],
      expectedReturnBoost: '+1.4% p.a.',
      riskReduction: '-2.1% Vol'
    },
    recommendations: [
      { id: 'rec1', type: 'REBALANCE', title: 'Trim Financials', desc: 'Financials exposure is 10% above benchmark. Trim HDFC Bank by 4%.', impact: 'HIGH' },
      { id: 'rec2', type: 'OPTIMIZE', title: 'Increase Debt', desc: 'Increase Debt allocation to 30% for better risk-adjusted returns.', impact: 'MEDIUM' },
      { id: 'rec3', type: 'OVERLAP', title: 'Exit Duplicate Holding', desc: 'Nippon Liquid and Cash have 45% overlap in underlying instruments.', impact: 'LOW' }
    ]
  }
};

window.GLOBAL_STATE = GLOBAL_STATE;
window.IAS_DATA = IAS_DATA;
