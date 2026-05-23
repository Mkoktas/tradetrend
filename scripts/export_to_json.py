"""
Export Python data structures to JSON for Node.js migration.
Mocks all heavy imports (streamlit, plotly, pandas) so we can exec the app.
"""

import sys, os, json, types
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

OUT_DIR = os.path.join(ROOT, "server", "data")
os.makedirs(OUT_DIR, exist_ok=True)

# ─── Mock heavy dependencies ─────────────────────────────────────────────────

def _make_mock(name):
    m = types.ModuleType(name)
    m.__getattr__ = lambda self, k: _make_mock(f"{name}.{k}")
    return m

class _Anything:
    def __init__(self, *a, **kw): pass
    def __call__(self, *a, **kw): return _Anything()
    def __getattr__(self, k): return _Anything()
    def __iter__(self): return iter([])
    def __enter__(self): return self
    def __exit__(self, *a): pass

class _StreamlitMock:
    cache_data   = staticmethod(lambda f=None, **kw: (lambda g: g)(f) if f else (lambda g: g))
    set_page_config = staticmethod(lambda **kw: None)
    markdown     = staticmethod(lambda *a, **kw: None)
    columns      = staticmethod(lambda *a, **kw: [_Anything()])
    expander     = staticmethod(lambda *a, **kw: _Anything())
    metric       = staticmethod(lambda *a, **kw: None)
    plotly_chart = staticmethod(lambda *a, **kw: None)
    selectbox    = staticmethod(lambda *a, **kw: 0)
    multiselect  = staticmethod(lambda *a, **kw: [])
    checkbox     = staticmethod(lambda *a, **kw: False)
    button       = staticmethod(lambda *a, **kw: False)
    sidebar      = _Anything()
    session_state = {}
    def __getattr__(self, k): return _Anything()

_st_mod = types.ModuleType("streamlit")
_st_mod.__dict__.update(_StreamlitMock.__dict__)
_st_mod.sidebar = _Anything()
_st_mod.session_state = {}

_plotly = types.ModuleType("plotly")
_plotly_go = types.ModuleType("plotly.graph_objects")
for name in ["Figure","Bar","Pie","Scatter","Indicator","Barpolar"]:
    setattr(_plotly_go, name, _Anything)
_plotly.graph_objects = _plotly_go

_pd = types.ModuleType("pandas")
_pd.DataFrame = _Anything

sys.modules["streamlit"]              = _st_mod
sys.modules["plotly"]                 = _plotly
sys.modules["plotly.graph_objects"]   = _plotly_go
sys.modules["pandas"]                 = _pd

# ─── Exec the app file ───────────────────────────────────────────────────────

with open(os.path.join(ROOT, "dashboard", "streamlit_app.py"), encoding="utf-8") as f:
    source = f.read()

NS = {
    "__builtins__": __builtins__,
    "__name__":     "__app__",
    "__file__":     os.path.join(ROOT, "dashboard", "streamlit_app.py"),
}
try:
    exec(compile(source, "streamlit_app.py", "exec"), NS)
except SystemExit:
    pass
except Exception as e:
    # Some UI-only errors are expected; data structures should already be set
    print(f"  (exec stopped at: {e.__class__.__name__}: {e})")

# ─── Verify we got the data ──────────────────────────────────────────────────

required = ["SECTOR_SUBCATEGORIES", "REGIONS", "REGION_CHANNEL_BIAS",
            "SEASONALITY_PATTERNS", "SECTORS", "_EMOJI_KW", "IMPORT_DATA"]
# Load IMPORT_DATA from import_analyzer (not exec'd from streamlit_app.py)
from trend_engine.import_analyzer import IMPORT_DATA as _IMPORT_DATA
NS["IMPORT_DATA"] = _IMPORT_DATA

missing = [k for k in required if k not in NS]
if missing:
    print(f"WARNING -- missing keys: {missing}")

# ─── Serializers ─────────────────────────────────────────────────────────────

def sig_to_dict(sig):
    return {
        "name": sig.name,
        "google_trend_score": sig.google_trend_score,
        "google_trend_change_pct": sig.google_trend_change_pct,
        "trendyol_sales_rank": sig.trendyol_sales_rank,
        "trendyol_rank_change": sig.trendyol_rank_change,
        "trendyol_review_count": sig.trendyol_review_count,
        "trendyol_rating": sig.trendyol_rating,
        "amazon_sales_rank": sig.amazon_sales_rank,
        "amazon_rank_change": sig.amazon_rank_change,
        "amazon_review_count": sig.amazon_review_count,
        "amazon_rating": sig.amazon_rating,
        "tiktok_trend_score": sig.tiktok_trend_score,
    }

def serialize_node(node):
    if node is None:
        return None
    if isinstance(node, list):
        return [sig_to_dict(s) for s in node]
    if isinstance(node, dict):
        return {k: serialize_node(v) for k, v in node.items()}
    return node

def imp_to_dict(o):
    return {
        "product_name": o.product_name,
        "subcategory": o.subcategory,
        "demand_score": o.demand_score,
        "local_supply_score": o.local_supply_score,
        "supply_gap": round(max(0.0, o.demand_score - o.local_supply_score), 1),
        "import_score": o.import_score,
        "monthly_searches_tr": o.monthly_searches_tr,
        "foreign_platforms": o.foreign_platforms,
        "avg_price_usd": o.avg_price_usd,
        "avg_price_try": o.avg_price_try,
        "trend_direction": o.trend_direction,
        "opportunity_label": o.opportunity_label,
        "insight": o.insight,
    }

def save(name, data):
    path = os.path.join(OUT_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  OK {name}.json")

# ─── Export ──────────────────────────────────────────────────────────────────

print("\nExporting to server/data/ ...")

save("sectors", serialize_node(NS["SECTOR_SUBCATEGORIES"]))

save("imports", {
    sector: [imp_to_dict(o) for o in items]
    for sector, items in NS["IMPORT_DATA"].items()
})

save("regions", {
    "REGIONS":                 NS["REGIONS"],
    "REGION_CHANNEL_BIAS":     NS["REGION_CHANNEL_BIAS"],
    "REGION_BASE_SCORE_DELTA": NS["REGION_BASE_SCORE_DELTA"],
    "REGION_SECTOR_AFFINITY":  NS["REGION_SECTOR_AFFINITY"],
    "REGION_META":             NS["REGION_META"],
    "SALES_CHANNELS":          NS["SALES_CHANNELS"],
})

save("seasonality", {
    "SEASONALITY_PATTERNS": NS["SEASONALITY_PATTERNS"],
    "MONTHS_TR":            NS["MONTHS_TR"],
    "MONTHS_FULL":          NS["MONTHS_FULL"],
    "PRODUCT_PATTERN":      NS["PRODUCT_PATTERN"],
    "SUBCAT_PATTERN":       NS["SUBCAT_PATTERN"],
    "SECTOR_PATTERN":       NS["SECTOR_PATTERN"],
    "SEASON_KEYWORD_RULES": [
        {"keywords": kws, "pattern": pat}
        for kws, pat in NS.get("_SEASON_KEYWORD_RULES", [])
    ],
})

save("constants", {
    "SECTORS":        NS["SECTORS"],
    "SECTOR_EMOJI":   NS["SECTOR_EMOJI"],
    "SECTOR_GRAD":    NS["SECTOR_GRAD"],
    "RISK_COLORS":    NS["RISK_COLORS"],
    "RISK_LABELS":    NS["RISK_LABELS"],
    "CHANNEL_MAP":    NS["CHANNEL_MAP"],
    "CHANNEL_COLOR":  NS["CHANNEL_COLOR"],
    "SIDEBAR_TO_KEY": NS["SIDEBAR_TO_KEY"],
})

save("emoji_kw", [
    {"keywords": kws, "emoji": emoji}
    for kws, emoji in NS["_EMOJI_KW"]
])

print("\nDone!\n")
