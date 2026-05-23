'use strict';

const express = require('express');
const router  = express.Router();
const IMPORT_DATA = require('../../data/imports.json');

// GET /api/imports?sector=xxx&min_score=65
router.get('/', (req, res) => {
  const { sector = 'kirtasiye', min_score = 0 } = req.query;
  const minScore = parseFloat(min_score) || 0;
  const all  = IMPORT_DATA[sector] || [];
  const data = all
    .filter(o => o.import_score >= minScore)
    .sort((a, b) => b.import_score - a.import_score);
  res.json({ sector, results: data, total: data.length });
});

module.exports = router;
