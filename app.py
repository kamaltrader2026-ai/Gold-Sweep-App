import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import pytz
from datetime import datetime, time

st.set_page_config(page_title="Gold Sweep AI", page_icon="🥇", layout="centered")

st.title("🥇 Gold Liquidity Sweep App")
st.markdown("استراتيجية سحب السيولة - تعمل من 5 مساءً حتى 12 منتصف الليل (توقيت بيروت)")

balance = st.number_input("أدخل رصيد حسابك الحالي ($):", min_value=10.0, value=380.0, step=10.0)
risk_percent = 1.0
risk_amount = balance * (risk_percent / 100)

beirut_tz = pytz.timezone('Asia/Beirut')
now_beirut = datetime.now(beirut_tz)
current_time = now_beirut.time()

is_active_time = (current_time >= time(17, 0)) and (current_time <= time(23, 59))
st.write(f"🕒 التوقيت الحالي في بيروت: **{now_beirut.strftime('%H:%M')}**")

if not is_active_time:
    st.warning("⏳ السوق خارج أوقات عملك المفضلة. التطبيق في وضع المراقبة فقط.")
else:
    st.success("✅ الوقت مناسب. جاري تحليل السوق...")

@st.cache_data(ttl=60)
def get_data():
    df = yf.download("GC=F", period="1d", interval="5m", progress=False)
    return df.dropna()

df = get_data()

if not df.empty:
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['ATR'] = (df['High'] - df['Low']).rolling(window=14).mean()
    
    current_price = df['Close'].iloc[-1]
    recent_high = df['High'].iloc[-20:-1].max()
    recent_low = df['Low'].iloc[-20:-1].min()
    last_candle = df.iloc[-1]
    
    signal = "WAIT"
    reason = ""
    
    if last_candle['High'] > recent_high and last_candle['Close'] < recent_high:
        signal = "SELL"
        reason = "Liquidity Sweep above previous high (Fakeout)."
        entry = current_price
        sl = last_candle['High'] + (last_candle['ATR'] * 0.5)
        tp = entry - ((sl - entry) * 2)
        
    elif last_candle['Low'] < recent_low and last_candle['Close'] > recent_low:
        signal = "BUY"
        reason = "Liquidity Sweep below previous low (Fakeout)."
        entry = current_price
        sl = last_candle['Low'] - (last_candle['ATR'] * 0.5)
        tp = entry + ((entry - sl) * 2)

    st.markdown("---")
    col1, col2 = st.columns(2)
    col1.metric("السعر الحالي (الذهب)", f"${current_price:.2f}")
    col2.metric("نسبة المخاطرة المقبولة", f"${risk_amount:.2f} (1%)")

    if signal != "WAIT":
        st.error(f"🚨 إشارة {signal} 🚨")
        st.write(f"**السبب:** {reason}")
        
        sl_distance = abs(entry - sl)
        lot_size = risk_amount / (sl_distance * 100) if sl_distance > 0 else 0.01
        lot_size = max(round(lot_size, 2), 0.01)
        
        st.markdown(f"""
        * **نقطة الدخول (Entry):** `{entry:.2f}`
        * **وقف الخسارة (SL):** `{sl:.2f}` ❌
        * **الهدف (TP):** `{tp:.2f}` 🎯
        * **حجم اللوت المقترح:** `{lot_size}`
        """)
    else:
        st.info("⏳ لا توجد إشارات سحب سيولة حالياً. جاري المراقبة...")
        
    st.line_chart(df['Close'].tail(50))
else:
    st.error("تعذر جلب البيانات. جرب إعادة التحديث.")
