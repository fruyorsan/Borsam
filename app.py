import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from google import genai
import time

# ==========================================
# 1. TEMA VE SAYFA AYARLARI
# ==========================================
st.set_page_config(page_title="Hızlı Borsa Terminali", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    h1, h2, h3 { color: #ffffff !important; }
    .css-1d391kg { background-color: #0f172a; }
    
    .ai-card {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border-left: 4px solid #00E5FF;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .tech-card {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        border-left: 4px solid #FFD700;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
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

API_KEY = "AQ.Ab8RN6LZmXUhhpdpvbTVfAkpJsLwD8nYLTyQnfbj7kTgkYxG7A"

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
@st.cache_data(ttl=900)
def fetch_stock_data(symbol: str):
    df = yf.download(symbol, period="4mo", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.ffill().dropna()
    
    df['RSI'] = RSIIndicator(close=df['Close'], window=14).rsi()
    df['EMA_20'] = EMAIndicator(close=df['Close'], window=20).ema_indicator()
    df['EMA_50'] = EMAIndicator(close=df['Close'], window=50).ema_indicator()
    df['Vol_SMA'] = df['Volume'].rolling(20).mean()
    return df

def get_master_signal(last):
    """Fiyatın yanındaki o boşluğu dolduran ana karar motoru"""
    rsi = last['RSI']
    ema20 = last['EMA_20']
    ema50 = last['EMA_50']
    
    if rsi < 35 and ema20 > ema50:
        return "🟢 GÜÇLÜ AL", "linear-gradient(to right, #059669, #10b981)" # Yeşil
    elif rsi > 70:
        return "🔴 SAT / KÂR AL", "linear-gradient(to right, #dc2626, #ef4444)" # Kırmızı
    elif ema20 > ema50:
        return "🔵 TUT / BEKLE", "linear-gradient(to right, #0284c7, #38bdf8)" # Mavi
    else:
        return "🟡 İZLE / RİSKLİ", "linear-gradient(to right, #ca8a04, #eab308)" # Sarı

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

def get_detailed_technical_signal(last):
    """Vurgulanmış Kelimelerle Detaylı Teknik İndikatör Analizi"""
    rsi = last['RSI']
    ema20 = last['EMA_20']
    ema50 = last['EMA_50']
    vol_ratio = (last['Volume'] / last['Vol_SMA']) if last['Vol_SMA'] > 0 else 1.0

    if rsi > 70:
        status = "🔴 DİKKAT / DÜZELTME BÖLGESİ"
    elif rsi < 35 and ema20 > ema50:
        status = "🟢 GÜÇLÜ ALIM FIRSATI"
    elif ema20 > ema50:
        status = "🔵 YÜKSELİŞ TRENDİ (TUT)"
    else:
        status = "🟡 DÜŞÜŞ BASKISI (İZLE)"

    details = []
    
    # RSI
    if rsi > 70:
        details.append(f"• **RSI ({rsi:.1f}):** <span style='color:#ef4444; font-weight:bold;'>Aşırı Alım.</span> Hisse kısa vadede şişmiş durumda, satış baskısı gelebilir.")
    elif rsi < 35:
        details.append(f"• **RSI ({rsi:.1f}):** <span style='color:#10b981; font-weight:bold;'>Aşırı Satım (Ucuz).</span> Fiyat matematiksel olarak dip noktalara yakın.")
    else:
        details.append(f"• **RSI ({rsi:.1f}):** <span style='color:#FFD700; font-weight:bold;'>Dengeli.</span> Göstergeler nötr seviyede (35-70 arası).")

    # EMA
    if ema20 > ema50:
        details.append(f"• **Trend (EMA):** Kısa vade (20) uzun vadenin (50) üzerinde. <span style='color:#10b981; font-weight:bold;'>Yön YUKARI ↗</span>")
    else:
        details.append(f"• **Trend (EMA):** Kısa vade uzun vadenin altında kalmış. <span style='color:#ef4444; font-weight:bold;'>Trend ZAYIF ↘</span>")

    # Hacim
    if vol_ratio > 1.3:
        details.append(f"• **Hacim:** İşlem hacmi normalin <span style='color:#38bdf8; font-weight:bold;'>%{((vol_ratio-1)*100):.0f} üzerinde</span>. Yön hareketi güçlü destekleniyor.")
    else:
        details.append("• **Hacim:** Hacim <span style='color:#94a3b8;'>rutin</span> seviyelerde, standart bir gün yaşanıyor.")

    return status, "<br>".join(details)

# ==========================================
# 3. SOL MENÜ (İzleme Listesi)
# ==========================================
st.sidebar.title("📌 BİST 30 Listem")
st.sidebar.write("Aşağıdan hisselerini seç, sağ tarafta anında analiz edilsin.")
selected_stocks = st.sidebar.multiselect(
    "Takip Edilen Hisseler:", 
    list(BIST30.keys()), 
    default=["TÜPRAŞ", "ASELSAN"]
)
st.sidebar.divider()
st.sidebar.caption("Sistem kesintisiz canlı indikatör ve AI analiz motoruyla çalışır.")

# ==========================================
# 4. ANA EKRAN (GRAFİK + CANLI KARTLAR)
# ==========================================
st.markdown("<h2 style='color:#00E5FF; margin-bottom: 20px;'>⚡ Hızlı & Akıllı Terminal</h2>", unsafe_allow_html=True)

if not selected_stocks:
    st.warning("Sol menüden analiz etmek istediğin hisseleri seç.")
else:
    for name in selected_stocks:
        symbol = BIST30[name]
        try:
            df = fetch_stock_data(symbol)
            last = df.iloc[-1]
            prev = df.iloc[-2]
            pct_change = ((last['Close'] - prev['Close']) / prev['Close']) * 100
            
            st.markdown(f"### {name} &nbsp; <span style='font-size:1.1rem; color:{'#10b981' if pct_change>=0 else '#ef4444'};'>({pct_change:+.2f}%)</span>", unsafe_allow_html=True)
            
            col_chart, col_info = st.columns([5.5, 4.5], gap="large")
            
            # --- SOL TARAF: KISALTILMIŞ GRAFİK ---
            with col_chart:
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.75, 0.25], vertical_spacing=0.03)
                fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                             increasing_line_color='#10b981', decreasing_line_color='#ef4444'), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='#00E5FF', width=1.5), name="EMA 20"), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df['EMA_50'], line=dict(color='#FFD700', width=1.5), name="EMA 50"), row=1, col=1)
                
                colors = ['#10b981' if r['Close'] >= r['Open'] else '#ef4444' for i, r in df.iterrows()]
                fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors), row=2, col=1)
                
                fig.update_layout(
                    template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(l=0, r=0, t=10, b=0), 
                    height=220,
                    showlegend=False,
                    xaxis=dict(rangeslider=dict(visible=False), showgrid=False),
                    xaxis2=dict(showgrid=False),
                    yaxis=dict(gridcolor='#1e293b'),
                    yaxis2=dict(showgrid=False)
                )
                st.plotly_chart(fig, use_container_width=True)

            # --- SAĞ TARAF: CANLANDIRILMIŞ BİLGİ ALANI ---
            with col_info:
                # Fiyat ve Yanındaki Yeni AL/SAT Rozeti
                master_text, master_bg = get_master_signal(last)
                st.markdown(f"""
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <div class='price-tag' style="margin-bottom: 0;">{last['Close']:,.2f} TL</div>
                    <div class='master-badge' style="background: {master_bg};">{master_text}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # 1. AI Yorum Kartı
                prompt_data = f"""
                Sen net konuşan bir finans analistisin. {name} hissesi için haber, bilanço ve piyasa durumunu en anlaşılır şekilde özetle. Önemli kelimeleri kalın yaz.
                """
                ai_response = auto_ask_gemini(name, last, pct_change, prompt_data)
                
                st.markdown(f"""
                <div class='ai-card'>
                    <div style='color:#00E5FF; font-weight:bold; margin-bottom:8px; font-size:15px;'>🤖 AI Güncel Yorumu:</div>
                    <div style='font-size:14px; color:#cbd5e1; line-height:1.6;'>{ai_response}</div>
                </div>
                """, unsafe_allow_html=True)

                # 2. Detaylı Teknik Sinyal Kartı
                tech_status, tech_details_html = get_detailed_technical_signal(last)
                st.markdown(f"""
                <div class='tech-card'>
                    <div style='color:#FFD700; font-weight:bold; margin-bottom:10px; font-size:15px;'>📐 {tech_status}</div>
                    <div style='font-size:14px; color:#cbd5e1; line-height:1.7;'>{tech_details_html}</div>
                </div>
                """, unsafe_allow_html=True)

            st.write("---")
            
        except Exception as e:
            st.error(f"{name} verisi yüklenirken hata oluştu.")