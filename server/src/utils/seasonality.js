'use strict';

const {
  SEASONALITY_PATTERNS,
  PRODUCT_PATTERN,
  SUBCAT_PATTERN,
  SECTOR_PATTERN,
  SEASON_KEYWORD_RULES,
} = require('../../data/seasonality.json');

function getSeasonality(productName, subcat = '', sector = '') {
  // 1. Exact product name
  let key = PRODUCT_PATTERN[productName];

  // 2. Keyword on product name
  if (!key) {
    const lowP = productName.toLowerCase();
    for (const { keywords, pattern } of SEASON_KEYWORD_RULES) {
      if (keywords.some(k => lowP.includes(k))) { key = pattern; break; }
    }
  }

  // 3. Exact subcat
  if (!key) key = SUBCAT_PATTERN[subcat];

  // 4. Keyword on subcat
  if (!key) {
    const lowS = subcat.toLowerCase();
    for (const { keywords, pattern } of SEASON_KEYWORD_RULES) {
      if (keywords.some(k => lowS.includes(k))) { key = pattern; break; }
    }
  }

  // 5. Sector fallback
  if (!key) key = SECTOR_PATTERN[sector] || 'evergreen';

  return SEASONALITY_PATTERNS[key] || SEASONALITY_PATTERNS.evergreen;
}

module.exports = { getSeasonality, SEASONALITY_PATTERNS };
