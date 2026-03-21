import streamlit as st
import os
import yfinance as yf
import plotly.graph_objects as go
from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv
from datetime import datetime
from html import escape

load_dotenv()

# ── Must be first Streamlit call ──────────────────────────────────────────────
st.set_page_config(
    page_title="Stock Finder by Interest",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

GROQ_KEY  = os.getenv("GROQ_KEY")  or st.secrets.get("GROQ_KEY")
TAVILY_KEY = os.getenv("TAVILY_KEY") or st.secrets.get("TAVILY_KEY")
client = Groq(api_key=GROQ_KEY)
tavily = TavilyClient(api_key=TAVILY_KEY)

RANGES = {
    "1D": ("1d", "5m"),
    "5D": ("5d", "30m"),
    "1M": ("1mo", "1d"),
    "6M": ("6mo", "1d"),
    "1Y": ("1y", "1d"),
    "5Y": ("5y", "1wk"),
    "All": ("max", "1mo"),
}

EXAMPLE_INTERESTS = [("🎮", "Gaming"), ("⚡", "Electric Vehicles"), ("🤖", "AI & Chips"), ("🚀", "Space")]
THEME_COLORS = ["#10b981", "#3b82f6", "#8b5cf6", "#f97316", "#ec4899", "#14b8a6"]

# ── CSS & JS injection ────────────────────────────────────────────────────────
def inject_styles():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] {
  font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}

/* Ambient glow background */
.stApp {
  background: #060912 !important;
}
.stApp::before {
  content: '';
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background:
    radial-gradient(ellipse 70% 50% at 10% 0%,  rgba(59,130,246,0.08) 0%, transparent 65%),
    radial-gradient(ellipse 60% 50% at 90% 90%, rgba(139,92,246,0.06) 0%, transparent 65%);
}

/* Hide Streamlit chrome */
#MainMenu, footer,
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

/* Layout */
.block-container {
  padding: 2rem 2.5rem 5rem !important;
  max-width: 1240px !important;
  position: relative; z-index: 1;
}

/* Typography */
h1,h2,h3,h4 { color: #f8fafc !important; letter-spacing: -0.3px; }
p { color: #64748b; }
a { color: #60a5fa !important; }

/* ── Text Input ── */
[data-testid="stTextInput"] > div > div {
  background: rgba(255,255,255,0.04) !important;
  border: 1.5px solid rgba(255,255,255,0.08) !important;
  border-radius: 14px !important;
  backdrop-filter: blur(12px) !important;
  transition: all 0.2s !important;
}
[data-testid="stTextInput"] > div > div:focus-within {
  border-color: rgba(59,130,246,0.5) !important;
  box-shadow: 0 0 0 3px rgba(59,130,246,0.1), 0 0 20px rgba(59,130,246,0.08) !important;
}
[data-testid="stTextInput"] input {
  color: #e2e8f0 !important;
  font-size: 0.95rem !important;
  background: transparent !important;
  padding: 0.2rem 0 !important;
}
[data-testid="stTextInput"] input::placeholder { color: #1e293b !important; }

/* ── All Buttons base ── */
[data-testid="stButton"] > button,
.stButton > button {
  background: rgba(255,255,255,0.04) !important;
  color: #475569 !important;
  border: 1px solid rgba(255,255,255,0.08) !important;
  border-radius: 10px !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.82rem !important;
  font-weight: 500 !important;
  transition: all 0.18s ease !important;
  line-height: 1.5 !important;
}
[data-testid="stButton"] > button:hover,
.stButton > button:hover {
  background: rgba(255,255,255,0.07) !important;
  color: #e2e8f0 !important;
  border-color: rgba(59,130,246,0.3) !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.2) !important;
}

/* Primary button */
[data-testid="stBaseButton-primary"],
button[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
  color: #fff !important;
  border: none !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  border-radius: 14px !important;
  box-shadow: 0 4px 16px rgba(59,130,246,0.35) !important;
}
[data-testid="stBaseButton-primary"]:hover,
button[data-testid="stBaseButton-primary"]:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
  box-shadow: 0 8px 24px rgba(59,130,246,0.45) !important;
  color: #fff !important;
  transform: translateY(-1px) !important;
  border: none !important;
}

/* ── Chip buttons (example interests) ── */
[data-btn-type="chip"] {
  border-radius: 50px !important;
  font-size: 0.78rem !important;
  color: #475569 !important;
  padding: 0.3rem 0.9rem !important;
}
[data-btn-type="chip"]:hover {
  background: rgba(59,130,246,0.08) !important;
  border-color: rgba(59,130,246,0.3) !important;
  color: #93c5fd !important;
  transform: none !important;
}

/* ── Card CTA buttons ── */
[data-btn-type="card-cta"] {
  background: rgba(59,130,246,0.07) !important;
  border: 1px solid rgba(59,130,246,0.18) !important;
  border-radius: 10px !important;
  color: #60a5fa !important;
  font-size: 0.78rem !important;
  font-weight: 600 !important;
  width: 100% !important;
  margin-top: 0 !important;
}
[data-btn-type="card-cta"]:hover {
  background: rgba(59,130,246,0.15) !important;
  border-color: rgba(59,130,246,0.4) !important;
  color: #93c5fd !important;
  transform: none !important;
  box-shadow: none !important;
}

/* ── Back button ── */
[data-btn-type="back"] {
  background: transparent !important;
  border: none !important;
  color: #334155 !important;
  font-size: 0.8rem !important;
  padding: 0 !important;
  box-shadow: none !important;
}
[data-btn-type="back"]:hover {
  background: transparent !important;
  border: none !important;
  color: #60a5fa !important;
  transform: none !important;
  box-shadow: none !important;
}

/* ── Show more button ── */
[data-btn-type="show-more"] {
  background: rgba(255,255,255,0.02) !important;
  border: 1px dashed rgba(255,255,255,0.1) !important;
  border-radius: 14px !important;
  color: #334155 !important;
  font-size: 0.82rem !important;
  width: 100% !important;
}
[data-btn-type="show-more"]:hover {
  border-color: rgba(59,130,246,0.3) !important;
  color: #60a5fa !important;
  transform: none !important;
  background: rgba(59,130,246,0.04) !important;
  box-shadow: none !important;
}

/* ── Range buttons ── */
[data-btn-type="range"] {
  border-radius: 8px !important;
  font-size: 0.75rem !important;
  font-weight: 600 !important;
  padding: 0.3rem 0.65rem !important;
}
[data-testid="stBaseButton-primary"][data-btn-type="range"] {
  background: rgba(59,130,246,0.15) !important;
  border: 1px solid rgba(59,130,246,0.4) !important;
  color: #60a5fa !important;
  border-radius: 8px !important;
  font-size: 0.75rem !important;
  font-weight: 600 !important;
  box-shadow: none !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 14px !important;
  padding: 1rem !important;
  backdrop-filter: blur(8px) !important;
}
[data-testid="stMetricLabel"] > div {
  font-size: 0.6rem !important;
  font-weight: 700 !important;
  text-transform: uppercase !important;
  letter-spacing: 1px !important;
  color: #1e293b !important;
}
[data-testid="stMetricValue"] {
  font-size: 1.05rem !important;
  font-weight: 700 !important;
  color: #f1f5f9 !important;
  letter-spacing: -0.3px !important;
}
[data-testid="stMetricDelta"] svg { display: none !important; }
[data-testid="stMetricDelta"] > div { font-size: 0.72rem !important; font-weight: 600 !important; }

/* ── Divider ── */
[data-testid="stDivider"] { border-color: rgba(255,255,255,0.04) !important; }
hr { border-color: rgba(255,255,255,0.04) !important; }

/* ── Info / Alert ── */
[data-testid="stAlert"] {
  background: rgba(59,130,246,0.05) !important;
  border: 1px solid rgba(59,130,246,0.15) !important;
  border-radius: 12px !important;
}
[data-testid="stAlert"] p,
[data-testid="stAlert"] * { color: #93c5fd !important; }

/* ── Expander ── */
[data-testid="stExpander"] {
  background: rgba(255,255,255,0.025) !important;
  border: 1px solid rgba(255,255,255,0.06) !important;
  border-radius: 12px !important;
}
[data-testid="stExpander"] summary { color: #3b82f6 !important; font-size: 0.8rem !important; }

/* ── Caption ── */
[data-testid="stCaptionContainer"] p { color: #1e293b !important; font-size: 0.72rem !important; }

/* ── Progress bar ── */
[data-testid="stProgressBar"] > div {
  background: linear-gradient(90deg, #3b82f6, #8b5cf6) !important;
  border-radius: 4px !important;
}
[data-testid="stProgressBar"] {
  background: rgba(255,255,255,0.04) !important;
  border-radius: 4px !important;
}

/* ── Toggle ── */
[data-testid="stToggle"] label { color: #475569 !important; font-size: 0.82rem !important; }

/* ── Status ── */
[data-testid="stStatusContainer"] {
  background: rgba(255,255,255,0.03) !important;
  border: 1px solid rgba(255,255,255,0.07) !important;
  border-radius: 12px !important;
}
[data-testid="stStatusContainer"] * { color: #94a3b8 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.07); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(59,130,246,0.4); }

/* ── Glass card (stock cards) ── */
.glass-card {
  background: rgba(255,255,255,0.035);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 20px;
  padding: 1.2rem 1.2rem 0.9rem;
  position: relative; overflow: hidden;
  margin-bottom: 0.5rem;
}
.glass-card::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.13), transparent);
}
.card-top-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.45rem; }
.ticker-pill {
  background: rgba(59,130,246,0.12);
  border: 1px solid rgba(59,130,246,0.2);
  color: #93c5fd; border-radius: 8px;
  padding: 0.18rem 0.55rem;
  font-size: 0.7rem; font-weight: 800; letter-spacing: 0.5px; font-family: 'Inter', monospace;
}
.chg-up { color: #10b981; font-size: 0.72rem; font-weight: 600; }
.chg-dn { color: #f43f5e; font-size: 0.72rem; font-weight: 600; }
.card-company { font-size: 0.85rem; font-weight: 600; color: #e2e8f0; margin-bottom: 0.2rem; line-height: 1.35; }
.card-price { font-size: 1.35rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px; margin-bottom: 0.5rem; }
.card-badges { display: flex; gap: 0.4rem; align-items: center; margin-bottom: 0.6rem; flex-wrap: wrap; }
.badge-cap-str { color: #334155; font-size: 0.68rem; }
.badge-cap-size {
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08);
  color: #475569; padding: 0.1rem 0.4rem; border-radius: 4px;
  font-size: 0.6rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px;
}
.card-reason {
  font-size: 0.72rem; color: #334155; font-style: italic; line-height: 1.55;
  border-top: 1px solid rgba(255,255,255,0.05); padding-top: 0.55rem;
}

/* App header HTML */
.app-header { display: flex; align-items: center; gap: 0.85rem; margin-bottom: 2.25rem; }
.app-icon {
  width: 42px; height: 42px; flex-shrink: 0;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  border-radius: 12px; display: flex; align-items: center; justify-content: center;
  font-size: 1.25rem; box-shadow: 0 4px 20px rgba(59,130,246,0.35);
}
.app-title-text { font-size: 1.4rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.5px; }
.app-subtitle { font-size: 0.76rem; color: #1e293b; margin-top: 0.1rem; }

/* Section label */
.sec-label {
  font-size: 0.68rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 1.5px; color: #1e2d3d; margin-bottom: 1rem;
}
.sec-label-accent { color: #3b82f6; }

/* Why matched */
.why-matched {
  background: rgba(59,130,246,0.06);
  border: 1px solid rgba(59,130,246,0.15);
  border-radius: 12px; padding: 0.7rem 1rem;
  font-size: 0.8rem; color: #93c5fd; margin: 0.5rem 0 1.25rem;
  display: flex; align-items: flex-start; gap: 0.5rem;
}

/* Live badge */
.live-badge {
  display: inline-flex; align-items: center; gap: 0.4rem;
  background: rgba(16,185,129,0.08); border: 1px solid rgba(16,185,129,0.2);
  color: #34d399; border-radius: 50px; padding: 0.18rem 0.65rem;
  font-size: 0.62rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
}
.live-dot {
  width: 6px; height: 6px; background: #10b981; border-radius: 50%;
  animation: livepulse 2s infinite;
}
@keyframes livepulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }

/* Analysis blocks */
.analysis-block {
  background: rgba(255,255,255,0.025);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 14px; padding: 1rem 1.25rem; margin-bottom: 0.75rem;
}

/* News items */
.news-row {
  display: flex; align-items: flex-start; gap: 0.75rem;
  padding: 0.85rem 0; border-bottom: 1px solid rgba(255,255,255,0.04);
}
.news-dot { width: 6px; height: 6px; background: #3b82f6; border-radius: 50%; margin-top: 0.35rem; flex-shrink: 0; }
.news-title { font-size: 0.82rem; font-weight: 500; color: #cbd5e1; line-height: 1.45; }
.news-title a { color: #cbd5e1 !important; text-decoration: none; }
.news-title a:hover { color: #60a5fa !important; }
.news-meta { font-size: 0.68rem; color: #1e293b; margin-top: 0.2rem; }

/* Disclaimer */
.disclaimer {
  background: rgba(255,255,255,0.018);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 10px; padding: 0.75rem 1rem;
  font-size: 0.7rem; color: #1e293b; line-height: 1.55; margin-top: 1rem;
}

/* Theme chart summary cards */
.theme-stat-row { display: flex; gap: 0.75rem; margin-top: 0.75rem; }
.theme-stat {
  flex: 1; background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 0.8rem 1rem;
}
.theme-stat-lbl { font-size: 0.62rem; color: #1e293b; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 0.3rem; }
.theme-stat-val { font-size: 1rem; font-weight: 700; color: #f8fafc; }
.theme-stat-sub { font-size: 0.7rem; margin-top: 0.15rem; }
</style>

<script>
(function() {
  function tag() {
    document.querySelectorAll('[data-testid="stButton"] button').forEach(function(b) {
      var t = b.textContent.trim();
      if (t === 'View Analysis \u2192')               b.setAttribute('data-btn-type', 'card-cta');
      else if (t === '\u2190 Back to results')         b.setAttribute('data-btn-type', 'back');
      else if (t.indexOf('Show More') !== -1)          b.setAttribute('data-btn-type', 'show-more');
      else if (['1D','5D','1M','6M','1Y','5Y','All'].indexOf(t) !== -1) b.setAttribute('data-btn-type', 'range');
      else if (['Gaming','Electric Vehicles','AI & Chips','Space'].some(function(c){ return t.indexOf(c) !== -1; })) b.setAttribute('data-btn-type', 'chip');
    });
  }
  tag();
  new MutationObserver(tag).observe(document.body, {childList:true, subtree:true});
})();
</script>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def format_market_cap(mc):
    if not mc: return "N/A"
    if mc >= 1e12: return f"${mc/1e12:.1f}T"
    if mc >= 1e9:  return f"${mc/1e9:.1f}B"
    if mc >= 1e6:  return f"${mc/1e6:.1f}M"
    return f"${mc:,.0f}"

def market_cap_badge(mc):
    if not mc: return "Unknown"
    if mc >= 200e9: return "Large Cap"
    if mc >= 10e9:  return "Mid Cap"
    if mc >= 2e9:   return "Small Cap"
    return "Micro Cap"

def stock_card_html(symbol, info, reason):
    dc = info["day_change_pct"]
    chg_class = "chg-up" if dc >= 0 else "chg-dn"
    arrow = "▲" if dc >= 0 else "▼"
    chg_str = f"{arrow} {abs(dc):.2f}% today"
    reason_html = f'<div class="card-reason">{escape(reason)}</div>' if reason else ""
    return f"""
<div class="glass-card">
  <div class="card-top-row">
    <span class="ticker-pill">{escape(symbol)}</span>
    <span class="{chg_class}">{chg_str}</span>
  </div>
  <div class="card-company">{escape(info['name'])}</div>
  <div class="card-price">${info['price']:.2f}</div>
  <div class="card-badges">
    <span class="badge-cap-str">{info['market_cap_str']}</span>
    <span class="badge-cap-size">{info['market_cap_badge']}</span>
  </div>
  {reason_html}
</div>"""

def news_item_html(title, url, source, pub_str):
    meta = "  ·  ".join(filter(None, [escape(source), pub_str]))
    return f"""
<div class="news-row">
  <div class="news-dot" style="margin-top:0.35rem;flex-shrink:0"></div>
  <div>
    <div class="news-title"><a href="{escape(url)}" target="_blank">{escape(title)}</a></div>
    <div class="news-meta">{meta}</div>
  </div>
</div>"""


# ── Data functions ────────────────────────────────────────────────────────────

def get_stock_data(symbol, period="1y", interval="1d"):
    try:
        df = yf.Ticker(symbol).history(period=period, interval=interval)
        return df[["Close", "Volume"]] if not df.empty else None
    except Exception:
        return None

def get_stock_info(symbol):
    try:
        info  = yf.Ticker(symbol).info
        price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        if not price: return None

        prev  = info.get("previousClose") or info.get("regularMarketPreviousClose")
        day_chg     = price - prev if prev else 0.0
        day_chg_pct = (day_chg / prev * 100) if prev else 0.0

        earn_ts = info.get("earningsTimestamp")
        earn_dt = None
        if earn_ts:
            try: earn_dt = datetime.fromtimestamp(earn_ts).strftime("%b %d, %Y")
            except Exception: pass

        rec_key = info.get("recommendationKey", "")
        rec_lbl = {"strong_buy":"Strong Buy","buy":"Buy","hold":"Hold",
                   "sell":"Sell","strong_sell":"Strong Sell"}.get(
            rec_key, rec_key.replace("_"," ").title() if rec_key else "N/A")

        div = info.get("dividendYield")
        sp  = info.get("shortPercentOfFloat")
        mc  = info.get("marketCap")

        return dict(
            price=price, name=info.get("longName", symbol),
            description=info.get("longBusinessSummary","No description available."),
            sector=info.get("sector","N/A"), industry=info.get("industry","N/A"),
            day_change=day_chg, day_change_pct=day_chg_pct,
            week52_change=info.get("52WeekChange",0)*100,
            market_cap=mc, market_cap_str=format_market_cap(mc), market_cap_badge=market_cap_badge(mc),
            pe_trailing=info.get("trailingPE"), pe_forward=info.get("forwardPE"),
            week52_high=info.get("fiftyTwoWeekHigh"), week52_low=info.get("fiftyTwoWeekLow"),
            analyst_target=info.get("targetMeanPrice"), analyst_rec=rec_lbl,
            earnings_date=earn_dt,
            dividend_yield=f"{div*100:.2f}%" if div else "None",
            beta=info.get("beta"),
            short_pct=f"{sp*100:.1f}%" if sp else "N/A",
            revenue=format_market_cap(info.get("totalRevenue")),
        )
    except Exception:
        return None

def is_valid_input(text):
    try:
        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":(
                f'Is "{text}" a valid topic related to publicly traded companies? '
                "YES or NO only.\n"
                "Valid: gaming, iphone, electric cars, sports, food\n"
                "Invalid: asdfgh, 123456, random gibberish"
            )}])
        return "YES" in r.choices[0].message.content.strip().upper()
    except Exception:
        return True

def fetch_companies(interest, exclude_symbols=None):
    excl = exclude_symbols or []
    excl_txt = f"Do NOT include: {', '.join(excl)}." if excl else ""
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":(
            f"The user is interested in: {interest}\n\n"
            "List 6 US publicly traded companies related to this interest.\n"
            f"{excl_txt}\n"
            "Format (exactly):\nCompany Name | TICKER | Short reason\n\n"
            "Example:\nApple | AAPL | Makes the iPhone\n\nOnly the list, no extra text."
        )}])
    return r.choices[0].message.content

def parse_companies(text):
    result = []
    for line in text.strip().split("\n"):
        if "|" not in line: continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) >= 3:
            name, ticker, reason = parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            name, ticker, reason = parts[0], parts[1], ""
        else: continue
        if ticker.replace("-","").isalpha() and ticker.isupper():
            result.append((name, ticker, reason))
    return result

def get_news_and_analysis(symbol, company_name, stock_info=None):
    try:
        year = datetime.now().year
        results = tavily.search(
            query=f"{company_name} {symbol} stock news analysis {year} {year+1}",
            max_results=5)
        news_items = results.get("results", [])
        news_text  = "\n".join([f"- {r['title']}: {r['content']}" for r in news_items])

        fin = ""
        if stock_info:
            pe  = f"{stock_info['pe_trailing']:.1f}x" if stock_info.get("pe_trailing") else "N/A"
            fpe = f"{stock_info['pe_forward']:.1f}x"  if stock_info.get("pe_forward")  else "N/A"
            w52h = f"${stock_info['week52_high']:.2f}" if stock_info.get("week52_high") else "N/A"
            w52l = f"${stock_info['week52_low']:.2f}"  if stock_info.get("week52_low")  else "N/A"
            tgt  = f"${stock_info['analyst_target']:.2f}" if stock_info.get("analyst_target") else "N/A"
            beta = f"{stock_info['beta']:.2f}" if stock_info.get("beta") else "N/A"
            fin = (
                f"\nFinancial snapshot:\n"
                f"- Price: ${stock_info['price']:.2f} | Market Cap: {stock_info['market_cap_str']}\n"
                f"- Trailing P/E: {pe} | Forward P/E: {fpe}\n"
                f"- 52W Range: {w52l} – {w52h}\n"
                f"- Analyst: {stock_info['analyst_rec']} | Target: {tgt}\n"
                f"- Earnings: {stock_info.get('earnings_date') or 'N/A'} | Beta: {beta}\n"
            )

        r = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role":"system","content":(
                    "You are a senior equity analyst. Be precise, cite numbers, reference provided financial data. "
                    "Never speculate without evidence. Always reference P/E, 52W range, and analyst target when provided.")},
                {"role":"user","content":(
                    f"Analyze {company_name} ({symbol}).\n{fin}\nRecent News:\n{news_text}\n\n"
                    "Structured analysis — use EXACTLY these section headers:\n\n"
                    "## Upcoming Catalysts\n2-3 events with dates. Reference earnings date if provided.\n\n"
                    "## Historical Comparison\n1-2 similar past events with dates and % moves.\n\n"
                    "## Price Impact Assessment\nReference 52W range and analyst target. Balanced upside/downside.\n\n"
                    "## Key Risks\n2-3 specific risks. Reference beta and valuation.\n\n"
                    "## Disclaimer\nFor research only. Not investment advice."
                )}])
        return r.choices[0].message.content, news_items
    except Exception:
        return "Analysis unavailable at this time.", []

def load_stocks(symbols):
    data, info_map = {}, {}
    if not symbols: return data, info_map
    prog = st.progress(0, text=f"Loading {len(symbols)} stocks…")
    for i, sym in enumerate(symbols):
        prog.progress((i+1)/len(symbols), text=f"Fetching {sym}… ({i+1}/{len(symbols)})")
        df   = get_stock_data(sym)
        info = get_stock_info(sym)
        if df is not None and info is not None:
            data[sym], info_map[sym] = df, info
    prog.empty()
    return data, info_map

def make_chart(df, symbol, show_ma=True):
    first, last = df["Close"].iloc[0], df["Close"].iloc[-1]
    up     = last >= first
    color  = "#10b981" if up else "#f43f5e"
    fill   = "rgba(16,185,129,0.12)" if up else "rgba(244,63,94,0.12)"
    chg    = last - first
    chg_pct = chg / first * 100
    chg_str = f"+{chg:.2f} (+{chg_pct:.2f}%)" if up else f"{chg:.2f} ({chg_pct:.2f}%)"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index, y=df["Close"], mode="lines", name="Price",
        line=dict(color=color, width=2), fill="tozeroy", fillcolor=fill,
        hovertemplate="%{x}<br>$%{y:.2f}<extra></extra>", yaxis="y1"))

    if show_ma and len(df) >= 50:
        ma50 = df["Close"].rolling(50).mean()
        fig.add_trace(go.Scatter(
            x=df.index, y=ma50, mode="lines", name="50-day MA",
            line=dict(color="#f97316", width=1.5, dash="dot"),
            hovertemplate="%{x}<br>MA50: $%{y:.2f}<extra></extra>", yaxis="y1"))

    if "Volume" in df.columns:
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"], name="Volume",
            marker_color="rgba(100,100,100,0.3)",
            hovertemplate="%{x}<br>Vol: %{y:,.0f}<extra></extra>", yaxis="y2"))

    fig.update_layout(
        title=dict(
            text=(f"<b>{symbol}</b>   "
                  f"<span style='font-size:20px'>${last:.2f}</span>   "
                  f"<span style='color:{color};font-size:14px'>{chg_str}</span>"),
            font=dict(size=15, color="#f8fafc")),
        xaxis=dict(showgrid=False, zeroline=False, color="#334155"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", zeroline=False,
                   side="right", color="#334155", domain=[0.25, 1.0]),
        yaxis2=dict(showgrid=False, zeroline=False, side="left",
                    color="#334155", domain=[0.0, 0.2]),
        plot_bgcolor="#080c14", paper_bgcolor="#080c14",
        hovermode="x unified",
        margin=dict(l=10, r=60, t=60, b=10),
        showlegend=True,
        legend=dict(orientation="h", y=1.08, x=0, font=dict(color="#475569", size=11)),
        font=dict(family="Inter, system-ui, sans-serif"),
    )
    return fig

def make_theme_chart(all_data, symbols, interest):
    fig = go.Figure()
    best_sym, worst_sym, best_val, worst_val = None, None, -999.0, 999.0
    returns = []

    for i, sym in enumerate(symbols):
        df = all_data.get(sym)
        if df is None or len(df) < 2: continue
        base = df["Close"].iloc[0]
        if base == 0: continue
        norm  = df["Close"] / base * 100
        final = norm.iloc[-1]
        ret   = final - 100
        returns.append(ret)
        if final > best_val:  best_val, best_sym   = final, sym
        if final < worst_val: worst_val, worst_sym = final, sym

        fig.add_trace(go.Scatter(
            x=df.index, y=norm, mode="lines", name=sym,
            line=dict(color=THEME_COLORS[i % len(THEME_COLORS)], width=2),
            hovertemplate=f"<b>{sym}</b>: %{{y:.1f}}<extra></extra>"))

    fig.add_hline(y=100, line_dash="dot", line_color="#1e2d45", opacity=0.8,
                  annotation_text="Start", annotation_position="left",
                  annotation_font_color="#334155")

    fig.update_layout(
        title=dict(
            text=f"<b>Theme: {escape(interest)}</b>  "
                 f"<span style='font-size:12px;color:#475569'>Rebased to 100 at start of period</span>",
            font=dict(size=15, color="#f8fafc")),
        xaxis=dict(showgrid=False, color="#334155"),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", color="#334155"),
        plot_bgcolor="#080c14", paper_bgcolor="#080c14",
        hovermode="x unified",
        margin=dict(l=10, r=10, t=60, b=10),
        legend=dict(orientation="h", y=-0.15, font=dict(color="#475569", size=11)),
        font=dict(family="Inter, system-ui, sans-serif"),
    )
    avg = sum(returns) / len(returns) if returns else 0
    return fig, best_sym, best_val - 100, worst_sym, worst_val - 100, avg


# ── Session state ─────────────────────────────────────────────────────────────
for k, v in [
    ("all_data", {}), ("result", ""), ("ranges", {}),
    ("stock_info", {}), ("selected_stock", None),
    ("analysis", {}), ("news_items", {}),
    ("current_interest", ""), ("all_symbols_shown", []),
    ("company_meta", {}), ("prefill_value", ""), ("trigger_search", False),
]:
    if k not in st.session_state:
        st.session_state[k] = v


# ── Styles ────────────────────────────────────────────────────────────────────
inject_styles()


# ══════════════════════════════════════════════════════════════════════════════
# DETAIL VIEW
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.selected_stock:
    symbol = st.session_state.selected_stock
    info   = st.session_state.stock_info.get(symbol)
    if not info:
        st.session_state.selected_stock = None
        st.rerun()

    meta   = st.session_state.company_meta.get(symbol, {})

    # Back button
    if st.button("← Back to results", key="back_btn"):
        st.session_state.selected_stock = None
        st.rerun()

    # Header
    st.markdown(f"## {escape(info['name'])} ({escape(symbol)})")
    st.caption(f"{info['sector']}  ·  {info['industry']}")

    if meta.get("reason"):
        st.markdown(
            f'<div class="why-matched">💡 <strong>Why it matched:</strong> {escape(meta["reason"])}</div>',
            unsafe_allow_html=True)

    # Description
    desc = info["description"]
    if len(desc) > 350:
        sentences = desc.split(". ")
        teaser = ". ".join(sentences[:2]) + ("." if len(sentences) > 2 else "")
        st.write(teaser)
        with st.expander("Read full company description"):
            st.write(desc)
    else:
        st.write(desc)

    st.divider()

    # ── Metrics ───────────────────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Key Metrics</div>', unsafe_allow_html=True)

    dc = info["day_change_pct"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Price",       f"${info['price']:.2f}",          f"{dc:+.2f}% today",  help="vs previous close")
    m2.metric("Market Cap",  info["market_cap_str"])
    m3.metric("Trailing P/E",f"{info['pe_trailing']:.1f}x"     if info.get("pe_trailing") else "N/A", help="Last 12-month earnings")
    m4.metric("Forward P/E", f"{info['pe_forward']:.1f}x"      if info.get("pe_forward")  else "N/A", help="Next 12-month estimate")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("52W High",    f"${info['week52_high']:.2f}"  if info.get("week52_high")  else "N/A")
    m6.metric("52W Low",     f"${info['week52_low']:.2f}"   if info.get("week52_low")   else "N/A")
    m7.metric("Analyst Target", f"${info['analyst_target']:.2f}" if info.get("analyst_target") else "N/A", help="Wall Street mean target")
    m8.metric("Analyst Rating", info["analyst_rec"])

    m9, m10, m11, m12 = st.columns(4)
    m9.metric("Earnings Date",  info["earnings_date"] or "N/A", help="Next quarterly release")
    m10.metric("Dividend Yield", info["dividend_yield"])
    m11.metric("Beta",          f"{info['beta']:.2f}" if info.get("beta") else "N/A", help="Volatility vs S&P 500")
    m12.metric("Short Interest", info["short_pct"], help="% of float sold short")

    st.divider()

    # ── Chart ─────────────────────────────────────────────────────────────────
    st.markdown('<div class="sec-label">Price Chart</div>', unsafe_allow_html=True)
    active_range = st.session_state.ranges.get(symbol, "1Y")
    rc = st.columns(len(RANGES))
    for i, label in enumerate(RANGES.keys()):
        btn_type = "primary" if label == active_range else "secondary"
        if rc[i].button(label, key=f"range_{symbol}_{label}", type=btn_type):
            if label != active_range:
                st.session_state.ranges[symbol] = label
                period, interval = RANGES[label]
                df_new = get_stock_data(symbol, period, interval)
                if df_new is not None:
                    st.session_state.all_data[symbol] = df_new
                st.rerun()

    df = st.session_state.all_data.get(symbol)
    if df is not None:
        st.plotly_chart(make_chart(df, symbol, show_ma=active_range not in ("1D","5D")),
                        width="stretch")

    st.divider()

    # ── AI Analysis ───────────────────────────────────────────────────────────
    col_title, col_badge = st.columns([3, 1])
    col_title.markdown("### AI Analysis")
    col_badge.markdown('<div class="live-badge" style="margin-top:0.5rem"><div class="live-dot"></div> Real-time</div>',
                       unsafe_allow_html=True)

    if symbol not in st.session_state.analysis:
        with st.status("Analyzing…", expanded=True) as status:
            st.write("🔍 Searching latest news and filings…")
            analysis, news_items = get_news_and_analysis(symbol, info["name"], stock_info=info)
            st.write("✅ Analysis complete.")
            status.update(label="Analysis ready", state="complete", expanded=False)
        st.session_state.analysis[symbol]   = analysis
        st.session_state.news_items[symbol] = news_items

    # Render each section of the analysis in a styled block
    raw = st.session_state.analysis[symbol]
    sections = raw.split("##")
    for sec in sections:
        sec = sec.strip()
        if not sec: continue
        lines = sec.split("\n", 1)
        title = lines[0].strip()
        body  = lines[1].strip() if len(lines) > 1 else ""
        st.markdown(
            f'<div class="analysis-block"><p style="font-size:0.68rem;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:1px;color:#3b82f6;margin-bottom:0.5rem">{escape(title)}</p>'
            f'<p style="font-size:0.82rem;color:#94a3b8;line-height:1.7;margin:0">{escape(body)}</p></div>',
            unsafe_allow_html=True)

    # ── News ──────────────────────────────────────────────────────────────────
    news = st.session_state.news_items.get(symbol, [])
    if news:
        st.divider()
        st.markdown("### Latest News")
        news_html = ""
        for article in news:
            title  = article.get("title","No title")
            url    = article.get("url","#")
            source = article.get("source","")
            pub    = article.get("published_date","")
            pub_str = ""
            if pub:
                try:
                    pub_str = datetime.fromisoformat(pub.replace("Z","+00:00")).strftime("%b %d, %Y")
                except Exception:
                    pub_str = pub[:10]
            news_html += news_item_html(title, url, source, pub_str)
        st.markdown(news_html, unsafe_allow_html=True)

    st.divider()
    st.markdown(
        '<div class="disclaimer">⚠️ For research and educational purposes only. '
        'Not investment advice. Always conduct your own due diligence before making investment decisions.</div>',
        unsafe_allow_html=True)

    st.stop()  # Don't render home screen below


# ══════════════════════════════════════════════════════════════════════════════
# HOME SCREEN
# ══════════════════════════════════════════════════════════════════════════════

# App header
st.markdown("""
<div class="app-header">
  <div class="app-icon">📈</div>
  <div>
    <div class="app-title-text">Stock Finder</div>
    <div class="app-subtitle">Discover stocks based on what you care about — powered by AI &amp; real market data</div>
  </div>
</div>""", unsafe_allow_html=True)

# Search bar
col_in, col_btn = st.columns([5, 1])
with col_in:
    interest = st.text_input(
        "interest", value=st.session_state.prefill_value,
        placeholder="e.g. gaming, electric vehicles, AI chips, space…",
        label_visibility="collapsed")
with col_btn:
    search_clicked = st.button("Search", type="primary", width="stretch")

# Example chips
st.caption("Try:")
chip_cols = st.columns(len(EXAMPLE_INTERESTS))
for i, (emoji, label) in enumerate(EXAMPLE_INTERESTS):
    with chip_cols[i]:
        if st.button(f"{emoji} {label}", key=f"chip_{i}", width="stretch"):
            st.session_state.prefill_value  = label
            st.session_state.trigger_search = True
            st.rerun()

# ── Search logic ──────────────────────────────────────────────────────────────
run_search = search_clicked or st.session_state.trigger_search
if st.session_state.trigger_search:
    st.session_state.trigger_search = False
    st.session_state.prefill_value  = ""

if run_search:
    topic = interest.strip()
    if not topic:
        st.error("Please enter an interest topic.")
    else:
        st.session_state.update(dict(
            selected_stock=None, analysis={}, news_items={},
            all_symbols_shown=[], company_meta={},
            current_interest=topic, all_data={}, stock_info={}))

        with st.spinner("Validating topic…"):
            if not is_valid_input(topic):
                st.error("Please enter a valid interest topic — e.g. gaming, electric cars, healthcare.")
                st.stop()

        with st.spinner("Finding relevant companies…"):
            result    = fetch_companies(topic)
            companies = parse_companies(result)
            symbols   = [t for _, t, _ in companies]
            for name, ticker, reason in companies:
                st.session_state.company_meta[ticker] = {"llm_name": name, "reason": reason}
            st.session_state.all_symbols_shown = symbols

        data, info_map = load_stocks(symbols)
        st.session_state.all_data   = data
        st.session_state.stock_info = info_map
        st.session_state.ranges     = {s: "1Y" for s in symbols}

        if not info_map:
            st.warning("Couldn't load stock data for these recommendations. Try a different interest.")

# ── Stock grid ────────────────────────────────────────────────────────────────
if st.session_state.stock_info:
    topic_safe = escape(st.session_state.current_interest)
    n = len(st.session_state.stock_info)
    st.markdown(
        f'<div class="sec-label">Stocks related to <span class="sec-label-accent">"{topic_safe}"</span>'
        f' — {n} results</div>',
        unsafe_allow_html=True)

    # Theme toggle
    show_theme = st.toggle("📊 View as Theme — compare all stocks on one chart")
    if show_theme:
        syms_with_data = [s for s in st.session_state.all_symbols_shown if s in st.session_state.all_data]
        if syms_with_data:
            fig, best, best_r, worst, worst_r, avg_r = make_theme_chart(
                st.session_state.all_data, syms_with_data, st.session_state.current_interest)
            st.plotly_chart(fig, width="stretch")
            sign = "+" if avg_r >= 0 else ""
            best_sign = "+" if best_r >= 0 else ""
            worst_sign = "+" if worst_r >= 0 else ""
            sub_color_avg   = "#10b981" if avg_r   >= 0 else "#f43f5e"
            sub_color_best  = "#10b981" if best_r  >= 0 else "#f43f5e"
            sub_color_worst = "#10b981" if worst_r >= 0 else "#f43f5e"
            st.markdown(f"""
<div class="theme-stat-row">
  <div class="theme-stat">
    <div class="theme-stat-lbl">Top Performer</div>
    <div class="theme-stat-val">{escape(best or "N/A")}</div>
    <div class="theme-stat-sub" style="color:{sub_color_best}">{best_sign}{best_r:.1f}%</div>
  </div>
  <div class="theme-stat">
    <div class="theme-stat-lbl">Laggard</div>
    <div class="theme-stat-val">{escape(worst or "N/A")}</div>
    <div class="theme-stat-sub" style="color:{sub_color_worst}">{worst_sign}{worst_r:.1f}%</div>
  </div>
  <div class="theme-stat">
    <div class="theme-stat-lbl">Theme Avg Return</div>
    <div class="theme-stat-val">{sign}{avg_r:.1f}%</div>
    <div class="theme-stat-sub" style="color:{sub_color_avg}">across {len(syms_with_data)} stocks</div>
  </div>
</div>""", unsafe_allow_html=True)
        else:
            st.info("No data available to build the theme chart yet.")

    st.divider()

    # Card grid
    items = list(st.session_state.stock_info.items())
    rows  = [items[i:i+3] for i in range(0, len(items), 3)]

    for row in rows:
        cols = st.columns(3)
        for ci, (symbol, info) in enumerate(row):
            with cols[ci]:
                reason = st.session_state.company_meta.get(symbol, {}).get("reason", "")
                st.markdown(stock_card_html(symbol, info, reason), unsafe_allow_html=True)
                if st.button("View Analysis →", key=f"card_{symbol}"):
                    st.session_state.selected_stock = symbol
                    st.rerun()

    st.divider()
    if st.button("➕ Show More Recommendations", width="stretch"):
        with st.spinner("Finding more companies…"):
            result    = fetch_companies(st.session_state.current_interest,
                                        exclude_symbols=st.session_state.all_symbols_shown)
            companies = parse_companies(result)
            new_syms  = [t for _, t, _ in companies]
            for name, ticker, reason in companies:
                st.session_state.company_meta[ticker] = {"llm_name": name, "reason": reason}
            st.session_state.all_symbols_shown += new_syms
            data, info_map = load_stocks(new_syms)
            st.session_state.all_data.update(data)
            st.session_state.stock_info.update(info_map)
            st.session_state.ranges.update({s: "1Y" for s in new_syms})
            st.rerun()
