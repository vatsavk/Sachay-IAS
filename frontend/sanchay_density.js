/**
 * SANCHAY IAS — Adaptive Density Engine
 * Tracks user mouse clicks, hotkey usage, and overall interaction speed
 * to adjust the design system layout density dynamically.
 */
'use strict';

class SanchayDensityEngine {
  constructor() {
    this.actionTimes = [];
    this.windowMs = 30000; // 30-second sliding window
    this.currentDensity = 'default';
    this.overrideActive = false; // True if user set manually in HUD
    
    // APM thresholds
    this.thresholdCompact = 45; // 45 actions/min
    this.thresholdRelaxed = 10; // Under 10 actions/min

    this.bindEvents();
    this.startAdaptiveTimer();
  }

  bindEvents() {
    // Record click interactions
    window.addEventListener('click', (e) => {
      // Ignore background clicks
      if (e.target === document.body || e.target.classList.contains('hud-backdrop')) return;
      this.recordAction();
    });

    // Record keydowns
    window.addEventListener('keydown', () => {
      this.recordAction();
    });

    // Listen for manual density changes (to stop auto-adaptation)
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'data-density') {
          const newDensity = document.body.getAttribute('data-density');
          // If the change didn't come from our auto engine, mark overrideActive = true
          if (newDensity && newDensity !== this.currentDensity) {
            this.overrideActive = true;
            this.currentDensity = newDensity;
          }
        }
      });
    });

    observer.observe(document.body, { attributes: true, attributeFilter: ['data-density'] });
  }

  recordAction() {
    const now = Date.now();
    this.actionTimes.push(now);
    this.cleanupOldActions(now);
  }

  cleanupOldActions(now) {
    const cutoff = now - this.windowMs;
    this.actionTimes = this.actionTimes.filter(t => t > cutoff);
  }

  calculateAPM() {
    const now = Date.now();
    this.cleanupOldActions(now);
    // Project count in sliding window to a per-minute rate
    const actionsCount = this.actionTimes.length;
    const apm = Math.round((actionsCount / this.windowMs) * 60000);
    return apm;
  }

  startAdaptiveTimer() {
    // Run evaluation every 10 seconds
    setInterval(() => {
      if (this.overrideActive) return; // Respect manual user preference

      const apm = this.calculateAPM();
      let targetDensity = 'default';

      if (apm >= this.thresholdCompact) {
        targetDensity = 'compact';
      } else if (apm < this.thresholdRelaxed && apm > 0) {
        targetDensity = 'relaxed';
      }

      if (targetDensity !== this.currentDensity) {
        this.currentDensity = targetDensity;
        document.body.setAttribute('data-density', targetDensity);
        
        if (typeof window.toast === 'function') {
          window.toast(`Layout adjusted to ${targetDensity} mode (APM: ${apm})`, 'info');
        } else {
          console.log(`[DENSITY] Layout adjusted to ${targetDensity} mode (APM: ${apm})`);
        }
      }
    }, 10000);
  }
}

// Auto init
document.addEventListener('DOMContentLoaded', () => {
  window.SanchayDensity = new SanchayDensityEngine();
});
