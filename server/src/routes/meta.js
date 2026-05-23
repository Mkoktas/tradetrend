'use strict';

const express  = require('express');
const router   = express.Router();
const constants  = require('../../data/constants.json');
const regions    = require('../../data/regions.json');
const seasonData = require('../../data/seasonality.json');

// GET /api/meta — all constants the frontend needs to boot
router.get('/', (req, res) => {
  res.json({
    SECTORS:                  constants.SECTORS,
    SECTOR_EMOJI:             constants.SECTOR_EMOJI,
    SECTOR_GRAD:              constants.SECTOR_GRAD,
    RISK_COLORS:              constants.RISK_COLORS,
    RISK_LABELS:              constants.RISK_LABELS,
    CHANNEL_MAP:              constants.CHANNEL_MAP,
    CHANNEL_COLOR:            constants.CHANNEL_COLOR,
    SIDEBAR_TO_KEY:           constants.SIDEBAR_TO_KEY,
    REGIONS:                  regions.REGIONS,
    REGION_META:              regions.REGION_META,
    REGION_BASE_SCORE_DELTA:  regions.REGION_BASE_SCORE_DELTA,
    REGION_SECTOR_AFFINITY:   regions.REGION_SECTOR_AFFINITY,
    SALES_CHANNELS:           regions.SALES_CHANNELS,
    MONTHS_TR:                seasonData.MONTHS_TR,
    MONTHS_FULL:              seasonData.MONTHS_FULL,
    SEASONALITY_PATTERNS:     seasonData.SEASONALITY_PATTERNS,
  });
});

module.exports = router;
