'use strict';

// ─── Ağırlıklar ──────────────────────────────────────────────────────────────
const WEIGHTS = { google: 0.25, trendyol: 0.35, amazon: 0.25, tiktok: 0.15 };

const CHANNEL_WEIGHTS = {
  trendyol:  { google: 0.20, trendyol: 0.50, amazon: 0.20, tiktok: 0.10 },
  amazon_tr: { google: 0.20, trendyol: 0.20, amazon: 0.50, tiktok: 0.10 },
  instagram: { google: 0.25, trendyol: 0.15, amazon: 0.15, tiktok: 0.45 },
  store:     { google: 0.35, trendyol: 0.25, amazon: 0.15, tiktok: 0.25 },
};

const RISK_THRESHOLDS = { low: 60, medium: 35 };

// ─── Helpers ─────────────────────────────────────────────────────────────────
const clamp  = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const round1 = v => Math.round(v * 10) / 10;

function mondayOf(d = new Date()) {
  const day = d.getDay();            // 0=Sun
  const diff = (day === 0) ? -6 : 1 - day;
  const m = new Date(d);
  m.setDate(d.getDate() + diff);
  return m.toISOString().slice(0, 10);
}

// ─── Score calculations (ported 1-to-1 from scorer.py) ───────────────────────

function googleScore(sig) {
  const base     = sig.google_trend_score;
  const momentum = clamp(sig.google_trend_change_pct * 0.4, -20, 20);
  return clamp(base + momentum, 0, 100);
}

function trendyolScore(sig) {
  const rank = sig.trendyol_sales_rank;
  const rankScore = (rank <= 0 || rank >= 999) ? 0 : Math.max(0, 100 - Math.log10(rank) * 50);
  const rankChg   = clamp(sig.trendyol_rank_change * 0.5, -15, 15);
  const reviews   = Math.min(20, Math.log10(Math.max(sig.trendyol_review_count, 1)) * 5);
  const rating    = sig.trendyol_rating > 0 ? (sig.trendyol_rating / 5) * 10 : 0;
  return clamp(rankScore * 0.55 + rankChg + reviews * 0.30 + rating * 0.15, 0, 100);
}

function amazonScore(sig) {
  const rank = sig.amazon_sales_rank;
  const rankScore = (rank <= 0 || rank >= 999) ? 0 : Math.max(0, 100 - Math.log10(rank) * 50);
  const rankChg   = clamp(sig.amazon_rank_change * 0.5, -15, 15);
  const reviews   = Math.min(20, Math.log10(Math.max(sig.amazon_review_count, 1)) * 5);
  const rating    = sig.amazon_rating > 0 ? (sig.amazon_rating / 5) * 10 : 0;
  return clamp(rankScore * 0.55 + rankChg + reviews * 0.30 + rating * 0.15, 0, 100);
}

function tiktokScore(sig) {
  return clamp(sig.tiktok_trend_score, 0, 100);
}

function compositeScore(g, t, a, tk) {
  return g * WEIGHTS.google + t * WEIGHTS.trendyol + a * WEIGHTS.amazon + tk * WEIGHTS.tiktok;
}

function riskLevel(composite) {
  if (composite >= RISK_THRESHOLDS.low)    return { level: 'low',    emoji: '🟢' };
  if (composite >= RISK_THRESHOLDS.medium) return { level: 'medium', emoji: '🟡' };
  return                                          { level: 'high',   emoji: '🔴' };
}

function channelRecommendations(g, t, a, tk) {
  const scores = { google: g, trendyol: t, amazon: a, tiktok: tk };
  const result = {};
  for (const [ch, wts] of Object.entries(CHANNEL_WEIGHTS)) {
    result[ch] = round1(
      Object.entries(wts).reduce((sum, [src, w]) => sum + scores[src] * w, 0)
    );
  }
  return result;
}

function weeklyForecast(composite, trendChange, weeks = 6) {
  const fc = [composite];
  const weekly = trendChange * 0.05;
  for (let i = 1; i < weeks; i++) {
    let nv = fc[fc.length - 1] + weekly * Math.pow(0.8, i);
    nv = clamp(nv + (50 - nv) * 0.05, 0, 100);
    fc.push(round1(nv));
  }
  return fc;
}

// ─── Main scorer ─────────────────────────────────────────────────────────────

function scoreProduct(sig) {
  const g  = googleScore(sig);
  const t  = trendyolScore(sig);
  const a  = amazonScore(sig);
  const tk = tiktokScore(sig);
  const comp = compositeScore(g, t, a, tk);
  const risk = riskLevel(comp);
  const channels = channelRecommendations(g, t, a, tk);
  const bestCh   = Object.entries(channels).sort((x, y) => y[1] - x[1])[0][0];
  return {
    product_name:            sig.name,
    google_score:            round1(g),
    trendyol_score:          round1(t),
    amazon_score:            round1(a),
    tiktok_score:            round1(tk),
    composite_score:         round1(comp),
    risk_level:              risk.level,
    risk_emoji:              risk.emoji,
    channel_recommendations: channels,
    best_channel:            bestCh,
    weekly_forecast:         weeklyForecast(comp, sig.google_trend_change_pct),
    week_start:              mondayOf(),
  };
}

function rankProducts(signals) {
  return signals.map(scoreProduct).sort((a, b) => b.composite_score - a.composite_score);
}

module.exports = { scoreProduct, rankProducts };
