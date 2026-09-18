// Direct test of render functions without browser
// Run with: node test_render.js

// Simulated DOM for testing
const DOM = {
  elements: {},
  getElementById: function(id) {
    if (!this.elements[id]) {
      this.elements[id] = { id, innerHTML: '', childNodes: [] };
    }
    return this.elements[id];
  },
  querySelector: function(selector) {
    // Handle selectors like "#table-id tbody"
    const parts = selector.split(' ');
    const id = parts[0].replace('#', '');
    const element = this.getElementById(id);
    if (parts[1] === 'tbody') {
      if (!element.tbody) {
        element.tbody = { innerHTML: '', parent: element };
      }
      return element.tbody;
    }
    return element;
  }
};

// Override document methods
global.document = DOM;

// Load data.js
const fs = require('fs');
const dataContent = fs.readFileSync('/e:/SANCHAY/Sanchay_IAS/data.js', 'utf8');
eval(dataContent);

console.log('=== INITIAL DATA STATE ===');
console.log('IAS_DATA.goals:', IAS_DATA.goals ? IAS_DATA.goals.length + ' goals' : 'UNDEFINED');
console.log('IAS_DATA.insights:', IAS_DATA.insights ? IAS_DATA.insights.length + ' insights' : 'UNDEFINED');
console.log('IAS_DATA.clients:', IAS_DATA.clients ? IAS_DATA.clients.length + ' clients' : 'UNDEFINED');

// Simulate the render functions
function renderInsightsScreen() {
  console.log('[renderInsightsScreen] Called');
  const body = document.getElementById('insights-body');
  console.log('[renderInsightsScreen] insights-body found?', !!body);
  if (!body) return;
  if (!IAS_DATA.insights || IAS_DATA.insights.length === 0) {
    body.innerHTML = '<div class="p-4 t3">No intelligence signals discovered.</div>';
    console.log('[renderInsightsScreen] Empty state rendered');
    return;
  }
  const html = IAS_DATA.insights.map(i => `<div>${i.title}</div>`).join('');
  body.innerHTML = html;
  console.log('[renderInsightsScreen] Rendered', IAS_DATA.insights.length, 'insights');
  console.log('[renderInsightsScreen] HTML length:', body.innerHTML.length);
}

function renderGoalsScreen() {
  console.log('[renderGoalsScreen] Called');
  const tbody = document.querySelector('#goals-table tbody');
  console.log('[renderGoalsScreen] goals-table tbody found?', !!tbody);
  if (!tbody) return;
  if (!IAS_DATA.goals || !Array.isArray(IAS_DATA.goals)) {
    tbody.innerHTML = '<tr><td>No goal data available</td></tr>';
    console.log('[renderGoalsScreen] No array - empty state');
    return;
  }
  if (IAS_DATA.goals.length === 0) {
    tbody.innerHTML = '<tr><td>No goals discovered</td></tr>';
    console.log('[renderGoalsScreen] Empty goals array');
    return;
  }
  const html = IAS_DATA.goals.map(g => `<tr><td>${g.client}</td><td>${g.name}</td></tr>`).join('');
  tbody.innerHTML = html;
  console.log('[renderGoalsScreen] Rendered', IAS_DATA.goals.length, 'goals');
  console.log('[renderGoalsScreen] HTML length:', tbody.innerHTML.length);
}

console.log('\n=== RUNNING RENDER FUNCTIONS ===');
renderInsightsScreen();
renderGoalsScreen();

console.log('\n=== FINAL DOM STATE ===');
const insightsBody = document.getElementById('insights-body');
const goalsTable = document.querySelector('#goals-table tbody');
console.log('insights-body innerHTML length:', insightsBody ? insightsBody.innerHTML.length : 'NOT FOUND');
console.log('goals-table tbody innerHTML length:', goalsTable ? goalsTable.innerHTML.length : 'NOT FOUND');

if (insightsBody && insightsBody.innerHTML.length > 0) {
  console.log('insights-body content:', insightsBody.innerHTML.substring(0, 100));
}
if (goalsTable && goalsTable.innerHTML.length > 0) {
  console.log('goals-table content:', goalsTable.innerHTML.substring(0, 100));
}
