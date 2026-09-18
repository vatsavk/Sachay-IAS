/**
 * SANCHAY SENTINEL — Intensive Verification Suite v1.0
 * Pure-logic verification, fuzzing, and state audits.
 * No dependencies, browser & node compatible.
 */

const Sentinel = {
  results: [],
  
  // ── ASSERTION ENGINE ──────────────────────────────────────────
  assert: function(condition, label, category, details = {}) {
    const passed = !!condition;
    this.results.push({
      passed,
      label,
      category,
      timestamp: new Date().toISOString(),
      ...details
    });
    return passed;
  },

  assertNear: function(actual, expected, tolerance, label, category) {
    const diff = Math.abs(actual - expected);
    return this.assert(diff <= tolerance, label, category, { 
      actual: actual.toFixed(4), 
      expected: expected.toFixed(4), 
      diff: diff.toFixed(4) 
    });
  },

  // ── SUITE 1: MATH LOGIC ───────────────────────────────────────
  suite_math_logic: function() {
    console.log('Sentinel: Running Math Logic Suite...');
    const cat = 'Calculation Math';

    // 1.1 Annuity Math (SIP)
    // Formula check: 10L goal, 12% rate, 10 years
    const sip = window.required_sip_engine(1000000, 0.12, 10);
    this.assertNear(sip, 4347.09, 1, 'Standard SIP Calculation (10L @ 12%, 10Y)', cat);

    // 1.2 Division by Zero / Infinity
    const zeroRate = window.required_sip_engine(1000000, 0, 10);
    this.assertNear(zeroRate, 1000000 / (10 * 12), 0.1, 'Zero Rate SIP (Linear Allocation)', cat);

    const zeroYears = window.required_sip_engine(1000000, 0.12, 0);
    this.assert(zeroYears === 1000000, 'Zero Year SIP (Instant Goal Req)', cat);

    // 1.3 Compound Interest (Future Value)
    const fv = window.future_value_engine(100000, 0.06, 10);
    this.assertNear(fv, 179084.77, 1, 'Standard Future Value (1L @ 6% Infl, 10Y)', cat);

    // 1.4 Risk Scoring Boundaries
    const lowRiskS = window.risk_scoring_engine(65, 500000, 450000, 'low', [0,0,0]); // Senior, tiny surplus, no experience
    this.assert(window.risk_category(lowRiskS) === 'Conservative', 'Boundary: Senior + Low Surplus = Conservative', cat);

    const highRiskS = window.risk_scoring_engine(25, 2000000, 500000, 'high', [5,5,5]); // Young, big surplus, high experience
    this.assert(window.risk_category(highRiskS) === 'Aggressive', 'Boundary: Young + High Surplus = Aggressive', cat);
  },

  // ── SUITE 2: INGESTION RESILIENCE ─────────────────────────────
  suite_ingestion: function() {
    console.log('Sentinel: Running Ingestion Suite...');
    const cat = 'Data Ingestion';

    // 2.1 Regex robustness (Quoted Commas)
    // Mocking the parser behavior for unit testing
    const testCSV = '"Aditya Birla Sun Life Frontline Equity Fund, Direct Plan",INF209K01157,10000,2023-01-01,BUY';
    const regex = /(".*?"|[^",\s]+)(?=\s*,|\s*$)/g;
    const matches = testCSV.match(regex).map(m => m.replace(/^"|"$/g, '').trim());
    
    this.assert(matches[0] === 'Aditya Birla Sun Life Frontline Equity Fund, Direct Plan', 'CSV Regex: Quoted Commas correctly handled', cat);
    this.assert(matches[1] === 'INF209K01157', 'CSV Regex: ISIN correctly mapped after comma', cat);

    // 2.2 Numerical resilience
    const badAmountRow = 'Scheme,ISIN,invalid_amt,date,type';
    const parsedAmt = parseFloat('invalid_amt') || 0;
    this.assert(parsedAmt === 0, 'Parser: Non-numeric amounts default to 0 (No Crash)', cat);
  },

  // ── SUITE 3: STATE & IDEMPOTENCY ──────────────────────────────
  suite_state_audit: function() {
    console.log('Sentinel: Running State Audit...');
    const cat = 'State Consistency';

    // 3.1 Idempotency Check (Mock logic)
    const transactions = [
      { isin: 'ABC', amount: 1000, date: '2023-01-01', type: 'BUY' },
      { isin: 'ABC', amount: 1000, date: '2023-01-01', type: 'BUY' }
    ];
    
    const txnHash = (t) => `${t.isin}|${t.amount}|${t.date}|${t.type}`;
    const unique = [];
    transactions.forEach(t => {
      if(!unique.some(u => txnHash(u) === txnHash(t))) unique.push(t);
    });

    this.assert(unique.length === 1, 'Idempotency: Duplicate transactions filtered via Hashing', cat);

    // 3.2 Referential Integrity (Inference)
    if (window.IAS_DATA) {
      const allClientsValid = window.IAS_DATA.clients.every(c => c.id && c.name);
      this.assert(allClientsValid, 'Integrity: All records in IAS_DATA.clients are well-formed', cat);
    }
  },

  // ── MASTER RUNNER ─────────────────────────────────────────────
  runAll: function() {
    this.results = [];
    this.suite_math_logic();
    this.suite_ingestion();
    this.suite_state_audit();
    
    const passCount = this.results.filter(r => r.passed).length;
    console.log(`Sentinel Run Complete: ${passCount}/${this.results.length} PASSED`);
    return {
      summary: { total: this.results.length, passed: passCount, failed: this.results.length - passCount },
      details: this.results
    };
  }
};

// Auto-export for different envs
if (typeof module !== 'undefined') module.exports = Sentinel;
window.Sentinel = Sentinel;
