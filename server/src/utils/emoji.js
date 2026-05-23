'use strict';

const EMOJI_KW  = require('../../data/emoji_kw.json');
const { SECTOR_EMOJI } = require('../../data/constants.json');

function getProductEmoji(productName, subcat = '', sector = '') {
  const low = (productName + ' ' + subcat).toLowerCase();
  for (const { keywords, emoji } of EMOJI_KW) {
    if (keywords.some(k => low.includes(k))) return emoji;
  }
  return SECTOR_EMOJI[sector] || '📦';
}

module.exports = { getProductEmoji };
