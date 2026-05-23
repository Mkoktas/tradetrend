'use strict';

const express = require('express');
const router  = express.Router();

const { rankProducts }  = require('../engine/scorer');
const { getProductEmoji } = require('../utils/emoji');
const { getSeasonality }  = require('../utils/seasonality');

const SECTORS_DATA = require('../../data/sectors.json');
const {
  REGION_CHANNEL_BIAS,
  REGION_BASE_SCORE_DELTA,
  REGION_SECTOR_AFFINITY,
} = require('../../data/regions.json');

// ─── Helpers ─────────────────────────────────────────────────────────────────

function collectProducts(node) {
  if (!node) return [];
  if (Array.isArray(node)) return node;
  return Object.entries(node)
    .filter(([k]) => k !== 'Tümü')
    .flatMap(([, v]) => collectProducts(v));
}

function getFilteredProducts(sectorKey, anaCat, altCat) {
  const sector = SECTORS_DATA[sectorKey];
  if (!sector) return [];
  if (!anaCat || anaCat === 'Tümü') return collectProducts(sector);
  const anaNode = sector[anaCat];
  if (!anaNode) return [];
  if (!altCat || altCat === 'Tümü') return collectProducts(anaNode);
  return collectProducts(anaNode[altCat]) ;
}

function productSubcatMap(sectorKey) {
  const map = {};
  const sector = SECTORS_DATA[sectorKey];
  if (!sector) return map;
  for (const [anaK, anaV] of Object.entries(sector)) {
    if (anaK === 'Tümü' || typeof anaV !== 'object' || Array.isArray(anaV)) continue;
    for (const [altK, altV] of Object.entries(anaV)) {
      if (altK === 'Tümü' || !Array.isArray(altV)) continue;
      for (const sig of altV) map[sig.name] = altK;
    }
  }
  return map;
}

const clamp  = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const round1 = v => Math.round(v * 10) / 10;

// ─── POST /api/trends ─────────────────────────────────────────────────────────
// Body: { sector, anaCat, altCat, region, channels[] }
router.post('/', (req, res) => {
  const { sector = 'kirtasiye', anaCat = 'Tümü', altCat = 'Tümü',
          region = 'Tüm Türkiye', channels = [] } = req.body;

  const signals = getFilteredProducts(sector, anaCat, altCat);
  if (!signals.length) return res.json({ results: [], meta: { sector, region } });

  let data = rankProducts(signals);

  // 1. Regional channel bias
  const chBias = REGION_CHANNEL_BIAS[region] || REGION_CHANNEL_BIAS['Tüm Türkiye'] || {};
  for (const item of data) {
    for (const [ch, delta] of Object.entries(chBias)) {
      if (ch in item.channel_recommendations) {
        item.channel_recommendations[ch] = round1(clamp(item.channel_recommendations[ch] + delta, 0, 100));
      }
    }
    item.best_channel = Object.entries(item.channel_recommendations)
      .sort((a, b) => b[1] - a[1])[0][0];
  }

  // 2. Score delta (base + sector affinity)
  const baseDelta   = REGION_BASE_SCORE_DELTA[region] || 0;
  const sectorDelta = (REGION_SECTOR_AFFINITY[region] || {})[sector] || 0;
  const scoreDelta  = baseDelta + sectorDelta;
  if (scoreDelta !== 0) {
    for (const item of data) {
      item.composite_score = round1(clamp(item.composite_score + scoreDelta, 0, 100));
      item.google_score    = round1(clamp(item.google_score + scoreDelta * 0.5, 0, 100));
    }
    data.sort((a, b) => b.composite_score - a.composite_score);
  }

  // 3. Channel filter
  if (channels.length) {
    for (const item of data) {
      item.channel_recommendations = Object.fromEntries(
        Object.entries(item.channel_recommendations).filter(([k]) => channels.includes(k))
      );
      if (Object.keys(item.channel_recommendations).length) {
        item.best_channel = Object.entries(item.channel_recommendations)
          .sort((a, b) => b[1] - a[1])[0][0];
      }
    }
  }

  // 4. Enrich with emoji + seasonality
  const subcatMap = productSubcatMap(sector);
  for (const item of data) {
    const sub = subcatMap[item.product_name] || altCat;
    item.emoji      = getProductEmoji(item.product_name, sub, sector);
    item.subcat     = sub;
    item.seasonality = getSeasonality(item.product_name, sub, sector);
  }

  res.json({ results: data, meta: { sector, anaCat, altCat, region, total: data.length } });
});

// ─── GET /api/trends/categories?sector=xxx ───────────────────────────────────
router.get('/categories', (req, res) => {
  const { sector = 'kirtasiye' } = req.query;
  const node = SECTORS_DATA[sector];
  if (!node) return res.json({ ana: [], alt: {} });

  const ana = Object.keys(node);
  const alt = {};
  for (const [k, v] of Object.entries(node)) {
    if (k === 'Tümü' || typeof v !== 'object' || Array.isArray(v)) continue;
    alt[k] = Object.keys(v);
  }
  res.json({ ana, alt });
});

module.exports = router;
