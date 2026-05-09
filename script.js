/* ============================================================
   OISignalFlow Dashboard — script.js
   Real-time monitoring dashboard controller
   Reads config.json every 2 seconds — no external dependencies
   ============================================================ */

'use strict';

// ─────────────────────────────────────────────
// App State
// ─────────────────────────────────────────────
const APP = {
  data:            null,
  prevSignalCount: 0,
  prevScanNum:     0,
  soundOn:         true,
  audioCtx:        null,
  pollTimer:       null,
  POLL_MS:         2000,
  connected:       false,
  firstLoad:       true,   // suppress toasts/sounds on initial config.json read
  sortKey:         'oi_change',
  sortAsc:         false,
  filterVal:       'all',
  searchTerm:      '',
  seenSignals:     new Set(),   // track already-alerted symbols
};

// ─────────────────────────────────────────────
// DOM helpers
// ─────────────────────────────────────────────
const $  = id => document.getElementById(id);
const $$ = sel => document.querySelectorAll(sel);

function setText(id, txt) {
  const el = $(id);
  if (el && el.textContent !== String(txt)) el.textContent = txt;
}

function setHTML(id, html) {
  const el = $(id);
  if (el) el.innerHTML = html;
}

function animVal(id, newVal) {
  const el = $(id);
  if (!el) return;
  const formatted = String(newVal);
  if (el.textContent !== formatted) {
    el.textContent = formatted;
    el.classList.remove('num-flash');
    void el.offsetWidth;
    el.classList.add('num-flash');
    setTimeout(() => el.classList.remove('num-flash'), 380);
  }
}

function setWidth(id, pct) {
  const el = $(id);
  if (el) el.style.width = Math.min(100, Math.max(0, pct)) + '%';
}

function setClass(el, ...classes) {
  if (!el) return;
  el.className = classes.filter(Boolean).join(' ');
}

// ─────────────────────────────────────────────
// Live Clock
// ─────────────────────────────────────────────
function tickClock() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, '0');
  const mm = String(now.getMinutes()).padStart(2, '0');
  const ss = String(now.getSeconds()).padStart(2, '0');
  setText('liveClock', `${hh}:${mm}:${ss}`);
}
setInterval(tickClock, 500);
tickClock();

// ─────────────────────────────────────────────
// Web Audio — alert sounds
// ─────────────────────────────────────────────
function getAudioCtx() {
  if (!APP.audioCtx) {
    try {
      APP.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    } catch (_) { return null; }
  }
  if (APP.audioCtx.state === 'suspended') APP.audioCtx.resume();
  return APP.audioCtx;
}

function beep(freqs, type = 'sine', vol = 0.15, spacing = 0.13) {
  if (!APP.soundOn) return;
  const ctx = getAudioCtx();
  if (!ctx) return;
  freqs.forEach((f, i) => {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = type;
    osc.frequency.value = f;
    const t = ctx.currentTime + i * spacing;
    gain.gain.setValueAtTime(vol, t);
    gain.gain.exponentialRampToValueAtTime(0.001, t + 0.28);
    osc.start(t);
    osc.stop(t + 0.3);
  });
}

const SOUNDS = {
  startup:  () => beep([440, 660, 880], 'sine', 0.12, 0.15),
  signal:   () => beep([523, 659, 784, 1047], 'sine', 0.18, 0.12),
  scan:     () => beep([330], 'sine', 0.07),
  connect:  () => beep([528, 660], 'sine', 0.1, 0.1),
};

// Sound toggle button
$('soundBtn').addEventListener('click', () => {
  APP.soundOn = !APP.soundOn;
  $('soundBtn').textContent = APP.soundOn ? '🔊' : '🔇';
  $('soundBtn').classList.toggle('muted', !APP.soundOn);
  // Initialize audio context on first user gesture
  getAudioCtx();
});

// ─────────────────────────────────────────────
// Navigation
// ─────────────────────────────────────────────
function switchSection(id) {
  $$('.nav-item').forEach(n => n.classList.toggle('active', n.dataset.section === id));
  $$('.section').forEach(s => s.classList.remove('active'));
  const target = $('section-' + id);
  if (target) target.classList.add('active');
  closeSidebar();
}

$$('.nav-item').forEach(item => {
  item.addEventListener('click', e => {
    e.preventDefault();
    switchSection(item.dataset.section);
  });
});

// Sidebar mobile
function openSidebar()  { $('sidebar').classList.add('open');  $('sidebarOverlay').classList.add('show'); }
function closeSidebar() { $('sidebar').classList.remove('open'); $('sidebarOverlay').classList.remove('show'); }
$('sidebarToggle').addEventListener('click', () => $('sidebar').classList.contains('open') ? closeSidebar() : openSidebar());
$('sidebarOverlay').addEventListener('click', closeSidebar);

// ─────────────────────────────────────────────
// Toast Notifications
// ─────────────────────────────────────────────
function toast(icon, title, msg, isSignal = false, ms = 6000) {
  const box = $('toastContainer');
  const el  = document.createElement('div');
  el.className = 'toast' + (isSignal ? ' toast-signal' : '');
  el.innerHTML = `
    <span class="toast-icon">${icon}</span>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      <div class="toast-msg">${msg}</div>
    </div>
    <button class="toast-x" aria-label="Close">×</button>`;
  el.querySelector('.toast-x').addEventListener('click', () => removeToast(el));
  box.appendChild(el);
  if (ms > 0) setTimeout(() => removeToast(el), ms);
}

function removeToast(el) {
  if (!el || el.classList.contains('out')) return;
  el.classList.add('out');
  setTimeout(() => el.remove(), 320);
}

// ─────────────────────────────────────────────
// Connection status
// ─────────────────────────────────────────────
function setConn(live, msg = '') {
  const dot  = $('connDot');
  const text = $('connText');
  if (dot)  dot.className  = 'conn-dot ' + (live ? 'live' : 'error');
  if (text) text.textContent = live ? 'Live' : (msg || 'Offline');
  APP.connected = live;
}

// ─────────────────────────────────────────────
// Data Fetch + Poll
// ─────────────────────────────────────────────
async function fetchConfig() {
  try {
    const res = await fetch('config.json?_=' + Date.now(), {
      cache: 'no-store',
      headers: { 'Cache-Control': 'no-cache, no-store' }
    });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();

    if (!APP.connected) {
      setConn(true);
      SOUNDS.connect();
      toast('✅', 'Dashboard Connected', 'Receiving live data from OISignalFlow scanner');
    }

    update(data);

  } catch (err) {
    setConn(false, 'No data');
    if (APP.connected) {
      APP.connected = false;
      toast('⚠️', 'Connection Lost', 'Cannot read config.json — make sure OISignalFlow.py is running', false, 8000);
    }
  }
}

function startPolling() {
  fetchConfig();
  APP.pollTimer = setInterval(fetchConfig, APP.POLL_MS);
}

// ─────────────────────────────────────────────
// Master Update Dispatcher
// ─────────────────────────────────────────────
function update(data) {
  APP.data = data;
  updateHeader(data);
  updateKPIs(data);
  updateOverviewRow(data);
  updateRecentSignals(data);
  updateLiveSignals(data);
  updateScanner(data);
  updateStats(data);
  updateResults(data);
  updateConfig(data);
  updateSidebarFooter(data);
  checkNewSignals(data);
}

// ─────────────────────────────────────────────
// Header
// ─────────────────────────────────────────────
function updateHeader(data) {
  const open = data.status.market_open;
  const badge = $('marketBadge');
  const dot   = $('marketDot');
  if (badge) badge.className = 'market-badge ' + (open ? 'open' : 'closed');
  if (dot)   dot.className   = 'market-dot '   + (open ? 'open' : 'closed');
  setText('marketStatusText', open ? '🟢 Market Open' : '🔴 Market Closed');
}

// ─────────────────────────────────────────────
// KPI Cards
// ─────────────────────────────────────────────
function updateKPIs(data) {
  const s = data.statistics;
  const c = data.configuration;

  animVal('kpiScans',   s.total_scans);
  animVal('kpiSignals', s.signals_found);
  animVal('kpiStocks',  c.fno_stocks_total);

  const mood   = (s.market_mood || 'NEUTRAL').toUpperCase();
  const moodEl = $('kpiMood');
  if (moodEl && moodEl.textContent !== mood) {
    moodEl.textContent = mood;
    moodEl.style.color = mood.includes('BULL') ? 'var(--green)'
                       : mood.includes('BEAR') ? 'var(--red)'
                       : 'var(--yellow)';
  }

  // Overview meta
  setText('overviewMeta', `Scan #${s.total_scans}  ·  ${c.fno_stocks_total} FNO stocks`);
}

// ─────────────────────────────────────────────
// Overview Row
// ─────────────────────────────────────────────
function updateOverviewRow(data) {
  const c = data.configuration;
  const s = data.statistics;
  const st = data.status;

  // Market info panel
  const miStatus = $('miStatus');
  if (miStatus) {
    miStatus.textContent = st.market_open ? '🟢 Open' : '🔴 Closed';
    miStatus.style.color = st.market_open ? 'var(--green)' : 'var(--red)';
  }
  setText('miApi',    c.api_source  || '—');
  setText('miFno',    (c.fno_stocks_total || '—') + ' stocks');
  setText('miData',   c.data_type   || '—');
  setText('miPeriod', c.period      || '—');
  const miApiS = $('miApiStatus');
  if (miApiS) {
    miApiS.textContent = c.api_status || '—';
    miApiS.style.color = c.api_status === 'Connected' ? 'var(--green)' : 'var(--red)';
  }

  // Distribution bars
  const total = s.long_buildup_count + s.short_buildup_count + s.short_covering_count + s.long_unwinding_count;
  const pct   = n => total > 0 ? Math.round((n / total) * 100) : 0;

  setWidth('dbarLong',     pct(s.long_buildup_count));
  setWidth('dbarShort',    pct(s.short_buildup_count));
  setWidth('dbarCovering', pct(s.short_covering_count));
  setWidth('dbarUnwinding',pct(s.long_unwinding_count));
  setText('dcntLong',     s.long_buildup_count);
  setText('dcntShort',    s.short_buildup_count);
  setText('dcntCovering', s.short_covering_count);
  setText('dcntUnwinding',s.long_unwinding_count);

  // Scanner mini
  const scanning = st.system_status === 'scanning';
  const dot = $('miniScanDot');
  if (dot) dot.className = 'pulse-dot' + (scanning ? ' on' : '');
  setText('smStatus', (st.system_status || 'READY').toUpperCase());
  setText('smStock',  scanning && st.current_stock ? `Scanning: ${st.current_stock}` : 'Waiting for next scan...');

  const scanned   = (data.all_scan_results || []).length;
  const totalStk  = c.fno_stocks_total || 209;
  const pctScanned= totalStk > 0 ? Math.round((scanned / totalStk) * 100) : 0;
  setWidth('smProgressFill', pctScanned);
  setText('smProgressText', `${scanned} / ${totalStk} stocks`);
}

// ─────────────────────────────────────────────
// Recent Signals (Overview quick view)
// ─────────────────────────────────────────────
function updateRecentSignals(data) {
  const sigs = data.recent_signals || [];
  const grid = $('recentGrid');
  if (!grid) return;

  if (sigs.length === 0) {
    grid.innerHTML = `<div class="empty-state"><div class="es-icon">🔍</div><div class="es-text">No CE signals yet — scanner is watching ${data.configuration.fno_stocks_total} stocks</div></div>`;
    return;
  }

  grid.innerHTML = sigs.map(s => buildSignalCard(s)).join('');
}

// ─────────────────────────────────────────────
// Live Signals Section
// ─────────────────────────────────────────────
function updateLiveSignals(data) {
  const sigs = data.recent_signals || [];
  setText('signalsMeta', `${sigs.length} CE signal${sigs.length !== 1 ? 's' : ''} found`);

  // Nav badge
  const badge = $('signalsBadge');
  if (badge) {
    badge.textContent = sigs.length;
    badge.style.display = sigs.length > 0 ? '' : 'none';
  }

  const grid = $('signalsGrid');
  if (!grid) return;

  if (sigs.length === 0) {
    grid.innerHTML = `<div class="empty-state large"><div class="es-icon">🎯</div><div class="es-text">No CE signals detected yet</div><div class="es-sub">Conditions: Long Buildup + OI ≥ ${data.configuration.oi_change_min}% + Price ≥ ${data.configuration.price_change_min}% + Volume ≥ ${data.configuration.volume_mult}x</div></div>`;
    return;
  }

  grid.innerHTML = sigs.map(s => buildSignalCard(s, true)).join('');
}

function buildSignalCard(s, markNew = false) {
  const veryStrong  = s.strength && s.strength.includes('VERY STRONG');
  const priceClass  = parseFloat(s.price_change) >= 0 ? 'pos' : 'neg';
  const priceSign   = parseFloat(s.price_change) >= 0 ? '+' : '';
  const oiSign      = parseFloat(s.oi_change)    >= 0 ? '+' : '';
  const newClass    = markNew ? ' new-card' : '';

  return `
  <div class="signal-card${newClass}">
    <div class="sc-header">
      <span class="sc-symbol">${esc(s.symbol)}</span>
      <span class="sc-time">⏱ ${esc(s.time)}</span>
    </div>
    <div class="sc-metrics">
      <div class="sc-metric">
        <span class="sc-mlabel">Price</span>
        <span class="sc-mval">₹${fmtNum(s.price, 2)}</span>
      </div>
      <div class="sc-metric">
        <span class="sc-mlabel">Price Change</span>
        <span class="sc-mval ${priceClass}">${priceSign}${fmtNum(s.price_change, 2)}%</span>
      </div>
      <div class="sc-metric">
        <span class="sc-mlabel">OI Change</span>
        <span class="sc-mval pos">${oiSign}${fmtNum(s.oi_change, 2)}%</span>
      </div>
      <div class="sc-metric">
        <span class="sc-mlabel">Volume Ratio</span>
        <span class="sc-mval pos">${fmtNum(s.volume_ratio, 1)}x</span>
      </div>
    </div>
    <div class="sc-footer">
      <span class="strength-tag${veryStrong ? ' very' : ''}">${esc(s.strength || '✅ MODERATE')}</span>
      <span class="sc-action">🎯 BUY ATM CE</span>
    </div>
  </div>`;
}

// ─────────────────────────────────────────────
// Scanner Section
// ─────────────────────────────────────────────
function updateScanner(data) {
  const st   = data.status;
  const conf = data.configuration;
  const res  = data.all_scan_results || [];

  const scanning    = st.system_status === 'scanning';
  const currentScan = st.current_scan  || 0;
  const totalStocks = conf.fno_stocks_total || 209;
  const scanned     = res.length;

  setText('scannerMeta', `Scan #${currentScan}`);

  // Scanner nav dot
  const pulse = $('scannerPulse');
  if (pulse) pulse.className = 'nav-pulse' + (scanning ? ' scanning' : '');

  // Ring & status text
  const ring = $('scanRing');
  if (ring) ring.className = 'scan-ring' + (scanning ? '' : ' idle');
  setText('scanRingText', (st.system_status || 'READY').toUpperCase());

  // Stock display
  setText('ssiStock', scanning && st.current_stock ? st.current_stock : '—');

  // Progress bar
  const pct = totalStocks > 0 ? Math.round((scanned / totalStocks) * 100) : 0;
  setText('spbCurrent', scanned);
  setText('spbTotal',   totalStocks);
  setText('spbScanNum', currentScan);
  setText('spbInterval',`Every ${conf.scan_interval || 5} min`);
  setWidth('spbBar', pct);
  setText('spbPct', pct + '%');

  // Filter table
  renderFilterTable(res, conf);
}

function renderFilterTable(results, conf) {
  const tbody = $('filterTbody');
  if (!tbody) return;

  if (results.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="td-empty">No data yet — start OISignalFlow.py</td></tr>';
    return;
  }

  tbody.innerHTML = results.slice(0, 80).map(r => {
    const isCE = r.filters?.signal_ok && r.filters?.oi_ok && r.filters?.price_ok && r.filters?.volume_ok;
    return `<tr>
      <td class="sym-bold${isCE ? ' sym-ce' : ''}">${esc(r.symbol)}</td>
      <td>₹${fmtNum(r.price, 2)}</td>
      <td class="${r.price_change >= 0 ? 'pos-val' : 'neg-val'}">${sign(r.price_change)}${fmtNum(r.price_change, 2)}%</td>
      <td class="${r.oi_change >= 0 ? 'pos-val' : 'neg-val'}">${sign(r.oi_change)}${fmtNum(r.oi_change, 2)}%</td>
      <td>${fmtNum(r.volume_ratio, 2)}x</td>
      <td>${signalTag(r.signal)}</td>
      <td><div class="fbadges">
        ${filterBadge(r.filters?.signal_ok, 'SIG', 'fb-green')}
        ${filterBadge(r.filters?.oi_ok,     'OI',  'fb-cyan')}
        ${filterBadge(r.filters?.price_ok,  'PR',  'fb-purple')}
        ${filterBadge(r.filters?.volume_ok, 'VOL', 'fb-orange')}
      </div></td>
      <td style="color:var(--text-3)">${esc(r.time)}</td>
    </tr>`;
  }).join('');
}

function filterBadge(ok, label, cls) {
  return `<span class="fbadge ${ok ? cls : 'fb-gray'}">${label}</span>`;
}

// ─────────────────────────────────────────────
// Statistics
// ─────────────────────────────────────────────
function updateStats(data) {
  const s    = data.statistics;
  const conf = data.configuration;

  setText('statsMeta', `Scan #${s.total_scans} — All-time stats`);

  // Breakdown counts
  animVal('bkLong',     s.long_buildup_count);
  animVal('bkShort',    s.short_buildup_count);
  animVal('bkCovering', s.short_covering_count);
  animVal('bkUnwinding',s.long_unwinding_count);

  // Proportional bar
  const total = s.long_buildup_count + s.short_buildup_count + s.short_covering_count + s.long_unwinding_count;
  if (total > 0) {
    $('pbGreen').style.flex  = s.long_buildup_count;
    $('pbRed').style.flex    = s.short_buildup_count;
    $('pbYellow').style.flex = s.short_covering_count;
    $('pbGray').style.flex   = s.long_unwinding_count;
  } else {
    ['pbGreen','pbRed','pbYellow','pbGray'].forEach(id => $(id).style.flex = 1);
  }

  // Mood gauge
  const mood    = (s.market_mood || 'NEUTRAL').toUpperCase();
  const moodEl  = $('moodBigText');
  if (moodEl) {
    moodEl.textContent = mood;
    moodEl.className   = 'mood-big-text ' + (mood.includes('BULL') ? 'bullish' : mood.includes('BEAR') ? 'bearish' : 'neutral');
  }
  const needle = $('mgNeedle');
  if (needle) needle.style.left = (mood.includes('BULL') ? 75 : mood.includes('BEAR') ? 25 : 50) + '%';

  animVal('mcBull', s.long_buildup_count);
  animVal('mcBear', s.short_buildup_count);

  // Scan metrics
  animVal('mrScans',       s.total_scans);
  animVal('mrStocksPerScan', conf.fno_stocks_total);
  animVal('mrCE',          s.signals_found);

  const hitRate = s.stocks_scanned > 0
    ? ((s.signals_found / s.stocks_scanned) * 100).toFixed(1)
    : '0.0';
  setText('mrHitRate', hitRate + '%');
  setText('mrInterval', (conf.scan_interval || 5) + ' min');
  animVal('mrScanned', s.stocks_scanned);
}

// ─────────────────────────────────────────────
// All Results Table
// ─────────────────────────────────────────────
function updateResults(data) {
  if (!data.all_scan_results) return;
  renderResultsTable(data.all_scan_results);
}

function renderResultsTable(rawResults) {
  const tbody = $('resultsTbody');
  if (!tbody) return;

  const search = APP.searchTerm.toLowerCase();
  const filter = APP.filterVal;

  // Filter
  let results = rawResults.filter(r => {
    if (search && !r.symbol.toLowerCase().includes(search)) return false;
    if (filter === 'long'     && !r.signal?.includes('LONG BUILDUP'))  return false;
    if (filter === 'short'    && !r.signal?.includes('SHORT BUILDUP')) return false;
    if (filter === 'covering' && !r.signal?.includes('SHORT COVERING'))return false;
    if (filter === 'unwinding'&& !r.signal?.includes('LONG UNWINDING'))return false;
    if (filter === 'ce') {
      const f = r.filters;
      if (!(f?.signal_ok && f?.oi_ok && f?.price_ok && f?.volume_ok)) return false;
    }
    return true;
  });

  // Sort
  results.sort((a, b) => {
    let av, bv;
    switch (APP.sortKey) {
      case 'symbol':       av = a.symbol;       bv = b.symbol;       break;
      case 'price':        av = a.price;        bv = b.price;        break;
      case 'price_change': av = a.price_change; bv = b.price_change; break;
      case 'volume_ratio': av = a.volume_ratio; bv = b.volume_ratio; break;
      default:             av = a.oi_change;    bv = b.oi_change;
    }
    if (typeof av === 'string') return APP.sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
    return APP.sortAsc ? av - bv : bv - av;
  });

  if (results.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="td-empty">No matching results</td></tr>';
    setText('resultsFooter', '');
    return;
  }

  tbody.innerHTML = results.map(r => {
    const isCE = r.filters?.signal_ok && r.filters?.oi_ok && r.filters?.price_ok && r.filters?.volume_ok;
    return `<tr>
      <td class="sym-bold${isCE ? ' sym-ce' : ''}">${esc(r.symbol)}</td>
      <td>₹${fmtNum(r.price, 2)}</td>
      <td class="${r.price_change >= 0 ? 'pos-val' : 'neg-val'}">${sign(r.price_change)}${fmtNum(r.price_change, 2)}%</td>
      <td class="${r.oi_change >= 0 ? 'pos-val' : 'neg-val'}">${sign(r.oi_change)}${fmtNum(r.oi_change, 2)}%</td>
      <td>${fmtNum(r.volume_ratio, 2)}x</td>
      <td>${signalTag(r.signal)}</td>
      <td><div class="fbadges">
        ${filterBadge(r.filters?.signal_ok, 'SIG', 'fb-green')}
        ${filterBadge(r.filters?.oi_ok,     'OI',  'fb-cyan')}
        ${filterBadge(r.filters?.price_ok,  'PR',  'fb-purple')}
        ${filterBadge(r.filters?.volume_ok, 'VOL', 'fb-orange')}
      </div></td>
      <td style="color:var(--text-3)">${esc(r.time)}</td>
    </tr>`;
  }).join('');

  setText('resultsFooter', `Showing ${results.length} of ${rawResults.length} stocks`);
}

// Sortable headers
$$('.sortable-table th[data-sort]').forEach(th => {
  th.addEventListener('click', () => {
    const key = th.dataset.sort;
    if (APP.sortKey === key) {
      APP.sortAsc = !APP.sortAsc;
    } else {
      APP.sortKey = key;
      APP.sortAsc = false;
    }
    // Update header classes
    $$('.sortable-table th').forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
    th.classList.add(APP.sortAsc ? 'sort-asc' : 'sort-desc');

    if (APP.data?.all_scan_results) renderResultsTable(APP.data.all_scan_results);
  });
});

// Search
$('resultsSearch').addEventListener('input', e => {
  APP.searchTerm = e.target.value.trim();
  if (APP.data?.all_scan_results) renderResultsTable(APP.data.all_scan_results);
});

// Filter select
$('resultsFilter').addEventListener('change', e => {
  APP.filterVal = e.target.value;
  if (APP.data?.all_scan_results) renderResultsTable(APP.data.all_scan_results);
});

// ─────────────────────────────────────────────
// Configuration Section
// ─────────────────────────────────────────────
function updateConfig(data) {
  const c  = data.configuration;
  const st = data.status;

  setText('cfgOi',       c.oi_change_min + '%');
  setText('cfgPrice',    c.price_change_min + '%');
  setText('cfgVol',      c.volume_mult + 'x');
  setText('cfgInterval', c.scan_interval + ' min');
  setText('cfgApiSource',c.api_source  || '—');
  setText('cfgDataType', c.data_type   || '—');
  setText('cfgPeriod',   c.period      || '—');
  setText('cfgOutput',   c.output_file || '—');
  setText('cfgFno',      (c.fno_stocks_total || '—') + ' stocks');

  // API status
  const apiEl = $('cfgApiStatus');
  if (apiEl) {
    apiEl.textContent = c.api_status || '—';
    apiEl.className   = 'cfg-val cfg-status ' + (c.api_status === 'Connected' ? 'connected' : 'error');
  }

  // Booleans
  setBoolCfg('cfgTelegram', c.telegram_enabled);
  setBoolCfg('cfgDesktop',  c.desktop_notifications);

  // System tiles
  const scannerRunning = st.scanner_running || st.system_status === 'scanning';
  setSysTile('sysScannerVal', scannerRunning ? 'RUNNING' : 'STOPPED', scannerRunning ? 'running' : 'stopped');
  setSysTile('sysSystemVal',  (st.system_status || 'ready').toUpperCase(), st.system_status === 'scanning' ? 'running' : 'ready');
  setSysTile('sysMarketVal',  st.market_open ? 'OPEN' : 'CLOSED', st.market_open ? 'open' : 'closed');
  const lastUpEl = $('sysLastUpdate');
  if (lastUpEl) { lastUpEl.textContent = st.last_update || '—'; lastUpEl.className = 'sys-tile-val small-val'; }
}

function setBoolCfg(id, val) {
  const el = $(id);
  if (!el) return;
  el.textContent = val ? '✅ Enabled' : '❌ Disabled';
  el.className   = 'cfg-val cfg-bool ' + (val ? 'enabled' : 'disabled');
}

function setSysTile(id, label, cls) {
  const el = $(id);
  if (!el) return;
  el.textContent = label;
  el.className   = 'sys-tile-val ' + cls;
}

// ─────────────────────────────────────────────
// Sidebar Footer
// ─────────────────────────────────────────────
function updateSidebarFooter(data) {
  setText('sidebarLastUpdate', data.status.last_update ? data.status.last_update.split(' ')[1] : '—');
  setText('sidebarSystem', (data.status.system_status || 'ready').toUpperCase());
}

// ─────────────────────────────────────────────
// New Signal Detection → Sound + Toast
// ─────────────────────────────────────────────
function checkNewSignals(data) {
  const signals  = data.recent_signals || [];
  const scanNum  = data.status?.current_scan || 0;

  // If scan number changed — it's a new scan run
  const newScan = scanNum > APP.prevScanNum;
  if (newScan) {
    APP.prevScanNum = scanNum;
    if (scanNum > 1) SOUNDS.scan();
  }

  // Seed seenSignals on first load — never alert for pre-existing signals
  if (APP.firstLoad) {
    signals.forEach(s => APP.seenSignals.add(`${s.symbol}_${s.time}`));
    APP.firstLoad = false;
    APP.prevSignalCount = signals.length;
    return;
  }

  // Check for genuinely new CE signals since last poll
  signals.forEach(s => {
    const key = `${s.symbol}_${s.time}`;
    if (!APP.seenSignals.has(key)) {
      APP.seenSignals.add(key);
      SOUNDS.signal();
      toast(
        '🟢',
        `CE Signal: ${s.symbol}`,
        `OI: ${sign(s.oi_change)}${fmtNum(s.oi_change, 2)}%  |  Price: ${sign(s.price_change)}${fmtNum(s.price_change, 2)}%  |  ${s.strength || 'MODERATE'}`,
        true,
        10000
      );
    }
  });

  APP.prevSignalCount = signals.length;
}

// ─────────────────────────────────────────────
// Signal Tag HTML helper
// ─────────────────────────────────────────────
function signalTag(signal) {
  if (!signal) return `<span class="tag tag-unwind">—</span>`;
  if (signal.includes('LONG BUILDUP'))  return `<span class="tag tag-long">🟢 Long Buildup</span>`;
  if (signal.includes('SHORT BUILDUP')) return `<span class="tag tag-short">🔴 Short Buildup</span>`;
  if (signal.includes('SHORT COVERING'))return `<span class="tag tag-cover">🟡 Short Covering</span>`;
  if (signal.includes('LONG UNWINDING'))return `<span class="tag tag-unwind">⚪ Long Unwinding</span>`;
  return `<span class="tag tag-unwind">${esc(signal)}</span>`;
}

// ─────────────────────────────────────────────
// Utility functions
// ─────────────────────────────────────────────
function fmtNum(n, decimals = 2) {
  const num = parseFloat(n);
  return isNaN(num) ? '—' : num.toFixed(decimals);
}

function sign(n) {
  return parseFloat(n) >= 0 ? '+' : '';
}

// XSS-safe escaping
function esc(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ─────────────────────────────────────────────
// Keyboard shortcut: Alt+S = sound toggle
// ─────────────────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.altKey && e.key === 's') $('soundBtn').click();
});

// ─────────────────────────────────────────────
// Init
// ─────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  startPolling();

  toast(
    '⚡', 'OISignalFlow Dashboard',
    'Connecting to scanner — make sure OISignalFlow.py is running',
    false, 5000
  );
});
