# Stock Finder by Interest

Discover stocks based on what you care about — powered by AI and real market data.

## The Problem

I always wanted to invest but didn't want to blindly follow internet recommendations.
I realised I could look at products I use every day and find the companies behind them —
without needing to be a finance expert. So I built this tool.

## What It Does

Enter any interest (e.g. gaming, electric vehicles, AI chips) and the app will:

- Find 6 publicly traded companies related to your interest, with a one-line reason for each
- Show live price, intraday change, market cap, and cap-size badge on every card
- Let you compare all stocks together on a normalised performance chart (Theme View)
- Provide an interactive price chart with volume and 50-day moving average
- Display 12 financial metrics: P/E, forward P/E, 52W range, analyst target & rating, earnings date, dividend yield, beta, short interest
- Generate a real-time AI analysis grounded in actual financial data and live news
- Link to the news articles used in the analysis with source and date

## Features

| Feature | Detail |
|---|---|
| Interest-based discovery | AI matches your topic to 6 US-listed companies |
| Glass & Glow UI | Dark glassmorphism design with ambient glow |
| Stock cards | Price, intraday %, market cap, LLM reason |
| Theme Portfolio View | All stocks on one normalised chart with top/laggard summary |
| Interactive charts | 1D → All-time, volume bars, 50-day MA overlay |
| 12-metric panel | P/E, forward P/E, 52W range, analyst target/rating, earnings date, beta, short interest |
| AI analysis | Grounded in real financials + live news; sections: Catalysts, Historical, Price Impact, Risks |
| Show More | Get 6 additional recommendations on the same topic |
| Input validation | AI rejects irrelevant or nonsense queries |

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core language |
| Streamlit | Web interface and session state |
| Groq (Llama 3.3 70B) | Company matching, input validation, equity analysis |
| Tavily | Real-time news search |
| yfinance | Stock price data and financial metrics |
| Plotly | Interactive charts |

## Setup

1. Clone the repo
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   GROQ_KEY=your_groq_key
   TAVILY_KEY=your_tavily_key
   ```
4. Run:
   ```bash
   streamlit run app.py
   ```

## Screenshots

![Home](screenshots/Home%20page.png)
![Stock Info](screenshots/Stock%20info.png)
![AI Analysis](screenshots/AI%20analysis.png)

---

> **Disclaimer:** This tool is for research and educational purposes only. It does not constitute investment advice. Always conduct your own due diligence before making investment decisions.
