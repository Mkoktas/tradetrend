"""
TradeTrend Dashboard v0.2
Liquid Glass UI · Amazon TR · Alt Kategoriler · İthalat Fırsatları
"""

import sys, os
# Proje kökünü her zaman path'e ekle (venv sandbox uyumluluğu için)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import date
from trend_engine.scorer import TrendScorer, ProductSignals
from trend_engine.import_analyzer import get_import_opportunities, ImportOpportunity

st.set_page_config(
    page_title="TradeTrend — Ne Sat, Ne Zaman, Nerede",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# LIQUID GLASS CSS
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ─── Background ──────────────────────────────────────────────────────── */
.stApp {
    background:
        radial-gradient(ellipse 70% 60% at 8% 12%,  rgba(29,78,216,0.13) 0%, transparent 65%),
        radial-gradient(ellipse 55% 50% at 92% 88%,  rgba(37,99,235,0.11) 0%, transparent 65%),
        radial-gradient(ellipse 40% 40% at 85% 15%,  rgba(147,197,253,0.09) 0%, transparent 55%),
        radial-gradient(ellipse 50% 45% at 30% 80%,  rgba(59,130,246,0.07) 0%, transparent 55%),
        linear-gradient(145deg, #f0f9ff 0%, #e0f2fe 35%, #dbeafe 65%, #eff6ff 100%) !important;
    background-attachment: fixed !important;
}

/* ─── Sidebar ─────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: rgba(240,249,255,0.85) !important;
    backdrop-filter: blur(24px) saturate(160%) !important;
    -webkit-backdrop-filter: blur(24px) saturate(160%) !important;
    border-right: 1px solid rgba(147,197,253,0.22) !important;
    box-shadow: 4px 0 24px rgba(29,78,216,0.07) !important;
}
[data-testid="stSidebar"] * { color: #0c1a3a !important; }

/* ─── Metric cards ────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.62) !important;
    backdrop-filter: blur(18px) saturate(160%) !important;
    -webkit-backdrop-filter: blur(18px) saturate(160%) !important;
    border: 1px solid rgba(255,255,255,0.78) !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 16px rgba(29,78,216,0.08), 0 1px 0 rgba(255,255,255,0.85) inset !important;
    padding: 0.65rem 0.9rem !important;
    transition: transform 0.22s cubic-bezier(.4,0,.2,1), box-shadow 0.22s cubic-bezier(.4,0,.2,1) !important;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-2px) scale(1.01) !important;
    box-shadow: 0 10px 28px rgba(29,78,216,0.15), 0 1px 0 rgba(255,255,255,0.9) inset !important;
}
[data-testid="stMetricValue"]  { color: #0c1a3a !important; font-size: 1.25rem !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"]  { color: #1d4ed8 !important; font-weight: 600 !important; font-size: 0.75rem !important; }
[data-testid="stMetricDelta"]  { color: #059669 !important; font-size: 0.72rem !important; }

/* ─── Expanders ───────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.58) !important;
    backdrop-filter: blur(14px) !important;
    -webkit-backdrop-filter: blur(14px) !important;
    border: 1px solid rgba(255,255,255,0.72) !important;
    border-radius: 16px !important;
    box-shadow: 0 4px 18px rgba(29,78,216,0.08) !important;
    overflow: hidden !important;
    margin-bottom: 0.65rem !important;
    transition: box-shadow 0.22s ease, transform 0.22s ease !important;
}
[data-testid="stExpander"]:hover {
    box-shadow: 0 10px 32px rgba(29,78,216,0.16) !important;
    transform: translateY(-1px) !important;
}
[data-testid="stExpander"] summary {
    background: rgba(240,249,255,0.7) !important;
    color: #0c1a3a !important;
    font-weight: 600 !important;
    padding: 0.8rem 1.1rem !important;
    border-radius: 16px !important;
}

/* ─── Buttons ─────────────────────────────────────────────────────────── */
[data-testid="stBaseButton-primary"] > button,
button[kind="primary"] {
    background: linear-gradient(135deg,#1d4ed8,#2563eb) !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 16px rgba(29,78,216,0.38) !important;
    transition: transform 0.18s ease, box-shadow 0.18s ease !important;
}
[data-testid="stBaseButton-primary"] > button:hover { transform: translateY(-2px) !important; box-shadow: 0 8px 24px rgba(29,78,216,0.50) !important; }

/* ─── Selectbox / Multiselect ─────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    background: rgba(255,255,255,0.68) !important;
    border: 1px solid rgba(29,78,216,0.18) !important;
    border-radius: 10px !important;
    backdrop-filter: blur(8px) !important;
    transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
}
[data-testid="stSelectbox"] > div > div:focus-within,
[data-testid="stMultiSelect"] > div > div:focus-within {
    border-color: rgba(29,78,216,0.45) !important;
    box-shadow: 0 0 0 3px rgba(29,78,216,0.12) !important;
}

/* ─── DataFrames ──────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    background: rgba(255,255,255,0.58) !important;
    border-radius: 14px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 20px rgba(29,78,216,0.08) !important;
}

/* ─── Tabs ────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: rgba(255,255,255,0.5) !important;
    border-radius: 10px 10px 0 0 !important;
    border: 1px solid rgba(147,197,253,0.2) !important;
    font-weight: 600 !important;
    color: #1e3a8a !important;
    transition: background 0.18s ease !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: rgba(29,78,216,0.12) !important;
    border-bottom: 2px solid #1d4ed8 !important;
    color: #1d4ed8 !important;
}

/* ─── Success / Warning / Error boxes ─────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 12px !important;
    backdrop-filter: blur(8px) !important;
}

/* ─── Typography ──────────────────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 { color: #0c1a3a !important; font-weight: 700 !important; }
p, li { color: #374151 !important; }
.stMarkdown a { color: #1d4ed8 !important; }

/* ─── Separator ───────────────────────────────────────────────────────── */
hr { border-color: rgba(147,197,253,0.25) !important; }

/* ─── Custom Glass Card (HTML) ────────────────────────────────────────── */
.tt-glass {
    background: rgba(255,255,255,0.62);
    backdrop-filter: blur(20px) saturate(160%);
    -webkit-backdrop-filter: blur(20px) saturate(160%);
    border: 1px solid rgba(255,255,255,0.78);
    border-radius: 14px;
    box-shadow: 0 4px 18px rgba(29,78,216,0.08), 0 1px 0 rgba(255,255,255,0.85) inset;
    transition: transform 0.24s cubic-bezier(.4,0,.2,1), box-shadow 0.24s cubic-bezier(.4,0,.2,1);
    padding: 0.95rem 1.2rem;
    margin-bottom: 0.5rem;
}
.tt-glass:hover {
    transform: translateY(-3px);
    box-shadow: 0 14px 36px rgba(29,78,216,0.14), 0 1px 0 rgba(255,255,255,0.9) inset;
}
.tt-header {
    background: linear-gradient(135deg, rgba(37,99,235,0.88), rgba(29,78,216,0.90));
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255,255,255,0.28);
    border-radius: 14px;
    padding: 0.8rem 1.3rem;
    margin-bottom: 1rem;
    box-shadow: 0 6px 20px rgba(37,99,235,0.22);
}
.tt-source-card {
    background: rgba(255,255,255,0.65);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255,255,255,0.75);
    border-radius: 16px;
    padding: 1.3rem;
    box-shadow: 0 4px 20px rgba(29,78,216,0.09);
    height: 100%;
    transition: transform 0.22s ease, box-shadow 0.22s ease;
}
.tt-source-card:hover { transform: translateY(-3px); box-shadow: 0 12px 32px rgba(29,78,216,0.16); }
.tt-import-card {
    background: rgba(255,255,255,0.62);
    backdrop-filter: blur(18px);
    border: 1px solid rgba(255,255,255,0.76);
    border-radius: 12px;
    padding: 0.75rem 1rem;
    box-shadow: 0 3px 14px rgba(29,78,216,0.07);
    margin-bottom: 0.4rem;
    transition: transform 0.22s ease, box-shadow 0.22s ease;
}
.tt-import-card:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(29,78,216,0.14); }
.tt-badge-high   { background: rgba(5,150,105,0.12); color:#065f46; border:1px solid rgba(5,150,105,0.25); border-radius:20px; padding:2px 10px; font-size:0.8rem; font-weight:700; }
.tt-badge-mid    { background: rgba(217,119,6,0.12);  color:#92400e; border:1px solid rgba(217,119,6,0.25);  border-radius:20px; padding:2px 10px; font-size:0.8rem; font-weight:700; }
.tt-badge-watch  { background: rgba(37,99,235,0.12); color:#1e40af; border:1px solid rgba(37,99,235,0.25); border-radius:20px; padding:2px 10px; font-size:0.8rem; font-weight:700; }
.tt-formula {
    background: rgba(30,27,75,0.92);
    color: #60a5fa;
    border-radius: 12px;
    padding: 1rem 1.4rem;
    font-family: monospace;
    font-size: 0.93rem;
    margin: 0.8rem 0;
    border: 1px solid rgba(29,78,216,0.3);
}
.tt-trend-up   { color:#059669; font-weight:700; }
.tt-trend-fast { color:#1d4ed8; font-weight:700; }
.tt-trend-stb  { color:#6b7280; font-weight:600; }

@keyframes slideUp {
    from { opacity:0; transform:translateY(18px); }
    to   { opacity:1; transform:translateY(0);    }
}
@keyframes floatY {
    0%,100% { transform:translateY(0);    }
    50%      { transform:translateY(-6px); }
}
@keyframes pulseRing {
    0%,100% { box-shadow: 0 0 0 0   rgba(29,78,216,0.28); }
    55%      { box-shadow: 0 0 0 8px rgba(29,78,216,0);    }
}
@keyframes shimmer {
    0%   { background-position: -400px 0; }
    100% { background-position:  400px 0; }
}

.tt-glass           { animation: slideUp 0.38s cubic-bezier(.22,.68,0,1.2) both; }
.tt-import-card     { animation: slideUp 0.40s cubic-bezier(.22,.68,0,1.2) both; }
.tt-header          { animation: floatY  5.5s ease-in-out infinite; }
.tt-badge-high      { animation: pulseRing 2.4s ease-in-out infinite; }
.tt-source-card:hover { animation: none; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SVG ICON HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def svg(name: str, color: str = "#1d4ed8", size: int = 20) -> str:
    S = f'width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"'
    icons = {
        "trend-up":    f'<svg {S}><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>',
        "globe":       f'<svg {S}><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>',
        "package":     f'<svg {S}><line x1="16.5" y1="9.4" x2="7.5" y2="4.21"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>',
        "book":        f'<svg {S}><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>',
        "bar-chart":   f'<svg {S}><line x1="12" y1="20" x2="12" y2="10"/><line x1="18" y1="20" x2="18" y2="4"/><line x1="6" y1="20" x2="6" y2="16"/></svg>',
        "map-pin":     f'<svg {S}><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>',
        "shopping":    f'<svg {S}><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>',
        "truck":       f'<svg {S}><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>',
        "refresh":     f'<svg {S}><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>',
        "filter":      f'<svg {S}><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>',
        "zap":         f'<svg {S} fill="{color}"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
        "star":        f'<svg {S} fill="{color}" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
        "alert":       f'<svg {S}><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        "check":       f'<svg {S}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        "layers":      f'<svg {S}><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
        "search":      f'<svg {S}><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
        "amazon":      f'<svg {S} stroke="none" fill="{color}"><path d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm0 2c4.418 0 8 3.582 8 8 0 1.466-.395 2.84-1.085 4.02C17.48 14.54 15.37 14 13 14c-1.092 0-2.14.14-3.09.39L8.5 13H7l-1.5-3.5C6.1 6.36 8.87 4 12 4zm-4.5 9.5c.552 0 1 .448 1 1s-.448 1-1 1-1-.448-1-1 .448-1 1-1zm9 0c.552 0 1 .448 1 1s-.448 1-1 1-1-.448-1-1 .448-1 1-1zm-4.5 3c1.38 0 2.64.37 3.7.97-.34.42-.84.71-1.4.81L14 19h-4l-.3-1.22c-.56-.1-1.06-.39-1.4-.81C9.36 16.37 10.62 16 12 16z"/></svg>',
        "tiktok":      f'<svg {S} stroke="none" fill="{color}"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.31 6.31 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.18 8.18 0 0 0 4.79 1.53V6.77a4.85 4.85 0 0 1-1.02-.08z"/></svg>',
        "instagram":   f'<svg {S}><rect x="2" y="2" width="20" height="20" rx="5" ry="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/></svg>',
        "store":       f'<svg {S}><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
        "google":      f'<svg {S} stroke="none" fill="{color}"><path d="M12.48 10.92v3.28h7.84c-.24 1.84-.853 3.187-1.787 4.133-1.147 1.147-2.933 2.4-6.053 2.4-4.827 0-8.6-3.893-8.6-8.72s3.773-8.72 8.6-8.72c2.6 0 4.507 1.027 5.907 2.347l2.307-2.307C18.747 1.44 16.133 0 12.48 0 5.867 0 .307 5.387.307 12s5.56 12 12.173 12c3.573 0 6.267-1.173 8.373-3.36 2.16-2.16 2.84-5.213 2.84-7.667 0-.76-.053-1.467-.173-2.053H12.48z"/></svg>',
    }
    return icons.get(name, "")


def icon_html(name: str, color: str = "#1d4ed8", size: int = 20) -> str:
    return f'<span style="vertical-align:middle;display:inline-flex;align-items:center;">{svg(name, color, size)}</span>'


# ═══════════════════════════════════════════════════════════════════════════════
# SABİTLER
# ═══════════════════════════════════════════════════════════════════════════════
RISK_COLORS = {"low": "#059669", "medium": "#d97706", "high": "#dc2626"}
RISK_LABELS = {"low": "Düşük Risk", "medium": "Orta Risk", "high": "Yüksek Risk"}

CHANNEL_MAP  = {
    "trendyol":  "Trendyol",
    "amazon_tr": "Amazon TR",
    "instagram": "Instagram",
    "store":     "Fiziksel Mağaza",
}
CHANNEL_ICON_NAME = {
    "trendyol":  "shopping",
    "amazon_tr": "amazon",
    "instagram": "instagram",
    "store":     "store",
}
CHANNEL_COLOR = {
    "trendyol":  "#f27a1a",
    "amazon_tr": "#f90",
    "instagram": "#e1306c",
    "store":     "#059669",
}

SIDEBAR_TO_KEY = {
    "Trendyol":       "trendyol",
    "Amazon TR":      "amazon_tr",
    "Instagram":      "instagram",
    "Fiziksel Mağaza":"store",
}

SECTORS = {
    "Kırtasiye":      "kirtasiye",
    "Elektronik":     "elektronik",
    "Giyim":          "giyim",
    "Ev & Yaşam":     "ev_yasam",
    "Kozmetik":       "kozmetik",
    "Spor & Outdoor": "spor",
    "Gıda & İçecek":  "gida",
    "Oyuncak & Hobi": "oyuncak",
}

# ─── Ürün Görsel Sistemi — anahtar kelime tabanlı (yeni ürünlere otomatik uyum) ─
SECTOR_EMOJI = {
    "kirtasiye": "✏️", "elektronik": "📱", "giyim": "👕",
    "ev_yasam":  "🏠", "kozmetik":   "💄", "spor":  "🏋️",
    "gida":      "🥗", "oyuncak":    "🎮",
}

# Kelime eşleşmesi: [(anahtar_kelimeler, emoji), ...]  — yukarıdan aşağı, ilk eşleşme kazanır
_EMOJI_KW: list = [
    # ── Elektronik ──────────────────────────────────────────────────────────
    (["kulak içi","tws","bluetooth kulaklık","anc kulaklık","spor kulak","wireless earbuds"], "🎧"),
    (["kafa üstü kulaklık","oyuncu kulaklık","studio kulaklık","surround","wireless kafa"], "🎧"),
    (["hoparlör","taşınabilir hoparlör","masaüstü studio"], "🔊"),
    (["mikrofon","podcast","kondenser","yayın mikrofon"], "🎙️"),
    (["mekanik klavye","wireless klavye","klavye & fare"], "⌨️"),
    (["oyuncu mouse","ergonomik mouse","dikey mouse"], "🖱️"),
    (["usb hub","docking station","hub & ekran"], "🔌"),
    (["webcam"], "📷"),
    (["powerbank","şarj istasyonu","araç şarj","güneş enerjili powerbank"], "🔋"),
    (["gan şarj","kablosuz şarj","magsafe şarj","wireless şarj"], "⚡"),
    (["ups "], "🔋"),
    (["akıllı saat","spor gps saati","gps saati"], "⌚"),
    (["fitness bileklik","akıllı yüzük"], "⌚"),
    (["led şerit","neon flex","neon led tabela"], "💡"),
    (["robot süpürge","lidar"], "🤖"),
    (["akıllı priz","akıllı ev"], "🔌"),
    (["akıllı terazi"], "⚖️"),
    (["kılıf","magsafe manyetik cüzdan","ekran koruyucu"], "📱"),
    (["selfie ışığı","ring light","tablet klavye"], "💡"),
    (["laptop stand","webcam hd"], "💻"),
    # ── Kırtasiye ──────────────────────────────────────────────────────────
    (["pilot","roller kalem","tükenmez","silinebilir","uni-ball","termal kalem"], "🖊️"),
    (["marker","fine liner","mildliner","copic","fosforlu kalem"], "🖊️"),
    (["brush pen","kaligrafi","tombow","nib & mürekkep"], "🖌️"),
    (["dolma kalem","mürekkep"], "✒️"),
    (["suluboya","pastel boya","akrilik boya"], "🎨"),
    (["washi tape"], "🎀"),
    (["epoxy resin","reçine sanat"], "🧪"),
    (["bullet journal","planlayıcı","ajanda","haftalık masa planeri"], "📔"),
    (["defter","spiralli","rocketbook"], "📒"),
    (["okul çantası","sırt çantası"], "🎒"),
    (["termos"], "♨️"),
    (["beslenme kutusu"], "🍱"),
    (["dosya","klasör","arşiv","etiket yazıcı"], "🗂️"),
    (["masa organizer","kalemlik organizer","post-it"], "✏️"),
    (["zımba","delgeç","bant dispenser"], "📎"),
    # ── Giyim ──────────────────────────────────────────────────────────────
    (["t-shirt","crop top","graphic tee","polo yaka","basic crop"], "👕"),
    (["hoodie","zip-up kapüşon"], "🧥"),
    (["kazak","ribana","bisiklet yaka"], "🧶"),
    (["saten bluz","şifon bluz","keten gömlek","denim gömlek"], "👔"),
    (["wide leg jean","mom jean","kargo pantolon","palazzo pantolon"], "👖"),
    (["mini etek","maxi etek","denim şort","deri görünümlü tayt"], "👗"),
    (["bomber ceket","denim ceket","blazer casual","örgü yelek"], "🧥"),
    (["puf mont","trençkot","yağmurluk","kürklü mont"], "🧥"),
    (["spor ayakkabı","sneaker platform","kolej bağcıklı"], "👟"),
    (["platform sandalet","şeffaf topuklu sandalet"], "👠"),
    (["chelsea bot","kovboy bot"], "🥾"),
    (["loafer"], "👞"),
    (["seamless spor tayt","yoga pantolonu","spor sütyeni","crop spor üst"], "🩱"),
    (["koşu üstü","termal içlik","rüzgarlık","spor şort"], "🏃"),
    # ── Ev & Yaşam ─────────────────────────────────────────────────────────
    (["makrome duvar","çerçeve seti galerisi","poster çerçeve"], "🖼️"),
    (["neon led tabela","neon flex lamba"], "🔆"),
    (["mum seti","wax melt"], "🕯️"),
    (["aroma diffuser","aromaterapi diffuser","oda kokusu"], "🌬️"),
    (["seramik vazo","kristal dekor","ahşap dekoratif"], "🏺"),
    (["dekoratif yastık"], "🛋️"),
    (["kahve demleme","v60","dripper","aeropress","cold brew sürahi","cold brew"], "☕"),
    (["moka pot"], "☕"),
    (["çay demleme"], "🍵"),
    (["manuka bal"], "🍯"),
    (["cam saklama kapları","bambu kesme tahtası","yemek hazırlama","salata spinner"], "🍽️"),
    (["hava fritözü"], "🍳"),
    (["blender","blend & go"], "🥤"),
    (["waffle makinesi"], "🧇"),
    (["sous vide","yavaş pişirici"], "👨‍🍳"),
    (["elektrikli fırın mini","fındık kırıcı","meyve sıkacağı"], "🔌"),
    (["mantar led lamba","yıldız projeksiyonu","kristal gece lambası"], "🍄"),
    (["led şerit akıllı wifi"], "💡"),
    (["masa lambası dokunma","bahçe ışık","gece lambası"], "🪔"),
    (["bambu organizer","dolap içi düzenleyici","modüler raf","vakumlu saklama"], "🗃️"),
    (["hava temizleyici hepa","ozon temizleyici","nem ölçer"], "🌀"),
    (["saksı seti seramik","askılı saksı makrome","teraryum cam"], "🪴"),
    (["sukulent seti","bitki toprağı","gübre seti"], "🌱"),
    (["hidroponik"], "🌿"),
    # ── Kozmetik ───────────────────────────────────────────────────────────
    (["c vitamini serum","hyalüronik asit serum","retinol krem","niasinamid serum"], "💊"),
    (["gözenek temizleyici","misel suyu","exfoliating tonik","çay ağacı yüz toniği"], "🧴"),
    (["güneş kremi","spf","bb krem","renkli güneş","yüz güneş spreyi"], "☀️"),
    (["tüp maskara","göz kalemi sıvı","lip liner"], "👁️"),
    (["dudak parlatıcı"], "💋"),
    (["fondöten","setting spray matlık"], "💄"),
    (["blush stick","highlighter tozu"], "✨"),
    (["makyaj fırça","beauty blender","silikon yüz masaj"], "🖌️"),
    (["sülfatsız şampuan","saç maskesi","deep conditioning","saç dökülme"], "🧴"),
    (["argan yağı","saç serumu","ısı koruyucu sprey","hint yağı"], "💆"),
    (["vücut peeling","self-tanner köpük","vücut yağı kuru"], "🧖"),
    (["gua sha","cupping set silikon"], "🪨"),
    (["el kremi","nemlendirici losyon"], "🤲"),
    (["banyo tuzu himalaya"], "🛁"),
    # ── Spor ───────────────────────────────────────────────────────────────
    (["ayarlanabilir dumbbell","kettlebell","barbell","ağırlık yeleği"], "🏋️"),
    (["resistance band","pull-up bar","trx askı","ab roller"], "💪"),
    (["tpe yoga matı","kork yoga matı","yoga mat"], "🧘"),
    (["yoga block","pilates band","meditasyon minderi","yoga block set"], "🧘"),
    (["pilates topu"], "⚽"),
    (["foam roller"], "🫙"),
    (["gps koşu saati"], "⌚"),
    (["koşu kemeri çantası","hidrasyon koşu yeleği"], "🏃"),
    (["atlama ipi"], "🪃"),
    (["mini stepper"], "🦶"),
    (["kamp hamağı","ultralight çadır","uyku tulumu"], "⛺"),
    (["kamp tenceresi"], "🍳"),
    (["trekking botu"], "🥾"),
    (["baş feneri şarjlı"], "🔦"),
    (["survival kit","trekking baton"], "🧰"),
    (["sporcu şişesi","grip strengthener","dirsek"], "💪"),
    # ── Gıda ───────────────────────────────────────────────────────────────
    (["matcha seti premium"], "🍵"),
    (["adaptogen mantar","spirulina","moringa tozu"], "🌿"),
    (["collagen peptide","mct oil","hidrolize kolajen","bitki bazlı protein"], "💊"),
    (["whey protein","kazein protein","vegan protein"], "🏋️"),
    (["bcaa","pre-workout formula","elektrolit tablet","glutamin"], "💊"),
    (["hindistan cevizi yağı","avokado yağı soğuk","organik zeytinyağı"], "🫒"),
    (["chia tohumu","goji berry","kuru incir","organik çiğ kakao","çiçek polen"], "🌰"),
    (["zerdeçal latte","hibiskus çay"], "🍵"),
    (["manuka bal premium"], "🍯"),
    (["cold brew sürahi","dripper pour-over","aeropress kahve"], "☕"),
    (["moka pot alüminyum","kahve değirmeni"], "☕"),
    (["çay demleme seti cam"], "🍵"),
    # ── Oyuncak ────────────────────────────────────────────────────────────
    (["kodlama robotu","scratch kodlama","robot koleksiyonu diy"], "🤖"),
    (["bilim deneyleri","mikroskop çocuk","teleskop başlangıç","kimya deney"], "🔬"),
    (["lego technic","lego creator","mini tuğla","nano blok"], "🧱"),
    (["manyetik yapı seti","manyetik tile","denge oyunu ahşap","ahşap yapı bloğu"], "🧲"),
    (["stop motion studio","çizim tableti çocuk","pottery wheel mini"], "🎬"),
    (["ahşap boyama seti","slime yapım","reçine sanat","kil modelleme","tie-dye"], "🎨"),
    (["rc drone kamera","drone fpv"], "🚁"),
    (["elektrikli scooter çocuk","paten ayarlanabilir"], "🛴"),
    (["rc araba offroad"], "🚗"),
    (["archery set çocuk"], "🏹"),
    (["mini basketbol potası"], "🏀"),
    (["kamp seti çocuk"], "⛺"),
    (["blind box figür","funko pop koleksiyon","gacha kapsül figür"], "🎁"),
    (["anime aksiyon figürü"], "🎌"),
    (["diecast model araba"], "🚗"),
    (["sensory fidget seti","pop-it oyuncak","infinity cube fidget"], "🌀"),
]

# Gerçekçi ürün fotoğrafı için anahtar kelimeler (loremflickr — API key gerektirmez)
_IMG_KW: list = [
    # Elektronik
    (["kulak içi","tws","bluetooth kulaklık","anc kulaklık"], ("wireless,earbuds",  1)),
    (["kafa üstü kulaklık","oyuncu kulaklık","studio kulaklık"], ("headphones",     2)),
    (["hoparlör","taşınabilir hoparlör"],              ("bluetooth,speaker",         3)),
    (["mikrofon","podcast"],                           ("microphone,studio",         4)),
    (["mekanik klavye","wireless klavye"],              ("mechanical,keyboard",       5)),
    (["oyuncu mouse","ergonomik mouse","dikey mouse"], ("gaming,mouse",              6)),
    (["usb hub","docking station"],                    ("usb,hub,technology",        7)),
    (["webcam"],                                       ("webcam,desk",               8)),
    (["powerbank","güneş enerjili powerbank"],         ("power,bank,charging",       9)),
    (["gan şarj","kablosuz şarj","magsafe şarj"],      ("wireless,charger",          10)),
    (["ups "],                                         ("ups,battery",               11)),
    (["akıllı saat","spor gps saati"],                 ("smartwatch",               12)),
    (["fitness bileklik","akıllı yüzük"],              ("fitness,tracker,wearable",  13)),
    (["led şerit","neon flex","neon led tabela"],      ("led,strip,lights,room",     14)),
    (["robot süpürge"],                                ("robot,vacuum,cleaner",      15)),
    (["laptop stand"],                                 ("laptop,stand,desk",         16)),
    (["kılıf","ekran koruyucu","magsafe manyetik cüzdan"], ("smartphone,case",      17)),
    (["selfie ışığı","ring light"],                    ("ring,light,photography",    18)),
    # Kırtasiye
    (["marker","fine liner","mildliner","copic"],      ("markers,colorful,stationery", 19)),
    (["brush pen","kaligrafi","tombow"],               ("calligraphy,brush,pen",     20)),
    (["dolma kalem","mürekkep"],                       ("fountain,pen,ink",          21)),
    (["tükenmez","roller kalem","kalem seti","pilot"], ("pen,stationery,desk",       22)),
    (["suluboya"],                                     ("watercolor,painting,art",   23)),
    (["washi tape"],                                   ("washi,tape,craft",          24)),
    (["epoxy resin","reçine sanat"],                   ("epoxy,resin,craft",         25)),
    (["bullet journal","planlayıcı","ajanda"],          ("bullet,journal,planner",   26)),
    (["defter","spiralli"],                            ("notebook,stationery",       27)),
    (["okul çantası","sırt çantası"],                  ("school,backpack",           28)),
    (["termos"],                                       ("thermos,drink,hot",         29)),
    (["masa organizer","kalemlik"],                    ("desk,organizer,stationery", 30)),
    (["pottery wheel"],                                ("pottery,wheel,clay",        31)),
    (["slime yapım","tie-dye"],                        ("slime,craft,kids",          32)),
    # Giyim
    (["t-shirt","crop top","graphic tee"],             ("tshirt,fashion,style",      33)),
    (["hoodie","zip-up kapüşon"],                      ("hoodie,fashion",            34)),
    (["kazak","ribana","bisiklet yaka"],               ("sweater,fashion,knitwear",  35)),
    (["saten bluz","şifon bluz","keten gömlek"],       ("blouse,fashion,women",      36)),
    (["wide leg jean","mom jean"],                     ("wide,leg,jeans,fashion",    37)),
    (["kargo pantolon"],                               ("cargo,pants,streetwear",    38)),
    (["palazzo pantolon"],                             ("palazzo,pants,fashion",     39)),
    (["mini etek"],                                    ("mini,skirt,fashion",        40)),
    (["maxi etek"],                                    ("maxi,dress,fashion",        41)),
    (["bomber ceket","denim ceket"],                   ("jacket,fashion,style",      42)),
    (["blazer"],                                       ("blazer,fashion,formal",     43)),
    (["trençkot"],                                     ("trench,coat,fashion",       44)),
    (["puf mont","kürklü mont"],                       ("winter,coat,warm",          45)),
    (["spor ayakkabı","sneaker"],                      ("sneakers,shoes,sport",      46)),
    (["sandalet","platform sandalet"],                 ("sandals,shoes,summer",      47)),
    (["bot ","chelsea bot","kovboy bot"],               ("boots,shoes,fashion",       48)),
    (["loafer"],                                       ("loafer,shoes,casual",       49)),
    (["seamless spor tayt","yoga pantolonu"],          ("yoga,pants,workout",        50)),
    (["spor sütyeni"],                                 ("sports,bra,workout",        51)),
    (["koşu üstü","termal içlik"],                     ("running,sport,activewear",  52)),
    # Ev & Yaşam
    (["makrome duvar"],                                ("macrame,wall,art",          53)),
    (["çerçeve seti"],                                 ("picture,frames,wall",       54)),
    (["neon led tabela"],                              ("neon,sign,room,decoration", 55)),
    (["mum seti kokulu","wax melt"],                   ("scented,candles,home",      56)),
    (["aroma diffuser","aromaterapi"],                 ("diffuser,aromatherapy",     57)),
    (["seramik vazo"],                                 ("ceramic,vase,flower",       58)),
    (["dekoratif yastık"],                             ("decorative,pillow,sofa",    59)),
    (["kahve demleme","v60","pour-over","aeropress"],  ("pour,over,coffee,brewing",  60)),
    (["cold brew sürahi"],                             ("cold,brew,coffee",          61)),
    (["moka pot"],                                     ("moka,pot,coffee",           62)),
    (["çay demleme seti"],                             ("tea,set,ceramic",           63)),
    (["manuka bal"],                                   ("manuka,honey,jar",          64)),
    (["cam saklama kapları"],                          ("glass,jar,storage,kitchen", 65)),
    (["bambu kesme tahtası"],                          ("bamboo,cutting,board",      66)),
    (["hava fritözü"],                                 ("air,fryer,kitchen",         67)),
    (["blender","blend & go"],                         ("blender,kitchen,smoothie",  68)),
    (["waffle makinesi"],                              ("waffle,maker,breakfast",     69)),
    (["sous vide","yavaş pişirici"],                   ("sous,vide,cooking",         70)),
    (["mantar led lamba","yıldız projeksiyonu"],       ("mushroom,lamp,decor",       71)),
    (["masa lambası dokunma"],                         ("desk,lamp,bedroom",         72)),
    (["bahçe ışık","güneş pilli"],                     ("solar,garden,light",        73)),
    (["bambu organizer","dolap içi düzenleyici"],      ("closet,organizer,storage",  74)),
    (["hava temizleyici"],                             ("air,purifier,home",         75)),
    (["nem ölçer"],                                    ("hygrometer,home",           76)),
    (["saksı seti seramik"],                           ("ceramic,pot,succulent",     77)),
    (["askılı saksı makrome"],                         ("macrame,plant,hanger",      78)),
    (["sukulent seti"],                                ("succulent,plants,pot",      79)),
    (["hidroponik"],                                   ("hydroponic,indoor,garden",  80)),
    (["teraryum cam"],                                 ("terrarium,glass,plants",    81)),
    # Kozmetik
    (["c vitamini serum","hyalüronik asit","retinol","niasinamid"], ("face,serum,skincare", 82)),
    (["güneş kremi","spf","bb krem","renkli güneş"],  ("sunscreen,skincare,spf",    83)),
    (["gözenek temizleyici","misel suyu","tonik"],     ("face,wash,cleanser",        84)),
    (["tüp maskara"],                                  ("mascara,makeup,eyes",       85)),
    (["dudak parlatıcı","lip liner"],                  ("lipstick,lips,makeup",      86)),
    (["fondöten","setting spray"],                     ("foundation,makeup,beauty",  87)),
    (["blush stick","highlighter tozu"],               ("blush,highlighter,makeup",  88)),
    (["makyaj fırça","beauty blender"],                ("makeup,brushes,beauty",     89)),
    (["şampuan","saç maskesi","saç dökülme"],          ("shampoo,hair,care",         90)),
    (["argan yağı","saç serumu","ısı koruyucu"],       ("hair,oil,serum",            91)),
    (["vücut peeling","body scrub"],                   ("body,scrub,spa",            92)),
    (["nemlendirici losyon"],                          ("body,lotion,moisturizer",   93)),
    (["gua sha"],                                      ("gua,sha,beauty,face",       94)),
    (["el kremi"],                                     ("hand,cream,care",           95)),
    (["banyo tuzu"],                                   ("bath,salts,relaxing",       96)),
    # Spor
    (["ayarlanabilir dumbbell"],                       ("adjustable,dumbbell,gym",   97)),
    (["kettlebell"],                                   ("kettlebell,workout",        98)),
    (["barbell","plaka"],                              ("barbell,weightlifting",     99)),
    (["resistance band","direnç bant"],                ("resistance,band,exercise", 100)),
    (["pull-up bar"],                                  ("pull,up,bar,fitness",      101)),
    (["trx askı"],                                     ("trx,suspension,trainer",   102)),
    (["ab roller"],                                    ("ab,roller,core,workout",   103)),
    (["tpe yoga matı","kork yoga matı"],               ("yoga,mat,exercise",        104)),
    (["pilates topu"],                                 ("pilates,ball,exercise",    105)),
    (["foam roller"],                                  ("foam,roller,recovery",     106)),
    (["yoga block"],                                   ("yoga,block,fitness",       107)),
    (["gps koşu saati"],                               ("running,watch,gps",        108)),
    (["koşu kemeri çantası"],                          ("running,belt,waist",       109)),
    (["hidrasyon koşu yeleği"],                        ("hydration,vest,running",   110)),
    (["atlama ipi"],                                   ("jump,rope,fitness",        111)),
    (["kamp hamağı"],                                  ("hammock,camping,outdoor",  112)),
    (["ultralight çadır","uyku tulumu"],               ("camping,tent,outdoor",     113)),
    (["kamp tenceresi titanyum"],                      ("camping,cookware",         114)),
    (["trekking botu"],                                ("hiking,boots,trail",       115)),
    (["baş feneri şarjlı"],                            ("headlamp,outdoor",         116)),
    (["survival kit","trekking baton"],                ("outdoor,survival,kit",     117)),
    # Gıda
    (["matcha seti premium"],                          ("matcha,tea,ceremony",      118)),
    (["adaptogen mantar","spirulina","moringa"],       ("health,supplements,green", 119)),
    (["collagen peptide","mct oil","kolajen"],         ("collagen,protein,powder",  120)),
    (["whey protein","kazein protein","vegan protein"],("protein,powder,fitness",   121)),
    (["bcaa","pre-workout","elektrolit","glutamin"],   ("supplements,fitness,gym",  122)),
    (["hindistan cevizi yağı","avokado yağı"],         ("coconut,oil,organic",      123)),
    (["chia tohumu","goji berry","organik çiğ kakao"],("superfood,organic,healthy", 124)),
    (["zerdeçal latte"],                               ("turmeric,latte,health",    125)),
    (["hibiskus çay"],                                 ("hibiscus,tea,drink",       126)),
    (["manuka bal premium"],                           ("manuka,honey,jar",         127)),
    (["cold brew sürahi seti","dripper","aeropress"],  ("coffee,brewing,pour",      128)),
    (["moka pot alüminyum"],                           ("moka,pot,espresso",        129)),
    # Oyuncak
    (["kodlama robotu","scratch kodlama"],             ("coding,robot,kids",        130)),
    (["bilim deneyleri","kimya deney","mikroskop çocuk","teleskop"], ("science,kit,children", 131)),
    (["lego technic","lego creator","nano blok"],      ("lego,bricks,colorful",     132)),
    (["manyetik yapı seti","manyetik tile"],           ("magnetic,tiles,kids",      133)),
    (["ahşap yapı bloğu","denge oyunu ahşap"],         ("wooden,blocks,kids",       134)),
    (["stop motion studio","çizim tableti çocuk"],     ("creative,kids,art",        135)),
    (["pottery wheel mini"],                           ("pottery,wheel,clay,art",   136)),
    (["slime yapım","reçine sanat","tie-dye"],         ("slime,craft,colorful",     137)),
    (["rc drone kamera","drone fpv"],                  ("drone,flying,camera",      138)),
    (["elektrikli scooter çocuk"],                     ("electric,scooter,kids",    139)),
    (["rc araba offroad"],                             ("rc,car,toy",               140)),
    (["paten ayarlanabilir"],                          ("roller,skates,sport",      141)),
    (["archery set çocuk"],                            ("archery,bow,target",       142)),
    (["kamp seti çocuk"],                              ("camping,kids,adventure",   143)),
    (["blind box figür","funko pop","gacha kapsül"],   ("collectible,figure,toy",   144)),
    (["anime aksiyon figürü"],                         ("anime,figure,collectible", 145)),
    (["sensory fidget","pop-it","infinity cube"],      ("fidget,toy,colorful",      146)),
    (["diecast model araba"],                          ("diecast,model,car",        147)),
]

_SECTOR_IMG_FALLBACK = {
    "elektronik": ("technology,gadget",   150),
    "giyim":      ("fashion,clothing",    151),
    "kirtasiye":  ("stationery,desk",     152),
    "ev_yasam":   ("home,interior,decor", 153),
    "kozmetik":   ("beauty,skincare",     154),
    "spor":       ("sport,fitness,gym",   155),
    "gida":       ("healthy,food",        156),
    "oyuncak":    ("toy,children,play",   157),
}

# Arka plan gradyanları — sektöre göre hafif renk tonu
SECTOR_GRAD = {
    "kirtasiye": ("214,234,254", "219,234,254"),   # mavi
    "elektronik": ("220,252,231", "209,250,229"),  # yeşil
    "giyim":      ("254,226,226", "254,215,215"),  # kırmızı
    "ev_yasam":   ("254,243,199", "253,230,138"),  # sarı
    "kozmetik":   ("252,231,243", "251,207,232"),  # pembe
    "spor":       ("220,252,231", "187,247,208"),  # yeşil koyu
    "gida":       ("236,253,245", "209,250,229"),  # nane
    "oyuncak":    ("237,233,254", "221,214,254"),  # mor
}

def get_product_emoji(product_name: str, subcat: str = "", sector: str = "") -> str:
    low = (product_name + " " + subcat).lower()
    for keywords, emoji in _EMOJI_KW:
        if any(k in low for k in keywords):
            return emoji
    return SECTOR_EMOJI.get(sector, "📦")


def get_product_image_url(product_name: str, subcat: str = "", sector: str = "") -> str:
    low = (product_name + " " + subcat).lower()
    for keywords, (en_kw, lock) in _IMG_KW:
        if any(k in low for k in keywords):
            return f"https://loremflickr.com/100/100/{en_kw}?lock={lock}"
    en_kw, lock = _SECTOR_IMG_FALLBACK.get(sector, ("product", 99))
    return f"https://loremflickr.com/100/100/{en_kw}?lock={lock}"

def _collect_products_recursive(node) -> list:
    """Dict veya list olan herhangi bir derinlikteki ürünleri toplar."""
    out = []
    if isinstance(node, list):
        out.extend(node)
    elif isinstance(node, dict):
        for k, v in node.items():
            if k == "Tümü" or v is None:
                continue
            out.extend(_collect_products_recursive(v))
    return out


def _get_all_products(sector_key: str) -> list:
    return _collect_products_recursive(SECTOR_SUBCATEGORIES.get(sector_key, {}))


def _get_filtered_products(sector_key: str, ana_cat: str, alt_cat: str) -> list:
    cats = SECTOR_SUBCATEGORIES.get(sector_key, {})
    if ana_cat == "Tümü":
        return _collect_products_recursive(cats)
    ana_node = cats.get(ana_cat, {})
    if alt_cat == "Tümü":
        return _collect_products_recursive(ana_node)
    leaf = ana_node.get(alt_cat) if isinstance(ana_node, dict) else None
    if leaf is None:
        return _collect_products_recursive(ana_node)
    return _collect_products_recursive(leaf)


@st.cache_data
def _product_subcat_map(sector_key: str) -> dict:
    """product_name → yaprak alt_kategori eşlemesi (3 seviyeli yapı)."""
    result = {}
    cats = SECTOR_SUBCATEGORIES.get(sector_key, {})
    for ana_k, ana_v in cats.items():
        if ana_k == "Tümü" or not isinstance(ana_v, dict):
            continue
        for alt_k, alt_v in ana_v.items():
            if alt_k == "Tümü" or not isinstance(alt_v, list):
                continue
            for sig in alt_v:
                result[sig.name] = alt_k
    return result

# ─── Sezonsal Trend Sistemi ───────────────────────────────────────────────────
MONTHS_TR = ["Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"]
MONTHS_FULL = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran",
               "Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]

SEASONALITY_PATTERNS = {
    "back_to_school": {
        "data":   [30, 28, 38, 42, 50, 52, 65, 95, 88, 48, 35, 32],
        "peaks":  ["Ağustos", "Eylül"],
        "season": "Sonbahar",
        "insight": "Okul açılış sezonu (Ağustos–Eylül) öncesinde aile alışverişleri zirveye ulaşır; veliler okul listelerini bu dönemde tamamlar.",
    },
    "winter": {
        "data":   [88, 80, 58, 40, 28, 22, 20, 24, 40, 65, 84, 92],
        "peaks":  ["Kasım", "Aralık", "Ocak"],
        "season": "Kış",
        "insight": "Soğuk hava dönemi (Kasım–Ocak) ürünü günlük zorunluluk haline getirir; yılbaşı hediye dönemi de talebi ikinci kez yükseltir.",
    },
    "summer": {
        "data":   [30, 32, 45, 62, 84, 96, 92, 85, 52, 36, 28, 25],
        "peaks":  ["Mayıs", "Haziran", "Temmuz"],
        "season": "Yaz",
        "insight": "Yaz mevsimi (Mayıs–Temmuz) kullanım ve bilinç artışıyla talebi zirveye taşır; tatil planlaması satın alma kararını erkene çeker.",
    },
    "new_year_fitness": {
        "data":   [95, 82, 65, 50, 45, 40, 36, 40, 72, 62, 58, 75],
        "peaks":  ["Ocak", "Şubat", "Eylül"],
        "season": "Kış / İlkbahar",
        "insight": "Ocak–Şubat 'yeni yıl kararları' dalgası ve Eylül 'sezon başı motivasyonu' ile yılda iki ayrı talep zirvesi oluşturur.",
    },
    "gift_season": {
        "data":   [45, 38, 42, 52, 50, 46, 48, 55, 60, 72, 90, 96],
        "peaks":  ["Kasım", "Aralık"],
        "season": "Kış",
        "insight": "Yılbaşı hediye sezonu (Kasım–Aralık) talebin en yüksek olduğu dönemdir; kampanya günleri (11.11, Kara Cuma) artışı önceden başlatır.",
    },
    "spring_fashion": {
        "data":   [35, 42, 68, 85, 90, 82, 70, 62, 68, 52, 38, 32],
        "peaks":  ["Nisan", "Mayıs"],
        "season": "İlkbahar",
        "insight": "İlkbahar–yaz koleksiyonu (Mart–Mayıs) sezon değişimiyle birlikte taze içerik patlamasına sahne olur; sosyal medya paylaşımları talebi yukarı çeker.",
    },
    "home_nesting": {
        "data":   [72, 65, 50, 44, 40, 35, 32, 38, 55, 74, 88, 90],
        "peaks":  ["Kasım", "Aralık", "Ocak"],
        "season": "Kış",
        "insight": "Kış aylarında evde geçirilen süre artınca ev düzenleme ve dekorasyon isteği yoğunlaşır; yılbaşı yenileme trendi ek ivme katar.",
    },
    "outdoor_spring": {
        "data":   [25, 30, 55, 75, 88, 90, 82, 75, 62, 42, 28, 22],
        "peaks":  ["Nisan", "Mayıs", "Haziran"],
        "season": "İlkbahar / Yaz",
        "insight": "Hava ısınmasıyla başlayan kamp ve outdoor sezonu (Nisan–Haziran) hazırlık alışverişlerini erkene çeker; uzun hafta sonu tatilleri talebi pekiştirir.",
    },
    "social_viral": {
        "data":   [50, 54, 62, 68, 74, 85, 92, 95, 78, 65, 58, 62],
        "peaks":  ["Temmuz", "Ağustos"],
        "season": "Yaz",
        "insight": "TikTok ve Instagram viral içerikleri yaz aylarında (Temmuz–Ağustos) en geniş erişime ulaşır; genç neslin yoğun ekran süresi talebi anında yükseltir.",
    },
    "evergreen": {
        "data":   [60, 58, 62, 64, 66, 64, 62, 65, 70, 74, 78, 80],
        "peaks":  ["Ekim", "Kasım", "Aralık"],
        "season": "Q4",
        "insight": "Yıl boyunca istikrarlı talep görür; Q4 kampanya döneminde (Ekim–Aralık) hafif yükseliş izlenir ve hediye alternatifi olarak öne çıkar.",
    },
}

PRODUCT_PATTERN = {
    # Kırtasiye
    "Okul Çantası":"back_to_school", "Sırt Çantası Mini":"back_to_school",
    "Beslenme Kutusu":"back_to_school", "Kalemlik Organizer":"back_to_school",
    "Termos":"winter", "Renkli Kalemler Seti":"back_to_school",
    "Fosforlu Kalem Seti":"back_to_school", "Çift Uçlu Marker Set":"back_to_school",
    "Brush Pen Kaligrafi Set":"evergreen", "Mürekkepli Dolma Kalem":"evergreen",
    "Akıllı Defter (Rocketbook)":"back_to_school", "Spiralli Defter A4":"back_to_school",
    "Yapışkanlı Not Kağıdı":"evergreen", "Bullet Journal":"new_year_fitness",
    "Haftalık Masa Planeri":"new_year_fitness", "Washi Tape Set":"social_viral",
    "Epoxy Resin Kit":"social_viral", "Suluboya Seti 36 Renk":"back_to_school",
    "Pastel Boya Seti":"back_to_school", "Post-it Dispenser":"evergreen",
    # Elektronik
    "Bluetooth Kulaklık TWS":"gift_season", "Taşınabilir Hoparlör":"gift_season",
    "GaN Şarj 65W":"gift_season", "Powerbank 20000mAh":"summer",
    "Mekanik Klavye TKL":"gift_season", "Akıllı Saat":"gift_season",
    "Robot Süpürge":"home_nesting", "LED Şerit Akıllı":"home_nesting",
    "Webcam HD 1080p":"new_year_fitness",
    # Giyim
    "Oversize T-Shirt":"spring_fashion", "Hoodie Oversize":"winter",
    "Wide Leg Jean":"spring_fashion", "Kargo Pantolon":"spring_fashion",
    "Spor Ayakkabı":"spring_fashion", "Puf Mont":"winter",
    "Platform Sandalet":"summer", "Sneaker Platform":"spring_fashion",
    "Seamless Spor Tayt":"new_year_fitness", "Yoga Pantolonu":"new_year_fitness",
    # Ev & Yaşam
    "Neon LED Tabela":"social_viral", "Mum Seti Kokulu":"home_nesting",
    "Aroma Diffuser":"home_nesting", "Hava Temizleyici":"home_nesting",
    "Mantar LED Lamba":"social_viral", "Sukulent Seti":"spring_fashion",
    "Askılı Saksı Makrome":"spring_fashion", "Kahve Demleme Set":"winter",
    # Kozmetik
    "Güneş Kremi SPF50":"summer", "Renkli Güneş Kremi":"summer",
    "BB Krem SPF 30":"summer", "Gua Sha Seti":"social_viral",
    "C Vitamini Serum":"evergreen", "Hyalüronik Asit":"evergreen",
    "Dudak Parlatıcı":"social_viral",
    # Spor
    "GPS Koşu Saati":"new_year_fitness", "Foam Roller Recovery":"new_year_fitness",
    "TPE Yoga Matı 6mm":"new_year_fitness", "Ayarlanabilir Dumbbell":"new_year_fitness",
    "Kamp Hamağı Taşınabilir":"outdoor_spring", "Ultralight Çadır":"outdoor_spring",
    "Trekking Botu Su Geçirmez":"outdoor_spring",
    # Gıda
    "Matcha Seti Premium":"social_viral", "Cold Brew Seti":"summer",
    "Whey Protein İzolat":"new_year_fitness", "Kreatin Monohidrat":"new_year_fitness",
    "Hava Fritözü 5L":"home_nesting", "Moka Pot Alüminyum":"winter",
    "Collagen Peptide Tozu":"new_year_fitness",
    # Oyuncak
    "Blind Box Figür":"gift_season", "Anime Aksiyon Figürü":"gift_season",
    "LEGO Technic Set":"gift_season", "RC Drone Kamera":"outdoor_spring",
    "Elektrikli Scooter Çocuk":"outdoor_spring",
    "Kodlama Robotu Çocuk":"back_to_school", "Manyetik Yapı Seti XL":"gift_season",
}

SUBCAT_PATTERN = {
    "Kalemler & Yazı":"back_to_school", "Defterler & Planlayıcı":"back_to_school",
    "Okul & Çanta":"back_to_school", "Sanat & Hobi":"social_viral",
    "Ofis Aksesuarı":"evergreen",
    "Ses & Müzik":"gift_season", "Telefon Aksesuarları":"evergreen",
    "Akıllı Cihazlar":"gift_season", "PC & Oyun":"gift_season", "Şarj & Güç":"gift_season",
    "Üst Giyim":"spring_fashion", "Alt Giyim":"spring_fashion", "Dış Giyim":"winter",
    "Ayakkabı":"spring_fashion", "Spor Giyim":"new_year_fitness",
    "Dekorasyon":"home_nesting", "Mutfak Aksesuarı":"home_nesting",
    "Temizlik & Düzen":"new_year_fitness", "Aydınlatma":"home_nesting",
    "Bahçe & Bitki":"spring_fashion",
    "Yüz Bakımı":"evergreen", "Güneş Koruma":"summer", "Makyaj":"social_viral",
    "Saç Bakımı":"evergreen", "Vücut Bakımı":"new_year_fitness",
    "Fitness & Ağırlık":"new_year_fitness", "Yoga & Pilates":"new_year_fitness",
    "Koşu & Kardiyo":"new_year_fitness", "Kamp & Outdoor":"outdoor_spring",
    "Aksesuarlar":"evergreen",
    "Sağlıklı Yaşam":"new_year_fitness", "Kahve & Çay":"winter",
    "Spor Beslenmesi":"new_year_fitness", "Organik & Doğal":"evergreen",
    "Mutfak Ekipmanı":"home_nesting",
    "STEM & Eğitici":"back_to_school", "Yapı & Lego":"gift_season",
    "Yaratıcılık & Sanat":"back_to_school", "Outdoor & Aktif":"outdoor_spring",
    "Koleksiyon & Figür":"gift_season",
}

SECTOR_PATTERN = {
    "kirtasiye":"back_to_school", "elektronik":"gift_season",
    "giyim":"spring_fashion", "ev_yasam":"home_nesting",
    "kozmetik":"evergreen", "spor":"new_year_fitness",
    "gida":"evergreen", "oyuncak":"gift_season",
}

# Keyword → seasonality pattern (fallback when exact name/subcat lookup misses)
_SEASON_KEYWORD_RULES: list = [
    # back_to_school
    (["okul çantası","sırt çantası","beslenme kutusu","kalemlik","renkli kalem",
       "fosforlu kalem","marker set","brush pen","kaligrafi","dolma kalem",
       "akıllı defter","spiralli defter","bullet journal","planlayıcı","ajanda",
       "suluboya","pastel boya","akrilik boya","sketch pad","lineer cetvel",
       "matematik seti","geometri","hesap makinesi","kitaplık","çocuk çanta"],
     "back_to_school"),
    # new_year_fitness
    (["dumbbell","kettlebell","barbell","resistance band","direnç bant","pull-up",
       "trx","ab roller","yoga matı","yoga mat","pilates","foam roller","yoga block",
       "gps koşu","koşu saati","atlama ipi","whey protein","kreatin","vegan protein",
       "bcaa","pre-workout","elektrolit","glutamin","haftalık planer","hedef planer"],
     "new_year_fitness"),
    # winter
    (["termos","puf mont","kışlık","bot su geçirmez","polar","yün","bere","atkı",
       "eldiven","kahve demleme","moka pot","çay demleme","ev tekstili kış"],
     "winter"),
    # summer
    (["güneş kremi","spf","renkli güneş","bb krem","platform sandalet","bikini",
       "mayo","şort","kamp hamağı","cold brew","powerbank","güneş gözlüğü",
       "havuz","plaj"],
     "summer"),
    # gift_season
    (["bluetooth kulaklık","tws","kafa üstü kulaklık","taşınabilir hoparlör",
       "mekanik klavye","akıllı saat","akıllı bileklik","drone","rc araba",
       "blind box","funko pop","anime figür","lego","manyetik yapı","oyun kolu",
       "ganşarj","gan şarj","parfüm","hediye seti"],
     "gift_season"),
    # home_nesting
    (["neon led","mum seti","aroma diffuser","hava temizleyici","mantar led",
       "robot süpürge","led şerit","yastık","yorgan","nevresim","halı","perde",
       "depolama","organizer kutu","cam kap seti","buharlı ütü","hava fritözü"],
     "home_nesting"),
    # spring_fashion
    (["oversize t-shirt","hoodie","wide leg","kargo pantolon","spor ayakkabı",
       "sneaker","triko","elbise","bluz","gömlek","sukulent","askılı saksı",
       "makrome","çiçek","bahar","ilkbahar","platform"],
     "spring_fashion"),
    # outdoor_spring
    (["kamp","ultralight çadır","uyku tulumu","trekking","baş feneri","survival",
       "hiking","açık hava","outdoor","doğa yürüyüşü","hamak","kamp tencere"],
     "outdoor_spring"),
    # social_viral
    (["washi tape","epoxy resin","slime","tie-dye","gua sha","fidget","pop-it",
       "sensory","reçine sanat","stop motion","pottery wheel","tiktok",
       "matcha","hibiskus","zerdeçal"],
     "social_viral"),
    # evergreen
    (["dolma kalem mürekkep","post-it","yapışkanlı not","webcam","usb hub",
       "şampuan","saç maskesi","el kremi","nemlendirici","c vitamini serum",
       "hyalüronik","retinol","niasinamid","gözenek temizleyici"],
     "evergreen"),
]


def get_seasonality(product_name: str, subcat: str = "", sector: str = "") -> dict:
    # 1. Exact product name match
    key = PRODUCT_PATTERN.get(product_name)
    if not key:
        # 2. Keyword match on product name
        low_p = product_name.lower()
        for keywords, pattern in _SEASON_KEYWORD_RULES:
            if any(k in low_p for k in keywords):
                key = pattern
                break
    if not key:
        # 3. Exact subcat name match
        key = SUBCAT_PATTERN.get(subcat)
    if not key:
        # 4. Keyword match on subcat name
        low_s = subcat.lower()
        for keywords, pattern in _SEASON_KEYWORD_RULES:
            if any(k in low_s for k in keywords):
                key = pattern
                break
    if not key:
        # 5. Sector fallback
        key = SECTOR_PATTERN.get(sector, "evergreen")
    return SEASONALITY_PATTERNS[key]

REGIONS = [
    "Tüm Türkiye",
    "Marmara",
    "Ege",
    "Akdeniz",
    "İç Anadolu",
    "Karadeniz",
    "Doğu Anadolu",
    "Güneydoğu Anadolu",
]
SALES_CHANNELS = ["Trendyol","Amazon TR","Instagram","Fiziksel Mağaza"]

# ── Bölgesel kanal tercihi (online vs fiziksel mağaza eğilimi) ────────────────
REGION_CHANNEL_BIAS = {
    "Tüm Türkiye":        {"trendyol":0,   "amazon_tr":0,   "instagram":0,   "store":0},
    "Marmara":            {"trendyol":7,   "amazon_tr":8,   "instagram":10,  "store":-5},
    "Ege":                {"trendyol":4,   "amazon_tr":4,   "instagram":8,   "store":-2},
    "Akdeniz":            {"trendyol":2,   "amazon_tr":2,   "instagram":5,   "store":2},
    "İç Anadolu":         {"trendyol":2,   "amazon_tr":2,   "instagram":3,   "store":3},
    "Karadeniz":          {"trendyol":-2,  "amazon_tr":-2,  "instagram":1,   "store":6},
    "Doğu Anadolu":       {"trendyol":-4,  "amazon_tr":-4,  "instagram":-2,  "store":9},
    "Güneydoğu Anadolu":  {"trendyol":-3,  "amazon_tr":-4,  "instagram":-1,  "store":9},
}

# ── Bölgesel e-ticaret penetrasyon skoru (composite skora eklenir) ────────────
REGION_BASE_SCORE_DELTA = {
    "Tüm Türkiye":        0,
    "Marmara":           +10,   # TR'nin en büyük dijital pazarı
    "Ege":               +6,    # Turizm + sofistike tüketici
    "Akdeniz":           +2,    # Turizm mevsimi ağırlıklı
    "İç Anadolu":        +1,    # Karma yapı (Ankara etkisi)
    "Karadeniz":         -4,    # Tarımsal, kırsal ağırlıklı
    "Doğu Anadolu":      -10,   # En düşük e-ticaret penetrasyonu
    "Güneydoğu Anadolu": -8,    # Fiziksel ticaret baskın
}

# ── Bölge × Sektör uyum katsayısı (bölgeye özgü ürün kategorisi talebi) ──────
REGION_SECTOR_AFFINITY = {
    "Tüm Türkiye":        {},
    "Marmara": {
        "giyim": +12, "elektronik": +10, "kozmetik": +10,
        "kirtasiye": +6,  "oyuncak": +5,  "ev_yasam": +4,
        "spor":  +3,  "gida":  +2,
    },
    "Ege": {
        "spor":  +12, "kozmetik": +8, "giyim": +8,
        "gida":  +8,  "ev_yasam": +6, "kirtasiye": +3,
        "elektronik": +2, "oyuncak": +2,
    },
    "Akdeniz": {
        "spor":  +14, "gida": +8,  "giyim": +6,
        "ev_yasam": +5, "kozmetik": +4,
        "kirtasiye": +1, "elektronik": 0, "oyuncak": +2,
    },
    "İç Anadolu": {
        "gida":  +8, "ev_yasam": +7, "kirtasiye": +6,
        "spor":  +4, "oyuncak": +4,  "kozmetik": +2,
        "giyim": +2, "elektronik": +2,
    },
    "Karadeniz": {
        "gida":  +14, "spor": +12, "ev_yasam": +8,
        "kirtasiye": +4, "oyuncak": +3,
        "giyim": -2,  "kozmetik": -3, "elektronik": -5,
    },
    "Doğu Anadolu": {
        "spor":  +10, "gida": +10, "ev_yasam": +6,
        "kirtasiye": +2, "oyuncak": +2,
        "kozmetik": -6, "elektronik": -10, "giyim": -4,
    },
    "Güneydoğu Anadolu": {
        "gida":  +12, "spor": +8, "ev_yasam": +6,
        "kirtasiye": +2, "oyuncak": +3,
        "kozmetik": -4, "elektronik": -8, "giyim": -3,
    },
}

# ── Bölge meta (UI etiket ve açıklama) ───────────────────────────────────────
REGION_META = {
    "Tüm Türkiye":        {"emoji": "🇹🇷", "desc": "Ulusal ortalama — bölge ayrımı yok"},
    "Marmara":            {"emoji": "🌆", "desc": "İstanbul, Bursa, Kocaeli · En yüksek e-ticaret"},
    "Ege":                {"emoji": "🌊", "desc": "İzmir, Muğla, Denizli · Turizm & organik yaşam"},
    "Akdeniz":            {"emoji": "☀️", "desc": "Antalya, Adana, Mersin · Turizm & outdoor"},
    "İç Anadolu":         {"emoji": "🏛️", "desc": "Ankara, Konya, Kayseri · Pratik & ev odaklı"},
    "Karadeniz":          {"emoji": "🌿", "desc": "Trabzon, Samsun, Rize · Doğa & gıda kültürü"},
    "Doğu Anadolu":       {"emoji": "🏔️", "desc": "Erzurum, Van, Malatya · Fiziksel mağaza baskın"},
    "Güneydoğu Anadolu":  {"emoji": "🌾", "desc": "Gaziantep, Şanlıurfa · Tarım & gıda odaklı"},
}

# ═══════════════════════════════════════════════════════════════════════════════
# ALT KATEGORİ VERİSİ  (5 sektör × 5 alt kategori × 4-5 ürün + Amazon)
# ═══════════════════════════════════════════════════════════════════════════════
def _p(name, g, gc, tr, trc, trv, trr, ar, arc, arv, arr, tk):
    """Kısa ProductSignals factory — Amazon alanları her versiyonla uyumlu."""
    # ProductSignals'ın Amazon alanlarına sahip olup olmadığını kontrol et
    _has_amazon = "amazon_sales_rank" in ProductSignals.__dataclass_fields__
    if _has_amazon:
        sig = ProductSignals(
            name=name,
            google_trend_score=g, google_trend_change_pct=gc,
            trendyol_sales_rank=tr, trendyol_rank_change=trc,
            trendyol_review_count=trv, trendyol_rating=trr,
            amazon_sales_rank=ar, amazon_rank_change=arc,
            amazon_review_count=arv, amazon_rating=arr,
            tiktok_trend_score=tk,
        )
    else:
        # Eski scorer.py versiyonu — Amazon alanlarını sonradan ekle
        sig = ProductSignals(
            name=name,
            google_trend_score=g, google_trend_change_pct=gc,
            trendyol_sales_rank=tr, trendyol_rank_change=trc,
            trendyol_review_count=trv, trendyol_rating=trr,
            tiktok_trend_score=tk,
        )
        sig.amazon_sales_rank  = ar
        sig.amazon_rank_change = arc
        sig.amazon_review_count = arv
        sig.amazon_rating      = arr
    return sig

SECTOR_SUBCATEGORIES: dict = {

    # ── KIRTASİYE ─────────────────────────────────────────────────────────────
    "kirtasiye": {
        "Tümü": None,

        "Yazı Gereçleri": {
            "Tümü": None,
            "Tükenmez & Roller Kalem": [
                _p("Pilot G2 Roller Kalem Seti",      72,18.0, 6, 2, 9500,4.8, 18, 3, 3800,4.6, 75),
                _p("Renkli Kalemler Seti 36",          65, 8.3, 7, 0, 8940,4.8, 20, 2, 3200,4.6, 71),
                _p("Silinebilir Tükenmez Seti",        60,10.0,12, 1, 7200,4.6, 25, 1, 2800,4.5, 65),
                _p("Termal Kalem Seti Pastel",         55,12.0,15, 2, 4200,4.6, 30, 1, 1600,4.4, 62),
                _p("Uni-ball Signo Seti 8 Renk",       68,14.0, 9, 2, 5200,4.7, 22, 2, 2100,4.5, 70),
            ],
            "Marker & Fine Liner": [
                _p("Çift Uçlu Marker Set 48 Renk",    72,18.0, 5, 3, 5600,4.7, 14, 4, 2100,4.5, 80),
                _p("Fosforlu Kalem Seti 8li",          48,-5.1,18, 0, 3200,4.4, 40,-1,  980,4.2, 55),
                _p("Staedtler Triplus Fineliner",      78,22.0, 7, 3, 6800,4.8, 15, 3, 2600,4.6, 82),
                _p("Copic Ciao Marker Başlangıç",      85,35.0, 4, 5, 3200,4.8,  9, 5, 1400,4.7, 88),
                _p("Mildliner Pastel Set 15li",        82,38.0, 5, 5, 8500,4.7,  8, 5, 3800,4.6, 86),
            ],
            "Kaligrafi & Brush Pen": [
                _p("Brush Pen Kaligrafi Set 12",       52,22.0,22, 5, 2400,4.6, 35, 3,  850,4.4, 75),
                _p("Tombow Dual Brush Pen Seti",       78,32.0, 8, 5, 4200,4.7, 12, 5, 1800,4.6, 84),
                _p("Kaligrafi Başlangıç Seti",         65,20.0,12, 3, 3800,4.6, 20, 3, 1400,4.5, 72),
                _p("Nib & Mürekkep Kaligrafi Seti",    58,15.0,18, 2, 2200,4.5, 28, 2,  860,4.4, 68),
            ],
            "Dolma Kalem & Mürekkep": [
                _p("Mürekkepli Dolma Kalem Orta",      58,12.0,15, 1, 1800,4.5, 28, 2,  760,4.3, 60),
                _p("Lamy Safari Dolma Kalem",          82,28.0, 7, 4, 2800,4.8,  9, 4, 1200,4.7, 80),
                _p("Pilot Metropolitan Dolma",         75,22.0, 9, 3, 2200,4.7, 14, 3,  980,4.6, 76),
                _p("Şişe Mürekkep Seti 5 Renk",       68,18.0,12, 3, 3500,4.6, 18, 3, 1500,4.5, 72),
                _p("Mürekkep Kartuş Seti 30lu",       42, 3.0,30, 0, 4800,4.3, 45, 0, 1800,4.2, 40),
            ],
        },

        "Defter & Planlama": {
            "Tümü": None,
            "Bullet Journal & Dotted": [
                _p("Bullet Journal Dotted A5",         70,25.0, 9, 4, 3200,4.8, 22, 3, 1100,4.6, 82),
                _p("Leuchtturm1917 A5 Noktalı",        80,30.0, 8, 4, 4500,4.8, 10, 4, 2000,4.7, 85),
                _p("Akıllı Defter Rocketbook",         58,15.2,12, 0, 1830,4.5, 35, 2,  620,4.2, 62),
                _p("Scribbles That Matter Dotted",     65,20.0,14, 3, 2800,4.6, 18, 3, 1100,4.5, 72),
                _p("Nuuna Notebook Squared",           68,22.0,12, 3, 2200,4.7, 16, 3,  900,4.5, 74),
            ],
            "Spiral & Çizgili Defter": [
                _p("Spiralli Defter A4 Çizgili",       52, 3.7,22, 0, 2100,4.3, 50,-1,  420,4.0, 38),
                _p("Oxford Spiral Defter Seti",        58, 8.0,18, 1, 5800,4.5, 28, 1, 2200,4.3, 52),
                _p("Paperblanks Ciltli Defter",        72,18.0,10, 2, 3200,4.6, 14, 2, 1400,4.5, 70),
                _p("Clairefontaine Defter A5",         60,12.0,16, 1, 2800,4.5, 22, 1, 1100,4.4, 62),
            ],
            "Planlayıcı & Ajanda": [
                _p("Haftalık Masa Planeri",            62,10.0,18, 2, 2800,4.5, 38, 1,  780,4.3, 65),
                _p("Yıllık Ajanda 2025 A5",            75,20.0,10, 3, 6500,4.6, 16, 3, 2800,4.5, 78),
                _p("Aylık Hedef Planlayıcı",           68,22.0,12, 3, 3200,4.6, 18, 3, 1400,4.5, 72),
                _p("Hobonichi Style Planner",          82,38.0, 6, 5, 2200,4.8,  8, 5, 1100,4.7, 88),
                _p("Yapışkanlı Not Kağıdı Seti",       44, 2.1,30, 0, 5600,4.6, 45, 0, 1800,4.4, 48),
            ],
        },

        "Sanat & Yaratıcılık": {
            "Tümü": None,
            "Suluboya & Akrilik": [
                _p("Suluboya Seti 36 Renk Pro",        68,20.0, 8, 3, 4200,4.7, 18, 4, 1600,4.5, 78),
                _p("Pastel Boya Seti 48 Renk",         62,15.0,12, 2, 3500,4.6, 28, 2, 1200,4.4, 70),
                _p("Akrilik Boya Seti 24 Renk",        58,12.0,15, 2, 4800,4.5, 24, 2, 1800,4.3, 65),
                _p("Suluboya Fırça Seti Pro",          65,15.0,12, 2, 3200,4.6, 18, 2, 1400,4.4, 68),
                _p("Çizim Defteri A3 Profesyonel",     55, 5.0,20, 0, 2800,4.5, 40, 1,  850,4.2, 58),
            ],
            "Washi Tape & Sticker": [
                _p("Washi Tape Set 30 Desen",          82,38.0, 4, 5, 6500,4.8,  8, 6, 3200,4.7, 90),
                _p("Aesthetic Sticker Seti 500+",      78,32.0, 6, 5, 8200,4.7,  9, 5, 4200,4.6, 88),
                _p("Journaling Sticker Pack Kore",     85,42.0, 5, 6, 5800,4.8,  7, 6, 2800,4.7, 92),
                _p("Foil Sticker Seti Metalik",        72,28.0, 8, 4, 4500,4.7, 11, 4, 2200,4.5, 80),
                _p("Masking Tape Pastel Set",          68,22.0,10, 3, 3800,4.6, 14, 3, 1700,4.5, 74),
            ],
            "Epoxy & DIY Sanat": [
                _p("Epoxy Resin Başlangıç Kiti",       58,28.0,18, 4, 1800,4.4, 35, 3,  680,4.2, 72),
                _p("Resin Pigment & Simli Set",        65,32.0,14, 5, 2400,4.5, 20, 4, 1000,4.4, 78),
                _p("Epoxy Kalıp Seti Silikon",         60,25.0,16, 4, 3200,4.5, 22, 4, 1400,4.3, 75),
                _p("UV Resin Kiti Şeffaf",             70,30.0,12, 4, 2800,4.6, 16, 4, 1200,4.4, 80),
            ],
        },

        "Okul & Öğrenci": {
            "Tümü": None,
            "Okul Çantaları": [
                _p("Okul Çantası Ergonomik",           88,45.0, 1, 0,12000,4.9,  5, 5, 4800,4.7, 92),
                _p("Sırt Çantası Mini Trend",          66, 8.0,10, 0, 7200,4.7, 25, 1, 2600,4.5, 74),
                _p("Liseli Çanta Aesthetic",           80,35.0, 4, 4, 9500,4.7,  8, 4, 4200,4.6, 88),
                _p("Laptop Sırt Çantası 15.6",         72,18.0, 7, 2,14000,4.6, 12, 2, 6500,4.5, 76),
            ],
            "Okul Seti & Aksesuar": [
                _p("Termos 500ml Çelik",               72,28.5, 3, 0, 4520,4.7, 12, 3, 1800,4.5, 85),
                _p("Beslenme Kutusu Bölmeli",          60,12.0, 8, 1, 3800,4.6, 18, 2, 1400,4.4, 68),
                _p("Kırtasiye Seti 8li Öğrenci",       55,10.0,20, 1, 5200,4.5, 32, 1, 2000,4.3, 60),
                _p("Su Matarası BPA Free 750ml",       65,15.0,11, 2, 8500,4.6, 20, 2, 3500,4.4, 70),
                _p("Kalemlik Organizer Geniş",         38,-8.0,42,-2, 1200,4.2, 75,-1,  280,4.0, 32),
            ],
        },

        "Ofis & Organizasyon": {
            "Tümü": None,
            "Masa Düzeni": [
                _p("Masa Organizer Bambu 6 Bölmeli",   58,10.0,14, 1, 4200,4.6, 30, 2, 1500,4.4, 62),
                _p("Post-it Dispenser Premium",        55, 8.0,20, 2, 5200,4.6, 38, 1, 1800,4.4, 55),
                _p("Kalemlik Set Seramik",             62,15.0,16, 2, 3500,4.6, 25, 2, 1300,4.4, 68),
                _p("Masa Pedi Geniş 90x45cm",          70,20.0,10, 3, 6800,4.5, 18, 3, 2800,4.4, 72),
                _p("Bant Dispenser Dekoratif",         38, 0.5,40,-1, 1800,4.2, 70,-1,  480,4.0, 35),
            ],
            "Dosyalama & Arşiv": [
                _p("Dosya Klasörü A4 Renkli Seti",     50, 5.0,25, 1, 3600,4.5, 45, 0,  980,4.3, 45),
                _p("Zımba Seti Elektrikli",            65,12.0,18, 1, 2800,4.5, 28, 1, 1100,4.3, 58),
                _p("Etiket Yazıcı Kablosuz",           75,30.0,12, 4, 4200,4.6, 18, 4, 1900,4.5, 78),
                _p("Delgeç 2li Güçlü",                 42, 2.0,38, 0, 2200,4.3, 55, 0,  750,4.1, 38),
            ],
        },
    },

    # ── ELEKTRONİK ──────────────────────────────────────────────────────────────
    "elektronik": {
        "Tümü": None,

        "Ses & Müzik": {
            "Tümü": None,
            "Kulak İçi & TWS": [
                _p("Bluetooth Kulaklık TWS",    90,35.0, 2, 3,25000,4.7,  4, 4,12000,4.6, 88),
                _p("Kulak İçi Aktif GN",        85,28.0, 3, 4,14000,4.6,  6, 5, 6800,4.5, 84),
                _p("ANC Gürültü Engelleme TWS", 88,32.0, 3, 5,18000,4.7,  5, 5, 9200,4.6, 88),
                _p("Spor Kulak İçi IP67",       72,20.0, 6, 3, 9500,4.5, 10, 3, 4800,4.4, 76),
            ],
            "Kafa Üstü Kulaklık": [
                _p("Kablolu Oyuncu Kulaklık",   74,18.0, 8, 2, 8500,4.6, 15, 3, 4200,4.4, 72),
                _p("Stüdyo Kulaklık",           65,10.0,18, 1, 4200,4.5, 25, 1, 2100,4.4, 58),
                _p("Wireless Kafa Üstü ANC",    80,25.0, 5, 4,12000,4.6,  8, 4, 6500,4.5, 82),
                _p("Oyuncu 7.1 Surround",       75,22.0, 6, 3, 9800,4.6, 10, 3, 5200,4.5, 78),
            ],
            "Hoparlör & Mikrofon": [
                _p("Taşınabilir Hoparlör",      78,22.0, 5, 3,18000,4.7,  8, 3, 8500,4.5, 80),
                _p("Masaüstü Studio Hoparlör",  68,15.0,10, 2, 6200,4.5, 16, 2, 3400,4.4, 68),
                _p("USB Kondenser Mikrofon",    75,30.0, 6, 4, 8500,4.6,  9, 4, 4800,4.5, 80),
                _p("Podcast Yayın Mikrofonu",   70,25.0, 8, 3, 5200,4.5, 12, 3, 3000,4.4, 74),
            ],
        },

        "Bilgisayar Aksesuarı": {
            "Tümü": None,
            "Klavye & Fare": [
                _p("Mekanik Klavye TKL",        80,25.0, 5, 4,12000,4.6,  9, 4, 6500,4.5, 82),
                _p("Oyuncu Mouse RGB",           72,15.0, 8, 2, 9800,4.5, 15, 2, 5200,4.4, 70),
                _p("Wireless Klavye & Fare Set", 68,18.0,10, 2, 7200,4.5, 14, 2, 3800,4.4, 72),
                _p("Ergonomik Dikey Mouse",      65,22.0,12, 3, 5500,4.5, 18, 3, 3000,4.4, 70),
            ],
            "Hub & Ekran": [
                _p("USB Hub 10-in-1",            75,20.0, 6, 2, 8200,4.5, 12, 3, 4200,4.4, 68),
                _p("USB-C Docking Station",      80,28.0, 5, 4, 9500,4.6,  8, 4, 5200,4.5, 78),
                _p("Webcam HD 1080p",            65,18.0,12, 2, 4200,4.5, 20, 2, 2400,4.4, 60),
                _p("Laptop Stand Alüminyum",     68,12.0,10, 2, 6200,4.4, 18, 2, 3400,4.3, 65),
            ],
        },

        "Telefon & Tablet": {
            "Tümü": None,
            "Kılıf & Koruyucu": [
                _p("MagSafe Manyetik Cüzdan",   72,30.0, 6, 4, 9500,4.5, 10, 5, 5200,4.4, 82),
                _p("Ekran Koruyucu Kırılmaz",   55, 3.0, 3, 0,42000,4.2,  5, 0,22000,4.1, 48),
                _p("Darbeye Dayanıklı Kılıf",   60, 5.0, 4, 0,38000,4.4,  6, 0,20000,4.3, 55),
                _p("Magsafe Silikon Kılıf",      65,12.0, 6, 2,28000,4.5,  9, 2,15000,4.4, 68),
            ],
            "Şarj & Aksesuar": [
                _p("Manyetik Şarj Kablosu",     68,30.0,10, 3, 6700,4.4, 18, 4, 3400,4.3, 72),
                _p("Telefon Tutucu Araç MagSafe",62, 8.0, 8, 1,12000,4.4, 14, 2, 6200,4.3, 60),
                _p("Selfie Işığı Ring Light",   70,22.0, 8, 3, 8500,4.5, 12, 3, 4600,4.4, 74),
                _p("Tablet Klavye Kılıf",        72,20.0, 7, 2, 6200,4.5, 11, 2, 3400,4.4, 72),
            ],
        },

        "Akıllı Cihaz": {
            "Tümü": None,
            "Giyilebilir Teknoloji": [
                _p("Akıllı Saat",               82,22.0, 4, 3,18000,4.6,  7, 3, 9200,4.5, 80),
                _p("Fitness Bileklik",           75,18.0, 7, 2,14000,4.5, 12, 2, 6800,4.4, 74),
                _p("Akıllı Yüzük Sağlık",       80,38.0, 5, 5, 5200,4.6,  8, 5, 3200,4.5, 85),
                _p("Spor GPS Saati",             85,28.0, 3, 4,12000,4.7,  5, 4, 6800,4.6, 83),
            ],
            "Akıllı Ev": [
                _p("LED Şerit Akıllı WiFi",     75,42.0, 5, 5, 9500,4.4, 10, 5, 5800,4.3, 91),
                _p("Robot Süpürge LiDAR",       88,30.0, 2, 4,22000,4.7,  4, 3,12000,4.6, 82),
                _p("Akıllı Terazi Vücut",       58, 8.0,20, 1, 5800,4.4, 28, 1, 3200,4.3, 55),
                _p("Akıllı Priz WiFi",          62,18.0,12, 2, 8500,4.4, 18, 2, 4800,4.3, 65),
            ],
        },

        "Şarj & Güç": {
            "Tümü": None,
            "Powerbank & Adaptör": [
                _p("Powerbank 20000mAh",        80,20.0, 3, 2,28000,4.6,  5, 2,14000,4.5, 72),
                _p("GaN Şarj 65W 3-Port",       85,40.0, 4, 5,12000,4.6,  7, 5, 6500,4.5, 85),
                _p("Kablosuz Şarj Pad 15W",     70,18.0, 9, 3, 9500,4.4, 15, 3, 5200,4.3, 74),
                _p("MagSafe Kablosuz Şarj",     75,25.0, 6, 4, 8200,4.5, 10, 4, 4800,4.4, 80),
            ],
            "Enerji Çözümleri": [
                _p("Güneş Enerjili Powerbank",  58,22.0,18, 4, 3200,4.3, 30, 3, 1800,4.2, 65),
                _p("UPS 650VA Offline",         48, 5.0,28, 0, 4200,4.4, 40, 0, 2400,4.3, 38),
                _p("Araç Şarj Adaptörü 65W",   62,15.0,12, 2, 9800,4.4, 18, 2, 5500,4.3, 65),
                _p("Masaüstü Şarj İstasyonu",   70,20.0, 8, 3, 7200,4.5, 12, 3, 4000,4.4, 72),
            ],
        },
    },

    # ── GİYİM ────────────────────────────────────────────────────────────────────
    "giyim": {
        "Tümü": None,

        "Üst Giyim": {
            "Tümü": None,
            "T-Shirt & Crop Top": [
                _p("Oversize T-Shirt",          85,50.0, 1, 5,45000,4.8,  3, 4,22000,4.7, 95),
                _p("Basic Crop Top",            72,28.0, 5, 3,18000,4.5,  8, 3, 9000,4.4, 88),
                _p("Baskılı Graphic Tee",       75,30.0, 4, 4,22000,4.6,  6, 4,11000,4.5, 85),
                _p("Polo Yaka T-Shirt",         62,12.0, 9, 1,14000,4.4, 14, 1, 7200,4.3, 65),
            ],
            "Kazak & Hoodie": [
                _p("Hoodie Oversize",           80,32.0, 3, 4,28000,4.7,  6, 3,14000,4.6, 88),
                _p("Bisiklet Yaka Kazak",       50, 5.0,18, 0, 6000,4.2, 30, 0, 2800,4.1, 50),
                _p("Zip-Up Kapüşonlu",          72,22.0, 6, 3,16000,4.5, 10, 3, 8500,4.4, 80),
                _p("Crop Kazak Ribana",         68,25.0, 7, 3,12000,4.5, 12, 3, 6500,4.4, 78),
            ],
            "Bluz & Gömlek": [
                _p("Saten Bluz",                68,20.0, 8, 2,12000,4.5, 15, 2, 6200,4.4, 75),
                _p("Oversize Keten Gömlek",     70,25.0, 7, 3,14000,4.5, 12, 3, 7500,4.4, 80),
                _p("Fırfırlı Şifon Bluz",       62,18.0,10, 2, 9500,4.4, 16, 2, 5000,4.3, 70),
                _p("Denim Gömlek",              65,15.0, 8, 1,11000,4.4, 14, 1, 6000,4.3, 68),
            ],
        },

        "Alt Giyim": {
            "Tümü": None,
            "Pantolon & Jean": [
                _p("Wide Leg Jean",             82,35.0, 4, 5,18000,4.6,  7, 4, 9500,4.5, 86),
                _p("Kargo Pantolon",            78,38.0, 3, 4,22000,4.6,  6, 3,11000,4.5, 89),
                _p("Palazzo Pantolon",          60,22.0,10, 3, 7500,4.5, 18, 2, 3800,4.4, 70),
                _p("Mom Jean Yırtık",           75,28.0, 5, 4,15000,4.5,  9, 4, 8000,4.4, 82),
            ],
            "Etek & Tayt": [
                _p("Mini Etek",                 70,25.0, 7, 3,14000,4.5, 12, 3, 7200,4.4, 82),
                _p("Maxi Etek Şifon",           62,18.0,10, 2,10000,4.4, 16, 2, 5500,4.3, 72),
                _p("Denim Şort",                68,22.0, 8, 3,12000,4.5, 12, 3, 6500,4.4, 78),
                _p("Deri Görünümlü Tayt",       55,10.0,12, 1,14000,4.3, 22, 1, 7000,4.2, 68),
            ],
        },

        "Dış Giyim & Ceket": {
            "Tümü": None,
            "Ceket & Yelek": [
                _p("Bomber Ceket",              65,15.0, 8, 1, 9000,4.4, 14, 1, 4500,4.3, 75),
                _p("Denim Ceket",               68,20.0, 7, 3,10000,4.5, 12, 2, 5200,4.4, 78),
                _p("Örgü Yelek",                55,10.0,15, 1, 6500,4.3, 25, 1, 3200,4.2, 60),
                _p("Blazer Casual",             72,20.0, 6, 2,12000,4.5, 10, 2, 6500,4.4, 76),
            ],
            "Mont & Kaban": [
                _p("Puf Mont Oversize",         80,30.0, 3, 4,16000,4.6,  5, 3, 8500,4.5, 82),
                _p("Trençkot",                  72,18.0, 5, 2,12000,4.6,  9, 2, 6200,4.5, 72),
                _p("Kürklü İç Astarlı Mont",    75,22.0, 5, 3,12000,4.6,  8, 3, 6800,4.5, 80),
                _p("Su Geçirmez Yağmurluk",     65,15.0, 9, 2, 8500,4.4, 14, 2, 4500,4.3, 68),
            ],
        },

        "Ayakkabı & Çanta": {
            "Tümü": None,
            "Spor & Günlük Ayakkabı": [
                _p("Spor Ayakkabı",             80,20.0, 2, 2,38000,4.7,  3, 2,20000,4.6, 82),
                _p("Sneaker Platform",           82,35.0, 4, 5,14000,4.6,  7, 4, 7500,4.5, 88),
                _p("Loafer",                    60, 8.0,12, 0, 9500,4.4, 20, 0, 5000,4.3, 62),
                _p("Kolej Bağcıklı",            65,15.0, 8, 2,12000,4.5, 12, 2, 6500,4.4, 72),
            ],
            "Sandalet & Bot": [
                _p("Platform Sandalet",         75,30.0, 5, 4,16000,4.6,  8, 3, 8500,4.5, 85),
                _p("Bot (Chelsea)",             68,12.0, 8, 1,12000,4.5, 14, 1, 6200,4.4, 70),
                _p("Kovboy Bot",                72,25.0, 6, 3,10000,4.5, 10, 3, 5500,4.4, 78),
                _p("Şeffaf Topuklu Sandalet",   65,20.0, 8, 3, 9500,4.5, 12, 3, 5000,4.4, 75),
            ],
        },

        "Spor Giyim": {
            "Tümü": None,
            "Fitness & Yoga Giyim": [
                _p("Seamless Spor Tayt",        80,30.0, 3, 4,18000,4.6,  5, 4, 9500,4.5, 88),
                _p("Spor Sütyeni",              68,18.0, 6, 2,16000,4.5, 10, 2, 8500,4.4, 78),
                _p("Yoga Pantolonu",            72,20.0, 4, 3,22000,4.7,  7, 3,12000,4.6, 80),
                _p("Crop Spor Üst",             65,22.0, 7, 3,14000,4.5, 11, 3, 7800,4.4, 78),
            ],
            "Koşu & Teknik Giyim": [
                _p("Koşu Üstü Teknik",          65,15.0, 8, 2,14000,4.5, 14, 2, 7500,4.4, 72),
                _p("Termal İçlik Set",           55,10.0,15, 1, 8000,4.3, 22, 1, 4200,4.2, 55),
                _p("Rüzgarlık Hafif",            68,18.0, 8, 2,10000,4.5, 12, 2, 5500,4.4, 72),
                _p("Spor Şort 2-in-1",           60,15.0,10, 2,12000,4.4, 16, 2, 6500,4.3, 65),
            ],
        },
    },

    # ── EV & YAŞAM ───────────────────────────────────────────────────────────────
    "ev_yasam": {
        "Tümü": None,

        "Dekorasyon": {
            "Tümü": None,
            "Duvar & Tablo": [
                _p("Makrome Duvar Süsü",        44,30.0,22, 4, 3400,4.6, 40, 3, 1600,4.4, 90),
                _p("Çerçeve Seti Galerisi",     62,15.0, 8, 2, 8500,4.5, 15, 2, 4200,4.3, 70),
                _p("Neon LED Tabela",            88,50.0, 3, 6, 5800,4.5,  5, 6, 3200,4.4, 92),
                _p("Poster Çerçeve Siyah",      55,10.0,14, 1, 7200,4.4, 22, 1, 3800,4.3, 60),
            ],
            "Mum & Aroma": [
                _p("Mum Seti Kokulu",           58,12.0,10, 2,12000,4.7, 18, 2, 6200,4.5, 88),
                _p("Aroma Diffuser Bambu",      75,32.0, 4, 4,22000,4.8,  7, 4,12000,4.6, 85),
                _p("Oda Kokusu Reed",            52,10.0,16, 1, 9500,4.5, 24, 1, 5200,4.4, 65),
                _p("Wax Melt Starter Kit",      60,18.0,12, 3, 5200,4.6, 18, 3, 2800,4.4, 72),
            ],
            "Dekoratif Aksesuar": [
                _p("Dekoratif Yastık",          52, 8.0,14, 1,18000,4.4, 24, 1, 8500,4.3, 65),
                _p("Seramik Vazo Seti",         60,15.0,12, 2, 6800,4.5, 18, 2, 3600,4.4, 70),
                _p("Ahşap Dekoratif Harf",      48,10.0,20, 1, 4200,4.4, 30, 1, 2200,4.3, 55),
                _p("Kristal Dekor Seti",        65,22.0,10, 3, 5500,4.5, 15, 3, 3000,4.4, 72),
            ],
        },

        "Mutfak & Kahve": {
            "Tümü": None,
            "Kahve & Demleme": [
                _p("Kahve Demleme Set V60",     72,22.0, 5, 3,12000,4.7,  9, 3, 6500,4.6, 80),
                _p("Cold Brew Sürahi",          68,25.0, 7, 3, 7500,4.6, 11, 3, 4200,4.5, 75),
                _p("Moka Pot Alüminyum",        65,15.0, 9, 1,10000,4.6, 14, 1, 5500,4.4, 68),
                _p("Kahve Değirmeni Manuel",    70,20.0, 8, 2, 8200,4.6, 12, 2, 4600,4.5, 72),
            ],
            "Mutfak Aksesuarı": [
                _p("Cam Saklama Kapları Seti",  48,15.0,18, 2, 6200,4.5, 28, 2, 3200,4.3, 60),
                _p("Bambu Kesme Tahtası",       55, 8.0,14, 1, 8200,4.5, 22, 1, 4200,4.4, 58),
                _p("Yemek Hazırlama Seti",      68,18.0, 6, 2, 9500,4.5, 12, 2, 5200,4.4, 72),
                _p("Salata Spinner",            42, 5.0,28, 0, 4500,4.3, 40, 0, 2200,4.2, 45),
            ],
        },

        "Aydınlatma": {
            "Tümü": None,
            "Dekoratif Aydınlatma": [
                _p("Mantar LED Lamba",          82,45.0, 4, 6, 6800,4.6,  8, 5, 3800,4.4, 92),
                _p("Neon Flex Lamba Özel",      78,40.0, 5, 5, 5200,4.5,  8, 5, 3000,4.4, 88),
                _p("Kristal Gece Lambası",      65,22.0,10, 3, 4800,4.5, 16, 3, 2600,4.4, 72),
                _p("Yıldız Projeksiyonu",       72,28.0, 7, 4, 7500,4.6, 11, 4, 4200,4.5, 80),
            ],
            "Fonksiyonel Aydınlatma": [
                _p("LED Şerit Akıllı WiFi",     75,42.0, 5, 5, 9500,4.4, 10, 5, 5800,4.3, 91),
                _p("Masa Lambası Dokunma",      68,20.0, 8, 3, 5800,4.5, 14, 3, 3200,4.4, 72),
                _p("Güneş Pilli Bahçe Işık",    52,15.0,18, 2, 4200,4.4, 28, 2, 2200,4.3, 60),
                _p("Gece Lambası LED Sensör",   60,18.0,12, 2, 7200,4.5, 20, 2, 3800,4.4, 70),
            ],
        },

        "Organizasyon & Temizlik": {
            "Tümü": None,
            "Dolap & Raf Düzeni": [
                _p("Bambu Organizer Çekmece",   62,25.0, 8, 3, 7800,4.6, 14, 3, 4200,4.4, 80),
                _p("Dolap İçi Düzenleyici",     55, 8.0,16, 1,10000,4.4, 25, 1, 5500,4.3, 60),
                _p("Vakumlu Saklama Torbası",   48,10.0,22, 1, 8500,4.4, 32, 1, 4500,4.3, 52),
                _p("Modüler Raf Sistemi",       65,18.0,10, 2, 6200,4.5, 15, 2, 3400,4.4, 68),
            ],
            "Hava Kalitesi": [
                _p("Hava Temizleyici HEPA",     82,40.0, 2, 4,15000,4.7,  4, 4, 8500,4.6, 78),
                _p("Nem Ölçer Dijital",         48,10.0,20, 1, 6200,4.4, 30, 1, 3200,4.3, 52),
                _p("Aromaterapi Diffuser",      68,22.0, 8, 3,12000,4.6, 12, 3, 6800,4.5, 75),
                _p("Ozon Temizleyici Mini",     55,15.0,18, 2, 4800,4.4, 26, 2, 2600,4.3, 62),
            ],
        },

        "Bahçe & Bitki": {
            "Tümü": None,
            "Saksı & Düzenleme": [
                _p("Mini Saksı Seti Seramik",   60,20.0,10, 3, 6500,4.6, 18, 3, 3400,4.4, 75),
                _p("Askılı Saksı Makrome",      70,28.0, 7, 4, 5200,4.6, 12, 4, 2800,4.5, 82),
                _p("Teraryum Cam Set",          65,22.0,10, 3, 4800,4.5, 15, 3, 2600,4.4, 72),
                _p("Saksı Altlığı Bambu Seti",  45, 8.0,25, 0, 3800,4.3, 38, 0, 2000,4.2, 48),
            ],
            "Bitki Bakım & Yetiştirme": [
                _p("Sukulent Seti 6'lı",        55,12.0,14, 2, 8200,4.5, 22, 2, 4400,4.4, 68),
                _p("Hidroponik Başlangıç Kiti", 68,35.0, 9, 5, 2800,4.5, 15, 5, 1600,4.4, 78),
                _p("Bitki Toprağı Premium",     45, 5.0,25, 0, 4800,4.3, 38, 0, 2500,4.2, 48),
                _p("Gübre Seti Organik",        42, 8.0,28, 1, 3600,4.3, 42, 1, 1900,4.2, 45),
            ],
        },
    },

    # ── KOZMETİK ─────────────────────────────────────────────────────────────────
    "kozmetik": {
        "Tümü": None,

        "Yüz Bakımı": {
            "Tümü": None,
            "Serum & Krem": [
                _p("C Vitamini Serum",          88,45.0, 1, 5,35000,4.8,  2, 5,18000,4.7, 92),
                _p("Hyalüronik Asit Serum",     78,35.0, 3, 4,22000,4.9,  5, 4,12000,4.7, 85),
                _p("Retinol Krem",              72,38.0, 6, 4, 8200,4.8, 10, 4, 4500,4.6, 82),
                _p("Niasinamid Serum",          80,40.0, 4, 5,16000,4.8,  7, 5, 9000,4.7, 88),
            ],
            "Güneş Koruma": [
                _p("Güneş Kremi SPF50",         82,55.0, 2, 6,28000,4.7,  3, 5,15000,4.6, 88),
                _p("Renkli Güneş Kremi",        72,30.0, 5, 4, 8500,4.6,  9, 4, 4800,4.5, 80),
                _p("BB Krem SPF 30",            68,20.0, 8, 2,12000,4.6, 14, 2, 6500,4.4, 72),
                _p("Yüz Güneş Spreyi",          65,22.0,10, 3, 7800,4.5, 16, 3, 4200,4.4, 75),
            ],
            "Temizlik & Tonik": [
                _p("Gözenek Temizleyici",       60,18.0, 9, 2, 9500,4.5, 16, 2, 5200,4.4, 75),
                _p("Misel Suyu",                55,10.0,14, 0,18000,4.4, 22, 0, 9800,4.3, 58),
                _p("Exfoliating Tonik AHA",     72,28.0, 6, 3, 8200,4.6, 10, 3, 4600,4.5, 80),
                _p("Çay Ağacı Yüz Toniği",     55,15.0,14, 2, 6800,4.4, 20, 2, 3800,4.3, 65),
            ],
        },

        "Makyaj": {
            "Tümü": None,
            "Göz & Dudak": [
                _p("Tüp Maskara Lash Tubing",   70,20.0, 5, 2,18000,4.6,  8, 2, 9500,4.5, 80),
                _p("Dudak Parlatıcı Cam",       65,28.0, 7, 3,14000,4.5, 12, 3, 7500,4.4, 90),
                _p("Göz Kalemi Sıvı",           68,15.0, 6, 1,16000,4.5,  9, 1, 8800,4.4, 72),
                _p("Lip Liner Seti",            62,20.0, 8, 2,10000,4.4, 13, 2, 5800,4.3, 70),
            ],
            "Ten & Allık": [
                _p("Fondöten SPF 20",           72,15.0, 4, 1,24000,4.6,  6, 1,13000,4.5, 75),
                _p("Blush Stick Krem",          78,35.0, 6, 4,12000,4.6, 10, 4, 6800,4.5, 88),
                _p("Highlighter Tozu",          65,22.0,10, 3, 9500,4.5, 16, 3, 5200,4.4, 78),
                _p("Setting Spray Matlık",      62,18.0, 8, 2, 8500,4.4, 13, 2, 4800,4.3, 68),
            ],
            "Fırça & Aplikatör": [
                _p("Makyaj Fırça Seti 16'lı",   72,25.0, 6, 3, 9500,4.6,  9, 3, 5500,4.5, 78),
                _p("Beauty Blender Seti",        65,18.0, 8, 2,14000,4.5, 12, 2, 8000,4.4, 72),
                _p("Makyaj Temizleme Pedi",     55,10.0,15, 1,10000,4.4, 22, 1, 5800,4.3, 60),
                _p("Silikon Yüz Masaj Aleti",   70,22.0, 7, 3, 7500,4.5, 11, 3, 4200,4.4, 74),
            ],
        },

        "Saç Bakımı": {
            "Tümü": None,
            "Şampuan & Krem": [
                _p("Doğal Sülfatsız Şampuan",   55,10.0,12, 0,11000,4.4, 20, 0, 5800,4.3, 65),
                _p("Saç Maskesi Keratin",       68,22.0, 7, 3, 8500,4.6, 12, 3, 4500,4.5, 74),
                _p("Deep Conditioning Maske",   65,18.0, 8, 2, 7200,4.5, 13, 2, 4000,4.4, 70),
                _p("Saç Dökülme Şampuanı",      60,15.0,10, 1, 9500,4.4, 16, 1, 5200,4.3, 65),
            ],
            "Yağ & Serum": [
                _p("Argan Yağı 100ml",          72,18.0, 5, 2,14000,4.7,  8, 2, 7500,4.5, 78),
                _p("Saç Serumu Düzleştirici",   65,20.0, 8, 2, 9800,4.5, 14, 2, 5200,4.4, 72),
                _p("Isı Koruyucu Sprey",        58,12.0,14, 1, 7200,4.4, 22, 1, 3800,4.3, 65),
                _p("Hint Yağı Saç Bakım",       60,15.0,12, 2, 8500,4.5, 18, 2, 4600,4.4, 68),
            ],
        },

        "Vücut & El Bakımı": {
            "Tümü": None,
            "Vücut Bakım": [
                _p("Vücut Peeling",             62,18.0, 8, 2, 9500,4.6, 14, 2, 5200,4.5, 70),
                _p("Nemlendirici Losyon",       58,10.0,10, 1,18000,4.5, 16, 1, 9800,4.4, 62),
                _p("Vücut Yağı Kuru",           70,25.0, 6, 3, 6800,4.6, 10, 3, 3800,4.5, 80),
                _p("Self-Tanner Köpük",         68,22.0, 8, 3, 5500,4.4, 12, 3, 3200,4.3, 72),
            ],
            "Masaj & Ritual": [
                _p("Gua Sha Seti Rose Quartz",  84,42.0, 3, 5, 8200,4.6,  5, 5, 4800,4.5, 88),
                _p("El Kremi İntensif",         48, 5.0,20, 0,12000,4.4, 30, 0, 6500,4.3, 52),
                _p("Cupping Set Silikon",       65,20.0,10, 3, 5800,4.5, 15, 3, 3400,4.4, 72),
                _p("Banyo Tuzu Himalaya",       55,12.0,14, 1, 8500,4.4, 20, 1, 4800,4.3, 60),
            ],
        },
    },

    # ── SPOR & OUTDOOR ───────────────────────────────────────────────────────────
    "spor": {
        "Tümü": None,

        "Fitness & Güç": {
            "Tümü": None,
            "Ağırlık & Barbell": [
                _p("Ayarlanabilir Dumbbell",    82,38.0, 4, 5,12000,4.7,  6, 5, 6200,4.6, 86),
                _p("Kettlebell Adjustable",     75,30.0, 7, 4, 8500,4.6, 12, 4, 4500,4.5, 80),
                _p("Ağırlık Yeleği 10kg",       65,20.0,12, 2, 5200,4.5, 18, 2, 2800,4.4, 68),
                _p("Barbell + Plaka Seti",      78,25.0, 5, 3, 7200,4.6,  8, 3, 4000,4.5, 78),
            ],
            "Direnç & Fonksiyonel": [
                _p("Resistance Band Pro Seti",  78,35.0, 5, 5, 9800,4.7,  9, 4, 5200,4.5, 82),
                _p("Pull-Up Bar Kapı",          58,15.0,16, 1, 6800,4.5, 22, 1, 3600,4.3, 62),
                _p("TRX Askı Sistemi",          72,25.0, 7, 3, 5500,4.5, 11, 3, 3200,4.4, 75),
                _p("Ab Roller Pro",             62,18.0,10, 2, 8200,4.5, 15, 2, 4500,4.4, 66),
            ],
        },

        "Yoga & Pilates": {
            "Tümü": None,
            "Mat & Zemin": [
                _p("TPE Yoga Matı 6mm",         72,22.0, 6, 3,14000,4.6, 10, 3, 7500,4.5, 78),
                _p("Pilates Topu 65cm",         62,15.0, 9, 2, 8500,4.5, 15, 2, 4500,4.4, 66),
                _p("Kork Yoga Matı",            68,20.0, 8, 3, 6500,4.5, 12, 3, 3500,4.4, 72),
                _p("Yoga Mat Çantası",          48, 8.0,22, 0, 5200,4.3, 32, 0, 2600,4.2, 50),
            ],
            "Aksesuar & Denge": [
                _p("Yoga Block Set Mantar",     55,10.0,14, 1, 7200,4.5, 22, 1, 3800,4.4, 58),
                _p("Foam Roller Recovery",      80,35.0, 5, 4,11000,4.7,  8, 4, 6200,4.6, 84),
                _p("Pilates Band Seti",         58,12.0,14, 1, 6800,4.4, 20, 1, 3600,4.3, 62),
                _p("Meditasyon Minderi",        60,18.0,12, 2, 4800,4.5, 18, 2, 2600,4.4, 66),
            ],
        },

        "Koşu & Kardiyo": {
            "Tümü": None,
            "Koşu Aksesuarı": [
                _p("GPS Koşu Saati",            85,28.0, 3, 4,18000,4.7,  5, 4, 9800,4.6, 82),
                _p("Koşu Kemeri Çantası",       58,12.0,14, 1, 6200,4.4, 20, 1, 3200,4.3, 60),
                _p("Hidrasyon Koşu Yeleği",     70,22.0, 7, 3, 5800,4.5, 11, 3, 3200,4.4, 74),
                _p("Atlama İpi Pro Dijital",    65,18.0, 8, 2, 9500,4.6, 12, 2, 5200,4.5, 72),
            ],
            "Kardiyo & Recovery": [
                _p("Spor Çorap Seti 5'li",      52, 6.0,18, 0,12000,4.4, 26, 0, 6500,4.3, 55),
                _p("Foam Silindir Titreşimli",  78,38.0, 5, 5, 7200,4.6,  8, 5, 3800,4.5, 84),
                _p("Grip Strengthener",         60,18.0,12, 2, 6800,4.5, 18, 2, 3600,4.4, 64),
                _p("Mini Stepper Ev",           68,22.0, 8, 3, 5500,4.5, 12, 3, 3000,4.4, 72),
            ],
        },

        "Kamp & Outdoor": {
            "Tümü": None,
            "Kamp Ekipmanı": [
                _p("Kamp Hamağı Taşınabilir",   75,30.0, 6, 4, 7200,4.6, 10, 4, 3800,4.5, 80),
                _p("Ultralight Çadır 2 Kişilik",72,32.0, 7, 4, 5500,4.6, 11, 4, 3000,4.5, 76),
                _p("Kamp Tenceresi Titanyum",   65,20.0,10, 2, 4800,4.5, 16, 2, 2600,4.4, 68),
                _p("Uyku Tulumu Mumya",         70,18.0, 8, 2, 6200,4.5, 12, 2, 3500,4.4, 72),
            ],
            "Trekking & Navigasyon": [
                _p("Trekking Botu Su Geçirmez", 80,18.0, 4, 2,15000,4.7,  7, 2, 8000,4.6, 78),
                _p("Baş Feneri Şarjlı",        70,25.0, 8, 3, 8500,4.6, 12, 3, 4500,4.5, 74),
                _p("Trekking Baton Karbon",     62,15.0,10, 2, 5200,4.5, 16, 2, 2800,4.4, 65),
                _p("Survival Kit 15-in-1",      65,22.0, 9, 3, 6800,4.5, 14, 3, 3800,4.4, 70),
            ],
        },
    },

    # ── GIDA & İÇECEK ────────────────────────────────────────────────────────────
    "gida": {
        "Tümü": None,

        "Sağlıklı Yaşam": {
            "Tümü": None,
            "Adaptogen & Superfoods": [
                _p("Matcha Seti Premium",       88,52.0, 2, 6, 9800,4.8,  3, 6, 5200,4.7, 92),
                _p("Adaptogen Mantar Karışım",  84,48.0, 3, 6, 5500,4.7,  5, 6, 3200,4.6, 88),
                _p("Spirulina Tablet",          68,25.0, 8, 3, 7200,4.5, 12, 3, 3800,4.4, 72),
                _p("Moringa Tozu Organik",      65,22.0,10, 3, 4800,4.4, 16, 3, 2600,4.3, 68),
            ],
            "Kolajen & Takviye": [
                _p("Collagen Peptide Tozu",     82,45.0, 4, 5, 8200,4.7,  6, 5, 4500,4.6, 86),
                _p("MCT Oil Tozu",              65,22.0,10, 3, 4800,4.5, 15, 3, 2600,4.4, 68),
                _p("Bitki Bazlı Protein",       72,30.0, 6, 3, 6500,4.5, 10, 3, 3800,4.4, 75),
                _p("Hidrolize Kolajen İçecek",  70,28.0, 7, 4, 5500,4.5, 11, 4, 3200,4.4, 74),
            ],
        },

        "Kahve & Çay": {
            "Tümü": None,
            "Kahve Ekipmanı": [
                _p("Cold Brew Sürahi Seti",     78,35.0, 5, 4, 8500,4.6,  8, 4, 4600,4.5, 82),
                _p("Dripper Pour-Over V60",     65,18.0,10, 2, 7200,4.5, 16, 2, 3800,4.4, 68),
                _p("Moka Pot Alüminyum",        72,20.0, 7, 2,14000,4.7, 12, 2, 7500,4.5, 76),
                _p("AeroPress Kahve Demleme",   70,22.0, 8, 3, 5800,4.6, 12, 3, 3400,4.5, 75),
            ],
            "Çay & Doğal İçecek": [
                _p("Çay Demleme Seti Cam",      58,12.0,14, 1, 9500,4.5, 20, 1, 5000,4.3, 60),
                _p("Manuka Bal Premium",        74,30.0, 6, 4, 6800,4.7,  9, 4, 3800,4.5, 78),
                _p("Zerdeçal Latte Karışım",    72,30.0, 7, 3, 6200,4.6, 11, 3, 3400,4.5, 76),
                _p("Hibiskus Çay Seti",         60,18.0,10, 2, 5500,4.5, 16, 2, 3000,4.4, 65),
            ],
        },

        "Spor Beslenmesi": {
            "Tümü": None,
            "Protein & Kreatin": [
                _p("Whey Protein İzolat",       85,38.0, 2, 4,22000,4.6,  3, 4,12000,4.5, 82),
                _p("Kreatin Monohidrat",        75,28.0, 5, 4,14000,4.6,  8, 4, 7500,4.5, 78),
                _p("Kazein Protein Gece",       68,20.0, 8, 2, 8500,4.5, 12, 2, 4800,4.4, 70),
                _p("Vegan Protein Blend",       70,25.0, 7, 3, 7200,4.5, 11, 3, 4200,4.4, 74),
            ],
            "Amino & Pre-Workout": [
                _p("BCAA Efervesan",            70,22.0, 7, 3,12000,4.5, 11, 3, 6500,4.4, 74),
                _p("Pre-Workout Formula",       68,25.0, 8, 3, 8500,4.5, 12, 3, 4800,4.4, 70),
                _p("Elektrolit Tablet",         60,20.0,12, 3, 6200,4.4, 18, 3, 3400,4.3, 64),
                _p("Glutamin Tozu",             62,15.0,10, 2, 6800,4.4, 16, 2, 3800,4.3, 65),
            ],
        },

        "Organik & Doğal": {
            "Tümü": None,
            "Bitkisel Yağlar": [
                _p("Hindistan Cevizi Yağı",     62,15.0,10, 2,12000,4.6, 16, 2, 6500,4.4, 65),
                _p("Avokado Yağı Soğuk",        58,12.0,14, 1, 8500,4.5, 20, 1, 4500,4.3, 60),
                _p("Organik Zeytinyağı Extra",  65,10.0, 9, 1,15000,4.6, 14, 1, 8500,4.5, 62),
                _p("Çiçek Polen Doğal",         55,18.0,14, 3, 5200,4.4, 20, 3, 2800,4.3, 65),
            ],
            "Süper Gıda": [
                _p("Organik Çiğ Kakao",         65,20.0,10, 2, 7800,4.5, 15, 2, 4200,4.4, 68),
                _p("Chia Tohumu Organik",       55, 8.0,18, 0,14000,4.4, 25, 0, 7500,4.3, 58),
                _p("Goji Berry Kurutulmuş",     60,15.0,12, 2, 6800,4.4, 18, 2, 3800,4.3, 62),
                _p("Kuru İncir Organik",        50, 8.0,20, 0,10000,4.4, 28, 0, 5500,4.3, 52),
            ],
        },

        "Mutfak Ekipmanı": {
            "Tümü": None,
            "Büyük Elektrikli": [
                _p("Hava Fritözü 5L",           88,42.0, 2, 5,28000,4.7,  3, 5,15000,4.6, 85),
                _p("Elektrikli Fırın Mini 25L",  78,20.0, 4, 2,18000,4.6,  6, 2,10000,4.5, 78),
                _p("Sous Vide Cihazı",          65,28.0, 9, 4, 4800,4.5, 14, 4, 2800,4.4, 70),
                _p("Yavaş Pişirici 6L",         68,15.0, 8, 1,12000,4.5, 12, 1, 6800,4.4, 68),
            ],
            "Küçük Elektrikli": [
                _p("Blend & Go Blender",        72,25.0, 6, 3,14000,4.5, 10, 3, 7800,4.4, 75),
                _p("Waffle Makinesi",           68,18.0, 7, 2,12000,4.5, 11, 2, 6500,4.4, 72),
                _p("Manuel Meyve Sıkacağı",     48, 5.0,22, 0, 8500,4.3, 32, 0, 4500,4.2, 48),
                _p("Elektrikli Fındık Kırıcı",  55,10.0,18, 1, 5200,4.3, 26, 1, 2800,4.2, 55),
            ],
        },
    },

    # ── OYUNCAK & HOBİ ───────────────────────────────────────────────────────────
    "oyuncak": {
        "Tümü": None,

        "STEM & Eğitici": {
            "Tümü": None,
            "Kodlama & Robot": [
                _p("Kodlama Robotu Çocuk",      80,42.0, 4, 5, 5200,4.7,  7, 5, 3200,4.6, 85),
                _p("Elektronik Devre Kiti",     68,22.0, 8, 3, 4200,4.5, 12, 3, 2600,4.4, 72),
                _p("Scratch Kodlama Kart Seti", 65,20.0, 9, 3, 3800,4.5, 14, 3, 2200,4.4, 70),
                _p("Robot Koleksiyonu DIY",     70,28.0, 7, 4, 4500,4.6, 11, 4, 2800,4.5, 76),
            ],
            "Deney & Keşif": [
                _p("Bilim Deneyleri Seti",      72,28.0, 6, 3, 6800,4.6, 10, 3, 4000,4.5, 76),
                _p("Mikroskop Çocuk 100x",      62,18.0,12, 2, 3800,4.5, 18, 2, 2200,4.4, 65),
                _p("Teleskop Başlangıç",        65,22.0,10, 3, 3200,4.5, 15, 3, 1900,4.4, 70),
                _p("Kimya Deney Seti",          68,25.0, 8, 3, 4200,4.5, 12, 3, 2600,4.4, 72),
            ],
        },

        "Yapı & İnşaat": {
            "Tümü": None,
            "LEGO & Uyumlu": [
                _p("LEGO Technic Set",          88,35.0, 1, 4,18000,4.9,  2, 4, 9500,4.8, 85),
                _p("LEGO Creator 3-in-1",       82,28.0, 3, 3,14000,4.8,  4, 3, 7500,4.7, 80),
                _p("Mini Tuğla Mimari Set",     70,25.0, 7, 3, 5800,4.6, 11, 3, 3400,4.5, 75),
                _p("Nano Blok Koleksiyonu",     65,20.0, 9, 3, 4200,4.5, 14, 3, 2600,4.4, 70),
            ],
            "Manyetik & Ahşap": [
                _p("Manyetik Yapı Seti XL",     86,50.0, 2, 6, 8500,4.8,  3, 6, 4800,4.7, 90),
                _p("Manyetik Tile Seti",        78,38.0, 5, 5, 7200,4.7,  8, 5, 4200,4.6, 83),
                _p("Ahşap Yapı Bloğu Seti",     60,12.0,12, 1, 9500,4.5, 18, 1, 5200,4.4, 62),
                _p("Denge Oyunu Ahşap",         55,10.0,15, 1, 6800,4.4, 22, 1, 3800,4.3, 58),
            ],
        },

        "Yaratıcılık & Sanat": {
            "Tümü": None,
            "Sanat & Atölye": [
                _p("Stop Motion Studio Kiti",   82,45.0, 4, 6, 4200,4.7,  6, 6, 2600,4.6, 86),
                _p("Pottery Wheel Mini",        78,38.0, 5, 5, 3500,4.6,  8, 5, 2200,4.5, 82),
                _p("Çizim Tableti Çocuk",       75,30.0, 6, 4, 6800,4.6,  9, 4, 4000,4.5, 80),
                _p("Ahşap Boyama Seti",         58,12.0,14, 1, 7500,4.4, 20, 1, 4200,4.3, 60),
            ],
            "DIY & Slime": [
                _p("Slime Yapım Kiti Premium",  72,32.0, 7, 4, 9800,4.5, 11, 4, 5800,4.4, 78),
                _p("Reçine Sanat Başlangıç",    68,28.0, 8, 4, 4500,4.5, 12, 4, 2800,4.4, 75),
                _p("Kil Modelleme Seti",        55,12.0,14, 1, 6200,4.4, 20, 1, 3500,4.3, 60),
                _p("Tie-Dye Kit",               62,20.0,10, 3, 5500,4.5, 15, 3, 3200,4.4, 68),
            ],
        },

        "Outdoor & Aktif": {
            "Tümü": None,
            "RC & Drone": [
                _p("RC Drone Kamera 4K",        80,35.0, 4, 5,12000,4.6,  6, 5, 7000,4.5, 84),
                _p("Elektrikli Scooter Çocuk",  85,30.0, 3, 4, 9500,4.7,  5, 4, 5800,4.6, 82),
                _p("RC Araba Offroad",          72,25.0, 6, 3, 7800,4.5,  9, 3, 4800,4.4, 76),
                _p("Drone FPV Gözetleme",       75,30.0, 5, 4, 8500,4.5,  8, 4, 5200,4.4, 80),
            ],
            "Aktif & Oyun Alanı": [
                _p("Paten Ayarlanabilir",       70,22.0, 7, 2, 7200,4.5, 11, 2, 4200,4.4, 72),
                _p("Kamp Seti Çocuk",           65,20.0, 9, 3, 4800,4.5, 14, 3, 2800,4.4, 68),
                _p("Archery Set Çocuk",         58,15.0,13, 2, 3600,4.4, 19, 2, 2100,4.3, 62),
                _p("Mini Basketbol Potası",     60,15.0,12, 2, 5800,4.4, 18, 2, 3200,4.3, 65),
            ],
        },

        "Koleksiyon & Figür": {
            "Tümü": None,
            "Anime & Pop Kültür": [
                _p("Blind Box Figür Serisi",    88,55.0, 3, 6, 8200,4.7,  4, 6, 5000,4.6, 92),
                _p("Anime Aksiyon Figürü",      82,40.0, 4, 5,14000,4.7,  6, 5, 8500,4.6, 88),
                _p("Funko Pop Koleksiyon",      75,30.0, 5, 4,10000,4.6,  8, 4, 6000,4.5, 82),
                _p("Gacha Kapsül Figür",        70,25.0, 7, 4, 7500,4.5, 11, 4, 4500,4.4, 76),
            ],
            "Sensory & Fidget": [
                _p("Diecast Model Araba",       65,15.0, 9, 1,10000,4.5, 14, 1, 6000,4.4, 68),
                _p("Sensory Fidget Seti",       72,28.0, 6, 3, 9500,4.6,  9, 3, 5800,4.5, 76),
                _p("Pop-It Oyuncak Seti",       60,10.0,12, 0,16000,4.3, 18, 0, 9500,4.2, 62),
                _p("Infinity Cube Fidget",      58,15.0,14, 2, 8200,4.4, 20, 2, 4800,4.3, 65),
            ],
        },
    },
}




# ═══════════════════════════════════════════════════════════════════════════════
# CHART HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
_BG = dict(
    paper_bgcolor="rgba(255,255,255,0.55)",
    plot_bgcolor="rgba(245,248,255,0.45)",
    font=dict(color="#0c1a3a", size=12),
)

_SOURCE_COLORS = {
    "google":    "#4285f4",
    "trendyol":  "#f27a1a",
    "amazon_tr": "#f90",
    "tiktok":    "#fe2c55",
}

def make_gauge(score, label, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        domain={"x":[0,1],"y":[0,1]},
        title={"text": label, "font": {"size": 11, "color": "#374151"}},
        number={"font": {"size": 24, "color": color}},
        gauge={
            "axis": {"range":[0,100],"tickfont":{"size":8,"color":"#6b7280"}},
            "bar":  {"color": color},
            "bgcolor": "rgba(243,246,255,0.6)",
            "bordercolor": "rgba(213,228,255,0.7)",
            "steps": [
                {"range":[0,35],  "color":"rgba(254,226,226,0.5)"},
                {"range":[35,60], "color":"rgba(254,249,195,0.5)"},
                {"range":[60,100],"color":"rgba(220,252,231,0.5)"},
            ],
        },
    ))
    fig.update_layout(height=170, margin=dict(t=32,b=0,l=12,r=12), **_BG)
    return fig


def make_forecast(forecast, name):
    labels = ["Şimdi"] + [f"+{i}h" for i in range(1, len(forecast))]

    # Y eksenini veriye göre yakınlaştır — eğim görünür olsun
    lo = max(0,  min(forecast) - 12)
    hi = min(100, max(forecast) + 12)

    # Alt dolgu referans çizgisi (görünmez, fill için baz)
    baseline = [lo] * len(forecast)

    fig = go.Figure()

    # Dolgu alanı: eksenin altına değil, yakınlaştırılmış tabana
    fig.add_trace(go.Scatter(
        x=labels, y=baseline,
        mode="lines", line=dict(width=0),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=labels, y=forecast,
        mode="lines+markers",
        line=dict(color="#1d4ed8", width=2.8),
        marker=dict(
            size=8, color="#1d4ed8",
            line=dict(color="white", width=2),
            symbol="circle",
        ),
        fill="tonexty",
        fillcolor="rgba(29,78,216,0.10)",
        hovertemplate="%{x}: <b>%{y:.0f}</b><extra></extra>",
    ))

    # İlk ve son değerleri annotate et — eğimi sayısal olarak göster
    delta = forecast[-1] - forecast[0]
    arrow_color = "#16a34a" if delta >= 0 else "#dc2626"
    arrow_sym   = "▲" if delta >= 0 else "▼"
    fig.add_annotation(
        x=labels[-1], y=forecast[-1],
        text=f"<b>{arrow_sym} {abs(delta):.1f}</b>",
        showarrow=False,
        font=dict(size=9, color=arrow_color),
        xanchor="left", xshift=6, yanchor="middle",
    )

    fig.update_layout(
        title=dict(text="6 Haftalık Talep Tahmini", font=dict(size=10, color="#0c1a3a")),
        xaxis_title="",
        yaxis_title="Trend Endeksi (0–100)",
        yaxis_range=[lo, hi + 6],   # biraz üst boşluk annotation için
        height=160,
        margin=dict(t=26, b=14, l=52, r=36),
        showlegend=False, **_BG,
    )
    fig.update_xaxes(showgrid=False, color="#6b7280", tickfont=dict(size=9))
    fig.update_yaxes(
        gridcolor="rgba(213,228,255,0.6)", gridwidth=1, color="#6b7280",
        title_font=dict(size=8, color="#9ca3af"),
        tickfont=dict(size=8),
    )
    return fig


def make_channel_bar(channels):
    if not channels: return go.Figure()
    names  = [CHANNEL_MAP.get(k, k) for k in channels]
    scores = list(channels.values())
    mx     = max(scores)
    colors = [CHANNEL_COLOR.get(k,"#1d4ed8") if scores[i]==mx else "#93c5fd"
              for i,k in enumerate(channels)]
    fig = go.Figure(go.Bar(
        x=names, y=scores,
        marker_color=colors,
        marker_line_color="rgba(255,255,255,0.6)",
        marker_line_width=1,
        text=[f"{s:.0f}" for s in scores],
        textposition="outside",
        textfont=dict(color="#0c1a3a", size=11),
    ))
    fig.update_layout(
        title=dict(text="Kanal Skoru",font=dict(size=10,color="#0c1a3a")),
        yaxis_range=[0,118], height=148,
        margin=dict(t=26,b=14,l=14,r=10), showlegend=False, **_BG,
    )
    fig.update_xaxes(showgrid=False, color="#6b7280", tickfont=dict(size=10))
    fig.update_yaxes(gridcolor="rgba(213,228,255,0.6)", color="#6b7280")
    return fig


def make_overview_bar(results):
    names  = [r["product_name"] for r in results]
    scores = [r["composite_score"] for r in results]
    colors = [RISK_COLORS[r["risk_level"]] for r in results]
    fig = go.Figure(go.Bar(
        x=scores, y=names, orientation="h",
        marker_color=colors,
        marker_line_color="rgba(255,255,255,0.5)",
        marker_line_width=1.5,
        text=[f"{s:.0f}" for s in scores],
        textposition="outside",
        textfont=dict(color="#0c1a3a", size=11),
    ))
    fig.update_layout(
        title=dict(text="Trend Skoru Karşılaştırması",font=dict(size=11,color="#0c1a3a")),
        xaxis_range=[0,120], xaxis_title="Trend Endeksi (0–100)",
        height=max(160, len(results)*28+50),
        margin=dict(t=28,b=18,l=155,r=42),
        yaxis=dict(autorange="reversed"), showlegend=False, **_BG,
    )
    fig.update_xaxes(showgrid=False, color="#6b7280")
    fig.update_yaxes(showgrid=False, color="#0c1a3a")
    return fig


def make_import_gauge(demand, supply):
    gap = max(0, demand - supply)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=gap,
        domain={"x":[0,1],"y":[0,1]},
        title={"text":"Arz Açığı","font":{"size":10,"color":"#374151"}},
        number={"font":{"size":22,"color":"#1d4ed8"}},
        gauge={
            "axis":{"range":[0,100],"tickfont":{"size":8}},
            "bar": {"color":"#1d4ed8"},
            "bgcolor":"rgba(243,246,255,0.5)",
            "bordercolor":"rgba(147,197,253,0.4)",
            "steps":[
                {"range":[0,30], "color":"rgba(220,252,231,0.4)"},
                {"range":[30,60],"color":"rgba(254,249,195,0.4)"},
                {"range":[60,100],"color":"rgba(219,234,254,0.5)"},
            ],
        },
    ))
    fig.update_layout(height=150,margin=dict(t=28,b=0,l=8,r=8),**_BG)
    return fig


def make_annual_trend(product_name: str, subcat: str, sector: str, composite: float):
    """12 aylık sezonsal trend grafiği + açıklama cümlesi döner."""
    seas  = get_seasonality(product_name, subcat, sector)
    raw   = seas["data"]
    # Ürünün composite skoru üzerinden normalize et
    scale = composite / max(raw) if max(raw) > 0 else 1
    data  = [round(v * scale, 1) for v in raw]

    peak_indices = {i for i, m in enumerate(MONTHS_FULL) if m in seas["peaks"]}
    bar_colors   = ["#1d4ed8" if i in peak_indices else "#93c5fd" for i in range(12)]
    bar_opacity  = [1.0 if i in peak_indices else 0.65 for i in range(12)]

    fig = go.Figure()

    # Mevsim arka plan bantları
    season_bands = [
        (0, 1,  "rgba(219,234,254,0.25)", "Kış"),    # Oca-Şub
        (2, 4,  "rgba(209,250,229,0.25)", "İlk"),    # Mar-May
        (5, 7,  "rgba(254,243,199,0.25)", "Yaz"),    # Haz-Ağu
        (8, 10, "rgba(254,226,226,0.22)", "Son"),    # Eyl-Kas
        (11,11, "rgba(219,234,254,0.25)", ""),        # Ara
    ]
    for x0, x1, color, label in season_bands:
        fig.add_vrect(x0=x0-0.5, x1=x1+0.5, fillcolor=color,
                      layer="below", line_width=0)
        if label:
            fig.add_annotation(x=(x0+x1)/2, y=102, text=label,
                               showarrow=False, font=dict(size=7.5, color="#9ca3af"),
                               yref="y")

    # Zirve aylar için noktalı çizgi referansı
    if peak_indices:
        avg_peak = sum(data[i] for i in peak_indices) / len(peak_indices)
        fig.add_hline(y=avg_peak, line_dash="dot", line_color="#1d4ed8",
                      line_width=1, opacity=0.45)

    # Sütun grafiği
    fig.add_trace(go.Bar(
        x=MONTHS_TR, y=data,
        marker_color=bar_colors,
        marker_opacity=bar_opacity,
        marker_line_color="rgba(255,255,255,0.5)",
        marker_line_width=1,
        text=[f"{v:.0f}" if i in peak_indices else "" for i, v in enumerate(data)],
        textposition="outside",
        textfont=dict(color="#1d4ed8", size=8, family="sans-serif"),
        hovertemplate="%{x}: %{y:.0f}<extra></extra>",
    ))

    # Trend çizgisi
    fig.add_trace(go.Scatter(
        x=MONTHS_TR, y=data, mode="lines",
        line=dict(color="#2563eb", width=1.5, dash="dot"),
        opacity=0.5, showlegend=False,
        hoverinfo="skip",
    ))

    peak_label = " · ".join(seas["peaks"])
    fig.update_layout(
        title=dict(
            text=f"Yıllık Talep Trendi — Trend Endeksi (0–100) &nbsp;|&nbsp; 🎯 Zirve: {peak_label}",
            font=dict(size=9.5, color="#0c1a3a"),
            x=0,
        ),
        height=165,
        margin=dict(t=30, b=12, l=52, r=12),
        yaxis_range=[0, 115],
        showlegend=False,
        bargap=0.22,
        **_BG,
    )
    fig.update_xaxes(showgrid=False, color="#6b7280", tickfont=dict(size=9))
    fig.update_yaxes(
        gridcolor="rgba(213,228,255,0.5)", color="#6b7280",
        tickfont=dict(size=8), showticklabels=True,
        title="Trend Endeksi",
        title_font=dict(size=8, color="#9ca3af"),
        tickvals=[0, 25, 50, 75, 100],
        ticktext=["0", "25", "50", "75", "100"],
    )
    return fig, seas["insight"]


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADER
# ═══════════════════════════════════════════════════════════════════════════════
def load_data(sector_key, ana_cat, alt_cat, region, channel_keys):
    scorer  = TrendScorer()
    signals = _get_filtered_products(sector_key, ana_cat, alt_cat)
    data    = [r.to_dict() for r in scorer.rank_products(signals)]

    # 1 ── Kanal bias: bölgenin online/fiziksel mağaza eğilimi
    ch_bias = REGION_CHANNEL_BIAS.get(region, REGION_CHANNEL_BIAS["Tüm Türkiye"])
    for item in data:
        for ch, delta in ch_bias.items():
            if ch in item["channel_recommendations"]:
                item["channel_recommendations"][ch] = round(
                    max(0, min(100, item["channel_recommendations"][ch] + delta)), 1)
        item["best_channel"] = max(item["channel_recommendations"],
                                   key=item["channel_recommendations"].get)

    # 2 ── Skor düzeltmesi: e-ticaret penetrasyonu + sektör uyumu
    base_delta   = REGION_BASE_SCORE_DELTA.get(region, 0)
    sector_delta = REGION_SECTOR_AFFINITY.get(region, {}).get(sector_key, 0)
    score_delta  = base_delta + sector_delta
    if score_delta != 0:
        for item in data:
            item["composite_score"] = round(
                max(0.0, min(100.0, item["composite_score"] + score_delta)), 1)
            # Google skoru daha ılımlı etkilenir (yarı katsayı)
            item["google_score"] = round(
                max(0.0, min(100.0, item["google_score"] + score_delta * 0.5)), 1)

    # 3 ── Bölgesel skora göre yeniden sırala
    data.sort(key=lambda x: x["composite_score"], reverse=True)

    # 4 ── Kanal filtresi
    if channel_keys:
        for item in data:
            item["channel_recommendations"] = {
                k: v for k, v in item["channel_recommendations"].items() if k in channel_keys
            }
            if item["channel_recommendations"]:
                item["best_channel"] = max(item["channel_recommendations"],
                                           key=item["channel_recommendations"].get)
    return data


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:10px;padding:0.3rem 0 0.8rem;">
        {svg("trend-up","#1d4ed8",26)}
        <span style="font-size:1.3rem;font-weight:800;color:#0c1a3a;letter-spacing:-0.02em;">TradeTrend</span>
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    page = st.radio(
        "",
        ["Trend Analizi", "İthalat Fırsatları", "Nasıl Çalışır?"],
        format_func=lambda x: {
            "Trend Analizi":      f"Trend Analizi",
            "İthalat Fırsatları": f"İthalat Fırsatları",
            "Nasıl Çalışır?":     f"Nasıl Çalışır?",
        }[x],
        label_visibility="collapsed",
    )

    st.markdown("---")

    if page in ("Trend Analizi", "İthalat Fırsatları"):
        st.markdown(
            f'{icon_html("filter","#1d4ed8",16)} &nbsp;<strong style="color:#0c1a3a">Filtreler</strong>',
            unsafe_allow_html=True,
        )
        selected_sector = st.selectbox(
            "Sektör",
            options=list(SECTORS.keys()),
            index=0,
        )
        sector_key = SECTORS[selected_sector]

        # ── Kategori seçimi (2 kademeli) ─────────────────────────────────────
        if page == "İthalat Fırsatları":
            _imp_all = get_import_opportunities(sector_key)
            _imp_subcats = ["Tümü"] + sorted(set(o.subcategory for o in _imp_all))
            selected_ana_cat = "Tümü"
            selected_alt_cat = st.selectbox("Alt Kategori", options=_imp_subcats, index=0)
        else:
            # Kademe 1 — Ana Kategori
            _sector_cats = SECTOR_SUBCATEGORIES.get(sector_key, {})
            ana_options   = list(_sector_cats.keys())   # "Tümü" + ana kategoriler
            selected_ana_cat = st.selectbox("Kategori", options=ana_options, index=0)

            # Kademe 2 — Alt Kategori (sadece ana seçiliyse)
            if selected_ana_cat != "Tümü":
                _ana_node = _sector_cats.get(selected_ana_cat, {})
                if isinstance(_ana_node, dict):
                    alt_options = list(_ana_node.keys())   # "Tümü" + alt kategoriler
                    selected_alt_cat = st.selectbox("Alt Kategori", options=alt_options, index=0)
                else:
                    selected_alt_cat = "Tümü"
            else:
                selected_alt_cat = "Tümü"

        if page == "Trend Analizi":
            _reg_labels = [
                f"{REGION_META[r]['emoji']} {r}  —  {REGION_META[r]['desc']}"
                for r in REGIONS
            ]
            _reg_idx = st.selectbox(
                "🗺️ Bölge",
                options=range(len(REGIONS)),
                format_func=lambda i: _reg_labels[i],
                index=0,
            )
            selected_region = REGIONS[_reg_idx]
            selected_ch_labels = st.multiselect(
                "Satış Kanalları",
                options=SALES_CHANNELS,
                default=["Trendyol","Amazon TR","Instagram","Fiziksel Mağaza"],
            )
            st.markdown("---")
            if st.button(
                f"Analizi Yenile",
                type="primary", use_container_width=True
            ):
                st.rerun()
        else:
            selected_region = "Tüm Türkiye"
            selected_ch_labels = SALES_CHANNELS[:]

    st.markdown("---")
    st.caption(f"Güncelleme: {date.today().strftime('%d.%m.%Y')}")
    st.caption("v0.2 · Google · Trendyol · Amazon TR · TikTok")


# ═══════════════════════════════════════════════════════════════════════════════
# SAYFA 1 — TREND ANALİZİ
# ═══════════════════════════════════════════════════════════════════════════════
if page == "Trend Analizi":
    channel_keys = list({SIDEBAR_TO_KEY[c] for c in selected_ch_labels if c in SIDEBAR_TO_KEY}) \
                   or list(CHANNEL_MAP.keys())
    all_results  = load_data(sector_key, selected_ana_cat, selected_alt_cat, selected_region, channel_keys)
    results      = all_results[:10]

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown(
        f"""<div class="tt-header">
        <div style="display:flex;align-items:center;gap:12px;">
            {svg("trend-up","white",28)}
            <h1 style="margin:0;color:white;font-size:1.25rem;font-weight:800;letter-spacing:-0.02em;">TradeTrend</h1>
        </div>
        <p style="margin:0.2rem 0 0;color:rgba(255,255,255,0.88);font-size:0.82rem;">
            {selected_sector} &nbsp;·&nbsp; {selected_ana_cat}{" › " + selected_alt_cat if selected_alt_cat != "Tümü" else ""} &nbsp;·&nbsp; {REGION_META[selected_region]["emoji"]} {selected_region} &nbsp;·&nbsp; Top 10 ürün
        </p>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── KPI kartları ─────────────────────────────────────────────────────────
    avg   = sum(r["composite_score"] for r in results) / len(results)
    low_n = sum(1 for r in results if r["risk_level"] == "low")
    best  = results[0]
    valid_ch = [c for c in channel_keys if any(c in r["channel_recommendations"] for r in results)]
    bco   = max(valid_ch, key=lambda c: sum(r["channel_recommendations"].get(c,0) for r in results)) if valid_ch else "-"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ort. Trend Skoru",  f"{avg:.1f}/100",     delta=f"{avg-50:+.1f}")
    c2.metric("Düşük Riskli",      f"{low_n}/{len(results)}")
    c3.metric("En Trend Ürün",     best["product_name"], delta=f"Skor: {best['composite_score']:.0f}")
    c4.metric("En İyi Kanal",      CHANNEL_MAP.get(bco, bco))
    st.markdown("---")

    # ── Genel bakış grafiği ───────────────────────────────────────────────────
    st.plotly_chart(make_overview_bar(results), use_container_width=True, key="ov")
    st.markdown("---")

    # ── Ürün kartları ─────────────────────────────────────────────────────────
    st.markdown(
        f'{icon_html("layers","#1d4ed8",20)} &nbsp;<span style="font-size:1.15rem;font-weight:700;color:#0c1a3a;">Top {len(results)} Ürün Detayları</span>',
        unsafe_allow_html=True,
    )

    psc_map = _product_subcat_map(sector_key)
    g1, g2 = SECTOR_GRAD.get(sector_key, ("214,234,254", "219,234,254"))

    for i, r in enumerate(results):
        rc        = RISK_COLORS[r["risk_level"]]
        rl        = RISK_LABELS[r["risk_level"]]
        bch       = r["best_channel"]
        bch_label = CHANNEL_MAP.get(bch, bch)
        prod_sub  = psc_map.get(r["product_name"], selected_alt_cat)
        emoji     = get_product_emoji(r["product_name"], prod_sub, sector_key)

        with st.expander(
            f"{emoji}  {r['product_name']}  ·  {r['composite_score']:.0f}/100  ·  {rl}  →  {bch_label}",
            expanded=False,
        ):
            # ── Mini kaynak skoru barları ─────────────────────────────────────
            sources = [
                ("Google",    r["google_score"],   "#4285f4"),
                ("Trendyol",  r["trendyol_score"], "#f27a1a"),
                ("Amazon TR", r["amazon_score"],   "#f90"),
                ("TikTok",    r["tiktok_score"],   "#fe2c55"),
            ]
            src_html = "".join(
                f"""<div style="flex:1;min-width:72px;">
                    <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                        <span style="font-size:0.68rem;color:#6b7280;font-weight:600;">{name}</span>
                        <span style="font-size:0.75rem;font-weight:700;color:{col};">{score:.0f}</span>
                    </div>
                    <div style="height:5px;background:rgba(0,0,0,0.07);border-radius:3px;overflow:hidden;">
                        <div style="width:{score:.0f}%;height:100%;background:{col};border-radius:3px;"></div>
                    </div>
                </div>"""
                for name, score, col in sources
            )
            st.markdown(
                f"""<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                    <div style="width:58px;height:58px;border-radius:16px;flex-shrink:0;
                        background:linear-gradient(135deg,rgba({g1},0.55),rgba({g2},0.85));
                        display:flex;align-items:center;justify-content:center;
                        font-size:1.9rem;
                        box-shadow:0 2px 10px rgba(29,78,216,0.10);">{emoji}</div>
                    <div style="flex:1;">
                        <div style="display:flex;align-items:baseline;gap:6px;margin-bottom:4px;">
                            <span style="font-size:1.5rem;font-weight:800;color:{rc};">{r['composite_score']:.0f}</span>
                            <span style="font-size:0.68rem;color:#9ca3af;">/100 &nbsp;·&nbsp;</span>
                            <span style="font-size:0.75rem;font-weight:700;color:{rc};">{rl}</span>
                        </div>
                        <div style="display:flex;gap:10px;flex-wrap:wrap;">{src_html}</div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
            # ── Yıllık Sezonsal Trend ────────────────────────────────────────
            ann_fig, ann_insight = make_annual_trend(
                r["product_name"], prod_sub, sector_key, r["composite_score"]
            )
            st.plotly_chart(ann_fig, use_container_width=True, key=f"ann{i}")
            st.markdown(
                f"""<div style="background:rgba(29,78,216,0.05);border-left:2px solid #2563eb;
                border-radius:0 8px 8px 0;padding:0.3rem 0.7rem;margin:-6px 0 8px;
                font-size:0.78rem;color:#374151;line-height:1.5;">
                💡 {ann_insight}
                </div>""",
                unsafe_allow_html=True,
            )
            # ── Forecast + Kanal ─────────────────────────────────────────────
            fc, ch = st.columns([2, 1.2])
            with fc:
                st.plotly_chart(make_forecast(r["weekly_forecast"], r["product_name"]),
                                use_container_width=True, key=f"fc{i}")
            with ch:
                if r["channel_recommendations"]:
                    st.plotly_chart(make_channel_bar(r["channel_recommendations"]),
                                    use_container_width=True, key=f"ch{i}")
                    bch_icon = svg(CHANNEL_ICON_NAME.get(bch,"shopping"), CHANNEL_COLOR.get(bch,"#1d4ed8"), 14)
                    st.markdown(
                        f"""<div style="background:rgba(29,78,216,0.07);border:1px solid rgba(29,78,216,0.16);
                        border-radius:8px;padding:0.4rem 0.7rem;text-align:center;">
                        <div style="display:flex;align-items:center;justify-content:center;gap:5px;font-size:0.82rem;">
                            {bch_icon}
                            <strong style="color:#1e3a8a;">{bch_label}</strong>
                        </div>
                        <div style="font-size:0.72rem;color:#1d4ed8;margin-top:1px;">
                            Skor: <strong>{r["channel_recommendations"].get(bch,0):.0f}/100</strong>
                        </div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                else:
                    st.info("Kanal seçimi yapılmadı.")

    # ── Karşılaştırma tablosu ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        f'{icon_html("bar-chart","#1d4ed8",20)} &nbsp;<span style="font-size:1.1rem;font-weight:700;color:#0c1a3a;">Karşılaştırma Tablosu</span>',
        unsafe_allow_html=True,
    )
    rows = []
    for i, r in enumerate(results):
        bch = r["best_channel"]
        rows.append({
            "#":           i+1,
            "Ürün":        r["product_name"],
            "Skor":        f"{r['composite_score']:.0f}/100",
            "Google":      f"{r['google_score']:.0f}",
            "Trendyol":    f"{r['trendyol_score']:.0f}",
            "Amazon TR":   f"{r['amazon_score']:.0f}",
            "TikTok":      f"{r['tiktok_score']:.0f}",
            "Risk":        RISK_LABELS[r["risk_level"]],
            "En İyi Kanal":CHANNEL_MAP.get(bch, bch),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.markdown(
        "<p style='text-align:center;color:#9ca3af;font-size:0.8rem;margin-top:1.2rem'>"
        "TradeTrend v0.2 — Google Trends · Trendyol · Amazon TR · TikTok Creative Center</p>",
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SAYFA 2 — İTHALAT FIRSATLARI
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "İthalat Fırsatları":
    st.markdown(
        f"""<div class="tt-header">
        <div style="display:flex;align-items:center;gap:12px;">
            {svg("truck","white",28)}
            <h1 style="margin:0;color:white;font-size:1.25rem;font-weight:800;letter-spacing:-0.02em;">İthalat Fırsatları</h1>
        </div>
        <p style="margin:0.2rem 0 0;color:rgba(255,255,255,0.88);font-size:0.82rem;">
            {selected_sector} &nbsp;·&nbsp; {selected_alt_cat if selected_alt_cat != "Tümü" else "Tüm Kategoriler"} &nbsp;·&nbsp;
            Türkiye'de talebi yüksek, yerli arzın yetersiz kaldığı ürünler
        </p>
        </div>""",
        unsafe_allow_html=True,
    )

    opps = get_import_opportunities(sector_key)
    if selected_alt_cat != "Tümü":
        opps = [o for o in opps if o.subcategory == selected_alt_cat]
    if not opps:
        st.info("Bu sektör için ithalat fırsatı verisi bulunamadı.")
    else:
        # KPI özet
        high_count = sum(1 for o in opps if o.opportunity_label == "Yüksek Fırsat")
        avg_demand = sum(o.demand_score for o in opps) / len(opps)
        avg_gap    = sum(o.supply_gap for o in opps) / len(opps)
        best_opp   = max(opps, key=lambda o: o.import_score)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Yüksek Fırsat",     f"{high_count} ürün")
        k2.metric("Ort. Talep Skoru",  f"{avg_demand:.0f}/100")
        k3.metric("Ort. Arz Açığı",    f"{avg_gap:.0f} puan")
        k4.metric("En İyi Fırsat",     best_opp.product_name, delta=f"Skor: {best_opp.import_score:.0f}")
        st.markdown("---")

        # Fırsat kartları
        st.markdown(
            f'{icon_html("package","#1d4ed8",20)} &nbsp;<span style="font-size:1.1rem;font-weight:700;color:#0c1a3a;">Fırsat Kartları</span>',
            unsafe_allow_html=True,
        )

        TREND_LABELS = {
            "rising_fast": ("Hızlı Yükseliş", "#1d4ed8"),
            "rising":      ("Yükseliş",        "#059669"),
            "stable":      ("Stabil",          "#6b7280"),
        }
        BADGE_CLASS = {
            "Yüksek Fırsat": "tt-badge-high",
            "Orta Fırsat":   "tt-badge-mid",
            "Takipte":       "tt-badge-watch",
        }

        sorted_opps = sorted(opps, key=lambda o: o.import_score, reverse=True)
        ig1, ig2 = SECTOR_GRAD.get(sector_key, ("214,234,254", "219,234,254"))
        # 2 sütunlu ızgara
        col_a, col_b = st.columns(2)
        for idx, opp in enumerate(sorted_opps):
            td_label, td_color = TREND_LABELS.get(opp.trend_direction, ("","#6b7280"))
            badge_cls = BADGE_CLASS.get(opp.opportunity_label, "tt-badge-watch")
            imp_emoji = get_product_emoji(opp.product_name, opp.subcategory, sector_key)
            platforms_html = " ".join(
                f'<span style="background:rgba(29,78,216,0.08);border:1px solid rgba(29,78,216,0.15);'
                f'border-radius:10px;padding:1px 7px;font-size:0.7rem;color:#1e3a8a;">{p}</span>'
                for p in opp.foreign_platforms
            )
            gap_pct = min(100, opp.supply_gap)
            target_col = col_a if idx % 2 == 0 else col_b
            with target_col:
                st.markdown(
                    f"""<div class="tt-import-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;">
                        <div style="display:flex;gap:10px;align-items:center;flex:1;">
                            <div style="width:46px;height:46px;border-radius:12px;flex-shrink:0;
                                background:linear-gradient(135deg,rgba({ig1},0.55),rgba({ig2},0.85));
                                display:flex;align-items:center;justify-content:center;font-size:1.55rem;
                                box-shadow:0 2px 8px rgba(29,78,216,0.09);">{imp_emoji}</div>
                            <div style="flex:1;min-width:0;">
                                <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap;">
                                    <span style="font-size:0.9rem;font-weight:700;color:#0c1a3a;white-space:nowrap;">{opp.product_name}</span>
                                    <span class="{badge_cls}" style="font-size:0.65rem;">{opp.opportunity_label}</span>
                                </div>
                                <div style="font-size:0.68rem;color:#9ca3af;">{opp.subcategory} &nbsp;·&nbsp; <span style="color:{td_color};font-weight:600;">{td_label}</span></div>
                            </div>
                        </div>
                        <div style="text-align:right;flex-shrink:0;">
                            <div style="font-size:1.3rem;font-weight:800;color:#1d4ed8;line-height:1;">{opp.import_score:.0f}</div>
                            <div style="font-size:0.6rem;color:#9ca3af;">/100</div>
                        </div>
                    </div>
                    <div style="display:flex;gap:12px;margin:0.45rem 0 0.35rem;align-items:center;">
                        <div style="font-size:0.7rem;color:#6b7280;">Talep <strong style="color:#0c1a3a;">{opp.demand_score:.0f}</strong></div>
                        <div style="font-size:0.7rem;color:#6b7280;">Arz <strong style="color:#0c1a3a;">{opp.local_supply_score:.0f}</strong></div>
                        <div style="font-size:0.7rem;color:#6b7280;">Açık <strong style="color:#dc2626;">{opp.supply_gap:.0f}</strong></div>
                        <div style="flex:1;height:4px;background:rgba(0,0,0,0.07);border-radius:2px;overflow:hidden;">
                            <div style="width:{gap_pct}%;height:100%;background:linear-gradient(90deg,#2563eb,#dc2626);border-radius:2px;"></div>
                        </div>
                    </div>
                    <div style="font-size:0.73rem;color:#374151;background:rgba(29,78,216,0.05);
                        border-left:2px solid #2563eb;border-radius:0 6px 6px 0;
                        padding:0.28rem 0.55rem;margin-bottom:0.35rem;line-height:1.4;">
                        {opp.insight}
                    </div>
                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:4px;">
                        <div style="font-size:0.65rem;color:#9ca3af;">
                            ~{opp.monthly_searches_tr:,} arama &nbsp;·&nbsp; ${opp.avg_price_usd} / ₺{opp.avg_price_try:,}
                        </div>
                        <div style="display:flex;gap:3px;flex-wrap:wrap;">{platforms_html}</div>
                    </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

        # Tablo
        st.markdown("---")
        st.markdown(
            f'{icon_html("bar-chart","#1d4ed8",18)} &nbsp;<span style="font-size:1.05rem;font-weight:700;color:#0c1a3a;">Tüm Fırsatlar — Karşılaştırma</span>',
            unsafe_allow_html=True,
        )
        df_rows = []
        for o in sorted(opps, key=lambda x: x.import_score, reverse=True):
            df_rows.append({
                "Ürün":            o.product_name,
                "Alt Kategori":    o.subcategory,
                "Fırsat Skoru":    f"{o.import_score:.0f}/100",
                "TR Talebi":       f"{o.demand_score:.0f}",
                "Yerli Arz":       f"{o.local_supply_score:.0f}",
                "Arz Açığı":       f"{o.supply_gap:.0f}",
                "Aylık Arama":     f"{o.monthly_searches_tr:,}",
                "Fiyat (USD)":     f"${o.avg_price_usd}",
                "Fiyat (TRY)":     f"₺{o.avg_price_try:,}",
                "Trend":           {"rising_fast":"↑↑ Hızlı","rising":"↑ Yükseliş","stable":"→ Stabil"}.get(o.trend_direction,""),
                "Seviye":          o.opportunity_label,
            })
        st.dataframe(pd.DataFrame(df_rows), use_container_width=True, hide_index=True)

        st.markdown(
            "<p style='text-align:center;color:#9ca3af;font-size:0.8rem;margin-top:1.2rem'>"
            "TradeTrend v0.2 — İthalat Fırsatları · Amazon TR · AliExpress · Etsy · SHEIN talebi analizi</p>",
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SAYFA 3 — NASIL ÇALIŞIR?
# ═══════════════════════════════════════════════════════════════════════════════
else:
    st.markdown(
        f"""<div class="tt-header">
        <div style="display:flex;align-items:center;gap:12px;">
            {svg("book","white",28)}
            <h1 style="margin:0;color:white;font-size:1.25rem;font-weight:800;letter-spacing:-0.02em;">Nasıl Çalışır?</h1>
        </div>
        <p style="margin:0.2rem 0 0;color:rgba(255,255,255,0.88);font-size:0.82rem;">
            Veri kaynakları · Algoritmalar · Hesaplama mantığı — İşletme diliyle
        </p>
        </div>""",
        unsafe_allow_html=True,
    )

    # ── 1. BÜYÜK RESİM ───────────────────────────────────────────────────────
    st.markdown(f"## {svg('globe','#1d4ed8',20)} &nbsp;Büyük Resim", unsafe_allow_html=True)
    st.markdown("""
TradeTrend, **dört farklı veri kaynağından** her hafta otomatik veri toplayarak bunları tek bir
**trend skoru** altında birleştirir. Bu skor sayesinde hangi ürünün şu an yükselişte olduğunu,
nerede satılmasının daha karlı olduğunu, stok riskinin ne kadar yüksek olduğunu ve
yurt dışından getirilmesi gereken ürün fırsatlarını anlık görebilirsiniz.
""")
    st.markdown(
        """<div class="tt-glass" style="border-left:4px solid #1d4ed8;padding:1rem 1.4rem;">
        <strong>Temel soru:</strong> "Bu ürünü şu an stoklamalı mıyım?" sorusuna
        dört farklı açıdan cevap veriyoruz: insanlar internette ne arıyor, Trendyol'da ne satıyor,
        Amazon TR'de ne alınıyor, TikTok'ta ne viral oluyor.
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── 2. VERİ KAYNAKLARI ───────────────────────────────────────────────────
    st.markdown(f"## {svg('layers','#1d4ed8',20)} &nbsp;Veri Kaynakları (4 Kaynak)", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    sources = [
        ("google",   "#4285f4", "Google Trends", "Haftalık",
         "Son 8 haftanın haftalık arama hacmi (0–100 arası). Türkiye geneli ve bölge bazlı ilgi dağılımı.",
         "Tüketici niyetinin en saf göstergesi. 'Termos' araması Ekim'de zirve yapıyorsa talep var demektir.",
         "Ücretsiz API"),
        ("shopping", "#f27a1a", "Trendyol", "Günlük",
         "'Çok Satanlar' sayfasından ürün sıralamaları, fiyat, puan ve yorum sayısı. İlk 72 ürün.",
         "Gerçek satış verisine en yakın gösterge. 30. sıradan 5. sıraya çıkan ürün ısınıyor demektir.",
         "Web scraping"),
        ("amazon",   "#f90",    "Amazon TR", "Günlük",
         "amazon.com.tr'deki bestseller sıralamaları, yorum sayısı ve ürün puanı. 2019'dan beri TR'de aktif.",
         "Batı yönelimli alıcı profilinin tercihlerini ölçer. Trendyol'da olmayan ürünlerin talebini yakalar.",
         "Web scraping"),
        ("tiktok",   "#fe2c55", "TikTok Creative Center", "Haftalık",
         "Ürünle ilgili hashtag gönderi sayısı, haftalık büyüme oranı. Türkiye filtreli (mümkün olduğunda).",
         "TikTok trendleri gerçek satıştan 2–4 hafta ÖNCE görünür hale gelir — öncü gösterge.",
         "Creative Center API / Apify"),
    ]
    for col, (icon_name, color, title, freq, what, how, src) in zip([c1,c2,c3,c4], sources):
        with col:
            st.markdown(
                f"""<div class="tt-source-card">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:0.7rem;">
                    {svg(icon_name, color, 22)}
                    <strong style="color:{color};font-size:1rem;">{title}</strong>
                </div>
                <span style="background:rgba(29,78,216,0.09);border-radius:10px;padding:1px 8px;
                    font-size:0.74rem;color:#1e3a8a;">{freq}</span>
                <p style="font-size:0.83rem;margin:0.7rem 0 0.4rem;"><strong>Ne alıyoruz?</strong><br>{what}</p>
                <p style="font-size:0.83rem;margin:0 0 0.4rem;"><strong>Nasıl kullanıyoruz?</strong><br>{how}</p>
                <p style="font-size:0.76rem;color:#6b7280;margin:0;">{svg("search",color,12)} &nbsp;{src}</p>
                </div>""",
                unsafe_allow_html=True,
            )
    st.markdown("---")

    # ── 3. COMPOSITE SKOR ────────────────────────────────────────────────────
    st.markdown(f"## {svg('bar-chart','#1d4ed8',20)} &nbsp;Trend Skoru Nasıl Hesaplanır?", unsafe_allow_html=True)
    st.markdown("Her ürün için **dört ayrı kaynak skoru** hesaplanır, sonra ağırlıklı olarak birleştirilir:")
    st.markdown(
        """<div class="tt-formula">
        Trend Skoru = (Google × 0.25) + (Trendyol × 0.35) + (Amazon TR × 0.25) + (TikTok × 0.15)
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown("""
**Neden bu ağırlıklar?**
- 🟠 **Trendyol %35** — Türkiye'nin en büyük e-ticaret sitesi; gerçek satış sinyal en güvenilir kaynak.
- 🔵 **Google %25** — Arama niyeti önemli, ama her arama alışverişe dönüşmez.
- 🟡 **Amazon TR %25** — Özellikle teknoloji, kitap ve genel ürünlerde güçlü alternatif veri.
- 🔴 **TikTok %15** — Öncü gösterge; viral bir video kısa ömürlü de olabilir.
""")

    with st.expander("Google Skoru nasıl hesaplanıyor?"):
        st.markdown("""
Ham Google Trends değeri 0–100 arasındadır. Buna ek olarak **momentum** hesaplanır:

Son 2 haftanın ortalaması ile önceki 2 haftanın ortalaması karşılaştırılır.
Yüzde değişim hesaplanıp skora maksimum **±20 puan** olarak yansır:
```
Momentum etkisi = trend_değişim_yüzdesi × 0.4   (max ±20 puan)
Google Skoru    = ham_skor + momentum_etkisi     (0–100 sınırlandırılır)
```
**Örnek:** "Termos" geçen hafta 72 puan, +%28.5 büyüme →
Momentum = 28.5 × 0.4 = **11.4**  → Google Skoru = **83.4**
        """)

    with st.expander("Trendyol & Amazon TR Skoru nasıl hesaplanıyor?"):
        st.markdown("""
Her iki platform için de aynı formül kullanılır:

| Bileşen | Ağırlık | Açıklama |
|---|---|---|
| Sıralama skoru | %55 | 1. sıra = 100 puan, log ölçekli düşüş |
| Sıralama değişimi | Doğrudan ±15 puan | Önceki haftaya göre iyileşme/kötüleşme |
| Sosyal kanıt (yorum) | %30 | Log ölçekli, max 20 puan |
| Puan bonusu | %15 | 5 üzerinden derecelendirme, max 10 puan |

**Sıralama formülü:** `Sıralama Skoru = max(0, 100 − log10(sıra) × 50)`
→ 1. sıra = 100 puan · 10. sıra ≈ 50 puan · 100. sıra ≈ 0 puan

**Amazon TR farkı:** Amazon Türkiye 2019'dan beri aktif. Trendyol'a kıyasla ürün yelpazesi daha geniş;
özellikle elektronikte ve kitapta bağımsız bir talep sinyali verir.
        """)

    with st.expander("TikTok Skoru nasıl hesaplanıyor?"):
        st.markdown("""
Hashtag gönderi sayısı logaritmik ölçekle normalize edilir:
```
TikTok Skoru = min(100, (log10(gönderi_sayısı) / 7) × 100)
```
- 10 gönderi → ~14 puan  ·  10.000 → ~57 puan  ·  10.000.000 → 100 puan

**Neden log ölçek?** "Termos" ile "Study" arasındaki 100×'lik gönderi farkını doğrudan kullansak,
büyük kategoriler küçükleri ezer. Log ölçek bu farkı makul bir aralığa çeker.
        """)
    st.markdown("---")

    # ── 4. RİSK ──────────────────────────────────────────────────────────────
    st.markdown(f"## {svg('alert','#1d4ed8',20)} &nbsp;Risk Seviyesi Nedir?", unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    with r1:
        st.success("**Düşük Risk — Skor ≥ 60**\n\nHem aranıyor hem satılıyor hem de sosyal medyada gündemde. Stoğa almak için güvenli bölge.")
    with r2:
        st.warning("**Orta Risk — Skor 35–59**\n\nBelirli sinyaller var ama tüm kanallar aynı fikirde değil. Küçük miktarda deneme yapılabilir.")
    with r3:
        st.error("**Yüksek Risk — Skor < 35**\n\nSinyaller zayıf veya düşüşte. Stok yapmaktan kaçının ya da mevcut stoku eritin.")
    st.info("**Not:** Risk seviyesi *talep riskini* ölçer, ürün kalitesiyle ilgisi yoktur.")
    st.markdown("---")

    # ── 5. KANAL ─────────────────────────────────────────────────────────────
    st.markdown(f"## {svg('shopping','#1d4ed8',20)} &nbsp;Kanal Önerisi Nasıl Belirleniyor?", unsafe_allow_html=True)
    st.markdown("Her satış kanalı için **farklı kaynak ağırlıkları** kullanılır:")
    st.dataframe(pd.DataFrame({
        "Kaynak":       ["Google Trends","Trendyol","Amazon TR","TikTok"],
        "Trendyol":     ["% 20","% 50","% 20","% 10"],
        "Amazon TR":    ["% 20","% 20","% 50","% 10"],
        "Instagram":    ["% 25","% 15","% 15","% 45"],
        "Fiz. Mağaza":  ["% 35","% 25","% 15","% 25"],
    }).set_index("Kaynak"), use_container_width=False)
    st.markdown("""
- **Trendyol / Amazon TR** → Platform satış verisi kritik. Zaten orada satıyorsa oraya koy.
- **Instagram** → TikTok trendi kritik (%45). Viral olan ürünler Instagram'da da tutar.
- **Fiziksel Mağaza** → Google aramaları belirleyici (%35). İnsanlar yakın mağazayı ararken Google kullanır.
""")
    st.markdown("---")

    # ── 6. BÖLGE ─────────────────────────────────────────────────────────────
    st.markdown(f"## {svg('map-pin','#1d4ed8',20)} &nbsp;Bölge Seçimi Skoru Nasıl Etkiler?", unsafe_allow_html=True)
    st.markdown("""
Türkiye **7 coğrafi bölge** olarak modellenmiştir. Her bölge için **üç katmanlı** bir düzeltme uygulanır:

1. **Kanal bias** — Bölgenin online/fiziksel mağaza eğilimi kanal skorlarını değiştirir
2. **E-ticaret penetrasyonu** — Bölgenin genel dijital olgunluğu composite skora eklenir
3. **Sektör uyumu** — Bölgenin o sektöre özgü talebi ek skor düzeltmesiyle yansıtılır
""")

    st.markdown("#### 📡 Kanal Tercihi (bölgeye göre online vs. fiziksel)")
    st.dataframe(pd.DataFrame({
        "Bölge":          ["Marmara","Ege","Akdeniz","İç Anadolu","Karadeniz","Doğu Anadolu","G.doğu Anadolu"],
        "Trendyol":       ["+7","+4","+2","+2","-2","-4","-3"],
        "Amazon TR":      ["+8","+4","+2","+2","-2","-4","-4"],
        "Instagram":      ["+10","+8","+5","+3","+1","-2","-1"],
        "Fiz. Mağaza":    ["-5","-2","+2","+3","+6","+9","+9"],
    }).set_index("Bölge"), use_container_width=True)

    st.markdown("#### 🏭 Sektör Uyumu (bölgenin güçlü/zayıf olduğu kategoriler)")
    st.dataframe(pd.DataFrame({
        "Bölge":        ["Marmara","Ege","Akdeniz","İç Anadolu","Karadeniz","Doğu Anadolu","G.doğu Anadolu"],
        "Giyim":        ["+12","+8","+6","+2","-2","-4","-3"],
        "Elektronik":   ["+10","+2","0","+2","-5","-10","-8"],
        "Kozmetik":     ["+10","+8","+4","+2","-3","-6","-4"],
        "Spor":         ["+3","+12","+14","+4","+12","+10","+8"],
        "Gıda":         ["+2","+8","+8","+8","+14","+10","+12"],
        "Ev & Yaşam":   ["+4","+6","+5","+7","+8","+6","+6"],
        "Oyuncak":      ["+5","+2","+2","+4","+3","+2","+3"],
        "Kırtasiye":    ["+6","+3","+1","+6","+4","+2","+2"],
    }).set_index("Bölge"), use_container_width=True)

    st.markdown("""
**Bölgesel mantık örnekleri:**
- 🌆 **Marmara** — E-ticaret en olgun, Instagram alışverişi güçlü. Giyim & kozmetik trendi hızlı yayılır.
- 🌿 **Karadeniz** — Gıda & spor talebi yüksek (yaylacılık, çay kültürü). Online penetrasyon düşük.
- 🏔️ **Doğu Anadolu** — Fiziksel mağaza baskın. Elektronik/kozmetik trend takibi zayıf; spor & gıda güçlü.
- ☀️ **Akdeniz** — Turizm etkisiyle outdoor & spor zirvede, mevsimsel dalgalanma belirgin.
""")
    st.markdown("---")

    # ── 7. ALT KATEGORİ ──────────────────────────────────────────────────────
    st.markdown(f"## {svg('filter','#1d4ed8',20)} &nbsp;Alt Kategori Filtresi Nasıl Çalışır?", unsafe_allow_html=True)
    st.markdown("""
Her sektör için **5 alt kategori** tanımlanmıştır. "Tümü" seçildiğinde tüm alt kategorilerdeki
ürünler tek listede birleştirilir ve puanlanır. Belirli bir alt kategori seçildiğinde yalnızca
o segmentteki ürünler analiz edilir.

**Örnek — Kırtasiye:**
| Alt Kategori | İçerik |
|---|---|
| Kalemler & Yazı | Renkli kalemler, fosforlu, marker, kaligrafi |
| Defterler & Planlayıcı | Spiralli, akıllı defter, bullet journal, planer |
| Okul & Çanta | Okul çantası, termos, beslenme kutusu |
| Sanat & Hobi | Suluboya, washi tape, epoxy resin |
| Ofis Aksesuarı | Masa organizer, dosya, zımba |

Bu sayede "Kırtasiye'de ne satayım?" yerine "Kırtasiye'nin sanat malzemeleri segmentinde trend ne?" sorusunu yanıtlayabilirsiniz.
""")
    st.markdown("---")

    # ── 8. İTHALAT ANALİZİ ───────────────────────────────────────────────────
    st.markdown(f"## {svg('truck','#1d4ed8',20)} &nbsp;İthalat Fırsatları Nasıl Hesaplanıyor?", unsafe_allow_html=True)
    st.markdown("""
**İthalat Fırsatı Analizi** üç temel soruyu yanıtlar:
1. Türk tüketiciler bu ürünü gerçekten istiyor mu? *(Talep skoru)*
2. Bu ürünü yerel piyasada bulmak kolay mı? *(Yerli arz skoru)*
3. Fark ne kadar büyük? *(Arz açığı)*
""")
    st.markdown(
        """<div class="tt-formula">
        İthalat Fırsat Skoru = (Talep Skoru × 0.55) + (Arz Açığı × 0.45)
        Arz Açığı = max(0, Talep Skoru − Yerli Arz Skoru)
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown("""
**Talep Skoru** nasıl ölçülüyor?
- Google TR aramaları (aylık hacim ve büyüme oranı)
- TikTok TR hashtag aktivitesi
- Amazon TR ve Trendyol'da yabancı ürün listelerinin görüntülenme/dönüşüm sinyali

**Yerli Arz Skoru** nasıl ölçülüyor?
- Trendyol'da yerli üretici sayısı ve stok derinliği
- Fiyat rekabeti (yerli ürün fiyatları yüksek = arz az = fiyat piyasası güçlü)
- Ürün çeşitliliği

**Fırsat Seviyeleri:**
- 🟢 **Yüksek Fırsat (≥70):** Talep yüksek, yerli arz yetersiz — harekete geçme zamanı
- 🟡 **Orta Fırsat (50–69):** Fırsat var ama rekabet var — araştırma gerekli
- ⚪ **Takipte (<50):** Henüz olgunlaşmamış — 3–6 ay izle

**Veri kaynakları:** Google Trends TR, AliExpress TR trafik analizi, SHEIN TR, Amazon US/DE ürünlerinin
TR istatistikleri, Etsy TR satıcı analizi
""")
    st.markdown("---")

    # ── 9. HAFTALIK TAHMİN ───────────────────────────────────────────────────
    st.markdown(f"## {svg('trend-up','#1d4ed8',20)} &nbsp;6 Haftalık Talep Tahmini", unsafe_allow_html=True)
    st.markdown(
        """<div class="tt-formula">
        Sonraki_Hafta = Önceki + (Momentum × 0.8^hafta) + Ortalamaya_Çekim
        Ortalamaya_Çekim = (50 − Mevcut) × 0.05
        </div>""",
        unsafe_allow_html=True,
    )
    st.markdown("Yükselen ürünler kısa vadede yükselmeye devam eder, ancak her hafta bu ivme **%20 zayıflar**. Uzak haftalar daha belirsizdir.")
    base, mom = 66.0, 28.5
    fc = [base]
    for w in range(1, 6):
        nv = fc[-1] + mom * 0.05 * (0.8**w)
        fc.append(round(max(0, min(100, nv + (50-nv)*0.05)), 1))
    st.plotly_chart(make_forecast(fc, "Örnek: Termos"), use_container_width=True, key="ex_fc")
    st.markdown("---")

    # ── 10. SINIRLAMALAR ─────────────────────────────────────────────────────
    st.markdown(f"## {svg('alert','#dc2626',20)} &nbsp;Sistemin Sınırlamaları ve Güçlü Yönleri", unsafe_allow_html=True)
    lc, rc = st.columns(2)
    with lc:
        st.markdown("""**Dikkat edilmesi gerekenler:**
- Google Trends görece ilgiyi ölçer, gerçek satış adedini değil
- Trendyol/Amazon scraping sitelerin HTML yapısı değişince etkilenebilir
- TikTok trendleri çok hızlı yükselir, çok hızlı düşer (flash trend riski)
- Mevsimsellik bağımsız olarak hesaplanmıyor
- Fiyat rekabeti ve kargo maliyetleri modele dahil değil
- İthalat fırsat skorları gösterge niteliğinde; gümrük ve lojistik maliyetler ayrıca hesaplanmalı""")
    with rc:
        st.markdown("""**Güçlü olduğu durumlar:**
- Yeni sektöre girerken hangi ürünlerden başlanacağını belirlemek
- Mevcut ürünlerin trend durumunu haftalık takip etmek
- Rakiplerin öne çıkardığı kategorileri erken fark etmek
- Hangi kanalda reklam bütçesi harcanacağına karar vermek
- Stoğa ne kadar yatırım yapılacağına referans oluşturmak
- Yurt dışından getirilmesi gereken ürünleri sistematik olarak tespit etmek""")

    st.markdown(
        "<p style='text-align:center;color:#9ca3af;font-size:0.8rem;margin-top:2rem'>"
        "TradeTrend v0.2 — Google Trends · Trendyol · Amazon TR · TikTok · İthalat Analizi</p>",
        unsafe_allow_html=True,
    )
