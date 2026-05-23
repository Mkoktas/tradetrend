/* TradeTrend — frontend app.js */
'use strict';

// ── State ─────────────────────────────────────────────────────────────────────
let META = null;
let ALT_CATS = {};
let currentView   = 'trends';
let currentPTab   = 'trends';
let currentResults = [];

// ── Debounce for filter changes ───────────────────────────────────────────────
let _loadTimer = null;
function debouncedLoad() {
  clearTimeout(_loadTimer);
  _loadTimer = setTimeout(loadTrends, 280);
}

// ── Boot ──────────────────────────────────────────────────────────────────────
async function boot() {
  META = await fetch('/api/meta').then(r => r.json());
  buildSectors();
  buildRegions();
  buildChannels();
  // Risk checkboxes (static in HTML) — attach auto-refresh
  document.querySelectorAll('#chk-risk input').forEach(cb =>
    cb.addEventListener('change', debouncedLoad));
  await onSectorChange();   // loads categories + initial data
}

// ── Sidebar builders ──────────────────────────────────────────────────────────
function buildSectors() {
  const sel = document.getElementById('sel-sector');
  sel.innerHTML = '';
  for (const [label, key] of Object.entries(META.SECTORS)) {
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = `${META.SECTOR_EMOJI[key] || ''} ${label}`;
    sel.appendChild(opt);
  }
}

function buildRegions() {
  const sel = document.getElementById('sel-region');
  sel.innerHTML = '';
  for (const r of META.REGIONS) {
    const m = META.REGION_META[r] || {};
    const opt = document.createElement('option');
    opt.value = r;
    opt.textContent = `${m.emoji || ''} ${r}  —  ${m.desc || ''}`;
    sel.appendChild(opt);
  }
}

function buildChannels() {
  const wrap = document.getElementById('chk-channels');
  wrap.innerHTML = '';
  for (const ch of META.SALES_CHANNELS) {
    const key = META.SIDEBAR_TO_KEY[ch];
    const lbl = document.createElement('label');
    lbl.innerHTML = `<input type="checkbox" value="${key}" checked> ${ch}`;
    lbl.querySelector('input').addEventListener('change', debouncedLoad);
    wrap.appendChild(lbl);
  }
}

// ── Category loaders ──────────────────────────────────────────────────────────
async function onSectorChange() {
  const sector = document.getElementById('sel-sector').value;
  const { ana, alt } = await fetch(`/api/trends/categories?sector=${sector}`).then(r => r.json());
  ALT_CATS = alt;

  const selAna = document.getElementById('sel-ana');
  selAna.innerHTML = '';
  for (const a of ana) {
    const opt = document.createElement('option');
    opt.value = a; opt.textContent = a;
    selAna.appendChild(opt);
  }
  await onAnaCatChange();
  if (currentPTab === 'imports') await loadImports();
}

async function onAnaCatChange() {
  const ana = document.getElementById('sel-ana').value;
  const selAlt = document.getElementById('sel-alt');
  selAlt.innerHTML = '';
  const alts = (ana === 'Tümü' ? ['Tümü'] : (ALT_CATS[ana] || ['Tümü']));
  for (const a of alts) {
    const opt = document.createElement('option');
    opt.value = a; opt.textContent = a;
    selAlt.appendChild(opt);
  }
  await loadTrends();
}

// ── View switching (sidebar tab removed; kept for compat) ─────────────────────
function switchView(view, btn) {
  if (view === 'trends')  setPageTab('trends');
  if (view === 'imports') setPageTab('imports');
}

function setPageTab(tab) {
  currentPTab = tab;
  document.getElementById('section-trends').style.display  = tab === 'trends'  ? '' : 'none';
  document.getElementById('section-imports').style.display = tab === 'imports' ? '' : 'none';
  document.getElementById('section-guide').style.display   = tab === 'guide'   ? '' : 'none';
  document.getElementById('ptab-trends').classList.toggle('active',  tab === 'trends');
  document.getElementById('ptab-imports').classList.toggle('active', tab === 'imports');
  document.getElementById('sidebar-guide-btn').classList.toggle('btn-guide-active', tab === 'guide');
  if (tab === 'imports') loadImports();
  if (tab === 'guide')   renderGuide();
}

// ── Selected helpers ──────────────────────────────────────────────────────────
function selectedChannels() {
  return [...document.querySelectorAll('#chk-channels input:checked')].map(i => i.value);
}
function selectedRisks() {
  return [...document.querySelectorAll('#chk-risk input:checked')].map(i => i.value);
}

// ── Load trends ───────────────────────────────────────────────────────────────
async function loadTrends() {
  document.getElementById('product-list').innerHTML = '<div class="loading"><div class="spinner"></div> Analiz ediliyor...</div>';

  const body = {
    sector:   document.getElementById('sel-sector').value,
    anaCat:   document.getElementById('sel-ana').value,
    altCat:   document.getElementById('sel-alt').value,
    region:   document.getElementById('sel-region').value,
    channels: selectedChannels(),
  };

  const data = await fetch('/api/trends', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(r => r.json());

  const risks = selectedRisks();
  currentResults = (data.results || []).filter(r => risks.includes(r.risk_level));

  updateHeader(body.sector, body.region);
  updateMetrics(currentResults, body.region);
  renderRegionMap(currentResults);
  renderOverviewCharts(currentResults);
  renderProductCards(currentResults, body.sector);
}

// ── Load imports ──────────────────────────────────────────────────────────────
async function loadImports() {
  document.getElementById('import-list').innerHTML = '<div class="loading"><div class="spinner"></div> Yükleniyor...</div>';
  const sector = document.getElementById('sel-sector').value;
  const data = await fetch(`/api/imports?sector=${sector}`).then(r => r.json());
  renderImportCards(data.results || []);
}

// ── Header ────────────────────────────────────────────────────────────────────
function updateHeader(sectorKey, region) {
  const sectorLabel = Object.entries(META.SECTORS).find(([,v]) => v === sectorKey)?.[0] || sectorKey;
  const regMeta     = META.REGION_META[region] || {};
  document.getElementById('header-title').textContent =
    `${META.SECTOR_EMOJI[sectorKey] || '📊'} ${sectorLabel} — ${regMeta.emoji || ''} ${region}`;
  document.getElementById('header-sub').textContent =
    `${regMeta.desc || 'Türkiye trend analizi'} · TradeTrend`;
}

// ── Metrics ───────────────────────────────────────────────────────────────────
function updateMetrics(results, region) {
  document.getElementById('m-total').textContent = results.length;
  if (!results.length) {
    ['m-avg','m-risk','m-channel'].forEach(id => document.getElementById(id).textContent = '—');
    return;
  }
  const avg = results.reduce((s, r) => s + r.composite_score, 0) / results.length;
  document.getElementById('m-avg').textContent    = avg.toFixed(1);
  document.getElementById('m-risk').textContent   = results.filter(r => r.risk_level === 'high').length;

  const chCounts = {};
  for (const r of results) chCounts[r.best_channel] = (chCounts[r.best_channel] || 0) + 1;
  const bestCh = Object.entries(chCounts).sort((a,b)=>b[1]-a[1])[0]?.[0] || '—';
  document.getElementById('m-channel').textContent = META.CHANNEL_MAP[bestCh] || bestCh;
}

// ── Turkey region map (CSS grid zone map) ────────────────────────────────────
const TR_REGIONS = [
  { key: 'Marmara',           emoji: '🌆', area: 'mar',   cities: 'İstanbul · Bursa'      },
  { key: 'Karadeniz',         emoji: '🌿', area: 'kara',  cities: 'Trabzon · Samsun'      },
  { key: 'Ege',               emoji: '🌊', area: 'ege',   cities: 'İzmir · Muğla'         },
  { key: 'İç Anadolu',        emoji: '🏛️', area: 'ic',    cities: 'Ankara · Konya'        },
  { key: 'Doğu Anadolu',      emoji: '🏔️', area: 'dand',  cities: 'Erzurum · Van'         },
  { key: 'Akdeniz',           emoji: '☀️', area: 'akt',   cities: 'Antalya · Adana'       },
  { key: 'Güneydoğu Anadolu', emoji: '🌾', area: 'gdand', cities: 'Gaziantep · Şanlıurfa' },
];

function renderRegionMap(results) {
  const el  = document.getElementById('chart-map');
  const sub = document.getElementById('map-subtitle');
  if (!results.length || !META.REGION_BASE_SCORE_DELTA) {
    el.innerHTML = '<div class="empty" style="height:190px;">Veri yok</div>';
    return;
  }

  const sector         = document.getElementById('sel-sector').value;
  const selectedRegion = document.getElementById('sel-region').value;
  const avgScore       = results.reduce((s, r) => s + r.composite_score, 0) / results.length;

  // API already applied the selected region's delta — subtract it to get neutral baseline
  const appliedBase = META.REGION_BASE_SCORE_DELTA[selectedRegion] || 0;
  const appliedAff  = (META.REGION_SECTOR_AFFINITY[selectedRegion] || {})[sector] || 0;
  const neutralAvg  = avgScore - appliedBase - appliedAff;

  const scored = TR_REGIONS.map(r => {
    const base  = META.REGION_BASE_SCORE_DELTA[r.key] || 0;
    const aff   = (META.REGION_SECTOR_AFFINITY[r.key] || {})[sector] || 0;
    const score = Math.min(100, Math.max(0, Math.round(neutralAvg + base + aff)));
    return { ...r, score };
  });

  // Color: low score → light blue-gray, high score → deep brand blue
  function scoreToStyle(score) {
    const t   = Math.max(0, Math.min(1, (score - 28) / 52)); // normalize 28-80 range
    const r   = Math.round(219 - t * 190);  // #dbeafe → #1d4ed8
    const g   = Math.round(234 - t * 156);
    const b   = Math.round(254 - t * 38);
    const bg  = `rgba(${r},${g},${b},0.88)`;
    const fg  = t > 0.42 ? '#ffffff' : '#1e3a8a';
    const sub = t > 0.42 ? 'rgba(255,255,255,.65)' : 'rgba(30,58,138,.55)';
    return { bg, fg, sub };
  }

  const cells = scored.map(r => {
    const { bg, fg, sub } = scoreToStyle(r.score);
    return `<div class="tr-region" style="grid-area:${r.area};background:${bg};"
               title="${r.key} — Fırsat Skoru: ${r.score}">
      <div class="tr-region-top">
        <span class="tr-region-emoji">${r.emoji}</span>
        <span class="tr-region-score" style="color:${fg};">${r.score}</span>
      </div>
      <div class="tr-region-name" style="color:${fg};">${r.key}</div>
      <div class="tr-region-cities" style="color:${sub};">${r.cities}</div>
    </div>`;
  }).join('');

  el.innerHTML = `<div class="tr-map-grid">${cells}</div>`;

  const ranked = [...scored].sort((a, b) => b.score - a.score);
  sub.textContent = `En güçlü: ${ranked[0].emoji} ${ranked[0].key} (${ranked[0].score}) · ${ranked[1].emoji} ${ranked[1].key} (${ranked[1].score})`;
}

// ── Overview charts ───────────────────────────────────────────────────────────
function renderOverviewCharts(results) {
  if (!results.length) {
    ['chart-overview','chart-risk'].forEach(id => { document.getElementById(id).innerHTML = '<div class="empty">Veri yok</div>'; });
    return;
  }

  // Bar chart
  const sorted = [...results].sort((a,b) => b.composite_score - a.composite_score).slice(0,15);
  Plotly.newPlot('chart-overview', [{
    type: 'bar', orientation: 'h',
    x: sorted.map(r => r.composite_score),
    y: sorted.map(r => r.emoji + ' ' + r.product_name),
    marker: { color: sorted.map(r => META.RISK_COLORS[r.risk_level]) },
    hovertemplate: '<b>%{y}</b><br>Skor: %{x}<extra></extra>',
  }], {
    margin: { l: 160, r: 20, t: 10, b: 30 },
    xaxis: { range: [0,100], title: '' },
    yaxis: { automargin: true, tickfont: { size: 10 } },
    paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
    height: 220,
  }, { displayModeBar: false, responsive: true });

  // Risk summary list (no chart)
  const riskCounts = { low: 0, medium: 0, high: 0 };
  for (const r of results) riskCounts[r.risk_level]++;
  const total = results.length;
  const riskRows = [
    { key: 'low',    icon: '🟢', label: 'Düşük Risk',  color: '#059669', bg: 'rgba(5,150,105,.08)'  },
    { key: 'medium', icon: '🟡', label: 'Orta Risk',   color: '#d97706', bg: 'rgba(217,119,6,.08)'  },
    { key: 'high',   icon: '🔴', label: 'Yüksek Risk', color: '#dc2626', bg: 'rgba(220,38,38,.08)'  },
  ];
  document.getElementById('chart-risk').innerHTML = riskRows.map(r => {
    const cnt = riskCounts[r.key];
    const pct = total ? Math.round(cnt / total * 100) : 0;
    return `<div style="display:flex;align-items:center;gap:.6rem;padding:.45rem .5rem;border-radius:10px;background:${r.bg};margin-bottom:.4rem;">
      <span style="font-size:1rem;">${r.icon}</span>
      <span style="flex:1;font-size:.82rem;font-weight:600;color:#374151;">${r.label}</span>
      <span style="font-size:1rem;font-weight:800;color:${r.color};">${cnt}</span>
      <span style="font-size:.72rem;color:#9ca3af;min-width:32px;text-align:right;">${pct}%</span>
    </div>`;
  }).join('');
}

// ── Product cards ─────────────────────────────────────────────────────────────
function renderProductCards(results, sectorKey) {
  const container = document.getElementById('product-list');
  if (!results.length) {
    container.innerHTML = '<div class="empty">🔍 Seçilen filtrelere uygun ürün bulunamadı.</div>';
    return;
  }

  const grad = META.SECTOR_GRAD[sectorKey] || ['214,234,254','219,234,254'];
  const [g1, g2] = Array.isArray(grad) ? grad : Object.values(grad);

  container.innerHTML = `<div style="font-size:.85rem;font-weight:700;color:#0c1a3a;margin-bottom:.6rem;">
    🏆 Top ${results.length} Ürün</div>`;

  results.forEach((r, i) => {
    const rc   = META.RISK_COLORS[r.risk_level];
    const rl   = META.RISK_LABELS[r.risk_level];
    const bch  = META.CHANNEL_MAP[r.best_channel] || r.best_channel;
    const card = document.createElement('div');
    card.className = 'glass-card';

    // Score bars HTML
    const bars = [
      ['Google',    r.google_score,   '#4285f4'],
      ['Trendyol',  r.trendyol_score, '#f27a1a'],
      ['Amazon TR', r.amazon_score,   '#f90'],
      ['TikTok',    r.tiktok_score,   '#fe2c55'],
    ].map(([name, score, col]) => `
      <div class="score-bar-item">
        <div class="score-bar-label">
          <span>${name}</span><span style="color:${col};font-weight:700;">${score.toFixed(0)}</span>
        </div>
        <div class="score-bar-track">
          <div class="score-bar-fill" style="width:${score}%;background:${col};"></div>
        </div>
      </div>`).join('');

    card.innerHTML = `
      <div class="glass-card-header" onclick="toggleCard(this)">
        <span>${r.emoji}  ${r.product_name}  ·  ${r.composite_score.toFixed(0)}/100  ·
          <span style="color:${rc};">${rl}</span>  →  ${bch}
        </span>
        <span class="chevron">▼</span>
      </div>
      <div class="glass-card-body" id="card-body-${i}">
        <div class="product-meta">
          <div class="product-icon"
               style="background:linear-gradient(135deg,rgba(${g1},.55),rgba(${g2},.85));">
            ${r.emoji}
          </div>
          <div class="product-scores">
            <div>
              <span class="score-big" style="color:${rc};">${r.composite_score.toFixed(0)}</span>
              <span class="score-sep">/100 · </span>
              <span class="risk-label" style="color:${rc};">${r.risk_emoji} ${rl}</span>
            </div>
            <div class="score-bars">${bars}</div>
          </div>
        </div>

        <!-- Annual trend -->
        <div id="ann-${i}" class="chart-box" style="min-height:160px;"></div>
        <div class="insight-box">💡 ${r.seasonality?.insight || ''}</div>

        <!-- Forecast + Channel -->
        <div class="chart-row">
          <div id="fc-${i}"  class="chart-box"></div>
          <div id="ch-${i}"  class="chart-box"></div>
        </div>
      </div>`;

    container.appendChild(card);
  });
}

// Toggle card open/close and lazy-render charts
function toggleCard(header) {
  header.classList.toggle('open');
  const body = header.nextElementSibling;
  body.classList.toggle('open');
  if (!body.classList.contains('open')) return;

  // Find index
  const idx = body.id.split('-').pop();
  const r   = currentResults[parseInt(idx)];
  if (!r || body.dataset.charted) return;
  body.dataset.charted = '1';

  renderAnnualChart(`ann-${idx}`, r);
  renderForecastChart(`fc-${idx}`, r);
  renderChannelChart(`ch-${idx}`, r);
}

// ── Annual seasonality chart ──────────────────────────────────────────────────
function renderAnnualChart(elId, r) {
  const S     = r.seasonality;
  const months = META.MONTHS_TR;
  const base   = S?.data || Array(12).fill(60);
  const scale  = r.composite_score / 100;
  const values = base.map(v => Math.min(100, Math.round(v * scale * 1.1 + r.composite_score * 0.2)));
  const now    = new Date().getMonth();

  Plotly.newPlot(elId, [
    { x: months, y: values, type: 'scatter', mode: 'lines+markers',
      fill: 'tozeroy', fillcolor: 'rgba(29,78,216,.07)',
      line: { color: '#2563eb', width: 2.5, shape: 'spline' },
      marker: { color: months.map((_, i) => i === now ? '#f59e0b' : '#2563eb'),
                size:  months.map((_, i) => i === now ? 9 : 5) },
      hovertemplate: '<b>%{x}</b><br>Talep: %{y}<extra></extra>',
    },
    { x: [months[now]], y: [values[now]], type: 'scatter', mode: 'markers+text',
      marker: { color: '#f59e0b', size: 10, symbol: 'diamond' },
      text: ['Şimdi'], textposition: 'top center', textfont: { size: 9, color: '#92400e' },
      showlegend: false, hoverinfo: 'skip', name: '',
    },
  ], {
    title: { text: `📅 Yıllık Trend · ${S?.season || ''} · Zirve: ${(S?.peaks||[]).join(', ')}`,
             font: { size: 11, color: '#374151' }, x: .01 },
    margin: { l: 30, r: 10, t: 36, b: 30 },
    xaxis: { tickfont: { size: 9 }, gridcolor: 'rgba(0,0,0,.04)' },
    yaxis: { range: [0, 105], tickfont: { size: 9 }, gridcolor: 'rgba(0,0,0,.04)' },
    paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
    showlegend: false,
    height: 180,
  }, { displayModeBar: false, responsive: true });
}

// ── Forecast chart ────────────────────────────────────────────────────────────
function renderForecastChart(elId, r) {
  const weeks = r.weekly_forecast || [];
  const labels = weeks.map((_, i) => i === 0 ? 'Bu hafta' : `+${i} hafta`);
  Plotly.newPlot(elId, [{
    x: labels, y: weeks, type: 'scatter', mode: 'lines+markers',
    fill: 'tozeroy', fillcolor: 'rgba(5,150,105,.07)',
    line: { color: '#059669', width: 2 },
    marker: { color: '#059669', size: 5 },
    hovertemplate: '<b>%{x}</b><br>%{y:.1f}<extra></extra>',
  }], {
    title: { text: '📈 6 Haftalık Tahmin', font: { size: 11, color: '#374151' }, x: .01 },
    margin: { l: 30, r: 10, t: 36, b: 30 },
    xaxis: { tickfont: { size: 9 }, gridcolor: 'rgba(0,0,0,.04)' },
    yaxis: { range: [0, 105], tickfont: { size: 9 }, gridcolor: 'rgba(0,0,0,.04)' },
    paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
    height: 180,
  }, { displayModeBar: false, responsive: true });
}

// ── Channel bar chart ─────────────────────────────────────────────────────────
function renderChannelChart(elId, r) {
  const chMap   = META.CHANNEL_MAP;
  const chColor = META.CHANNEL_COLOR;
  const entries = Object.entries(r.channel_recommendations)
    .sort((a, b) => b[1] - a[1]);

  Plotly.newPlot(elId, [{
    type: 'bar', orientation: 'h',
    x: entries.map(([,v]) => v),
    y: entries.map(([k]) => chMap[k] || k),
    marker: { color: entries.map(([k]) => chColor[k] || '#1d4ed8') },
    text: entries.map(([,v]) => v.toFixed(0)),
    textposition: 'outside',
    hovertemplate: '<b>%{y}</b><br>%{x:.1f}<extra></extra>',
  }], {
    title: { text: '📡 Kanal Skoru', font: { size: 11, color: '#374151' }, x: .01 },
    margin: { l: 100, r: 30, t: 36, b: 20 },
    xaxis: { range: [0, 115], tickfont: { size: 9 } },
    yaxis: { tickfont: { size: 9 } },
    paper_bgcolor: 'transparent', plot_bgcolor: 'transparent',
    height: 180,
  }, { displayModeBar: false, responsive: true });
}

// ── Import cards ──────────────────────────────────────────────────────────────
function renderImportCards(results) {
  const container = document.getElementById('import-list');
  if (!results.length) {
    container.innerHTML = '<div class="empty">Bu sektör için ithalat fırsatı bulunamadı.</div>';
    return;
  }

  const cards = results.map(o => {
    const badgeCls = o.opportunity_label.includes('Yüksek') ? 'badge-high'
                   : o.opportunity_label.includes('Orta')   ? 'badge-mid' : 'badge-watch';
    const trendIcon = o.trend_direction === 'rising_fast' ? '🚀'
                    : o.trend_direction === 'rising' ? '📈' : '➡️';
    const trendLabel = o.trend_direction === 'rising_fast' ? 'Hızlı Yükseliş'
                     : o.trend_direction === 'rising' ? 'Yükseliş' : 'Stabil';
    const platforms = (o.foreign_platforms || []).map(p =>
      `<span class="platform-tag">${p}</span>`).join('');

    const demand  = Math.min(100, Math.round(o.demand_score));
    const supply  = Math.min(100, Math.round(o.local_supply_score));
    const gap     = Math.min(100, Math.max(0, Math.round(o.supply_gap)));
    const scorePct = Math.round(o.import_score);

    // 3-segment bar: blue=supply, red=gap, gray=remainder
    const supplyBarPct = supply;
    const gapBarPct    = Math.min(gap, 100 - supply);

    return `<div class="import-card">
      <div class="ic-header">
        <div class="ic-icon">${trendIcon}</div>
        <div class="ic-title-col">
          <div class="ic-name">${o.product_name}</div>
          <div class="ic-sub">${o.subcategory} · <span style="color:#059669;font-weight:600;">${trendLabel}</span></div>
        </div>
        <div class="ic-score-col">
          <span class="import-badge ${badgeCls}">${o.opportunity_label}</span>
          <div class="ic-score">${scorePct}<span class="ic-score-denom">/100</span></div>
        </div>
      </div>

      <div class="ic-stats-row">
        <span>Talep <b>${demand}</b></span>
        <span>Arz <b>${supply}</b></span>
        <span>Açık <b>${gap}</b></span>
      </div>
      <div class="ic-gap-bar">
        <div class="ic-gap-supply" style="width:${supplyBarPct}%"></div>
        <div class="ic-gap-open"   style="width:${gapBarPct}%"></div>
      </div>

      <div class="import-insight">"${o.insight}"</div>

      <div class="ic-meta">~${(o.monthly_searches_tr||0).toLocaleString('tr-TR')} arama · $${o.avg_price_usd} / ₺${(o.avg_price_try||0).toLocaleString('tr-TR')}</div>
      <div class="platforms">${platforms}</div>
    </div>`;
  });

  container.innerHTML = `<div class="import-grid-2col">${cards.join('')}</div>`;
}

// ── Nasıl Çalışır rehberi ─────────────────────────────────────────────────────
let _guideRendered = false;
function renderGuide() {
  if (_guideRendered) return;
  _guideRendered = true;

  document.getElementById('guide-content').innerHTML = `

  <!-- Header -->
  <div class="header" style="margin-bottom:1.2rem;">
    <div class="header-title">📖 Nasıl Çalışır?</div>
    <div class="header-sub">Veri kaynakları · Algoritmalar · Hesaplama mantığı — İşletme diliyle</div>
  </div>

  <!-- 1. Büyük Resim -->
  <div class="guide-section">
    <h2 class="guide-h2">🌐 Büyük Resim</h2>
    <p class="guide-p">TradeTrend, <strong>dört farklı veri kaynağından</strong> her hafta otomatik veri toplayarak bunları tek bir
    <strong>trend skoru</strong> altında birleştirir. Bu skor sayesinde hangi ürünün şu an yükselişte olduğunu,
    nerede satılmasının daha karlı olduğunu, stok riskinin ne kadar yüksek olduğunu ve
    yurt dışından getirilmesi gereken ürün fırsatlarını anlık görebilirsiniz.</p>
    <div class="guide-callout">
      <strong>Temel soru:</strong> "Bu ürünü şu an stoklamalı mıyım?" sorusuna dört farklı açıdan cevap veriyoruz:
      insanlar internette ne arıyor, Trendyol'da ne satıyor, Amazon TR'de ne alınıyor, TikTok'ta ne viral oluyor.
    </div>
  </div>

  <!-- 2. Veri Kaynakları -->
  <div class="guide-section">
    <h2 class="guide-h2">🗂️ Veri Kaynakları (4 Kaynak)</h2>
    <div class="guide-sources">

      <div class="guide-source-card" style="border-top:3px solid #4285f4;">
        <div class="guide-source-title" style="color:#4285f4;">🔵 Google Trends</div>
        <div class="guide-source-freq">Haftalık</div>
        <p class="guide-p">Son 8 haftanın haftalık arama hacmi (0–100 arası). Türkiye geneli ve bölge bazlı ilgi dağılımı.</p>
        <p class="guide-p"><strong>Ne için kullanıyoruz?</strong> Tüketici niyetinin en saf göstergesi.
        "Termos" araması Ekim'de zirve yapıyorsa talep var demektir.</p>
        <div class="guide-src-tag">Ücretsiz API</div>
      </div>

      <div class="guide-source-card" style="border-top:3px solid #f27a1a;">
        <div class="guide-source-title" style="color:#f27a1a;">🟠 Trendyol</div>
        <div class="guide-source-freq">Günlük</div>
        <p class="guide-p">"Çok Satanlar" sayfasından ürün sıralamaları, fiyat, puan ve yorum sayısı. İlk 72 ürün.</p>
        <p class="guide-p"><strong>Ne için kullanıyoruz?</strong> Gerçek satış verisine en yakın gösterge.
        30. sıradan 5. sıraya çıkan ürün ısınıyor demektir.</p>
        <div class="guide-src-tag">Web scraping</div>
      </div>

      <div class="guide-source-card" style="border-top:3px solid #f90;">
        <div class="guide-source-title" style="color:#e07b00;">🟡 Amazon TR</div>
        <div class="guide-source-freq">Günlük</div>
        <p class="guide-p">amazon.com.tr'deki bestseller sıralamaları, yorum sayısı ve ürün puanı. 2019'dan beri TR'de aktif.</p>
        <p class="guide-p"><strong>Ne için kullanıyoruz?</strong> Batı yönelimli alıcı profilini ölçer.
        Trendyol'da olmayan ürünlerin talebini yakalar.</p>
        <div class="guide-src-tag">Web scraping</div>
      </div>

      <div class="guide-source-card" style="border-top:3px solid #fe2c55;">
        <div class="guide-source-title" style="color:#fe2c55;">🔴 TikTok</div>
        <div class="guide-source-freq">Haftalık</div>
        <p class="guide-p">Ürünle ilgili hashtag gönderi sayısı ve haftalık büyüme oranı. Türkiye filtreli.</p>
        <p class="guide-p"><strong>Ne için kullanıyoruz?</strong> TikTok trendleri gerçek satıştan 2–4 hafta
        <em>önce</em> görünür hale gelir — öncü gösterge.</p>
        <div class="guide-src-tag">Creative Center API</div>
      </div>

    </div>
  </div>

  <!-- 3. Composite Skor -->
  <div class="guide-section">
    <h2 class="guide-h2">📊 Trend Skoru Nasıl Hesaplanır?</h2>
    <p class="guide-p">Her ürün için <strong>dört ayrı kaynak skoru</strong> hesaplanır, sonra ağırlıklı olarak birleştirilir:</p>
    <div class="guide-formula">
      Trend Skoru = (Google × 0.25) + (Trendyol × 0.35) + (Amazon TR × 0.25) + (TikTok × 0.15)
    </div>
    <div class="guide-weight-table">
      <div class="gwt-row gwt-header">
        <span>Kaynak</span><span>Ağırlık</span><span>Neden?</span>
      </div>
      <div class="gwt-row">
        <span>🟠 Trendyol</span><span class="gwt-badge" style="background:rgba(242,122,26,.15);color:#9a4700;">%35</span>
        <span>Türkiye'nin en büyük e-ticaret sitesi; gerçek satış sinyali en güvenilir kaynak.</span>
      </div>
      <div class="gwt-row">
        <span>🔵 Google</span><span class="gwt-badge" style="background:rgba(66,133,244,.12);color:#1a4a9a;">%25</span>
        <span>Arama niyeti önemli, ama her arama alışverişe dönüşmez.</span>
      </div>
      <div class="gwt-row">
        <span>🟡 Amazon TR</span><span class="gwt-badge" style="background:rgba(255,153,0,.12);color:#7a4e00;">%25</span>
        <span>Özellikle teknoloji ve genel ürünlerde bağımsız talep sinyali verir.</span>
      </div>
      <div class="gwt-row">
        <span>🔴 TikTok</span><span class="gwt-badge" style="background:rgba(254,44,85,.1);color:#9a001f;">%15</span>
        <span>Öncü gösterge; viral bir video kısa ömürlü de olabilir.</span>
      </div>
    </div>

    <div class="guide-expanders">
      <details class="guide-details">
        <summary>Google Skoru nasıl hesaplanıyor?</summary>
        <div class="guide-details-body">
          <p>Ham Google Trends değeri 0–100 arasındadır. Buna ek olarak <strong>momentum</strong> hesaplanır:</p>
          <div class="guide-code">Momentum etkisi = trend_değişim_yüzdesi × 0.4   (max ±20 puan)
Google Skoru    = ham_skor + momentum_etkisi       (0–100 sınırlandırılır)</div>
          <p><strong>Örnek:</strong> "Termos" geçen hafta 72 puan, +%28.5 büyüme →
          Momentum = 28.5 × 0.4 = <strong>11.4</strong> → Google Skoru = <strong>83.4</strong></p>
        </div>
      </details>

      <details class="guide-details">
        <summary>Trendyol & Amazon TR Skoru nasıl hesaplanıyor?</summary>
        <div class="guide-details-body">
          <p>Her iki platform için aynı formül kullanılır:</p>
          <table class="guide-table">
            <tr><th>Bileşen</th><th>Ağırlık</th><th>Açıklama</th></tr>
            <tr><td>Sıralama skoru</td><td>%55</td><td>1. sıra = 100 puan, log ölçekli düşüş</td></tr>
            <tr><td>Sıralama değişimi</td><td>Doğrudan ±15 puan</td><td>Önceki haftaya göre iyileşme/kötüleşme</td></tr>
            <tr><td>Sosyal kanıt (yorum)</td><td>%30</td><td>Log ölçekli, max 20 puan</td></tr>
            <tr><td>Puan bonusu</td><td>%15</td><td>5 üzerinden derecelendirme, max 10 puan</td></tr>
          </table>
          <div class="guide-code">Sıralama Skoru = max(0, 100 − log10(sıra) × 50)
→ 1. sıra = 100 puan · 10. sıra ≈ 50 puan · 100. sıra ≈ 0 puan</div>
        </div>
      </details>

      <details class="guide-details">
        <summary>TikTok Skoru nasıl hesaplanıyor?</summary>
        <div class="guide-details-body">
          <p>Hashtag gönderi sayısı logaritmik ölçekle normalize edilir:</p>
          <div class="guide-code">TikTok Skoru = min(100, (log10(gönderi_sayısı) / 7) × 100)
10 gönderi → ~14 puan  ·  10.000 → ~57 puan  ·  10.000.000 → 100 puan</div>
          <p><strong>Neden log ölçek?</strong> "Termos" ile "Study" arasındaki 100×'lik gönderi farkını doğrudan kullansak,
          büyük kategoriler küçükleri ezer. Log ölçek bu farkı makul bir aralığa çeker.</p>
        </div>
      </details>
    </div>
  </div>

  <!-- 4. Risk -->
  <div class="guide-section">
    <h2 class="guide-h2">⚠️ Risk Seviyesi Nedir?</h2>
    <div class="guide-risk-row">
      <div class="guide-risk-card" style="border-color:#059669;background:rgba(5,150,105,.06);">
        <div style="font-size:1.4rem;margin-bottom:.4rem;">🟢</div>
        <strong style="color:#065f46;">Düşük Risk — Skor ≥ 60</strong>
        <p>Hem aranıyor hem satılıyor hem de sosyal medyada gündemde. Stoğa almak için güvenli bölge.</p>
      </div>
      <div class="guide-risk-card" style="border-color:#d97706;background:rgba(217,119,6,.06);">
        <div style="font-size:1.4rem;margin-bottom:.4rem;">🟡</div>
        <strong style="color:#92400e;">Orta Risk — Skor 35–59</strong>
        <p>Belirli sinyaller var ama tüm kanallar aynı fikirde değil. Küçük miktarda deneme yapılabilir.</p>
      </div>
      <div class="guide-risk-card" style="border-color:#dc2626;background:rgba(220,38,38,.06);">
        <div style="font-size:1.4rem;margin-bottom:.4rem;">🔴</div>
        <strong style="color:#991b1b;">Yüksek Risk — Skor &lt; 35</strong>
        <p>Sinyaller zayıf veya düşüşte. Stok yapmaktan kaçının ya da mevcut stoku eritin.</p>
      </div>
    </div>
    <div class="guide-info">💡 Risk seviyesi <em>talep riskini</em> ölçer, ürün kalitesiyle ilgisi yoktur.</div>
  </div>

  <!-- 5. Kanal -->
  <div class="guide-section">
    <h2 class="guide-h2">📡 Kanal Önerisi Nasıl Belirleniyor?</h2>
    <p class="guide-p">Her satış kanalı için <strong>farklı kaynak ağırlıkları</strong> kullanılır:</p>
    <table class="guide-table">
      <tr><th>Kaynak</th><th>Trendyol</th><th>Amazon TR</th><th>Instagram</th><th>Fiz. Mağaza</th></tr>
      <tr><td>Google Trends</td><td>%20</td><td>%20</td><td>%25</td><td>%35</td></tr>
      <tr><td>Trendyol</td><td><strong>%50</strong></td><td>%20</td><td>%15</td><td>%25</td></tr>
      <tr><td>Amazon TR</td><td>%20</td><td><strong>%50</strong></td><td>%15</td><td>%15</td></tr>
      <tr><td>TikTok</td><td>%10</td><td>%10</td><td><strong>%45</strong></td><td>%25</td></tr>
    </table>
    <ul class="guide-list">
      <li><strong>Trendyol / Amazon TR</strong> → Platform satış verisi kritik. Zaten orada satıyorsa oraya koy.</li>
      <li><strong>Instagram</strong> → TikTok trendi kritik (%45). Viral olan ürünler Instagram'da da tutar.</li>
      <li><strong>Fiziksel Mağaza</strong> → Google aramaları belirleyici (%35). İnsanlar yakın mağazayı ararken Google kullanır.</li>
    </ul>
  </div>

  <!-- 6. Bölge -->
  <div class="guide-section">
    <h2 class="guide-h2">🗺️ Bölge Seçimi Skoru Nasıl Etkiler?</h2>
    <p class="guide-p">Türkiye <strong>7 coğrafi bölge</strong> olarak modellenmiştir. Her bölge için <strong>üç katmanlı</strong> bir düzeltme uygulanır:</p>
    <ol class="guide-list">
      <li><strong>Kanal bias</strong> — Bölgenin online/fiziksel mağaza eğilimi kanal skorlarını değiştirir</li>
      <li><strong>E-ticaret penetrasyonu</strong> — Bölgenin genel dijital olgunluğu composite skora eklenir</li>
      <li><strong>Sektör uyumu</strong> — Bölgenin o sektöre özgü talebi ek skor düzeltmesiyle yansıtılır</li>
    </ol>

    <h3 class="guide-h3">📡 Kanal Tercihi (online vs. fiziksel)</h3>
    <div style="overflow-x:auto;">
      <table class="guide-table">
        <tr><th>Bölge</th><th>Trendyol</th><th>Amazon TR</th><th>Instagram</th><th>Fiz. Mağaza</th></tr>
        <tr><td>🌆 Marmara</td><td>+7</td><td>+8</td><td>+10</td><td>-5</td></tr>
        <tr><td>🌊 Ege</td><td>+4</td><td>+4</td><td>+8</td><td>-2</td></tr>
        <tr><td>☀️ Akdeniz</td><td>+2</td><td>+2</td><td>+5</td><td>+2</td></tr>
        <tr><td>🏛️ İç Anadolu</td><td>+2</td><td>+2</td><td>+3</td><td>+3</td></tr>
        <tr><td>🌿 Karadeniz</td><td>-2</td><td>-2</td><td>+1</td><td>+6</td></tr>
        <tr><td>🏔️ Doğu Anadolu</td><td>-4</td><td>-4</td><td>-2</td><td>+9</td></tr>
        <tr><td>🌾 G.doğu Anadolu</td><td>-3</td><td>-4</td><td>-1</td><td>+9</td></tr>
      </table>
    </div>

    <h3 class="guide-h3">🏭 Sektör Uyumu (bölgenin güçlü/zayıf kategorileri)</h3>
    <div style="overflow-x:auto;">
      <table class="guide-table">
        <tr><th>Bölge</th><th>Giyim</th><th>Elektronik</th><th>Kozmetik</th><th>Spor</th><th>Gıda</th><th>Ev&Yaşam</th></tr>
        <tr><td>🌆 Marmara</td><td>+12</td><td>+10</td><td>+10</td><td>+3</td><td>+2</td><td>+4</td></tr>
        <tr><td>🌊 Ege</td><td>+8</td><td>+2</td><td>+8</td><td>+12</td><td>+8</td><td>+6</td></tr>
        <tr><td>☀️ Akdeniz</td><td>+6</td><td>0</td><td>+4</td><td>+14</td><td>+8</td><td>+5</td></tr>
        <tr><td>🏛️ İç Anadolu</td><td>+2</td><td>+2</td><td>+2</td><td>+4</td><td>+8</td><td>+7</td></tr>
        <tr><td>🌿 Karadeniz</td><td>-2</td><td>-5</td><td>-3</td><td>+12</td><td>+14</td><td>+8</td></tr>
        <tr><td>🏔️ Doğu Anadolu</td><td>-4</td><td>-10</td><td>-6</td><td>+10</td><td>+10</td><td>+6</td></tr>
        <tr><td>🌾 G.doğu Anadolu</td><td>-3</td><td>-8</td><td>-4</td><td>+8</td><td>+12</td><td>+6</td></tr>
      </table>
    </div>

    <ul class="guide-list" style="margin-top:.8rem;">
      <li>🌆 <strong>Marmara</strong> — E-ticaret en olgun, Instagram alışverişi güçlü. Giyim & kozmetik trendi hızlı yayılır.</li>
      <li>🌿 <strong>Karadeniz</strong> — Gıda & spor talebi yüksek (yaylacılık, çay kültürü). Online penetrasyon düşük.</li>
      <li>🏔️ <strong>Doğu Anadolu</strong> — Fiziksel mağaza baskın. Elektronik/kozmetik trend takibi zayıf; spor & gıda güçlü.</li>
      <li>☀️ <strong>Akdeniz</strong> — Turizm etkisiyle outdoor & spor zirvede, mevsimsel dalgalanma belirgin.</li>
    </ul>
  </div>

  <!-- 7. Alt Kategori -->
  <div class="guide-section">
    <h2 class="guide-h2">🔽 Alt Kategori Filtresi Nasıl Çalışır?</h2>
    <p class="guide-p">Her sektör için <strong>3 seviyeli hiyerarşi</strong> tanımlanmıştır. "Tümü" seçildiğinde tüm alt kategorilerdeki
    ürünler tek listede birleştirilir ve puanlanır. Belirli bir alt kategori seçildiğinde yalnızca
    o segmentteki ürünler analiz edilir.</p>
    <table class="guide-table">
      <tr><th>Ana Kategori</th><th>Alt Kategori</th><th>Örnek Ürünler</th></tr>
      <tr><td rowspan="4">Yazı Gereçleri</td><td>Tükenmez & Roller Kalem</td><td>Pilot G2, Uni-ball, Silinebilir Kalem</td></tr>
      <tr><td>Marker & Fine Liner</td><td>Copic, Staedtler, Mildliner</td></tr>
      <tr><td>Kaligrafi & Brush Pen</td><td>Tombow, Brush Pen Set</td></tr>
      <tr><td>Dolma Kalem & Mürekkep</td><td>Lamy Safari, Pilot Metropolitan</td></tr>
    </table>
    <div class="guide-info">Bu sayede "Kırtasiye'de ne satayım?" yerine "Kırtasiye'nin kaligrafi segmentinde trend ne?" sorusunu yanıtlayabilirsiniz.</div>
  </div>

  <!-- 8. İthalat -->
  <div class="guide-section">
    <h2 class="guide-h2">🚢 İthalat Fırsatları Nasıl Hesaplanıyor?</h2>
    <p class="guide-p"><strong>İthalat Fırsatı Analizi</strong> üç temel soruyu yanıtlar:</p>
    <ol class="guide-list">
      <li>Türk tüketiciler bu ürünü gerçekten istiyor mu? <em>(Talep skoru)</em></li>
      <li>Bu ürünü yerel piyasada bulmak kolay mı? <em>(Yerli arz skoru)</em></li>
      <li>Fark ne kadar büyük? <em>(Arz açığı)</em></li>
    </ol>
    <div class="guide-formula">
      İthalat Fırsat Skoru = (Talep Skoru × 0.55) + (Arz Açığı × 0.45)
      Arz Açığı = max(0, Talep Skoru − Yerli Arz Skoru)
    </div>
    <div class="guide-two-col">
      <div>
        <strong>Talep Skoru nasıl ölçülüyor?</strong>
        <ul class="guide-list">
          <li>Google TR aramaları (aylık hacim ve büyüme oranı)</li>
          <li>TikTok TR hashtag aktivitesi</li>
          <li>Amazon TR ve Trendyol'da yabancı ürün listelerinin dönüşüm sinyali</li>
        </ul>
      </div>
      <div>
        <strong>Yerli Arz Skoru nasıl ölçülüyor?</strong>
        <ul class="guide-list">
          <li>Trendyol'da yerli üretici sayısı ve stok derinliği</li>
          <li>Fiyat rekabeti (yüksek fiyat = arz az)</li>
          <li>Ürün çeşitliliği</li>
        </ul>
      </div>
    </div>
    <div class="guide-risk-row" style="margin-top:.8rem;">
      <div class="guide-risk-card" style="border-color:#059669;background:rgba(5,150,105,.06);">
        <strong style="color:#065f46;">🟢 Yüksek Fırsat ≥ 70</strong>
        <p>Talep yüksek, yerli arz yetersiz — harekete geçme zamanı</p>
      </div>
      <div class="guide-risk-card" style="border-color:#d97706;background:rgba(217,119,6,.06);">
        <strong style="color:#92400e;">🟡 Orta Fırsat 50–69</strong>
        <p>Fırsat var ama rekabet var — araştırma gerekli</p>
      </div>
      <div class="guide-risk-card" style="border-color:#9ca3af;background:rgba(156,163,175,.06);">
        <strong style="color:#374151;">⚪ Takipte &lt; 50</strong>
        <p>Henüz olgunlaşmamış — 3–6 ay izle</p>
      </div>
    </div>
  </div>

  <!-- 9. Haftalık Tahmin -->
  <div class="guide-section">
    <h2 class="guide-h2">📈 6 Haftalık Talep Tahmini</h2>
    <div class="guide-formula">
      Sonraki_Hafta = Önceki + (Momentum × 0.8^hafta) + Ortalamaya_Çekim
      Ortalamaya_Çekim = (50 − Mevcut) × 0.05
    </div>
    <p class="guide-p">Yükselen ürünler kısa vadede yükselmeye devam eder, ancak her hafta bu ivme <strong>%20 zayıflar</strong>.
    Uzak haftalar daha belirsizdir — tahmin ufku 6 haftayla sınırlandırılmıştır.</p>
  </div>

  <!-- 10. Sınırlamalar -->
  <div class="guide-section">
    <h2 class="guide-h2">🚧 Sistemin Sınırlamaları ve Güçlü Yönleri</h2>
    <div class="guide-two-col">
      <div>
        <strong style="color:#dc2626;">⚠️ Dikkat edilmesi gerekenler:</strong>
        <ul class="guide-list" style="margin-top:.4rem;">
          <li>Google Trends görece ilgiyi ölçer, gerçek satış adedini değil</li>
          <li>Trendyol/Amazon scraping sitelerin HTML yapısı değişince etkilenebilir</li>
          <li>TikTok trendleri çok hızlı yükselir, çok hızlı düşer (flash trend riski)</li>
          <li>Fiyat rekabeti ve kargo maliyetleri modele dahil değil</li>
          <li>İthalat fırsat skorları gösterge niteliğinde; gümrük ve lojistik ayrıca hesaplanmalı</li>
        </ul>
      </div>
      <div>
        <strong style="color:#059669;">✅ Güçlü olduğu durumlar:</strong>
        <ul class="guide-list" style="margin-top:.4rem;">
          <li>Yeni sektöre girerken hangi ürünlerden başlanacağını belirlemek</li>
          <li>Mevcut ürünlerin trend durumunu haftalık takip etmek</li>
          <li>Rakiplerin öne çıkardığı kategorileri erken fark etmek</li>
          <li>Hangi kanalda reklam bütçesi harcanacağına karar vermek</li>
          <li>Stoğa ne kadar yatırım yapılacağına referans oluşturmak</li>
          <li>Yurt dışından getirilmesi gereken ürünleri sistematik tespit etmek</li>
        </ul>
      </div>
    </div>
  </div>

  <div style="text-align:center;color:#9ca3af;font-size:.78rem;padding:1.5rem 0 .5rem;">
    TradeTrend v1.0 — Google Trends · Trendyol · Amazon TR · TikTok · İthalat Analizi
  </div>`;
}

// ── Init ──────────────────────────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', boot);
