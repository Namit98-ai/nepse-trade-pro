"""
NEPSE Trade Pro — Main Dashboard
=================================
Streamlit app with:
- Live scanner across all 250+ NEPSE stocks
- Sector filtering
- Volume spike alerts
- Full backtesting with Sharpe/Sortino
- AI analysis (Gemini)
- Telegram + Email alerts
- Settings persistence via .env
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import asyncio
import datetime
import os
import sys

# Ensure src is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__)'..'))

from src.data_provider import NepseDataProvider, ALL_NEPSE_SYMBOLS, ALL_SYMBOLS_FLAT
from src.strategies import StrategyEngine
from src.backtester import Backtester
from src.ai_analyzer import AIAnalyzer
from src.alerts import AlertSystem

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NEPSE Trade Pro",
    page_icon="🇳🇵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(135deg, #1e3a5f, #0d2137);
    border-radius: 10px;
    padding: 12px;
    border-left: 4px solid #00b4d8;
}
.signal-buy  { color: #00ff88; font-weight: bold; font-size: 1.2em; }
.signal-sell { color: #ff4444; font-weight: bold; font-size: 1.2em; }
.signal-hold { color: #ffd700; font-weight: bold; font-size: 1.2em; }
.stButton > button { border-radius: 8px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def run_async(coro):
    """Run async coroutine safely in Streamlit."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except Exception:
        return asyncio.run(coro)

@st.cache_resource(show_spinner=False)
def get_provider():
    return NepseDataProvider()

@st.cache_resource(show_spinner=False)
def get_components():
    provider  = NepseDataProvider()
    analyzer  = AIAnalyzer(api_key=os.getenv("GEMINI_API_KEY"))
    backtester = Backtester()
    alerts    = AlertSystem()
    return provider, analyzer, backtester, alerts

provider, analyzer, backtester, alert_system = get_components()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🇳🇵 NEPSE Trade Pro")
    st.markdown("---")
    menu = st.selectbox(
        "📂 Navigation",
        ["🏠 Dashboard", "📡 Live Scanner", "🔍 Full Market Scan",
         "🧪 Backtesting", "🤖 AI Insights", "📈 Strategy Compare", "⚙️ Settings"]
    )
    st.markdown("---")
    st.caption("⚠️ For educational use only. Not financial advice.")
    st.caption(f"📅 {datetime.datetime.now().strftime('%a, %d %b %Y %I:%M %p')}")

# ── DASHBOARD ─────────────────────────────────────────────────────────────────
if menu == "🏠 Dashboard":
    st.title("📊 NEPSE Trade Pro — Dashboard")

    col1, col2, col3, col4 = st.columns(4)
    summary = run_async(provider.get_live_market_summary())

    if summary:
        change_color = "normal" if hasattr(summary, 'change_point') else "normal"
        col1.metric("NEPSE Index",
                    f"{summary.index_value:,.2f}",
                    f"{summary.change_point:+.2f} ({summary.percent_change:+.2f}%)")
        col2.metric("Total Turnover",
                    f"Rs. {summary.total_turnover/1e7:.1f} Cr")
        col3.metric("Market Status",
                    "🟢 OPEN" if summary.is_open else "🔴 CLOSED")
        col4.metric("Listed Stocks", f"{len(ALL_SYMBOLS_FLAT)}+")

    st.markdown("---")

    # Quick sector overview
    st.subheader("📁 Sectors at a Glance")
    sector_data = {sector: len(syms) for sector, syms in ALL_NEPSE_SYMBOLS.items()}
    fig_sector = px.bar(
        x=list(sector_data.keys()),
        y=list(sector_data.values()),
        labels={"x": "Sector", "y": "Listed Stocks"},
        color=list(sector_data.values()),
        color_continuous_scale="teal",
        title="Stocks Per Sector"
    )
    fig_sector.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    st.plotly_chart(fig_sector, use_container_width=True)

    # Strategy reference
    with st.expander("📖 Strategy Reference Card"):
        strat_df = pd.DataFrame([
            {"Strategy": "RSI Bounce", "Win Rate": "~65%", "Risk:Reward": "1:1.5",
             "Best For": "Sideways market", "Timeframe": "Daily"},
            {"Strategy": "EMA Crossover (20/50)", "Win Rate": "~45-50%", "Risk:Reward": "1:3",
             "Best For": "Strong trends", "Timeframe": "Daily"},
            {"Strategy": "50-Day Breakout", "Win Rate": "~55-60%", "Risk:Reward": "1:2+",
             "Best For": "Bull markets", "Timeframe": "Daily"},
            {"Strategy": "Volume Spike", "Win Rate": "Variable", "Risk:Reward": "High",
             "Best For": "Breakout confirmation", "Timeframe": "Intraday/Daily"},
            {"Strategy": "MACD Crossover", "Win Rate": "~50-55%", "Risk:Reward": "1:2",
             "Best For": "Momentum", "Timeframe": "Daily"},
            {"Strategy": "Bollinger Bands", "Win Rate": "~60%", "Risk:Reward": "1:1.5",
             "Best For": "Range-bound", "Timeframe": "Daily"},
            {"Strategy": "Consensus (All)", "Win Rate": "~60-65%", "Risk:Reward": "1:2",
             "Best For": "High confidence", "Timeframe": "Daily"},
        ])
        st.dataframe(strat_df, use_container_width=True, hide_index=True)

# ── LIVE SCANNER ──────────────────────────────────────────────────────────────
elif menu == "📡 Live Scanner":
    st.title("📡 Live Stock Scanner")

    col_l, col_r = st.columns([1, 3])

    with col_l:
        sectors = ["All Sectors"] + list(ALL_NEPSE_SYMBOLS.keys())
        selected_sector = st.selectbox("🏢 Sector Filter", sectors)

        if selected_sector == "All Sectors":
            symbol_list = ALL_SYMBOLS_FLAT
        else:
            symbol_list = sorted(ALL_NEPSE_SYMBOLS[selected_sector])

        st.caption(f"{len(symbol_list)} stocks in this filter")
        selected_symbol = st.selectbox("🔍 Select Stock", symbol_list)

        strategy_choice = st.selectbox(
            "📐 Strategy",
            ["Consensus (Recommended)", "RSI Bounce", "EMA Crossover",
             "50-Day Breakout", "Volume Spike", "MACD", "Bollinger Bands"]
        )
        days = st.slider("📅 Data Period (days)", 90, 730, 365)
        scan_btn = st.button("🚀 Scan Now", use_container_width=True)

    with col_r:
        if scan_btn:
            with st.spinner(f"Analyzing {selected_symbol}..."):
                df = run_async(provider.get_historical_data(selected_symbol, days))

                if df.empty:
                    st.error("No data available for this symbol.")
                else:
                    # Apply chosen strategy
                    strategy_map = {
                        "Consensus (Recommended)": lambda d: StrategyEngine.combine_strategies(d),
                        "RSI Bounce":              lambda d: StrategyEngine.rsi_strategy(d),
                        "EMA Crossover":           lambda d: StrategyEngine.ema_crossover_strategy(d),
                        "50-Day Breakout":         lambda d: StrategyEngine.breakout_strategy(d),
                        "Volume Spike":            lambda d: StrategyEngine.volume_spike_strategy(d),
                        "MACD":                    lambda d: StrategyEngine.macd_strategy(d),
                        "Bollinger Bands":         lambda d: StrategyEngine.bollinger_bands_strategy(d),
                    }
                    df = strategy_map[strategy_choice](df)
                    summary_info = StrategyEngine.get_signal_summary(df, selected_symbol)

                    # Signal Banner
                    sig = summary_info['signal']
                    sig_color = {"BUY": "success", "SELL": "error", "HOLD": "info"}[sig]
                    sig_emoji = {"BUY": "🚀", "SELL": "🔻", "HOLD": "⚖️"}[sig]

                    if sig == "BUY":
                        st.success(f"{sig_emoji} **{sig} SIGNAL** — {selected_symbol} | Price: Rs. {summary_info['price']:,.2f} | Confidence: {summary_info['confidence']:.0f}%")
                    elif sig == "SELL":
                        st.error(f"{sig_emoji} **{sig} SIGNAL** — {selected_symbol} | Price: Rs. {summary_info['price']:,.2f} | Confidence: {summary_info['confidence']:.0f}%")
                    else:
                        st.info(f"{sig_emoji} **{sig}** — {selected_symbol} | Price: Rs. {summary_info['price']:,.2f}")

                    # Key metrics row
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Current Price", f"Rs. {summary_info['price']:,.2f}")
                    if summary_info.get('rsi'):
                        m2.metric("RSI", f"{summary_info['rsi']:.1f}",
                                  "Oversold" if summary_info['rsi'] < 30 else ("Overbought" if summary_info['rsi'] > 70 else "Neutral"))
                    if summary_info.get('atr'):
                        stop_loss = summary_info['price'] - (summary_info['atr'] * 2)
                        m3.metric("ATR Stop-Loss", f"Rs. {stop_loss:,.2f}")
                    m4.metric("Signal", sig)

                    if summary_info.get('reasons'):
                        st.markdown("**Signal Reasons:** " + " | ".join(summary_info['reasons']))

                    # Candlestick chart
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(
                        x=df.index, open=df['Open'], high=df['High'],
                        low=df['Low'], close=df['Close'], name="Price"
                    ))
                    # Add EMAs if available
                    if 'EMA_Short' in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_Short'],
                                                  name='EMA 20', line=dict(color='#00b4d8', width=1.5)))
                    if 'EMA_Long' in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df['EMA_Long'],
                                                  name='EMA 50', line=dict(color='#ff9f1c', width=1.5)))
                    if 'BB_Upper' in df.columns:
                        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'],
                                                  name='BB Upper', line=dict(color='gray', dash='dot')))
                        fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'],
                                                  name='BB Lower', line=dict(color='gray', dash='dot')))

                    # Mark BUY/SELL signals on chart
                    buy_signals  = df[df['Signal'] == 1]
                    sell_signals = df[df['Signal'] == -1]
                    if not buy_signals.empty:
                        fig.add_trace(go.Scatter(x=buy_signals.index, y=buy_signals['Low'] * 0.99,
                                                  mode='markers', marker=dict(symbol='triangle-up', color='#00ff88', size=10),
                                                  name='BUY'))
                    if not sell_signals.empty:
                        fig.add_trace(go.Scatter(x=sell_signals.index, y=sell_signals['High'] * 1.01,
                                                  mode='markers', marker=dict(symbol='triangle-down', color='#ff4444', size=10),
                                                  name='SELL'))

                    fig.update_layout(
                        title=f"{selected_symbol} — {strategy_choice}",
                        xaxis_rangeslider_visible=False,
                        plot_bgcolor='rgba(14,17,23,1)',
                        paper_bgcolor='rgba(14,17,23,1)',
                        font=dict(color='white'),
                        height=450
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    # Volume chart
                    if 'Volume' in df.columns:
                        fig_vol = go.Figure()
                        vol_colors = ['#00ff88' if c >= o else '#ff4444'
                                      for c, o in zip(df['Close'], df['Open'])]
                        fig_vol.add_trace(go.Bar(x=df.index, y=df['Volume'],
                                                  marker_color=vol_colors, name='Volume'))
                        if 'Volume_MA' in df.columns:
                            fig_vol.add_trace(go.Scatter(x=df.index, y=df['Volume_MA'],
                                                          name='Avg Volume', line=dict(color='yellow', width=1.5)))
                        fig_vol.update_layout(
                            title="Volume", height=180,
                            plot_bgcolor='rgba(14,17,23,1)',
                            paper_bgcolor='rgba(14,17,23,1)',
                            font=dict(color='white'),
                            showlegend=True
                        )
                        st.plotly_chart(fig_vol, use_container_width=True)

                    # RSI chart
                    if 'RSI' in df.columns:
                        fig_rsi = go.Figure()
                        fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'],
                                                      line=dict(color='#00b4d8', width=2), name='RSI'))
                        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red",   annotation_text="Overbought (70)")
                        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
                        fig_rsi.update_layout(
                            title="RSI (14)", height=200, yaxis=dict(range=[0, 100]),
                            plot_bgcolor='rgba(14,17,23,1)',
                            paper_bgcolor='rgba(14,17,23,1)',
                            font=dict(color='white')
                        )
                        st.plotly_chart(fig_rsi, use_container_width=True)

                    # Telegram alert button
                    st.markdown("---")
                    if st.button("📲 Send Signal to Telegram"):
                        msg = alert_system.format_signal_alert(
                            symbol=selected_symbol,
                            signal=sig,
                            price=summary_info['price'],
                            rsi=summary_info.get('rsi'),
                            reason=" | ".join(summary_info.get('reasons', [])),
                            confidence=summary_info.get('confidence')
                        )
                        sent = alert_system.send_telegram_sync(msg)
                        if sent:
                            st.success("✅ Alert sent to Telegram!")
                        else:
                            st.warning("⚠️ Telegram not configured. Go to Settings.")

# ── FULL MARKET SCAN ──────────────────────────────────────────────────────────
elif menu == "🔍 Full Market Scan":
    st.title("🔍 Full Market Scanner — All Stocks")
    st.info("Scans multiple stocks and returns those with active signals. This may take a moment.")

    col1, col2 = st.columns(2)
    with col1:
        scan_sector = st.selectbox(
            "Sector to Scan",
            ["Banking", "Hydropower", "Insurance", "Development Bank",
             "Finance", "Microfinance", "Manufacturing", "Hotels"]
        )
    with col2:
        scan_strategy = st.selectbox(
            "Strategy",
            ["RSI Bounce", "EMA Crossover", "Volume Spike", "Consensus (Recommended)"]
        )

    max_stocks = st.slider("Max stocks to scan", 10, 50, 20)

    if st.button("🔎 Run Scan", use_container_width=True):
        symbols_to_scan = ALL_NEPSE_SYMBOLS.get(scan_sector, [])[:max_stocks]
        results = []

        progress = st.progress(0)
        status_text = st.empty()

        for i, sym in enumerate(symbols_to_scan):
            status_text.text(f"Scanning {sym} ({i+1}/{len(symbols_to_scan)})...")
            try:
                df = run_async(provider.get_historical_data(sym, 180))
                if df.empty:
                    continue

                strategy_map = {
                    "RSI Bounce":              StrategyEngine.rsi_strategy,
                    "EMA Crossover":           StrategyEngine.ema_crossover_strategy,
                    "Volume Spike":            StrategyEngine.volume_spike_strategy,
                    "Consensus (Recommended)": StrategyEngine.combine_strategies,
                }
                df = strategy_map[scan_strategy](df)
                summary_info = StrategyEngine.get_signal_summary(df, sym)

                if summary_info['signal'] in ["BUY", "SELL"]:
                    results.append(summary_info)
            except Exception as e:
                pass
            progress.progress((i + 1) / len(symbols_to_scan))

        progress.empty()
        status_text.empty()

        if results:
            st.success(f"Found {len(results)} active signals in {scan_sector}!")
            results_df = pd.DataFrame(results)
            results_df = results_df.sort_values("confidence", ascending=False)

            # Colour-code signal column
            def style_signal(val):
                color = '#00ff8833' if val == 'BUY' else '#ff444433' if val == 'SELL' else ''
                return f'background-color: {color}'

            st.dataframe(
                results_df[['symbol', 'signal', 'confidence', 'price', 'rsi']].rename(columns={
                    'symbol': 'Symbol', 'signal': 'Signal',
                    'confidence': 'Confidence %', 'price': 'Price (Rs.)', 'rsi': 'RSI'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning(f"No strong signals found in {scan_sector} right now.")

# ── BACKTESTING ───────────────────────────────────────────────────────────────
elif menu == "🧪 Backtesting":
    st.title("🧪 Strategy Backtester")

    col1, col2, col3 = st.columns(3)
    with col1:
        bt_sector = st.selectbox("Sector", ["All"] + list(ALL_NEPSE_SYMBOLS.keys()))
        if bt_sector == "All":
            bt_symbols = ALL_SYMBOLS_FLAT
        else:
            bt_symbols = sorted(ALL_NEPSE_SYMBOLS[bt_sector])
        bt_symbol = st.selectbox("Symbol", bt_symbols)
    with col2:
        bt_strategy = st.selectbox(
            "Strategy",
            ["Consensus (Recommended)", "RSI Bounce", "EMA Crossover",
             "50-Day Breakout", "Volume Spike", "MACD", "Bollinger Bands"]
        )
    with col3:
        bt_capital = st.number_input("Initial Capital (Rs.)", 10000, 10000000, 100000, step=10000)
        bt_days    = st.slider("Backtest Period (days)", 180, 1095, 365)

    if st.button("▶️ Run Backtest", use_container_width=True):
        with st.spinner("Running backtest..."):
            df = run_async(provider.get_historical_data(bt_symbol, bt_days))

            if df.empty:
                st.error("No data for this symbol.")
            else:
                strategy_map = {
                    "Consensus (Recommended)": lambda d: StrategyEngine.combine_strategies(d),
                    "RSI Bounce":              lambda d: StrategyEngine.rsi_strategy(d),
                    "EMA Crossover":           lambda d: StrategyEngine.ema_crossover_strategy(d),
                    "50-Day Breakout":         lambda d: StrategyEngine.breakout_strategy(d),
                    "Volume Spike":            lambda d: StrategyEngine.volume_spike_strategy(d),
                    "MACD":                    lambda d: StrategyEngine.macd_strategy(d),
                    "Bollinger Bands":         lambda d: StrategyEngine.bollinger_bands_strategy(d),
                }
                df = strategy_map[bt_strategy](df)

                bt = Backtester(initial_capital=bt_capital)
                results_df, metrics = bt.run(df)

                if not metrics:
                    st.error("Backtest failed — insufficient data.")
                else:
                    # Metrics grid
                    st.subheader("📊 Performance Metrics")
                    m1, m2, m3, m4 = st.columns(4)
                    m5, m6, m7, m8 = st.columns(4)

                    m1.metric("Total Return",    metrics['Total Return'])
                    m2.metric("Annual Return",   metrics['Annual Return'])
                    m3.metric("Max Drawdown",    metrics['Max Drawdown'])
                    m4.metric("Final Value",     metrics['Final Value'])
                    m5.metric("Sharpe Ratio",    metrics['Sharpe Ratio'],
                              help="≥1.0 is good; ≥2.0 is excellent")
                    m6.metric("Sortino Ratio",   metrics['Sortino Ratio'])
                    m7.metric("Win Rate",        metrics['Win Rate'])
                    m8.metric("Total Trades",    str(metrics['Total Trades']))

                    col_l, col_r = st.columns(2)
                    col_l.metric("Avg Win",      metrics['Avg Win'])
                    col_r.metric("Profit Factor",metrics['Profit Factor'])

                    # Equity curve
                    st.subheader("📈 Equity Curve")
                    fig_eq = go.Figure()
                    fig_eq.add_trace(go.Scatter(
                        x=results_df.index,
                        y=results_df['Equity_Curve'],
                        fill='tozeroy',
                        line=dict(color='#00b4d8', width=2),
                        name='Portfolio Value'
                    ))
                    fig_eq.add_hline(y=bt_capital, line_dash="dash",
                                      line_color="white", annotation_text="Start Capital")
                    fig_eq.update_layout(
                        height=350,
                        plot_bgcolor='rgba(14,17,23,1)',
                        paper_bgcolor='rgba(14,17,23,1)',
                        font=dict(color='white')
                    )
                    st.plotly_chart(fig_eq, use_container_width=True)

                    # Drawdown chart
                    st.subheader("📉 Drawdown")
                    fig_dd = go.Figure()
                    fig_dd.add_trace(go.Scatter(
                        x=results_df.index,
                        y=results_df['Drawdown'] * 100,
                        fill='tozeroy',
                        line=dict(color='#ff4444', width=1.5),
                        name='Drawdown %'
                    ))
                    fig_dd.update_layout(
                        height=250,
                        plot_bgcolor='rgba(14,17,23,1)',
                        paper_bgcolor='rgba(14,17,23,1)',
                        font=dict(color='white'),
                        yaxis_title="Drawdown %"
                    )
                    st.plotly_chart(fig_dd, use_container_width=True)

                    # NEPSE cost breakdown
                    with st.expander("💰 NEPSE Transaction Cost Breakdown"):
                        st.markdown("""
| Cost Type | Rate | Notes |
|-----------|------|-------|
| Broker Commission | 0.40% | Per transaction (buy/sell) |
| SEBON Fee | 0.015% | Per transaction |
| DP Fee | Rs. 25 | Per transaction |
| Capital Gains Tax | 5% | On profit (individuals) |
| **Total Round-Trip** | **~0.83%+** | **Included in backtest** |
""")

# ── AI INSIGHTS ───────────────────────────────────────────────────────────────
elif menu == "🤖 AI Insights":
    st.title("🤖 AI Market Commentary")
    st.info("Powered by Google Gemini 1.5 Flash (free tier). Set your API key in Settings.")

    col1, col2 = st.columns([2, 1])
    with col1:
        ai_symbol = st.selectbox("Stock for Signal Analysis", ALL_SYMBOLS_FLAT)
    with col2:
        ai_strategy = st.selectbox("Strategy", ["Consensus (Recommended)", "RSI Bounce", "EMA Crossover"])

    if st.button("🧠 Generate AI Analysis", use_container_width=True):
        with st.spinner("Fetching data & generating analysis..."):
            summary_obj = run_async(provider.get_live_market_summary())
            df = run_async(provider.get_historical_data(ai_symbol, 180))

            if not df.empty:
                if ai_strategy == "RSI Bounce":
                    df = StrategyEngine.rsi_strategy(df)
                elif ai_strategy == "EMA Crossover":
                    df = StrategyEngine.ema_crossover_strategy(df)
                else:
                    df = StrategyEngine.combine_strategies(df)

                sig_info = StrategyEngine.get_signal_summary(df, ai_symbol)
                signals_str = (
                    f"{ai_symbol}: Signal={sig_info['signal']}, "
                    f"RSI={sig_info.get('rsi', 'N/A')}, "
                    f"Price=Rs.{sig_info['price']}, "
                    f"Confidence={sig_info['confidence']}%, "
                    f"Reasons: {', '.join(sig_info.get('reasons', []))}"
                )
                summary_str = (
                    f"NEPSE Index: {summary_obj.index_value}, "
                    f"Change: {summary_obj.change_point} ({summary_obj.percent_change}%), "
                    f"Turnover: Rs.{summary_obj.total_turnover}"
                ) if summary_obj else "Market data unavailable"

                commentary = analyzer.analyze_market(summary_str, signals_str)
                st.markdown(commentary)

                # Explanation for specific signal
                st.markdown("---")
                st.subheader(f"Signal Explanation: {ai_symbol}")
                explanation = analyzer.explain_signal(
                    symbol=ai_symbol,
                    signal=sig_info['signal'],
                    rsi=sig_info.get('rsi', 50) or 50,
                    ema_cross="Bullish" if sig_info['signal'] == "BUY" else "Bearish",
                    volume_ratio=1.0
                )
                st.info(explanation)

# ── STRATEGY COMPARE ──────────────────────────────────────────────────────────
elif menu == "📈 Strategy Compare":
    st.title("📈 Compare Strategies on One Stock")

    compare_sector = st.selectbox("Sector", ["All"] + list(ALL_NEPSE_SYMBOLS.keys()), key="cmp_sector")
    if compare_sector == "All":
        cmp_syms = ALL_SYMBOLS_FLAT
    else:
        cmp_syms = sorted(ALL_NEPSE_SYMBOLS[compare_sector])

    cmp_symbol = st.selectbox("Symbol", cmp_syms, key="cmp_sym")
    cmp_days   = st.slider("Period (days)", 180, 730, 365, key="cmp_days")

    if st.button("📊 Compare All Strategies"):
        with st.spinner("Running all 6 strategies..."):
            df_raw = run_async(provider.get_historical_data(cmp_symbol, cmp_days))
            if df_raw.empty:
                st.error("No data available.")
            else:
                bt = Backtester()
                compare_results = []
                strategies = {
                    "RSI Bounce":        StrategyEngine.rsi_strategy,
                    "EMA Crossover":     StrategyEngine.ema_crossover_strategy,
                    "50-Day Breakout":   StrategyEngine.breakout_strategy,
                    "Volume Spike":      StrategyEngine.volume_spike_strategy,
                    "MACD":              StrategyEngine.macd_strategy,
                    "Bollinger Bands":   StrategyEngine.bollinger_bands_strategy,
                    "Consensus":         StrategyEngine.combine_strategies,
                }
                equity_fig = go.Figure()

                for name, func in strategies.items():
                    try:
                        df_s = func(df_raw.copy())
                        df_r, m = bt.run(df_s)
                        if m:
                            compare_results.append({
                                "Strategy":      name,
                                "Total Return":  m['Total Return'],
                                "Annual Return": m['Annual Return'],
                                "Sharpe":        m['Sharpe Ratio'],
                                "Win Rate":      m['Win Rate'],
                                "Max Drawdown":  m['Max Drawdown'],
                                "Trades":        m['Total Trades'],
                                "Final Value":   m['Final Value'],
                            })
                            equity_fig.add_trace(go.Scatter(
                                x=df_r.index,
                                y=df_r['Equity_Curve'],
                                name=name
                            ))
                    except Exception:
                        pass

                # Equity curves overlay
                equity_fig.update_layout(
                    title=f"Equity Curves — {cmp_symbol}",
                    height=400,
                    plot_bgcolor='rgba(14,17,23,1)',
                    paper_bgcolor='rgba(14,17,23,1)',
                    font=dict(color='white')
                )
                st.plotly_chart(equity_fig, use_container_width=True)

                # Comparison table
                cmp_df = pd.DataFrame(compare_results)
                st.dataframe(cmp_df, use_container_width=True, hide_index=True)

# ── SETTINGS ──────────────────────────────────────────────────────────────────
elif menu == "⚙️ Settings":
    st.title("⚙️ System Settings")

    st.subheader("🤖 AI Configuration")
    gemini_key = st.text_input("Google Gemini API Key",
                                type="password",
                                value=os.getenv("GEMINI_API_KEY", ""),
                                help="Get free key from aistudio.google.com")

    st.subheader("📲 Telegram Alerts")
    tg_token   = st.text_input("Telegram Bot Token", type="password",
                                value=os.getenv("TELEGRAM_BOT_TOKEN", ""))
    tg_chat_id = st.text_input("Telegram Chat ID",
                                value=os.getenv("TELEGRAM_CHAT_ID", ""),
                                help="Get from @userinfobot on Telegram")

    st.subheader("📧 Email Alerts (Optional)")
    email_sender   = st.text_input("Gmail Sender Address", value=os.getenv("EMAIL_SENDER", ""))
    email_password = st.text_input("Gmail App Password", type="password",
                                    value=os.getenv("EMAIL_PASSWORD", ""),
                                    help="Use App Password, not your main Gmail password")
    email_receiver = st.text_input("Receiver Email", value=os.getenv("EMAIL_RECEIVER", ""))

    if st.button("💾 Save Settings", use_container_width=True):
        env_path = os.path.join(os.path.dirname(__file__), ".env")
        with open(env_path, "w") as f:
            if gemini_key:    f.write(f"GEMINI_API_KEY={gemini_key}\n")
            if tg_token:      f.write(f"TELEGRAM_BOT_TOKEN={tg_token}\n")
            if tg_chat_id:    f.write(f"TELEGRAM_CHAT_ID={tg_chat_id}\n")
            if email_sender:  f.write(f"EMAIL_SENDER={email_sender}\n")
            if email_password:f.write(f"EMAIL_PASSWORD={email_password}\n")
            if email_receiver:f.write(f"EMAIL_RECEIVER={email_receiver}\n")

        # Update live components
        analyzer.set_api_key(gemini_key)
        alert_system.bot_token      = tg_token
        alert_system.chat_id        = tg_chat_id
        alert_system.email_sender   = email_sender
        alert_system.email_password = email_password
        alert_system.email_receiver = email_receiver

        st.success("✅ Settings saved! Restart the app to apply all changes.")

    st.markdown("---")
    st.subheader("🔧 System Info")
    st.markdown(f"""
| Item | Status |
|------|--------|
| Total NEPSE Symbols Loaded | {len(ALL_SYMBOLS_FLAT)} |
| Sectors Available | {len(ALL_NEPSE_SYMBOLS)} |
| Gemini API | {'✅ Configured' if os.getenv('GEMINI_API_KEY') else '❌ Not Set'} |
| Telegram | {'✅ Configured' if os.getenv('TELEGRAM_BOT_TOKEN') else '❌ Not Set'} |
| Data Cache | `./data/` folder |
""")

    with st.expander("📖 How to get free API keys"):
        st.markdown("""
**Gemini API Key (Free):**
1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Sign in with Google → Click "Get API Key"
3. Create API key → Copy it here

**Telegram Bot Token (Free):**
1. Open Telegram → Search `@BotFather`
2. Send `/newbot` → Follow instructions
3. Copy the token provided

**Telegram Chat ID:**
1. Open Telegram → Search `@userinfobot`
2. Start the bot → It sends your Chat ID
""")
