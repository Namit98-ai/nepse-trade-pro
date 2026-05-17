# 🇳🇵 NEPSE Trade Pro

A professional-grade automated trading research, backtesting, and live market analysis system for the **Nepal Stock Exchange (NEPSE)**.

## ✨ What's New (v2.0)
- ✅ **250+ stocks** across all NEPSE sectors (Banking, Hydropower, Insurance, etc.)
- ✅ **Sector filtering** — scan by Banking, Hydropower, Insurance, etc.
- ✅ **Full Market Scanner** — bulk scan an entire sector for signals
- ✅ **Volume Spike detection** with confirmation logic
- ✅ **MACD & Bollinger Bands** strategies added
- ✅ **Sharpe Ratio & Sortino Ratio** in backtester
- ✅ **Trade log** with individual trade P&L
- ✅ **Strategy Comparison** — compare all 7 strategies on one chart
- ✅ **Email alerts** added (alongside Telegram)
- ✅ **Gemini 1.5 Flash** (faster free model)
- ✅ **MeroLagani fallback** scraper for real historical data
- ✅ Bug fixes: async handling, EMA crossover detection, cost modeling

## 🚀 Features
| Feature | Description |
|---------|-------------|
| 📡 Live Scanner | RSI, EMA, MACD, Volume Spike, Bollinger Bands, Consensus |
| 🔍 Full Market Scan | Bulk scan 10–50 stocks in a sector |
| 🧪 Backtester | Sharpe/Sortino, drawdown, trade log, NEPSE costs |
| 🤖 AI Insights | Gemini-powered commentary & signal explanation |
| 📈 Strategy Compare | Equity curves for all 7 strategies side-by-side |
| 📲 Telegram Alerts | Instant mobile notifications |
| 📧 Email Alerts | Optional Gmail alerts |

## 🛠️ Quick Setup

### Local PC
```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/nepse-trade-pro.git
cd nepse-trade-pro

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and fill in your API keys
cp .env.example .env
# Edit .env with your keys

# 4. Run!
streamlit run app.py
```

### Google Colab (Mobile-Friendly)
1. Upload `NEPSE_Trade_Pro_Colab.ipynb` to [colab.research.google.com](https://colab.research.google.com)
2. Upload the project zip and unzip it
3. Run all 4 cells
4. Open the localtunnel URL on your phone

## 📁 Project Structure
```
nepse_trade_pro/
├── src/
│   ├── data_provider.py   # NEPSE API + MeroLagani scraper + 250+ symbols
│   ├── strategies.py      # RSI, EMA, MACD, Volume, BB, Breakout, Consensus
│   ├── backtester.py      # Sharpe, Sortino, trade log, NEPSE costs
│   ├── ai_analyzer.py     # Gemini 1.5 Flash integration + fallback
│   └── alerts.py          # Telegram + Email alerts
├── app.py                 # Streamlit dashboard (7 pages)
├── requirements.txt
├── .env.example           # API key template
└── NEPSE_Trade_Pro_Colab.ipynb
```

## 📊 Strategies Reference
| Strategy | Win Rate | R:R | Best For |
|----------|----------|-----|----------|
| RSI Bounce | ~65% | 1:1.5 | Sideways market |
| EMA Crossover (20/50) | ~45-50% | 1:3 | Trending market |
| 50-Day Breakout | ~55-60% | 1:2+ | Bull market |
| Volume Spike | Variable | High | Breakout confirmation |
| MACD | ~50-55% | 1:2 | Momentum |
| Bollinger Bands | ~60% | 1:1.5 | Range-bound |
| **Consensus (All)** | **~60-65%** | **1:2** | **High confidence** |

## 💰 NEPSE Transaction Costs (Included in Backtester)
| Cost | Rate |
|------|------|
| Broker Commission | 0.40% per trade |
| SEBON Fee | 0.015% per trade |
| DP Fee | Rs. 25 per trade |
| Capital Gains Tax | 5% on profit |

## ⚠️ Disclaimer
This system is for **educational and research purposes only**. Trading involves significant risk. Always do your own research before making financial decisions.

## 📄 License
MIT License — Free for personal and educational use.
