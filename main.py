yfinance
plotly
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="한국 & 미국 주식 비교 분석",
    page_icon="📈",
    layout="wide",
)

# ── 스타일 ───────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center;
        color: #888;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ── 주요 종목 딕셔너리 ───────────────────────────────────
KOREAN_STOCKS = {
    "삼성전자":       "005930.KS",
    "SK하이닉스":     "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "현대차":         "005380.KS",
    "POSCO홀딩스":    
