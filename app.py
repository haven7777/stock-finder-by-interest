import streamlit as st
import os
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from groq import Groq
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

GROQ_KEY = os.getenv("GROQ_KEY") or st.secrets.get("GROQ_KEY")
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
    "All": ("max", "1mo")
}

def get_stock_data(symbol, period="1y", interval="1d"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        return df[["Close", "Volume"]]
    except Exception:
        return None

def get_stock_info(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        if not price:
            return None
        return {
            "price": price,
            "description": info.get("longBusinessSummary", "No description available.")[:200],
            "name": info.get("longName", symbol),
            "change_pct": info.get("52WeekChange", 0) * 100
        }
    except Exception:
        return None

def is_valid_input(text):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": f"""
                    Is "{text}" a valid topic that can be related to publicly traded companies?
                    Answer only YES or NO, nothing else.
                    Examples of valid: gaming, iphone, electric cars, sports, food
                    Examples of invalid: asdfgh, 123456, random gibberish
                    """
                }
            ]
        )
        answer = response.choices[0].message.content.strip().upper()
        return "YES" in answer
    except Exception:
        return True

def fetch_companies(interest, exclude_symbols=[]):
    exclude_text = f"Do NOT include these companies: {', '.join(exclude_symbols)}." if exclude_symbols else ""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": f"""
                The user is interested in: {interest}

                Return a list of 6 US publicly traded companies related to these interests.
                {exclude_text}
                For each company use exactly this format:
                Company Name | TICKER | Short reason

                Example:
                Apple | AAPL | Makes the iPhone

                Only the list, no extra text.
                """
            }
        ]
    )
    return response.choices[0].message.content

def get_news_and_analysis(symbol, company_name):
    try:
        results = tavily.search(
            query=f"{company_name} {symbol} stock news analysis 2025 2026",
            max_results=5
        )
        news_items = results.get("results", [])
        news_text = "\n".join([f"- {r['title']}: {r['content']}" for r in news_items])

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": """You are a senior equity analyst at a top-tier investment bank.
You analyze stocks with precision, cite specific data points, and compare current events to historical patterns.
You are objective, data-driven, and never speculative without evidence.
You always reference specific dates, percentages, and events when available."""
                },
                {
                    "role": "user",
                    "content": f"""
Analyze {company_name} ({symbol}) based on these recent news articles:

{news_text}

Write a structured analysis using exactly these sections:

## Upcoming Catalysts
List 2-3 specific upcoming events with dates if available.
Explain why each event matters for the stock price.

## Historical Comparison
Find 1-2 similar past events for this company or sector.
Include specific dates and percentage price moves when available.

## Price Impact Assessment
Give a balanced view of potential upside and downside scenarios.
Be specific - mention price ranges or percentage moves if data supports it.

## Key Risks
List 2-3 specific risks that could negatively impact the stock.

## Disclaimer
This analysis is for research purposes only and does not constitute investment advice.
Always conduct your own research before making investment decisions.
"""
                }
            ]
        )
        return response.choices[0].message.content, news_items
    except Exception:
        return "Analysis unavailable at this time.", []

def extract_symbols(text):
    symbols = []
    for line in text.strip().split("\n"):
        if "|" in line:
            parts = line.split("|")
            if len(parts) >= 2:
                symbol = parts[1].strip()
                if symbol.replace("-", "").isalpha() and symbol.isupper():
                    symbols.append(symbol)
    return symbols

def load_stocks(symbols):
    data = {}
    info_map = {}
    for symbol in symbols:
        with st.spinner(f"Fetching data for {symbol}..."):
            df = get_stock_data(symbol)
            info = get_stock_info(symbol)
            if df is not None and info is not None:
                data[symbol] = df
                info_map[symbol] = info
            else:
                st.warning(f"Could not fetch data for {symbol}, skipping.")
    return data, info_map

def make_chart(df, symbol):
    first = df["Close"].iloc[0]
    last = df["Close"].iloc[-1]
    went_up = last >= first
    color = "#00C805" if went_up else "#FF3B30"
    fill_color = "rgba(0,200,5,0.15)" if went_up else "rgba(255,59,48,0.15)"
    change = last - first
    change_pct = (change / first) * 100
    change_str = f"+{change:.2f} (+{change_pct:.2f}%)" if went_up else f"{change:.2f} ({change_pct:.2f}%)"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df["Close"],
        mode="lines",
        name="Price",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=fill_color,
        hovertemplate="%{x}<br>$%{y:.2f}<extra></extra>",
        yaxis="y1"
    ))

    if "Volume" in df.columns:
        fig.add_trace(go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            marker_color="rgba(100,100,100,0.4)",
            hovertemplate="%{x}<br>Vol: %{y:,.0f}<extra></extra>",
            yaxis="y2"
        ))

    fig.update_layout(
        title=dict(
            text=f"<b>{symbol}</b>   <span style='font-size:20px'>${last:.2f}</span>   <span style='color:{color};font-size:14px'>{change_str}</span>",
            font=dict(size=16, color="white")
        ),
        xaxis=dict(showgrid=False, showline=False, zeroline=False, color="gray"),
        yaxis=dict(showgrid=True, gridcolor="#333333", zeroline=False, side="right", color="gray", domain=[0.25, 1.0]),
        yaxis2=dict(showgrid=False, zeroline=False, side="left", color="gray", domain=[0.0, 0.2]),
        plot_bgcolor="#0d1117",
        paper_bgcolor="#0d1117",
        hovermode="x unified",
        margin=dict(l=10, r=60, t=60, b=10),
        showlegend=False
    )
    return fig

for key, default in [
    ("all_data", {}), ("result", ""), ("ranges", {}),
    ("stock_info", {}), ("selected_stock", None),
    ("analysis", {}), ("news_items", {}),
    ("current_interest", ""), ("all_symbols_shown", [])
]:
    if key not in st.session_state:
        st.session_state[key] = default

st.title("Stock Finder by Interest")
st.caption("This tool is for research purposes only and does not constitute investment advice.")

interest = st.text_input("What are your interests? e.g. gaming, iPhone, electric cars")

if st.button("Search"):
    if not interest.strip():
        st.error("Please enter an interest topic.")
    else:
        st.session_state.selected_stock = None
        st.session_state.analysis = {}
        st.session_state.news_items = {}
        st.session_state.all_symbols_shown = []
        st.session_state.current_interest = interest

        with st.spinner("Validating input..."):
            if not is_valid_input(interest):
                st.error("Please enter a valid interest topic, for example: gaming, electric cars, healthcare.")
                st.stop()

        with st.spinner("Finding relevant companies..."):
            result = fetch_companies(interest)
            st.session_state.result = result
            symbols = extract_symbols(result)
            st.session_state.all_symbols_shown = symbols
            data, info_map = load_stocks(symbols)
            st.session_state.all_data = data
            st.session_state.stock_info = info_map
            st.session_state.ranges = {s: "1Y" for s in symbols}

if st.session_state.stock_info and st.session_state.selected_stock is None:
    st.write("### Select a stock to analyze:")

    items = list(st.session_state.stock_info.items())
    rows = [items[i:i+3] for i in range(0, len(items), 3)]

    for row in rows:
        cols = st.columns(3)
        for i, (symbol, info) in enumerate(row):
            with cols[i]:
                price = info["price"]
                change = info["change_pct"]
                arrow = "🟢" if change >= 0 else "🔴"
                change_str = f"+{change:.1f}%" if change >= 0 else f"{change:.1f}%"
                if st.button(
                    f"**{symbol}**\n\n${price:.2f}\n\n{arrow} {change_str}",
                    key=f"card_{symbol}",
                    use_container_width=True
                ):
                    st.session_state.selected_stock = symbol

    if st.button("Show More Recommendations"):
        with st.spinner("Finding more companies..."):
            result = fetch_companies(
                st.session_state.current_interest,
                exclude_symbols=st.session_state.all_symbols_shown
            )
            new_symbols = extract_symbols(result)
            st.session_state.all_symbols_shown += new_symbols
            data, info_map = load_stocks(new_symbols)
            st.session_state.all_data = data
            st.session_state.stock_info = info_map
            st.session_state.ranges = {s: "1Y" for s in new_symbols}
            st.session_state.analysis = {}
            st.session_state.news_items = {}
            st.rerun()

if st.session_state.selected_stock:
    symbol = st.session_state.selected_stock
    info = st.session_state.stock_info[symbol]

    if st.button("Back"):
        st.session_state.selected_stock = None
        st.rerun()

    st.write(f"## {info['name']} ({symbol})")
    st.write(f"{info['description']}...")

    col1, col2 = st.columns(2)
    col1.metric("Current Price", f"${info['price']:.2f}")
    col2.metric("52W Change", f"{info['change_pct']:+.1f}%")

    st.write("**Time Range:**")
    range_cols = st.columns(len(RANGES))
    for i, label in enumerate(RANGES.keys()):
        if range_cols[i].button(label, key=f"range_{symbol}_{label}"):
            st.session_state.ranges[symbol] = label
            period, interval = RANGES[label]
            df = get_stock_data(symbol, period, interval)
            if df is not None:
                st.session_state.all_data[symbol] = df

    df = st.session_state.all_data.get(symbol)
    if df is not None:
        fig = make_chart(df, symbol)
        st.plotly_chart(fig, use_container_width=True)

    st.write("### AI Analysis (Real-Time)")
    if symbol not in st.session_state.analysis:
        with st.spinner("Analyzing news and events..."):
            analysis, news_items = get_news_and_analysis(symbol, info["name"])
            st.session_state.analysis[symbol] = analysis
            st.session_state.news_items[symbol] = news_items

    st.markdown(st.session_state.analysis[symbol])

    if st.session_state.news_items.get(symbol):
        st.write("### Latest News")
        for article in st.session_state.news_items[symbol]:
            title = article.get("title", "No title")
            url = article.get("url", "#")
            source = article.get("source", "")
            st.markdown(f"- [{title}]({url}) — *{source}*")