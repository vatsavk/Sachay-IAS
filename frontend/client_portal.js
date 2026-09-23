async function loadClientPortal() {
  // If the user is an advisor previewing this, we'll pick the first client ID
  let url = '/my/dashboard/analytics';
  let holdingsUrl = '/my/portfolio';
  
  if (GLOBAL_STATE.current_user && GLOBAL_STATE.current_user.role !== 'client') {
    if (!IAS_DATA.clients || IAS_DATA.clients.length === 0) {
      document.getElementById('cp-net-worth').innerText = "No Clients";
      return;
    }
    const previewClientId = IAS_DATA.clients[0].id;
    url += `?client_id=${previewClientId}`;
    holdingsUrl += `?client_id=${previewClientId}`;
  }

  try {
    const analytics = await apiFetch(url);
    if (analytics) {
      document.getElementById('cp-net-worth').innerText = `$${analytics.current_value.toLocaleString()}`;
      document.getElementById('cp-returns').innerText = `${(analytics.prob_success * 100).toFixed(1)}%`;
      document.getElementById('cp-goals').innerText = analytics.goals.length;
      
      const goalsTbody = document.getElementById('cp-mygoals-tbody');
      if (analytics.goals.length > 0) {
        goalsTbody.innerHTML = analytics.goals.map(g => `
          <tr>
            <td>${g.goal_name}</td>
            <td>$${g.target_amount.toLocaleString()}</td>
            <td><span class="tag ${g.current_amount >= g.target_amount ? 'green' : 'blue'}">${g.current_amount >= g.target_amount ? 'Achieved' : 'On Track'}</span></td>
          </tr>
        `).join('');
      } else {
        goalsTbody.innerHTML = `<tr><td colspan="3" style="text-align:center;">No active goals</td></tr>`;
      }
    }
    
    const portfolioData = await apiFetch(holdingsUrl);
    const holdings = portfolioData ? portfolioData.portfolio : [];
    const holdingsTbody = document.getElementById('cp-holdings-tbody');
    if (holdings && holdings.length > 0) {
        holdingsTbody.innerHTML = holdings.map(h => `
          <tr>
            <td>${h.asset_name}</td>
            <td>${h.category_name}</td>
            <td>$${h.current_value.toLocaleString()}</td>
          </tr>
        `).join('');
    } else {
        holdingsTbody.innerHTML = `<tr><td colspan="3" style="text-align:center;">No holdings found</td></tr>`;
    }
  } catch (e) {
    console.error("Error loading client portal:", e);
    document.getElementById('cp-net-worth').innerText = "Error";
    document.getElementById('cp-holdings-tbody').innerHTML = `<tr><td colspan="3" style="color:red;text-align:center;">Failed to load data</td></tr>`;
  }
}
