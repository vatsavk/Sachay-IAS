/**
 * SANCHAY IAS — Data Canvas Engine
 * Enables drag-and-drop dashboard layouts, custom grid snapping, 
 * widget pinning, and dynamic SVG thread lines linking charts to metrics.
 */
'use strict';

class SanchayDataCanvas {
  constructor() {
    this.active = false;
    this.widgets = [];
    this.threads = [];
    this.storageKey = 'sanchay_canvas_positions';

    this.initSVG();
    this.bindWindowEvents();
  }

  initSVG() {
    // Check if SVG threads container exists
    this.svgContainer = document.getElementById('sanchay-canvas-svg');
    if (!this.svgContainer) {
      this.svgContainer = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      this.svgContainer.id = 'sanchay-canvas-svg';
      this.svgContainer.setAttribute('class', 'sanchay-canvas-threads');
      this.svgContainer.style.position = 'absolute';
      this.svgContainer.style.top = '0';
      this.svgContainer.style.left = '0';
      this.svgContainer.style.width = '100%';
      this.svgContainer.style.height = '100%';
      this.svgContainer.style.pointerEvents = 'none';
      this.svgContainer.style.zIndex = '1';
    }
  }

  toggleMode(containerSelector) {
    const container = document.querySelector(containerSelector);
    if (!container) return;

    this.active = !this.active;
    
    if (this.active) {
      container.classList.add('sanchay-canvas-grid');
      // Put SVG threads container inside the main content container
      container.appendChild(this.svgContainer);
      this.enableCanvas(container);
      if (typeof window.toast === 'function') window.toast('Data Canvas mode activated', 'success');
    } else {
      container.classList.remove('sanchay-canvas-grid');
      if (container.contains(this.svgContainer)) {
        container.removeChild(this.svgContainer);
      }
      this.disableCanvas(container);
      if (typeof window.toast === 'function') window.toast('Standard Dashboard layout restored', 'info');
    }
  }

  enableCanvas(container) {
    // Collect child cards to make them widgets
    const cards = Array.from(container.children).filter(el => 
      el !== this.svgContainer && 
      (el.classList.contains('card') || el.classList.contains('stats-grid') || el.classList.contains('stats-container'))
    );

    const savedPositions = this.loadPositions();

    cards.forEach((card, index) => {
      // Upgrade card structure to a canvas widget if not already done
      if (!card.classList.contains('canvas-widget')) {
        card.classList.add('canvas-widget');
        
        // Add a header if it doesn't exist
        let hdr = card.querySelector('.card-header') || card.querySelector('.card-hdr');
        if (!hdr) {
          hdr = document.createElement('div');
          hdr.className = 'canvas-widget-hdr';
          hdr.innerHTML = `
            <div class="canvas-widget-title">Widget #${index + 1}</div>
            <div class="canvas-pin-btn" title="Pin Widget">📌</div>
          `;
          card.insertBefore(hdr, card.firstChild);
        } else {
          hdr.classList.add('canvas-widget-hdr');
          if (!hdr.querySelector('.canvas-pin-btn')) {
            const pinBtn = document.createElement('div');
            pinBtn.className = 'canvas-pin-btn';
            pinBtn.title = 'Pin Widget';
            pinBtn.innerHTML = '📌';
            hdr.appendChild(pinBtn);
          }
        }

        // Add body wrap around siblings
        let body = card.querySelector('.card-body');
        if (!body) {
          body = document.createElement('div');
          body.className = 'canvas-widget-body';
          // Move all elements after header into body
          while (card.children.length > 1) {
            body.appendChild(card.children[1]);
          }
          card.appendChild(body);
        } else {
          body.classList.add('canvas-widget-body');
        }

        // Setup Drag events
        this.setupDrag(card, container);
      }

      // Apply saved position or defaults
      const widgetId = card.id || `widget-${index}`;
      card.setAttribute('data-widget-id', widgetId);
      
      if (savedPositions[widgetId]) {
        card.style.gridColumn = savedPositions[widgetId].gridColumn;
        card.style.gridRow = savedPositions[widgetId].gridRow;
      } else {
        // Default standard 12-column spans
        if (card.classList.contains('stats-grid') || card.classList.contains('stats-container')) {
          card.style.gridColumn = 'span 12';
        } else {
          card.style.gridColumn = 'span 6';
        }
      }
    });

    this.widgets = cards;
    this.drawThreads();
  }

  disableCanvas(container) {
    const cards = Array.from(container.children).filter(el => el.classList.contains('canvas-widget'));
    cards.forEach(card => {
      card.classList.remove('canvas-widget');
      card.style.gridColumn = '';
      card.style.gridRow = '';
    });
    this.clearThreads();
  }

  setupDrag(widget, container) {
    const hdr = widget.querySelector('.canvas-widget-hdr');
    if (!hdr) return;

    let startX = 0, startY = 0;
    
    const dragStart = (e) => {
      if (e.target.classList.contains('canvas-pin-btn')) {
        // Toggle pin state
        widget.classList.toggle('pinned');
        this.savePositions();
        return;
      }
      
      if (widget.classList.contains('pinned')) return;

      e = e || window.event;
      startX = e.clientX || e.touches[0].clientX;
      startY = e.clientY || e.touches[0].clientY;

      document.onmouseup = dragEnd;
      document.onmousemove = dragMove;
      
      document.ontouchend = dragEnd;
      document.ontouchmove = dragMove;
    };

    const dragMove = (e) => {
      e = e || window.event;
      const clientX = e.clientX || (e.touches && e.touches[0].clientX);
      const clientY = e.clientY || (e.touches && e.touches[0].clientY);
      
      const dx = clientX - startX;
      const dy = clientY - startY;

      // Visual feedback — transform offset
      widget.style.transform = `translate(${dx}px, ${dy}px)`;
      widget.style.zIndex = '1000';
    };

    const dragEnd = (e) => {
      document.onmouseup = null;
      document.onmousemove = null;
      document.ontouchend = null;
      document.ontouchmove = null;

      widget.style.transform = '';
      widget.style.zIndex = '';

      e = e || window.event;
      const clientX = e.clientX || (e.changedTouches && e.changedTouches[0].clientX);
      const clientY = e.clientY || (e.changedTouches && e.changedTouches[0].clientY);

      // Simple grid placement calculation relative to target container
      const rect = container.getBoundingClientRect();
      const relativeX = clientX - rect.left;
      
      // Snapping to columns
      const colWidth = rect.width / 12;
      let targetCol = Math.floor(relativeX / colWidth) + 1;
      targetCol = Math.max(1, Math.min(12, targetCol));

      // Update widget styling
      const colSpanStr = widget.style.gridColumn.split('span')[1] || ' 6';
      const colSpan = parseInt(colSpanStr.trim());
      
      widget.style.gridColumn = `${targetCol} / span ${colSpan}`;
      
      this.savePositions();
      this.drawThreads();
    };

    hdr.addEventListener('mousedown', dragStart);
    hdr.addEventListener('touchstart', dragStart);
  }

  savePositions() {
    const positions = {};
    this.widgets.forEach(w => {
      const widgetId = w.getAttribute('data-widget-id');
      positions[widgetId] = {
        gridColumn: w.style.gridColumn,
        gridRow: w.style.gridRow,
        pinned: w.classList.contains('pinned')
      };
    });
    localStorage.setItem(this.storageKey, JSON.stringify(positions));
  }

  loadPositions() {
    try {
      return JSON.parse(localStorage.getItem(this.storageKey)) || {};
    } catch {
      return {};
    }
  }

  addThread(sourceSelector, targetSelector) {
    this.threads.push({ source: sourceSelector, target: targetSelector });
    this.drawThreads();
  }

  clearThreads() {
    if (this.svgContainer) {
      this.svgContainer.innerHTML = '';
    }
  }

  drawThreads() {
    if (!this.active) return;
    this.clearThreads();

    this.threads.forEach(t => {
      const src = document.querySelector(t.source);
      const dest = document.querySelector(t.target);
      if (!src || !dest) return;

      const srcRect = src.getBoundingClientRect();
      const destRect = dest.getBoundingClientRect();
      const parentRect = this.svgContainer.getBoundingClientRect();

      // Coordinates relative to SVG canvas
      const x1 = srcRect.left + srcRect.width / 2 - parentRect.left;
      const y1 = srcRect.top + srcRect.height / 2 - parentRect.top;
      
      const x2 = destRect.left + destRect.width / 2 - parentRect.left;
      const y2 = destRect.top + destRect.height / 2 - parentRect.top;

      // Draw dynamic spline curve (cubic bezier path)
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      const cx1 = x1 + (x2 - x1) / 2;
      const cy1 = y1;
      const cx2 = x1 + (x2 - x1) / 2;
      const cy2 = y2;
      
      const d = `M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`;
      path.setAttribute('d', d);
      path.setAttribute('class', 'canvas-thread-line');
      
      this.svgContainer.appendChild(path);
    });
  }

  bindWindowEvents() {
    window.addEventListener('resize', () => {
      if (this.active) {
        this.drawThreads();
      }
    });
  }
}

// Auto init
document.addEventListener('DOMContentLoaded', () => {
  window.SanchayCanvas = new SanchayDataCanvas();
});
