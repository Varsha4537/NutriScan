/**
 * dashboard.js — Protected dashboard logic
 * Checks session on load, handles scan, dietary profile, history.
 */

(function () {
  // ══ State ════════════════════════════════════════════════════════
  let currentUser   = null;
  let scanHistory   = [];
  const dietOptions = [
    { id: 'vegetarian',  label: 'Vegetarian',  emoji: '🥕' },
    { id: 'vegan',       label: 'Vegan',        emoji: '🌱' },
    { id: 'gluten-free', label: 'Gluten-Free',  emoji: '🌾' },
    { id: 'dairy-free',  label: 'Dairy-Free',   emoji: '🥛' },
    { id: 'nut-free',    label: 'Nut-Free',     emoji: '🥜' },
    { id: 'keto',        label: 'Keto',         emoji: '🥑' },
    { id: 'halal',       label: 'Halal',        emoji: '☪️'  },
    { id: 'kosher',      label: 'Kosher',       emoji: '✡️'  },
  ];

  // ══ API Service Layer (Clean Architecture) ═══════════════════════
  const ApiService = {
    getUser: async () => {
      const res = await fetch('/api/user/me');
      if (!res.ok) throw new Error('Unauthenticated');
      return res.json();
    },
    logout: async () => {
      return fetch('/api/auth/logout', { method: 'POST' });
    },
    scanImage: async (formData) => {
      const res = await fetch('/api/food/scan', { method: 'POST', body: formData });
      if (!res.ok) throw new Error('Scan failed');
      return res.json();
    },
    scanText: async (text) => {
      const res = await fetch('/api/food/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      if (!res.ok) throw new Error('Scan failed');
      return res.json();
    },
    saveDietaryProfile: async (profile) => {
      const res = await fetch('/api/user/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ profile })
      });
      if (!res.ok) throw new Error('Save failed');
      return res.json();
    },
    getScanHistory: async () => {
      const res = await fetch('/api/scans/history');
      if (!res.ok) throw new Error('Fetch failed');
      return res.json();
    }
  };

  // ══ Boot — verify session ═════════════════════════════════════════
  async function boot() {
    try {
      currentUser = await ApiService.getUser();
      renderUserInfo();
      renderDietGrid();
      renderActiveFilters();
      await loadScanHistory();
    } catch {
      window.location.href = '/login';
    }
  }

  // ══ User Info ════════════════════════════════════════════════════
  function renderUserInfo() {
    const name = currentUser.name || 'User';
    const avatar = name.charAt(0).toUpperCase();
    const el = document.getElementById('sidebar-avatar');
    const eln = document.getElementById('sidebar-name');
    const navG = document.getElementById('nav-greeting');
    if (el)  el.textContent  = avatar;
    if (eln) eln.textContent = name;
    if (navG) navG.textContent = `Hi, ${name.split(' ')[0]} 👋`;
  }

  // ══ Sidebar Navigation ════════════════════════════════════════════
  document.querySelectorAll('.sidebar-item[data-panel]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sidebar-item').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const panel = btn.dataset.panel;
      document.getElementById('panel-scan').style.display    = panel === 'scan'    ? '' : 'none';
      document.getElementById('panel-profile').style.display = panel === 'profile' ? '' : 'none';
      document.getElementById('panel-history').style.display = panel === 'history' ? '' : 'none';
    });
  });

  // "Set dietary profile" link inside scan panel
  const goProfileLink = document.getElementById('go-profile-link');
  if (goProfileLink) {
    goProfileLink.addEventListener('click', (e) => {
      e.preventDefault();
      document.querySelector('.sidebar-item[data-panel="profile"]')?.click();
    });
  }

  // ══ Logout ══════════════════════════════════════════════════════=
  document.getElementById('logout-btn')?.addEventListener('click', async () => {
    await ApiService.logout();
    window.location.href = '/';
  });

  // ══ File Upload & Scan ═══════════════════════════════════════════
  const fileInput  = document.getElementById('file-input');
  const uploadZone = document.getElementById('upload-zone');
  const previewImg = document.getElementById('preview-img');
  const scanBtn    = document.getElementById('scan-btn');
  const clearBtn   = document.getElementById('clear-btn');

  // Drag-and-drop visual feedback
  uploadZone?.addEventListener('dragover',  (e) => { e.preventDefault(); uploadZone.classList.add('drag-over'); });
  uploadZone?.addEventListener('dragleave', ()  => uploadZone.classList.remove('drag-over'));
  uploadZone?.addEventListener('drop',      (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length) {
      fileInput.files = e.dataTransfer.files;
      handleFileChosen();
    }
  });

  fileInput?.addEventListener('change', handleFileChosen);

  function handleFileChosen() {
    const file = fileInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      previewImg.style.display = 'block';
    };
    reader.readAsDataURL(file);
    scanBtn.style.display  = 'inline-flex';
    clearBtn.style.display = 'inline-flex';
    document.getElementById('results-section').classList.remove('show');
  }

  clearBtn?.addEventListener('click', () => {
    fileInput.value   = '';
    previewImg.src    = '';
    previewImg.style.display = 'none';
    scanBtn.style.display    = 'none';
    clearBtn.style.display   = 'none';
    document.getElementById('results-section').classList.remove('show');
  });

  scanBtn?.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) return;
    scanBtn.disabled = true;
    document.getElementById('scan-loading').style.display = 'block';

    const formData = new FormData();
    formData.append('image', file);

    try {
      const data = await ApiService.scanImage(formData);
      document.getElementById('scan-loading').style.display = 'none';
      scanBtn.disabled = false;
      
      if (data.partial) {
        renderPartialResults(data);
      } else {
        renderResults(data);
        addToHistory(data, file.name || 'Image Scan');
      }
    } catch (err) {
      document.getElementById('scan-loading').style.display = 'none';
      scanBtn.disabled = false;
      alert(err.message || 'Scan failed. Please try again.');
    }
  });

  // ══ Manual Text Scan ═════════════════════════════════════════════
  const manualInput = document.getElementById('manual-input');
  const manualBtn   = document.getElementById('manual-scan-btn');

  manualBtn?.addEventListener('click', async () => {
    const text = manualInput.value.trim();
    if (!text) return;

    manualBtn.disabled = true;
    document.getElementById('scan-loading').style.display = 'block';
    document.getElementById('results-section').classList.remove('show');

    try {
      const data = await ApiService.scanText(text);
      document.getElementById('scan-loading').style.display = 'none';
      manualBtn.disabled = false;
      
      if (data.partial) {
        renderPartialResults(data);
      } else {
        renderResults(data);
        manualInput.value = ''; // clear
        addToHistory(data, `Text: ${text.substring(0,20)}...`);
      }
    } catch (err) {
      document.getElementById('scan-loading').style.display = 'none';
      manualBtn.disabled = false;
      alert(err.message || 'Scan failed. Please try again.');
    }
  });

  // ══ Render Premium Results (Clean Code Architecture) ═══════════════
  
  function buildScoreCard(d, score, pct) {
    const name   = d.name || 'Unknown Product';
    const sub    = d.subtitle || 'General Analysis';
    const advise = d.consumption_advice || '';
    
    let adviceHTML = '';
    if (advise) {
      const advStyle = score >= 7 ? 'advice-good' : (score <= 4 ? '' : 'advice-warn');
      const advIcon  = score >= 7 ? '🟢' : (score <= 4 ? '🔴' : '🟡');
      adviceHTML = `<div class="advice-pill ${advStyle}">${advIcon} ${advise}</div>`;
    }

    return `
      <div class="score-card">
        <div class="category-pill">${sub}</div>
        <h2>${name}</h2>
        <div class="gauge-container" style="--score-pct: ${pct}%">
          <div class="gauge-inner">
            <span class="gauge-number">${score}</span>
            <span class="gauge-label">out of 10</span>
          </div>
        </div>
        ${adviceHTML}
      </div>
    `;
  }

  function buildNutritionGrid(breakdown) {
    if (!breakdown || breakdown.length === 0) return '';
    return `
      <div class="nutrition-grid">
        ${breakdown.map(n => {
          const isHigh = n.level.includes('High') || n.level.includes('❌');
          const color = isHigh ? 'var(--danger)' : (n.level.includes('Moderate') ? 'var(--warning)' : 'var(--accent)');
          return `
          <div class="nutri-card">
            <div class="nutri-header">
              <div class="nutri-header-left">
                <div class="nutri-icon">📊</div>
                <span class="nutri-name">${n.name}</span>
              </div>
              <span class="nutri-level" style="color:${color}">${n.level}</span>
            </div>
            <div class="nutri-bar-bg" style="background: rgba(255,255,255,0.05);">
              <div class="nutri-bar-fill" style="width: ${n.percentage || 50}%; background: ${color};"></div>
            </div>
            <div class="nutri-tip">
              <span style="opacity:0.6">💡</span> ${n.tip || ''}
            </div>
          </div>`;
        }).join('')}
      </div>
    `;
  }

  function buildSummaryAndFlags(summary, flags, regWarnings) {
    let result = '';
    if (summary) {
      result += `
        <div class="summary-card">
          <h3><i>✨</i> What this means for you</h3>
          <p>${summary}</p>
        </div>
      `;
    }
    if (regWarnings && regWarnings.length > 0) {
      result += `
        <div class="flags-card" style="background:var(--danger); background-image:linear-gradient(to bottom right, var(--danger), #8b0000);">
          <h3 style="color:#fff;"><i>⚖️</i> Official Regulatory Warnings</h3>
          <div class="flags-list">
            ${regWarnings.map(rw => `
              <div style="background:rgba(0,0,0,0.4); padding: 12px; border-radius: 8px; margin-bottom: 8px; flex: 1 1 100%;">
                <strong style="color:#fff; display:block; margin-bottom:4px;">${rw.standard} Warning: ${rw.chemical}</strong>
                <span style="color:#ccc; font-size:0.9rem;">${rw.warning}</span>
              </div>
            `).join('')}
          </div>
        </div>
      `;
    }
    if (flags && flags.length > 0) {
      result += `
        <div class="flags-card">
          <h3><i>⚠️</i> Ingredient Red Flags</h3>
          <div class="flags-list">
            ${flags.map(f => `<span class="flag-pill">${f}</span>`).join('')}
          </div>
        </div>
      `;
    }
    return result;
  }

  function buildAlternatives(alts) {
    if (!alts || alts.length === 0) return '';
    return `
      <div style="margin-bottom: 16px;">
        <h3 style="font-size:1.1rem;margin-bottom:16px;">Better Alternatives</h3>
        <div class="alt-grid">
          ${alts.map(a => `
            <div class="alt-card">
              <div class="alt-icon">${a.emoji || '📦'}</div>
              <div class="alt-name">${a.name}</div>
              <div class="alt-sub">${a.subtitle || ''}</div>
              <a href="${a.link || '#'}" target="_blank" class="alt-link">
                🛒 Search on Amazon
              </a>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  function renderResults(d) {
    const resSec = document.getElementById('results-section');
    resSec.classList.add('show');

    const score = typeof d.health_score === 'number' ? d.health_score : 5;
    const pct   = (score / 10) * 100;

    resSec.innerHTML = `
      <div class="glass-panel" style="background:var(--bg-secondary); border:transparent; padding:0;">
        ${buildScoreCard(d, score, pct)}
        <div style="padding: 0 24px 24px;">
          <h3 style="font-size:1.1rem;margin-bottom:16px;">Nutrition Breakdown</h3>
          ${buildNutritionGrid(d.nutrition_breakdown)}
          ${buildSummaryAndFlags(d.summary, d.red_flags, d.regulatory_warnings)}
          ${buildAlternatives(d.alternatives)}
        </div>
      </div>
    `;

    setTimeout(() => {
      document.querySelectorAll('.nutri-bar-fill').forEach(el => el.style.width = el.style.width);
    }, 100);

    resSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function renderPartialResults(d) {
    const resSec = document.getElementById('results-section');
    resSec.classList.add('show');

    resSec.innerHTML = `
      <div class="glass-panel" style="background:var(--bg-secondary); border: 2px dashed var(--warning); padding:24px;">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:16px;">
          <span style="font-size:2rem;">⚠️</span>
          <div>
            <h3 style="margin:0; color:var(--warning);">Partial Analysis</h3>
            <p style="margin:0; font-size:0.9rem; opacity:0.8;">${d.error || 'AI analysis failed, but we extracted text.'}</p>
          </div>
        </div>
        <div style="background:rgba(0,0,0,0.2); padding:16px; border-radius:8px;">
          <h4 style="margin-top:0; font-size:0.85rem; text-transform:uppercase; opacity:0.6;">Extracted Ingredients</h4>
          <p style="margin-bottom:0; font-family:monospace; font-size:0.9rem; line-height:1.5;">${d.raw_text}</p>
        </div>
        <p style="margin-top:16px; font-size:0.85rem; color:var(--text-muted);">
          Tip: Try a clearer photo or copy-pasting the text above into the manual entry box.
        </p>
      </div>
    `;
    resSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // ══ Scan History ═════════════════════════════════════════════════
  async function loadScanHistory() {
    try {
      const res = await ApiService.getScanHistory();
      scanHistory = res.history || [];
      renderHistory();
    } catch(e) {
      console.error("Failed to load history.");
    }
  }

  function renderHistory() {
    const el = document.getElementById('history-list');
    if (!el) return;
    if (!scanHistory.length) {
      el.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:32px 0;font-size:0.9rem;">No scans yet. They will save permanently here!</p>';
      return;
    }
    el.innerHTML = scanHistory.map((h, i) => {
      const d = new Date(h.timestamp);
      const hs = h.data.health_score || 5;
      return `
      <div style="display:flex;align-items:center;justify-content:space-between;padding:12px 0;border-bottom:1px solid var(--glass-border);">
        <div>
          <p style="font-weight:600;font-size:0.9rem;">${h.data.name || 'Unknown Product'}</p>
          <p style="font-size:0.78rem;color:var(--text-muted);">${h.filename} · ${d.toLocaleDateString()} ${d.toLocaleTimeString()}</p>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="grade-badge grade-${hs >= 7 ? 'A' : (hs <= 4 ? 'F' : 'C')}" style="font-size:0.75rem; padding: 4px 10px; height:auto; border-radius:12px;">
            ${hs >= 7 ? 'Good' : (hs <= 4 ? 'Poor' : 'Fair')}
          </span>
          <span style="font-size:0.85rem;font-weight:700;color:var(--accent);">${hs}<span style="font-size:0.7rem;color:var(--text-muted);font-weight:400;"> /10</span></span>
        </div>
      </div>
    `}).join('');
  }

  /**
   * Adds a new scan to the history list by refreshing from server.
   * Called after successful scan in both image and manual text flows.
   */
  async function addToHistory(data, filename) {
    if (data.partial) return; // Don't add partial results to permanent history
    await loadScanHistory();
  }

  // ══ Dietary Profile ══════════════════════════════════════════════
  function renderDietGrid() {
    const grid = document.getElementById('diet-grid');
    if (!grid) return;
    const saved = currentUser.dietary_profile || [];
    grid.innerHTML = dietOptions.map(opt => `
      <label class="diet-option ${saved.includes(opt.id) ? 'selected' : ''}" id="opt-${opt.id}">
        <input type="checkbox" value="${opt.id}" ${saved.includes(opt.id) ? 'checked' : ''} />
        <span class="diet-emoji">${opt.emoji}</span>
        <span class="diet-label">${opt.label}</span>
      </label>
    `).join('');

    grid.querySelectorAll('label.diet-option').forEach(lbl => {
      lbl.addEventListener('click', () => {
        const cb = lbl.querySelector('input');
        // Toggle happens naturally; sync class
        setTimeout(() => lbl.classList.toggle('selected', cb.checked), 0);
      });
    });
  }

  function renderActiveFilters() {
    const box  = document.getElementById('active-filters');
    if (!box) return;
    const saved = currentUser?.dietary_profile || [];
    if (!saved.length) {
      box.innerHTML = `<span style="color:var(--text-muted);font-size:0.85rem;">No filters set. <a href="#" id="go-profile-link">Set dietary profile →</a></span>`;
      document.getElementById('go-profile-link')?.addEventListener('click', (e) => {
        e.preventDefault();
        document.querySelector('.sidebar-item[data-panel="profile"]')?.click();
      });
      return;
    }
    box.innerHTML = saved.map(s => {
      const opt = dietOptions.find(o => o.id === s);
      return `<span class="ingredient-pill">${opt?.emoji || ''} ${opt?.label || s}</span>`;
    }).join('');
  }

  document.getElementById('save-profile-btn')?.addEventListener('click', async () => {
    const checked = [...document.querySelectorAll('#diet-grid input:checked')].map(cb => cb.value);
    const btn     = document.getElementById('save-profile-btn');
    const alertEl = document.getElementById('profile-alert');
    btn.disabled  = true;

    try {
      await ApiService.saveDietaryProfile(checked);
      currentUser.dietary_profile = checked;
      renderActiveFilters();
      alertEl.className = 'alert alert-success show';
      alertEl.textContent = '✅ Dietary profile saved!';
    } catch {
      alertEl.className = 'alert alert-error show';
      alertEl.textContent = 'Failed to save. Please try again.';
    }
    btn.disabled = false;
    setTimeout(() => alertEl.classList.remove('show'), 3000);
  });

  // ══ Start ════════════════════════════════════════════════════════
  boot();
})();
