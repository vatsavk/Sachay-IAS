/**
 * SANCHAY IAS — Command HUD Controller (Ctrl+K / ⌘K)
 */
'use strict';

class SanchayCommandHUD {
  constructor() {
    this.active = false;
    this.selectedIndex = 0;
    this.filteredItems = [];
    this.commands = [
      // Screen Navigation
      { title: 'Go to Dashboard', category: 'Navigation', icon: '📊', action: () => this.navigate('s-dashboard') },
      { title: 'Go to Clients Directory', category: 'Navigation', icon: '👥', action: () => this.navigate('s-clients') },
      { title: 'Go to Active Goals', category: 'Navigation', icon: '🎯', action: () => this.navigate('s-goals') },
      { title: 'Go to Compliance Hub', category: 'Navigation', icon: '🛡️', action: () => this.navigate('s-compliance') },
      { title: 'Go to AI Copilot Chat', category: 'Navigation', icon: '🤖', action: () => this.navigate('s-ai-copilot') },
      { title: 'Go to Portfolio Reviews', category: 'Navigation', icon: '📋', action: () => this.navigate('s-reviews') },
      { title: 'Go to Revenue & Analytics', category: 'Navigation', icon: '💰', action: () => this.navigate('s-revenue') },
      { title: 'Go to Team Management', category: 'Navigation', icon: '🏢', action: () => this.navigate('s-team') },
      
      // Theme Control
      { title: 'Set Theme: Obsidian Dark', category: 'System Theme', icon: '🌙', shortcut: '/theme dark', action: () => this.setTheme('dark') },
      { title: 'Set Theme: Obsidian Light', category: 'System Theme', icon: '☀️', shortcut: '/theme light', action: () => this.setTheme('light') },
      
      // Density Control
      { title: 'Set Spacing: Compact (Bloomberg)', category: 'Layout Spacing', icon: '🗜️', shortcut: '/density compact', action: () => this.setDensity('compact') },
      { title: 'Set Spacing: Default', category: 'Layout Spacing', icon: '📏', shortcut: '/density default', action: () => this.setDensity('default') },
      { title: 'Set Spacing: Relaxed (Clean)', category: 'Layout Spacing', icon: '🛋️', shortcut: '/density relaxed', action: () => this.setDensity('relaxed') },
      
      // Utilities
      { title: 'Sync Client Data Platforms', category: 'Quick Action', icon: '🔄', shortcut: '/sync', action: () => {
        if (typeof window.triggerSync === 'function') {
          window.triggerSync();
        } else {
          alert('Sync API not available on this screen');
        }
      }},
      { title: 'Onboard New Client', category: 'Quick Action', icon: '➕', shortcut: '/onboard', action: () => {
        if (typeof window.showModal === 'function') {
          window.showModal('modal-add-client');
        } else {
          const m = document.getElementById('modal-add-client');
          if (m) m.classList.add('active');
        }
      }}
    ];

    this.initDOM();
    this.bindEvents();
    this.applyPreferences();
  }

  initDOM() {
    // Check if HUD already exists
    if (document.getElementById('sanchay-hud')) return;

    // Create Backdrop
    this.backdrop = document.createElement('div');
    this.backdrop.id = 'sanchay-hud-backdrop';
    this.backdrop.className = 'hud-backdrop';
    document.body.appendChild(this.backdrop);

    // Create HUD Panel
    this.hud = document.createElement('div');
    this.hud.id = 'sanchay-hud';
    this.hud.className = 'sanchay-command-hud';
    this.hud.innerHTML = `
      <div class="hud-search-container">
        <span class="hud-search-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
        </span>
        <input type="text" id="hud-search-input" class="hud-input" placeholder="Type a command, page name, or client name..." autocomplete="off">
      </div>
      <div id="hud-results-pane" class="hud-results"></div>
      <div class="hud-footer">
        <div class="hud-tips">
          <span><kbd class="hud-shortcut">↑↓</kbd> Navigation</span>
          <span><kbd class="hud-shortcut">Enter</kbd> Confirm</span>
          <span><kbd class="hud-shortcut">Esc</kbd> Close</span>
        </div>
        <div>SANCHAY HUD v3.0</div>
      </div>
    `;
    document.body.appendChild(this.hud);

    this.searchInput = document.getElementById('hud-search-input');
    this.resultsPane = document.getElementById('hud-results-pane');
  }

  bindEvents() {
    // Listen for Ctrl+K or Cmd+K
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        this.toggle();
      }
      if (e.key === 'Escape' && this.active) {
        e.preventDefault();
        this.close();
      }
    });

    this.backdrop.addEventListener('click', () => this.close());

    // Input listening
    this.searchInput.addEventListener('input', () => this.renderResults());
    this.searchInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
  }

  toggle() {
    if (this.active) {
      this.close();
    } else {
      this.open();
    }
  }

  open() {
    this.active = true;
    this.hud.classList.add('active');
    this.backdrop.classList.add('active');
    this.searchInput.value = '';
    this.selectedIndex = 0;
    this.renderResults();
    setTimeout(() => this.searchInput.focus(), 50);
  }

  close() {
    this.active = false;
    this.hud.classList.remove('active');
    this.backdrop.classList.remove('active');
    this.searchInput.blur();
  }

  navigate(screenId) {
    if (typeof window.nav === 'function') {
      window.nav(screenId);
    } else {
      // client portal navigation
      const navItem = document.querySelector(`.nav-item[data-screen="${screenId}"]`);
      if (navItem) {
        navItem.click();
      } else {
        // Fallback for custom body attribute routing
        document.body.setAttribute('data-screen', screenId);
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        const activeScr = document.getElementById(screenId);
        if (activeScr) activeScr.classList.add('active');
      }
    }
    this.close();
  }

  setTheme(theme) {
    document.body.setAttribute('data-theme', theme);
    localStorage.setItem('sanchay_pref_theme', theme);
    this.close();
    if (typeof window.toast === 'function') {
      window.toast(`Theme changed to Obsidian ${theme.toUpperCase()}`, 'success');
    }
  }

  setDensity(density) {
    document.body.setAttribute('data-density', density);
    localStorage.setItem('sanchay_pref_density', density);
    this.close();
    if (typeof window.toast === 'function') {
      window.toast(`Density adjusted to ${density.toUpperCase()}`, 'success');
    }
  }

  applyPreferences() {
    const theme = localStorage.getItem('sanchay_pref_theme') || 'dark';
    const density = localStorage.getItem('sanchay_pref_density') || 'default';
    document.body.setAttribute('data-theme', theme);
    document.body.setAttribute('data-density', density);
  }

  getClientItems() {
    // Dynamically retrieve client names from the global clientsList if it exists
    const list = window.clientsList || [];
    return list.map(c => ({
      title: `Client Profile: ${c.name}`,
      category: 'Clients',
      icon: '👤',
      action: () => {
        if (typeof window.showClient360 === 'function') {
          window.showClient360(c.client_id || c.id);
        } else {
          // If not directly accessible, go to clients page
          this.navigate('s-clients');
        }
      }
    }));
  }

  getFilteredItems() {
    const query = this.searchInput.value.toLowerCase().trim();
    const allItems = [...this.commands, ...this.getClientItems()];

    if (!query) return allItems;

    return allItems.filter(item => 
      item.title.toLowerCase().includes(query) || 
      item.category.toLowerCase().includes(query) ||
      (item.shortcut && item.shortcut.toLowerCase().includes(query))
    );
  }

  renderResults() {
    this.filteredItems = this.getFilteredItems();
    
    if (this.selectedIndex >= this.filteredItems.length) {
      this.selectedIndex = Math.max(0, this.filteredItems.length - 1);
    }

    if (this.filteredItems.length === 0) {
      this.resultsPane.innerHTML = `<div style="padding: 16px; text-align: center; color: var(--text-muted);">No commands or clients matching "${this.searchInput.value}"</div>`;
      return;
    }

    // Group by category
    const groups = {};
    this.filteredItems.forEach((item, index) => {
      if (!groups[item.category]) groups[item.category] = [];
      groups[item.category].push({ item, index });
    });

    let html = '';
    for (const [category, items] of Object.entries(groups)) {
      html += `<div class="hud-group-label">${category}</div>`;
      items.forEach(({ item, index }) => {
        const isSelected = index === this.selectedIndex;
        const shortcutHtml = item.shortcut ? `<span class="hud-shortcut">${item.shortcut}</span>` : '';
        html += `
          <div class="hud-item ${isSelected ? 'selected' : ''}" data-index="${index}">
            <div class="hud-item-left">
              <span style="margin-right: 8px;">${item.icon}</span>
              <span>${item.title}</span>
            </div>
            ${shortcutHtml}
          </div>
        `;
      });
    }

    this.resultsPane.innerHTML = html;

    // Bind click events on items
    this.resultsPane.querySelectorAll('.hud-item').forEach(el => {
      el.addEventListener('click', () => {
        const idx = parseInt(el.getAttribute('data-index'));
        this.filteredItems[idx].action();
      });
    });
  }

  handleKeyDown(e) {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      this.selectedIndex = (this.selectedIndex + 1) % this.filteredItems.length;
      this.renderResults();
      this.scrollToSelected();
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      this.selectedIndex = (this.selectedIndex - 1 + this.filteredItems.length) % this.filteredItems.length;
      this.renderResults();
      this.scrollToSelected();
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (this.filteredItems[this.selectedIndex]) {
        this.filteredItems[this.selectedIndex].action();
      }
    }
  }

  scrollToSelected() {
    const selectedEl = this.resultsPane.querySelector('.hud-item.selected');
    if (selectedEl) {
      selectedEl.scrollIntoView({ block: 'nearest' });
    }
  }
}

// Auto init on page load
document.addEventListener('DOMContentLoaded', () => {
  window.SanchayHUD = new SanchayCommandHUD();
});
