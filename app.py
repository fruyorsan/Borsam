import streamlit as st
import yfinance as yf
import pandas as pd
from html import escape
from datetime import datetime, timezone
import re
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange, BollingerBands
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google import genai
import time
import os

# ==========================================
# 1. TEMA VE SAYFA AYARLARI
# ==========================================
st.set_page_config(page_title="Hızlı Borsa Terminali", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp {
        background:
            radial-gradient(circle at 12% 8%, rgba(119, 132, 148, 0.16), transparent 30%),
            radial-gradient(circle at 92% 16%, rgba(74, 101, 111, 0.12), transparent 28%),
            #101a1a;
        color: #e7eaee;
    }
    h1, h2, h3 { color: #ffffff !important; }
    .topbar {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 0 0 14px;
        padding: 8px 10px;
        border: 1px solid rgba(180, 190, 201, 0.14);
        border-radius: 12px;
        background: rgba(38, 43, 50, 0.68);
        box-shadow: 0 8px 22px rgba(0, 0, 0, 0.14);
        backdrop-filter: blur(18px);
    }
    .topbar-label {
        color: #aeb7c1;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.08em;
        white-space: nowrap;
    }
    .news-section-title {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 4px 0 10px;
        color: #f4f6f8;
        font-size: 14px;
        font-weight: 800;
    }
    .news-section-title span { color: #8f9aa7; font-size: 10px; font-weight: 600; }
    .news-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 9px;
        margin-bottom: 22px;
    }
    .news-card {
        min-height: 104px;
        padding: 12px;
        border: 1px solid rgba(180, 190, 201, 0.14);
        border-radius: 10px;
        background: rgba(43, 48, 56, 0.58);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .news-card:hover { transform: translateY(-2px); border-color: rgba(101, 217, 255, 0.42); }
    .news-symbol { color: #65d9ff; font-size: 10px; font-weight: 800; }
    .news-source { float: right; color: #7f8b98; font-size: 9px; }
    .news-title { margin-top: 8px; color: #e7eaee; font-size: 12px; font-weight: 700; line-height: 1.4; }
    .news-time { margin-top: 7px; color: #87919d; font-size: 9px; }
    .news-feed {
        margin: 0 0 22px;
        border-top: 1px solid rgba(180, 190, 201, 0.14);
    }
    .news-row {
        display: grid;
        grid-template-columns: 70px minmax(0, 1fr);
        gap: 10px;
        padding: 11px 4px;
        border-bottom: 1px solid rgba(180, 190, 201, 0.1);
    }
    .news-row-meta { color: #65d9ff; font-size: 10px; font-weight: 800; line-height: 1.4; }
    .news-row-source { display: block; margin-top: 3px; color: #7f8b98; font-size: 9px; font-weight: 600; }
    .news-row-title { color: #e7eaee; font-size: 12px; font-weight: 700; line-height: 1.45; }
    .analyst-panel-note {
        margin: 4px 0 12px;
        color: #87919d;
        font-size: 10px;
        line-height: 1.4;
    }
    .analyst-group {
        margin: 0 0 17px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(180, 190, 201, 0.1);
    }
    .analyst-symbol {
        margin-bottom: 9px;
        color: #f4f6f8;
        font-size: 12px;
        font-weight: 800;
    }
    .analyst-row {
        display: grid;
        grid-template-columns: 54px minmax(0, 1fr) 35px;
        align-items: center;
        gap: 8px;
        margin: 7px 0;
    }
    .analyst-label { color: #b8c2cd; font-size: 11px; font-weight: 800; }
    .analyst-bar {
        height: 7px;
        overflow: hidden;
        border-radius: 99px;
        background: rgba(116, 127, 143, 0.25);
    }
    .analyst-fill { height: 100%; border-radius: inherit; }
    .analyst-buy { background: #50e3a4; }
    .analyst-hold { background: #aeb7c1; }
    .analyst-sell { background: #f05b6f; }
    .analyst-count { color: #aeb7c1; font-size: 10px; font-weight: 800; text-align: right; }
    .sidebar-news-feed {
        max-height: 360px;
        overflow-y: auto;
        padding-right: 6px;
        scrollbar-color: #53665f #1b2523;
        scrollbar-width: thin;
    }
    .sidebar-news-item { padding: 10px 0; border-bottom: 1px solid rgba(180, 190, 201, 0.1); }
    .sidebar-news-meta { color: #79e6b2; font-size: 10px; font-weight: 800; }
    .sidebar-news-source { float: right; color: #83928c; font-size: 9px; font-weight: 600; }
    .sidebar-news-title { clear: both; padding-top: 5px; color: #eef4f0; font-size: 11px; font-weight: 700; line-height: 1.45; }
    .sidebar-news-empty { color: #879a91; font-size: 10px; line-height: 1.45; }
    .fundamental-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin: 4px 0 10px;
        color: #f4f6f8;
        font-size: 14px;
        font-weight: 800;
    }
    .fundamental-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 7px;
        margin-bottom: 14px;
    }
    .fundamental-item {
        padding: 9px 10px;
        border: 1px solid rgba(180, 190, 201, 0.12);
        border-radius: 8px;
        background: rgba(43, 48, 56, 0.52);
    }
    .fundamental-label { color: #8f9aa7; font-size: 9px; font-weight: 700; }
    .fundamental-value { margin-top: 3px; color: #eef4f0; font-size: 12px; font-weight: 800; }
    .levels-card {
        margin: 0 0 14px;
        padding: 12px;
        border: 1px solid rgba(53, 208, 160, 0.2);
        border-radius: 10px;
        background: rgba(24, 52, 43, 0.44);
    }
    .levels-title { color: #dff8ff; font-size: 11px; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; }
    .levels-values { display: flex; gap: 20px; margin-top: 8px; }
    .level-value { color: #f4f6f8; font-size: 15px; font-weight: 800; }
    .level-value span { display: block; color: #8f9aa7; font-size: 9px; font-weight: 700; }
    .levels-note { margin-top: 8px; color: #aeb7c1; font-size: 9px; line-height: 1.4; }
    .trading-title { color: #f4f6f8; font-size: 18px; font-weight: 800; }
    .trade-card { margin: 0 0 14px; padding: 14px; border: 1px solid rgba(101, 217, 255, 0.18); border-radius: 10px; background: rgba(43, 48, 56, 0.58); }
    .trade-action { font-size: 20px; font-weight: 900; }
    [data-testid="stButton"] button {
        min-height: 38px;
        border: 1px solid rgba(101, 217, 255, 0.3);
        border-radius: 9px;
        background: rgba(43, 48, 56, 0.76);
        color: #e7eaee;
        font-weight: 800;
        letter-spacing: 0.04em;
        transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
    }
    [data-testid="stButton"] button:hover {
        transform: translateY(-1px);
        border-color: #65d9ff;
        background: rgba(54, 79, 88, 0.9);
        color: #ffffff;
    }
    [data-testid="stButton"] button[kind="primary"] {
        border-color: rgba(53, 208, 160, 0.72);
        background: linear-gradient(135deg, #087f6a, #35d0a0);
        color: #071714;
        box-shadow: 0 6px 18px rgba(53, 208, 160, 0.22);
    }
    @media (max-width: 760px) { .news-grid { grid-template-columns: 1fr; } }
    .market-ticker {
        position: relative;
        margin: 0 0 22px;
        border: 1px solid rgba(180, 190, 201, 0.16);
        border-radius: 12px;
        overflow: hidden;
        background: rgba(38, 43, 50, 0.78);
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.18);
        backdrop-filter: blur(18px);
    }
    .ticker-head {
        display: flex;
        align-items: center;
        gap: 8px;
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        z-index: 2;
        padding: 0 16px;
        background: rgba(38, 43, 50, 0.96);
        border-right: 1px solid rgba(180, 190, 201, 0.14);
        color: #f0f2f5;
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 0.1em;
    }
    .ticker-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #35d0a0;
        box-shadow: 0 0 10px rgba(53, 208, 160, 0.8);
    }
    .ticker-window { overflow: hidden; padding-left: 118px; }
    .ticker-track {
        display: flex;
        width: max-content;
        animation: ticker-slide 28s linear infinite;
    }
    .ticker-track:hover { animation-play-state: paused; }
    .ticker-item {
        min-width: 148px;
        padding: 13px 18px;
        border-right: 1px solid rgba(180, 190, 201, 0.1);
        white-space: nowrap;
    }
    .ticker-name { color: #aeb7c1; font-size: 11px; font-weight: 700; }
    .ticker-price { margin-top: 3px; color: #f4f6f8; font-size: 14px; font-weight: 800; }
    .ticker-change { margin-left: 6px; font-size: 11px; font-weight: 700; }
    .ticker-up { color: #35d0a0; }
    .ticker-down { color: #ff6b81; }
    @keyframes ticker-slide {
        from { transform: translateX(0); }
        to { transform: translateX(-50%); }
    }
    @media (max-width: 640px) {
        .ticker-head { padding: 0 10px; font-size: 10px; }
        .ticker-window { padding-left: 84px; }
        .ticker-item { min-width: 132px; padding: 12px 14px; }
    }
    .brand-signature {
        position: fixed;
        top: 18px;
        right: 28px;
        z-index: 999999;
        color: #d9dee5;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-shadow: 0 0 14px rgba(217, 222, 229, 0.28);
        background: linear-gradient(180deg, #f4f6f8 0%, #aeb7c1 52%, #eef1f4 100%);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    @media (max-width: 640px) {
        .brand-signature {
            top: 12px;
            right: 16px;
            font-size: 12px;
        }
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(38, 43, 50, 0.92), rgba(25, 29, 34, 0.96));
        border-right: 1px solid rgba(180, 190, 201, 0.12);
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 2.4rem;
    }
    .sidebar-brand {
        animation: sidebar-enter 0.65s ease-out both;
        margin: 0 0 22px;
        padding: 16px 15px;
        border: 1px solid rgba(180, 190, 201, 0.16);
        border-radius: 14px;
        background: linear-gradient(135deg, rgba(74, 82, 93, 0.55), rgba(38, 43, 50, 0.48));
        box-shadow: 0 12px 26px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(18px);
    }
    .sidebar-brand-title {
        color: #f2f4f7;
        font-size: 16px;
        font-weight: 800;
        letter-spacing: 0.03em;
    }
    .sidebar-brand-subtitle {
        margin-top: 5px;
        color: #9da8b4;
        font-size: 11px;
        line-height: 1.45;
    }
    .sidebar-live {
        display: flex;
        align-items: center;
        gap: 7px;
        margin-top: 12px;
        color: #35d0a0;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.1em;
    }
    .sidebar-live-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #35d0a0;
        box-shadow: 0 0 0 0 rgba(53, 208, 160, 0.65);
        animation: live-pulse 1.8s infinite;
    }
    [data-testid="stSidebar"] label {
        color: #b9c2cc !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        border: 1px solid rgba(180, 190, 201, 0.2);
        border-radius: 10px;
        background: rgba(52, 59, 68, 0.7);
        transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div:hover {
        border-color: rgba(101, 217, 255, 0.65);
        box-shadow: 0 0 0 3px rgba(101, 217, 255, 0.08);
        transform: translateY(-1px);
    }
    [data-testid="stSidebar"] [data-baseweb="tag"] {
        border-radius: 7px;
        background: rgba(101, 217, 255, 0.16);
        color: #c8f1ff;
    }
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #7f8b98;
        font-size: 10px;
    }
    @keyframes sidebar-enter {
        from { opacity: 0; transform: translateX(-12px); }
        to { opacity: 1; transform: translateX(0); }
    }
    @keyframes live-pulse {
        0% { box-shadow: 0 0 0 0 rgba(53, 208, 160, 0.65); }
        70% { box-shadow: 0 0 0 7px rgba(53, 208, 160, 0); }
        100% { box-shadow: 0 0 0 0 rgba(53, 208, 160, 0); }
    }
    [data-testid="stPlotlyChart"] {
        background: rgba(43, 48, 56, 0.72);
        border: 1px solid rgba(180, 190, 201, 0.14);
        border-radius: 12px;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.20);
        overflow: hidden;
    }

    .ai-card {
        background: rgba(51, 57, 66, 0.62);
        border: 1px solid rgba(101, 217, 255, 0.18);
        border-left: 4px solid #65d9ff;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        box-shadow: 0 10px 28px rgba(0,0,0,0.18);
        backdrop-filter: blur(18px);
    }
    .indicator-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
        margin: 0 0 14px;
    }
    .indicator-box {
        padding: 11px 12px;
        border: 1px solid rgba(180, 190, 201, 0.14);
        border-radius: 10px;
        background: rgba(43, 48, 56, 0.58);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .indicator-box:hover {
        transform: translateY(-2px);
        border-color: rgba(101, 217, 255, 0.42);
    }
    .indicator-label {
        color: #8f9aa7;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .indicator-value {
        margin-top: 4px;
        color: #f4f6f8;
        font-size: 15px;
        font-weight: 800;
    }
    .indicator-note {
        margin-top: 3px;
        color: #aeb7c1;
        font-size: 10px;
        line-height: 1.35;
    }
    .indicator-positive { color: #35d0a0; }
    .indicator-negative { color: #ff6b81; }
    .indicator-neutral { color: #f3c969; }
    .signal-summary {
        margin: -6px 0 14px;
        padding: 10px 12px;
        border-left: 2px solid #65d9ff;
        border-radius: 0 8px 8px 0;
        background: rgba(101, 217, 255, 0.07);
        color: #b8c2cd;
        font-size: 11px;
        line-height: 1.45;
    }
    .ema-focus-card {
        margin: 0 0 14px;
        padding: 14px;
        border: 1px solid rgba(101, 217, 255, 0.22);
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(47, 68, 80, 0.56), rgba(43, 48, 56, 0.6));
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.16);
    }
    .ema-focus-title {
        color: #dff8ff;
        font-size: 12px;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }
    .ema-focus-values {
        display: flex;
        gap: 20px;
        margin-top: 10px;
    }
    .ema-focus-value { color: #f4f6f8; font-size: 16px; font-weight: 800; }
    .ema-focus-value span { color: #8f9aa7; font-size: 10px; font-weight: 700; }
    .ema-focus-note { margin-top: 9px; color: #b8c2cd; font-size: 11px; line-height: 1.45; }
    .price-tag {
        font-size: 28px;
        font-weight: bold;
        color: #ffffff;
    }
    .master-badge {
        color: white;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 800;
        font-size: 16px;
        margin-left: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.5);
    }
</style>
""", unsafe_allow_html=True)

API_KEY = os.getenv("GEMINI_API_KEY", "")

BIST30 = {
    "AKBANK": "AKBNK.IS", "ALARKO HOLDİNG": "ALARK.IS", "ASELSAN": "ASELS.IS",
    "ASTOR ENERJİ": "ASTOR.IS", "BİM": "BIMAS.IS", "EKGYO": "EKGYO.IS",
    "ENKA İNŞAAT": "ENKAI.IS", "ENERJİSA": "ENJSA.IS", "EREĞLİ DEMİR ÇELİK": "EREGL.IS",
    "FORD OTOSAN": "FROTO.IS", "GARANTİ BBVA": "GARAN.IS", "GÜBRE FABRİKALARI": "GUBRF.IS",
    "HEKTAŞ": "HEKTS.IS", "İŞ BANKASI (C)": "ISCTR.IS", "KOÇ HOLDİNG": "KCHOL.IS",
    "KONTROLMATİK": "KONTR.IS", "KOZA ALTIN": "KOZAL.IS", "KARDEMİR (D)": "KRDMD.IS",
    "ODAS ELEKTRİK": "ODAAS.IS", "PETKİM": "PETKM.IS", "PEGASUS": "PGSUS.IS",
    "SABANCI HOLDİNG": "SAHOL.IS", "SASA POLYESTER": "SASA.IS", "ŞİŞECAM": "SISE.IS",
    "TURKCELL": "TCELL.IS", "TÜRK HAVA YOLLARI": "THYAO.IS", "TOFAŞ": "TOASO.IS",
    "TÜPRAŞ": "TUPRS.IS", "YAPI KREDİ": "YKBNK.IS"
}

# ==========================================
# 2. MOTORLAR (VERİ & RENKLENDİRİLMİŞ AI)
# ==========================================
CHART_TIMEFRAMES = {
    "1Y": {"period": "10y", "interval": "1d", "label": "1 Yıl"},
}

@st.cache_data(ttl=900)
def fetch_stock_data(symbol: str, timeframe: str = "1Y"):
    chart_config = CHART_TIMEFRAMES[timeframe]
    df = yf.download(
        symbol,
        period=chart_config["period"],
        interval=chart_config["interval"],
        progress=False,
        auto_adjust=False,
    )
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.ffill().dropna()
    
    df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()
    df['EMA_20'] = EMAIndicator(close=df['Close'], window=20).ema_indicator()
    df['EMA_50'] = EMAIndicator(close=df['Close'], window=50).ema_indicator()
    macd = MACD(close=df['Close'], window_slow=26, window_fast=12, window_sign=9)
    df['MACD'] = macd.macd()
    df['MACD_Signal'] = macd.macd_signal()
    bollinger = BollingerBands(close=df['Close'], window=20, window_dev=2)
    df['BB_High'] = bollinger.bollinger_hband()
    df['BB_Low'] = bollinger.bollinger_lband()
    stochastic = StochasticOscillator(
        high=df['High'], low=df['Low'], close=df['Close'], window=14, smooth_window=3
    )
    df['Stoch'] = stochastic.stoch()
    df['ATR'] = AverageTrueRange(
        high=df['High'], low=df['Low'], close=df['Close'], window=14
    ).average_true_range()
    df['Vol_SMA'] = df['Volume'].rolling(20).mean()
    return df

@st.cache_data(ttl=90)
def fetch_day_trading_data(symbol: str):
    """5 dakikalik veriden gun ici sinyal icin gerekli gostergeleri uretir."""
    df = yf.download(
        symbol,
        period="5d",
        interval="5m",
        progress=False,
        auto_adjust=False,
        prepost=False,
    )
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    required = {"Open", "High", "Low", "Close", "Volume"}
    if df.empty or not required.issubset(df.columns):
        return pd.DataFrame()
    df = df[["Open", "High", "Low", "Close", "Volume"]].ffill().dropna()
    df["EMA_9"] = EMAIndicator(close=df["Close"], window=9).ema_indicator()
    df["EMA_21"] = EMAIndicator(close=df["Close"], window=21).ema_indicator()
    df["RSI"] = RSIIndicator(close=df["Close"], window=14).rsi()
    typical_price = (df["High"] + df["Low"] + df["Close"]) / 3
    session_key = pd.Series(df.index.date, index=df.index)
    df["VWAP"] = (typical_price * df["Volume"]).groupby(session_key).cumsum() / df["Volume"].groupby(session_key).cumsum()
    df["ATR"] = AverageTrueRange(high=df["High"], low=df["Low"], close=df["Close"], window=14).average_true_range()
    return df.dropna()

def get_day_trading_signal(df):
    if df.empty:
        return {"action": "VERİ YOK", "class": "indicator-neutral", "price": None, "entry": None, "stop": None, "target": None, "note": "5 dakikalık veri alınamadı."}
    last = df.iloc[-1]
    bullish = last["EMA_9"] > last["EMA_21"] and last["Close"] > last["VWAP"] and 52 <= last["RSI"] <= 70
    bearish = last["EMA_9"] < last["EMA_21"] and last["Close"] < last["VWAP"] and 30 <= last["RSI"] <= 48
    if bullish:
        action, css_class, note = "AL", "indicator-positive", "EMA 9, VWAP ve RSI birlikte yukarı yönü destekliyor."
        stop = last["Close"] - (last["ATR"] * 1.2)
        target = last["Close"] + (last["ATR"] * 1.8)
    elif bearish:
        action, css_class, note = "SAT", "indicator-negative", "EMA 9, VWAP ve RSI birlikte aşağı yönü destekliyor."
        stop = last["Close"] + (last["ATR"] * 1.2)
        target = last["Close"] - (last["ATR"] * 1.8)
    else:
        action, css_class, note = "BEKLE", "indicator-neutral", "Koşullar aynı yönde yeterince kesişmedi; teyit bekleniyor."
        stop = target = None
    return {
        "action": action,
        "class": css_class,
        "price": float(last["Close"]),
        "entry": float(last["Close"]),
        "stop": float(stop) if stop is not None else None,
        "target": float(target) if target is not None else None,
        "rsi": float(last["RSI"]),
        "vwap": float(last["VWAP"]),
        "updated": df.index[-1].strftime("%d.%m %H:%M"),
        "note": note,
    }

def get_support_resistance(df):
    recent = df.tail(60)
    support = float(recent["Low"].rolling(10).min().iloc[-1])
    resistance = float(recent["High"].rolling(10).max().iloc[-1])
    return support, resistance

def get_master_signal(last):
    """Tum teknik gostergeleri birlestiren kisa vadeli karar motoru."""
    rsi = last['RSI']
    ema20 = last['EMA_20']
    ema50 = last['EMA_50']
    macd = last['MACD']
    macd_signal = last['MACD_Signal']
    stoch = last['Stoch']
    close = last['Close']
    bb_high = last['BB_High']
    bb_low = last['BB_Low']
    volume_ratio = last['Volume'] / last['Vol_SMA'] if last['Vol_SMA'] > 0 else 1.0

    score = 0
    score += 1 if ema20 > ema50 else -1
    score += 1 if macd > macd_signal else -1
    score += 1 if 30 <= rsi <= 65 else -1 if rsi > 70 else 0
    score += 1 if 20 <= stoch <= 80 else -1 if stoch > 85 else 0
    score += 1 if close > bb_low and close < bb_high else -1 if close >= bb_high else 0
    if volume_ratio > 1.3:
        score += 1 if close >= last['Open'] else -1

    if score >= 3:
        return "🟢 AL", "linear-gradient(to right, #047857, #35d0a0)"
    if score <= -2:
        return "🔴 SAT", "linear-gradient(to right, #be123c, #ff6b81)"
    if score <= 0:
        return "🟡 BEKLE / RİSKLİ", "linear-gradient(to right, #a16207, #f3c969)"
    return "🔵 TUT", "linear-gradient(to right, #0369a1, #65d9ff)"

def get_signal_summary(last):
    """Kararin nedenini tek satirlik, kullaniciya donuk bir ozet olarak uretir."""
    rsi = last['RSI']
    trend_up = last['EMA_20'] > last['EMA_50']
    momentum_up = last['MACD'] > last['MACD_Signal']
    volume_ratio = last['Volume'] / last['Vol_SMA'] if last['Vol_SMA'] > 0 else 1.0
    reasons = []
    reasons.append("trend yukarı" if trend_up else "trend zayıf")
    reasons.append("momentum pozitif" if momentum_up else "momentum zayıf")
    if rsi > 70:
        reasons.append("RSI aşırı alımda")
    elif rsi < 30:
        reasons.append("RSI aşırı satımda")
    else:
        reasons.append("RSI dengeli")
    if volume_ratio > 1.3:
        reasons.append("yüksek hacim")
    return " · ".join(reasons).capitalize() + "."

def get_indicator_readouts(last):
    """Indikatorleri teknik deger yerine dogrudan sonuca cevirir."""
    rsi = last['RSI']
    trend_up = last['EMA_20'] > last['EMA_50']
    momentum_up = last['MACD'] > last['MACD_Signal']
    stoch = last['Stoch']
    volume_ratio = last['Volume'] / last['Vol_SMA'] if last['Vol_SMA'] > 0 else 1.0
    price = last['Close']
    atr_ratio = (last['ATR'] / price) * 100 if price else 0

    if rsi > 70:
        rsi_result, rsi_note, rsi_class = "AŞIRI ALIM", "Kısa vadede yükseliş yorulmuş olabilir.", "indicator-negative"
    elif rsi < 30:
        rsi_result, rsi_note, rsi_class = "AŞIRI SATIM", "Tepki yükselişi ihtimali var, tek başına alım sinyali değil.", "indicator-positive"
    else:
        rsi_result, rsi_note, rsi_class = "DENGELİ", "Fiyat momentumu aşırı bölgelere girmemiş.", "indicator-neutral"

    if trend_up:
        ema_result, ema_note, ema_class = "YUKARI TREND", "EMA 20, EMA 50'nin üstünde; kısa yön güçlü.", "indicator-positive"
    else:
        ema_result, ema_note, ema_class = "AŞAĞI BASKI", "EMA 20, EMA 50'nin altında; yükseliş teyitsiz.", "indicator-negative"

    if momentum_up:
        macd_result, macd_note, macd_class = "POZİTİF", "Momentum hareketi destekliyor.", "indicator-positive"
    else:
        macd_result, macd_note, macd_class = "ZAYIF", "Momentum güç kaybediyor.", "indicator-negative"

    if price >= last['BB_High']:
        band_result, band_note, band_class = "ÜST BANDA YAKIN", "Fiyat kısa vadede gerilmiş olabilir.", "indicator-negative"
    elif price <= last['BB_Low']:
        band_result, band_note, band_class = "ALT BANDA YAKIN", "Fiyat baskı altında; tepki ihtimali izlenir.", "indicator-positive"
    else:
        band_result, band_note, band_class = "NORMAL ALAN", "Fiyat olağan oynaklık bandında.", "indicator-neutral"

    if stoch > 80:
        stoch_result, stoch_note, stoch_class = "AŞIRI ALIM", "Kısa vadeli düzeltme riski artmış.", "indicator-negative"
    elif stoch < 20:
        stoch_result, stoch_note, stoch_class = "AŞIRI SATIM", "Kısa vadeli toparlanma izlenebilir.", "indicator-positive"
    else:
        stoch_result, stoch_note, stoch_class = "NORMAL", "Kısa vadeli hareket dengeli.", "indicator-neutral"

    volume_result = "YÜKSEK HACİM" if volume_ratio > 1.3 else "NORMAL HACİM"
    volume_note = "Hareket güçlü katılımla oluşuyor." if volume_ratio > 1.3 else "Fiyat hareketi olağan hacimde."
    volume_class = "indicator-positive" if volume_ratio > 1.3 else "indicator-neutral"
    risk_result = "YÜKSEK OYNAKLIK" if atr_ratio > 4 else "DÜŞÜK / ORTA OYNAKLIK"
    risk_note = f"Ortalama günlük hareket fiyatın %{atr_ratio:.1f}'i."
    risk_class = "indicator-negative" if atr_ratio > 4 else "indicator-neutral"

    return [
        ("RSI · güç", rsi_result, rsi_note, rsi_class),
        ("EMA · trend", ema_result, ema_note, ema_class),
        ("MACD · momentum", macd_result, macd_note, macd_class),
        ("Bollinger · fiyat alanı", band_result, band_note, band_class),
        ("Stochastic · kısa dönüş", stoch_result, stoch_note, stoch_class),
        ("Hacim / ATR · risk", f"{volume_result} · {risk_result}", f"{volume_note} {risk_note}", risk_class if atr_ratio > 4 else volume_class),
    ]

def get_smart_fallback_analysis(name, last, pct_change):
    """Renklendirilmiş canlı piyasa özeti"""
    rsi = last['RSI']
    vol_ratio = (last['Volume'] / last['Vol_SMA']) if last['Vol_SMA'] > 0 else 1.0
    
    analysis = f"**{name}** şu an **{last['Close']:.2f} TL** seviyesinde ve günlük **%{pct_change:+.2f}** değişim gösteriyor. "
    
    if rsi > 70:
        analysis += "<span style='color:#ef4444; font-weight:bold;'>Aşırı alım (şişkinlik)</span> bölgesinde. Hisse çok hızlı yükseldiği için kısa vadede <span style='color:#ef4444; font-weight:bold;'>kâr satışları riski</span> oldukça yüksek. "
    elif rsi < 35:
        analysis += "RSI dip seviyelerde. Hisse şu an tepki alımlarına açık, <span style='color:#10b981; font-weight:bold;'>ucuz ve cazip (fırsat)</span> bir bölgede yer alıyor. "
    else:
        analysis += "Fiyat hareketleri şu an <span style='color:#FFD700; font-weight:bold;'>nötr ve dengeli</span> kulvarda ilerliyor. "
        
    if vol_ratio > 1.3:
        analysis += "İşlem hacmi ortalamanın %30 üzerinde; tahtada <span style='color:#38bdf8; font-weight:bold;'>büyük oyuncu (balina) hareketliliği</span> var."
    else:
        analysis += "İşlem hacmi <span style='color:#94a3b8;'>olağan seviyelerde</span>, panik yapılacak bir durum yok."
        
    if "TÜPRAŞ" in name:
        analysis += "<br><br>🛢️ *Not: Brent petrol fiyatlarındaki hareketlilik TÜPRAŞ marjlarını doğrudan etkiler, haber akışını takip et.*"
    elif "THY" in name or "PEGASUS" in name:
        analysis += "<br><br>✈️ *Not: Turizm verileri ve jet yakıtı (petrol) maliyetleri yönü belirleyecektir.*"
        
    return analysis

def auto_ask_gemini(name, last, pct_change, prompt: str):
    """API yoğunluk verirse anında renkli şablonu basar"""
    try:
        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(model="gemini-1.5-flash", contents=prompt)
        if response.text:
            return response.text
        else:
            return get_smart_fallback_analysis(name, last, pct_change)
    except Exception:
        return get_smart_fallback_analysis(name, last, pct_change)

def normalize_news_item(item):
    """Yahoo Finance'in eski ve yeni haber formatlarini ayni ciktiya cevirir."""
    item = item if isinstance(item, dict) else {}
    content = item.get("content") if isinstance(item.get("content"), dict) else item
    provider = content.get("provider") or item.get("publisher") or {}
    publisher = provider.get("displayName") or provider.get("name") if isinstance(provider, dict) else str(provider)
    published = content.get("pubDate") or content.get("providerPublishTime") or item.get("providerPublishTime")
    if isinstance(published, (int, float)):
        published = datetime.fromtimestamp(published, tz=timezone.utc).strftime("%d.%m %H:%M")
    elif published:
        published = str(published).replace("T", " ")[:16]
    title = content.get("title") or item.get("title")
    return str(title).strip() if title else "", publisher, published or "Güncel"

@st.cache_data(ttl=900)
def fetch_fundamental_context(symbol: str):
    """Bilanço özeti ve haber başlıklarını AI analizine taşır."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info or {}
        financials = {
            "Şirket": info.get("longName") or info.get("shortName") or symbol,
            "Sektör": info.get("sector") or "Belirtilmemiş",
            "Piyasa değeri": info.get("marketCap"),
            "F/K": info.get("trailingPE"),
            "PD/DD": info.get("priceToBook"),
            "Son çeyrek gelir": info.get("totalRevenue"),
            "Kâr marjı": info.get("profitMargins"),
            "Borç/özsermaye": info.get("debtToEquity"),
        }
        news_lines = []
        for item in (ticker.news or [])[:6]:
            title, publisher, _ = normalize_news_item(item)
            if title:
                news_lines.append(f"- {title} ({publisher or 'kaynak belirtilmemiş'})")
        return financials, news_lines
    except Exception:
        return {}, []

def format_fundamental_context(symbol: str):
    financials, news_lines = fetch_fundamental_context(symbol)
    metrics = "\n".join(
        f"- {key}: {value}" for key, value in financials.items() if value is not None
    ) or "- Temel veri alınamadı; kesin yorum yapılmamalı."
    news = "\n".join(news_lines) or "- Son haber başlığı alınamadı."
    return f"ŞİRKET VE FİNANSALLAR:\n{metrics}\n\nSON HABERLER:\n{news}"

def render_fundamental_panel(symbol: str):
    financials, _ = fetch_fundamental_context(symbol)
    st.markdown('<div class="fundamental-header">Temel veriler</div>', unsafe_allow_html=True)
    cards = []
    for key, value in financials.items():
        if value is None:
            continue
        if isinstance(value, float) and key == "Kâr marjı":
            value = f"%{value * 100:.1f}"
        elif isinstance(value, (int, float)):
            value = f"{value:,.2f}"
        cards.append(
            f"<div class='fundamental-item'><div class='fundamental-label'>{escape(str(key))}</div>"
            f"<div class='fundamental-value'>{escape(str(value))}</div></div>"
        )
    st.markdown(
        "<div class='fundamental-grid'>" + "".join(cards or [
            "<div class='fundamental-item'><div class='fundamental-value'>Temel veri alınamadı.</div></div>"
        ]) + "</div>",
        unsafe_allow_html=True,
    )

@st.cache_data(ttl=180)
def fetch_followed_news(symbols):
    """Takip listesinden tekrarsiz, kisa haber akisi getirir."""
    news_items = []
    seen_titles = set()
    context_symbols = ("XU100.IS", "XU030.IS", "BZ=F", "GC=F", "USDTRY=X")
    source_symbols = tuple(dict.fromkeys((*symbols, *context_symbols)))
    for symbol in source_symbols:
        try:
            ticker = yf.Ticker(symbol)
            for item in (ticker.news or [])[:5]:
                title, source, published = normalize_news_item(item)
                normalized_title = str(title).strip()
                if normalized_title and normalized_title.lower() not in seen_titles:
                    seen_titles.add(normalized_title.lower())
                    news_items.append({
                        "symbol": symbol.replace(".IS", "").replace("=F", "").replace("=X", ""),
                        "title": normalized_title[:155] + ("..." if len(normalized_title) > 155 else ""),
                        "source": source or "Yahoo Finance",
                        "time": published or "Güncel",
                    })
        except Exception:
            continue
    return news_items[:24]

@st.cache_data(ttl=1800)
def summarize_news_items(news_items):
    """Kaynak basliklarini tek Gemini cagrisinda kisa Turkce ozetlere cevirir."""
    news_items = [dict(item) for item in news_items]
    if not news_items:
        return []
    titles = "\n".join(f"{index + 1}. {item['title']}" for index, item in enumerate(news_items))
    prompt = f"""
ZORUNLU ÇIKTI DİLİ: TÜRKÇE.
Aşağıdaki İngilizce veya farklı dildeki finans haber başlıklarını Türkçeye çevirip her biri için tek kısa, tarafsız cümlelik özet yaz.
İngilizce kelime bırakma; şirket ve marka adları özel isim olarak kalabilir.
Sadece numaralı satırları döndür; yorum, yatırım tavsiyesi veya yeni bilgi ekleme.

{titles}
"""
    try:
        response = genai.Client(api_key=API_KEY).models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
        )
        summaries = {}
        for line in (response.text or "").splitlines():
            match = re.match(r"^\s*(\d+)\s*[.)-]\s*(.+)$", line.strip())
            if match:
                summaries[int(match.group(1))] = match.group(2).strip()
        return [
            {**dict(item), "title": summaries.get(index + 1, item["title"])}
            for index, item in enumerate(news_items)
        ]
    except Exception:
        return [dict(item) for item in news_items]

@st.fragment(run_every="1s")
def render_sidebar_news(symbols):
    with st.sidebar.expander("📰 Takip haberleri", expanded=True):
        remaining = 180 - (int(time.time()) % 180)
        st.caption(f"Kısa Türkçe özet · yeni tarama: {remaining} sn")
        news_items = fetch_followed_news(tuple(symbols))
        if not news_items:
            st.markdown('<div class="sidebar-news-empty">Seçili hisseler için güncel haber bulunamadı.</div>', unsafe_allow_html=True)
            return
        news_items = summarize_news_items(tuple(tuple(sorted(item.items())) for item in news_items))
        items = "".join(
            f"<div class='sidebar-news-item'><span class='sidebar-news-meta'>{escape(item['symbol'])}</span>"
            f"<span class='sidebar-news-source'>{escape(str(item['source']))} · {escape(str(item['time']))}</span>"
            f"<div class='sidebar-news-title'>{escape(str(item['title']))}</div></div>"
            for item in news_items
        )
        st.markdown(f"<div class='sidebar-news-feed'>{items}</div>", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def fetch_analyst_overview(symbols):
    """Guncel Yahoo analist ozetini dogrudan AL/TUT/SAT dagilimina cevirir."""
    overview = []
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            recommendations = ticker.recommendations_summary
            if recommendations is None or recommendations.empty:
                recommendations = ticker.recommendations
            if recommendations is None or recommendations.empty:
                overview.append((symbol, "Güncel", {"AL": 0, "TUT": 0, "SAT": 0}))
                continue
            latest = recommendations.iloc[0]
            values = {
                str(key).lower(): int(float(value))
                for key, value in latest.items()
                if pd.notna(value) and str(key).lower() != "period"
            }
            counts = {
                "AL": values.get("strongbuy", 0) + values.get("buy", 0),
                "TUT": values.get("hold", 0),
                "SAT": values.get("sell", 0) + values.get("strongsell", 0),
            }
            overview.append((symbol, f"{latest.get('period', 'Güncel')} · {sum(counts.values())} görüş", counts))
        except Exception:
            overview.append((symbol, "Güncel", {"AL": 0, "TUT": 0, "SAT": 0}))
    return overview

@st.fragment(run_every="1s")
def render_analyst_sidebar(symbols):
    with st.sidebar.expander("👥 Analist görüşleri", expanded=True):
        remaining = 300 - (int(time.time()) % 300)
        st.markdown(f'<div class="analyst-panel-note">Tek tek isim yerine yayınlanan analist oy dağılımı gösteriliyor.<br>Yeni analist verisi: {remaining} sn</div>', unsafe_allow_html=True)
        for symbol, period, counts in fetch_analyst_overview(tuple(symbols)):
            total = sum(counts.values())
            st.markdown(f'<div class="analyst-group"><div class="analyst-symbol">{escape(symbol.replace(".IS", ""))} · {escape(period)}</div>', unsafe_allow_html=True)
            if not total:
                st.caption("Analist verisi bulunamadı.")
                st.markdown('</div>', unsafe_allow_html=True)
                continue
            for label, css_class in [("AL", "analyst-buy"), ("TUT", "analyst-hold"), ("SAT", "analyst-sell")]:
                count = counts[label]
                percent = count / total * 100
                st.markdown(
                    f'<div class="analyst-row"><div class="analyst-label">{label}</div>'
                    f'<div class="analyst-bar"><div class="analyst-fill {css_class}" style="width:{percent:.0f}%"></div></div>'
                    f'<div class="analyst-count">{count} · {percent:.0f}%</div></div>',
                    unsafe_allow_html=True,
                )
            st.markdown('</div>', unsafe_allow_html=True)

MARKET_WATCHLIST = {
    "BIST 100": "XU100.IS",
    "BIST 30": "XU030.IS",
    "PETROL": "BZ=F",
    "ALTIN": "GC=F",
    "USD/TRY": "USDTRY=X",
    "EUR/TRY": "EURTRY=X",
}

@st.cache_data(ttl=60)
def fetch_market_snapshot():
    snapshot = []
    for name, symbol in MARKET_WATCHLIST.items():
        try:
            market_df = yf.download(
                symbol,
                period="5d",
                interval="1d",
                progress=False,
                auto_adjust=False,
            )
            if isinstance(market_df.columns, pd.MultiIndex):
                market_df.columns = market_df.columns.get_level_values(0)
            closes = market_df["Close"].dropna()
            if len(closes) < 2:
                raise ValueError("Yeterli piyasa verisi yok")
            current = float(closes.iloc[-1])
            previous = float(closes.iloc[-2])
            change = ((current - previous) / previous) * 100
            snapshot.append((name, current, change))
        except Exception:
            snapshot.append((name, None, None))
    return snapshot

@st.fragment(run_every="60s")
def render_market_ticker():
    items = []
    for name, price, change in fetch_market_snapshot():
        if price is None or change is None:
            items.append(f'<div class="ticker-item"><div class="ticker-name">{name}</div><div class="ticker-price">--</div></div>')
            continue
        direction = "up" if change >= 0 else "down"
        arrow = "▲" if change >= 0 else "▼"
        items.append(
            f'<div class="ticker-item"><div class="ticker-name">{name}</div>'
            f'<div class="ticker-price">{price:,.2f}'
            f'<span class="ticker-change ticker-{direction}">{arrow} {change:+.2f}%</span></div></div>'
        )
    ticker_items = "".join(items)
    st.markdown(
        '<div class="market-ticker"><div class="ticker-head"><span class="ticker-dot"></span> PİYASA</div>'
        f'<div class="ticker-window"><div class="ticker-track">{ticker_items}{ticker_items}</div></div></div>',
        unsafe_allow_html=True,
    )

# ==========================================
# 4. ANA EKRAN (GRAFİK + CANLI KARTLAR)
# ==========================================
if "active_view" not in st.session_state:
    st.session_state.active_view = "market"

title_col, market_col, trading_col, refresh_col = st.columns([3, 2, 2, 3], gap="small")
with title_col:
    st.markdown('<div class="trading-title">⚡ Hızlı & Akıllı Terminal</div>', unsafe_allow_html=True)
with market_col:
    if st.button("PİYASA", use_container_width=True, help="Piyasa analizini göster"):
        st.session_state.active_view = "market"
with trading_col:
    if st.button("TRADEING", type="primary", use_container_width=True, help="Day trading görünümünü aç"):
        st.session_state.active_view = "trading"
with refresh_col:
    if st.button("VERİLERİ YENİLE", icon=":material/refresh:", use_container_width=True, help="Grafik, indikatör ve piyasa verilerini güncelle"):
        fetch_stock_data.clear()
        fetch_day_trading_data.clear()
        fetch_market_snapshot.clear()
        st.rerun()

toolbar_col, status_col = st.columns([4, 6], gap="large")
with toolbar_col:
    st.markdown('<div class="topbar-label">TAKİP LİSTESİ</div>', unsafe_allow_html=True)
    selected_stocks = st.multiselect(
        "Takip hisseleri",
        list(BIST30.keys()),
        default=["TÜPRAŞ", "ASELSAN"],
        placeholder="Hisse ara ve takip listene ekle",
        label_visibility="collapsed",
    )
with status_col:
    st.markdown('<div class="topbar-label">PİYASA 60 sn · TEKNİK VERİ 900 sn · TEMEL VERİ 900 sn</div>', unsafe_allow_html=True)
selected_symbols = [BIST30[name] for name in selected_stocks]
render_sidebar_news(selected_symbols)
render_analyst_sidebar(selected_symbols)
st.markdown('<div class="brand-signature">ByFurkan</div>', unsafe_allow_html=True)

if st.session_state.active_view == "trading" and selected_stocks:
    st.markdown('<div class="trade-card"><div class="fundamental-header">Day trading sinyalleri</div><div class="levels-note">5 dakikalık veri · sinyal garanti değildir; risk yönetimi ve emir kararını kullanıcı verir.</div></div>', unsafe_allow_html=True)
    trade_cols = st.columns(min(len(selected_stocks), 3))
    for index, name in enumerate(selected_stocks):
        trade_df = fetch_day_trading_data(BIST30[name])
        trade = get_day_trading_signal(trade_df)
        with trade_cols[index % len(trade_cols)]:
            if trade["price"] is None:
                st.warning(f"{name}: {trade['note']}")
            else:
                stop = f"{trade['stop']:,.2f}" if trade['stop'] is not None else "-"
                target = f"{trade['target']:,.2f}" if trade['target'] is not None else "-"
                st.markdown(
                    f"<div class='trade-card'><div>{escape(name)} · {trade['updated']}</div>"
                    f"<div class='trade-action {trade['class']}'>{trade['action']}</div>"
                    f"<div class='levels-note'>Fiyat {trade['price']:,.2f} · RSI {trade['rsi']:.1f} · VWAP {trade['vwap']:,.2f}<br>Stop: {stop} · Hedef: {target}<br>{escape(trade['note'])}</div></div>",
                    unsafe_allow_html=True,
                )

if st.session_state.active_view == "market":
    render_market_ticker()

if not selected_stocks:
    st.warning("Sol menüden analiz etmek istediğin hisseleri seç.")
elif st.session_state.active_view == "market":
    for name in selected_stocks:
        symbol = BIST30[name]
        try:
            df = fetch_stock_data(symbol, "1Y")
            last = df.iloc[-1]
            prev = df.iloc[-2]
            pct_change = ((last['Close'] - prev['Close']) / prev['Close']) * 100
            support, resistance = get_support_resistance(df)

            st.markdown(f"### {name} &nbsp; <span style='font-size:1.1rem; color:{'#10b981' if pct_change>=0 else '#ef4444'};'>({pct_change:+.2f}%)</span>", unsafe_allow_html=True)

            col_chart, col_info = st.columns([5, 5], gap="large")

            # --- SOL TARAF: KISALTILMIŞ GRAFİK ---
            with col_chart:
                up_color = '#35d08a'
                down_color = '#e05260'
                chart_range = [df.index[-1] - pd.DateOffset(years=1), df.index[-1]]
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['BB_High'],
                    line=dict(color='rgba(126, 166, 145, 0.34)', width=1),
                    name='Bollinger üst',
                    hoverinfo='skip',
                ))
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['BB_Low'],
                    line=dict(color='rgba(126, 166, 145, 0.34)', width=1),
                    fill='tonexty',
                    fillcolor='rgba(35, 104, 75, 0.12)',
                    name='Bollinger alanı',
                    hoverinfo='skip',
                ))
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                    increasing_line_color=up_color,
                    increasing_fillcolor=up_color,
                    decreasing_line_color=down_color,
                    decreasing_fillcolor=down_color,
                    whiskerwidth=0.5,
                    name='Fiyat',
                    hovertemplate='<b>%{x|%d %b %Y}</b><br>Açılış: %{open:,.2f}<br>Yüksek: %{high:,.2f}<br>Düşük: %{low:,.2f}<br>Kapanış: %{close:,.2f}<extra></extra>',
                ))
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['EMA_20'],
                    line=dict(color='#65e0b0', width=2.2),
                    name='EMA 20', hovertemplate='EMA 20: %{y:,.2f}<extra></extra>',
                ))
                fig.add_trace(go.Scatter(
                    x=df.index, y=df['EMA_50'],
                    line=dict(color='#d8c38f', width=2),
                    name='EMA 50', hovertemplate='EMA 50: %{y:,.2f}<extra></extra>',
                ))
                fig.update_layout(
                    paper_bgcolor='#0d1716',
                    plot_bgcolor='#14241f',
                    margin=dict(l=8, r=12, t=12, b=58),
                    height=285,
                    showlegend=False,
                    dragmode='pan',
                    uirevision='borsam-price-chart',
                    hovermode='x unified',
                    hoverlabel=dict(bgcolor='#243b32', bordercolor='#668675', font=dict(color='#f4f7f5', size=12)),
                    font=dict(family='Inter, Segoe UI, sans-serif', color='#b8c8bf', size=11),
                    xaxis=dict(
                        type='date', range=chart_range, fixedrange=False, showline=False,
                        showgrid=True, gridcolor='rgba(112, 157, 132, 0.13)',
                        rangeselector=dict(
                            buttons=[
                                dict(count=1, label='1G', step='day', stepmode='backward'),
                                dict(count=7, label='1H', step='day', stepmode='backward'),
                                dict(count=1, label='1A', step='month', stepmode='backward'),
                                dict(count=1, label='1Y', step='year', stepmode='backward'),
                                dict(step='all', label='Tümü'),
                            ],
                            x=0, y=-0.18, xanchor='left', yanchor='top',
                            bgcolor='#253a31', activecolor='#35d08a',
                            font=dict(color='#f4f6f8', size=11),
                        ),
                    ),
                    yaxis=dict(side='right', fixedrange=False, showgrid=True,
                               gridcolor='rgba(112, 157, 132, 0.16)', zeroline=False,
                               tickfont=dict(color='#b8c8bf'), tickformat=',.2f'),
                )
                fig.update_xaxes(showspikes=True, spikemode='across', spikesnap='cursor',
                                 spikecolor='#718091', spikethickness=1)
                st.plotly_chart(fig, use_container_width=True, config={
                    'displaylogo': False,
                    'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'autoScale2d'],
                    'scrollZoom': True,
                    'doubleClick': 'reset',
                    'displayModeBar': True,
                    'responsive': True,
                })

            # --- SAĞ TARAF: CANLANDIRILMIŞ BİLGİ ALANI ---
            with col_info:
                st.markdown(
                    f"<div class='levels-card'><div class='levels-title'>Destek / direnç</div>"
                    f"<div class='levels-values'><div class='level-value'><span>Destek</span>{support:,.2f}</div>"
                    f"<div class='level-value'><span>Direnç</span>{resistance:,.2f}</div></div>"
                    f"<div class='levels-note'>Son 60 günlük hareket içindeki yakın bölgeler; kesin fiyat seviyesi değildir.</div></div>",
                    unsafe_allow_html=True,
                )
                # Fiyat ve Yanındaki Yeni AL/SAT Rozeti
                master_text, master_bg = get_master_signal(last)
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div class='price-tag' style="margin-bottom: 0;">{last['Close']:,.2f} TL</div>
                    <div class='master-badge' style="background: {master_bg};">{master_text}</div>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(
                    f'<div class="signal-summary"><strong>Ne oluyor?</strong> {get_signal_summary(last)}</div>',
                    unsafe_allow_html=True,
                )
                ema20_value = last['EMA_20']
                ema50_value = last['EMA_50']
                ema_spread = ((ema20_value - ema50_value) / ema50_value) * 100 if ema50_value else 0
                price_vs_ema = ((last['Close'] - ema20_value) / ema20_value) * 100 if ema20_value else 0
                ema_direction = "Yukarı yön teyitli" if ema20_value > ema50_value else "Aşağı yön baskın"
                ema_class = "indicator-positive" if ema20_value > ema50_value else "indicator-negative"
                ema_note = (
                    "Kısa vadeli ortalama uzun vadeli ortalamanın üzerinde; yükseliş momentumu korunuyor."
                    if ema20_value > ema50_value
                    else "Kısa vadeli ortalama uzun vadeli ortalamanın altında; tepki yükselişlerinde temkinli ol."
                )
                st.markdown(f"""
                <div class="ema-focus-card">
                    <div class="ema-focus-title">EMA yön paneli</div>
                    <div class="ema-focus-values">
                        <div class="ema-focus-value"><span>EMA 20</span><br>{ema20_value:,.2f}</div>
                        <div class="ema-focus-value"><span>EMA 50</span><br>{ema50_value:,.2f}</div>
                        <div class="ema-focus-value {ema_class}"><span>Fark</span><br>{ema_spread:+.2f}%</div>
                    </div>
                    <div class="ema-focus-note"><strong>{ema_direction}.</strong> {ema_note}<br>
                    Fiyat EMA 20'ye göre %{price_vs_ema:+.2f} uzaklıkta.</div>
                </div>
                """, unsafe_allow_html=True)

                indicator_readouts = get_indicator_readouts(last)
                indicator_cards = "".join(
                    f"<div class='indicator-box'><div class='indicator-label'>{label}</div>"
                    f"<div class='indicator-value {result_class}'>{result}</div>"
                    f"<div class='indicator-note'>{note}</div></div>"
                    for label, result, note, result_class in indicator_readouts
                )
                st.markdown(f"""
                <div class="indicator-grid">
                    {indicator_cards}
                </div>
                """, unsafe_allow_html=True)

                render_fundamental_panel(symbol)
                
                # 1. AI Yorum Kartı
                fundamental_context = format_fundamental_context(symbol)
                prompt_data = f"""
                Sen temkinli bir finans analistisin. {name} ({symbol}) için sadece güncel haber,
                bilanço ve genel piyasa etkisini Türkçe, kısa ve anlaşılır biçimde özetle.
                Yatırım tavsiyesi verme; veri eksikse bunu söyle, rakam veya haber uydurma.
                En fazla 4 kısa madde kullan: Bilanço, Haberler, Piyasa etkisi, Dikkat edilmesi gereken.
                Günlük fiyat değişimi: %{pct_change:+.2f}

                {fundamental_context}
                """
                ai_response = auto_ask_gemini(name, last, pct_change, prompt_data)
                
                st.markdown(f"""
                <div class='ai-card'>
                    <div style='color:#00E5FF; font-weight:bold; margin-bottom:8px; font-size:15px;'>📰 Güncel Haber & Bilanço:</div>
                    <div style='font-size:14px; color:#cbd5e1; line-height:1.6;'>{ai_response}</div>
                </div>
                """, unsafe_allow_html=True)

            st.write("---")
            
        except Exception as e:
            st.error(f"{name} verisi yüklenirken hata oluştu.")
            