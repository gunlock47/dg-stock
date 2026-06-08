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
    .metric-card {
        background: #1e1e2e;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .positive { color: #00c853; font-weight: bold; }
    .negative { color: #ff1744; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ── 주요 종목 딕셔너리 ───────────────────────────────────
KOREAN_STOCKS = {
    "삼성전자":   "005930.KS",
    "SK하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "현대차":     "005380.KS",
    "POSCO홀딩스": "005490.KS",
    "카카오":     "035720.KS",
    "네이버(NAVER)": "035420.KS",
    "삼성바이오로직스": "207940.KS",
    "기아":       "000270.KS",
    "셀트리온":   "068270.KS",
}

US_STOCKS = {
    "Apple":      "AAPL",
    "Microsoft":  "MSFT",
    "NVIDIA":     "NVDA",
    "Amazon":     "AMZN",
    "Alphabet(Google)": "GOOGL",
    "Meta":       "META",
    "Tesla":      "TSLA",
    "Berkshire Hathaway": "BRK-B",
    "JPMorgan Chase": "JPM",
    "ExxonMobil": "XOM",
}

PERIOD_MAP = {
    "1개월":  "1mo",
    "3개월":  "3mo",
    "6개월":  "6mo",
    "1년":    "1y",
    "2년":    "2y",
    "5년":    "5y",
}

# ── 데이터 로드 함수 ─────────────────────────────────────
@st.cache_data(ttl=600)
def load_stock_data(tickers: list, period: str) -> dict:
    """여러 종목의 OHLCV 데이터를 딕셔너리로 반환"""
    result = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
            if not df.empty:
                result[ticker] = df
        except Exception:
            pass
    return result

@st.cache_data(ttl=600)
def load_stock_info(ticker: str) -> dict:
    """종목 기본 정보 반환"""
    try:
        info = yf.Ticker(ticker).info
        return info
    except Exception:
        return {}

def calc_return(df: pd.DataFrame) -> float:
    """기간 수익률(%) 계산"""
    if df is None or df.empty:
        return None
    close = df["Close"].dropna()
    if len(close) < 2:
        return None
    return float((close.iloc[-1] / close.iloc[0] - 1) * 100)

def normalize(df: pd.DataFrame) -> pd.Series:
    """첫 날 = 100 기준 정규화"""
    close = df["Close"].dropna()
    return close / close.iloc[0] * 100

# ════════════════════════════════════════════════════════
#  메인 UI
# ════════════════════════════════════════════════════════
st.markdown('<p class="main-title">📈 한국 & 미국 주식 비교 분석</p>',
            unsafe_allow_html=True)
st.markdown('<p class="sub-title">yfinance 기반 실시간 수익률 & 차트 비교 플랫폼</p>',
            unsafe_allow_html=True)

# ── 사이드바 ─────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 분석 설정")

    period_label = st.selectbox("📅 분석 기간", list(PERIOD_MAP.keys()), index=3)
    period = PERIOD_MAP[period_label]

    st.markdown("---")
    st.subheader("🇰🇷 한국 종목 선택")
    selected_kr = st.multiselect(
        "한국 주식",
        list(KOREAN_STOCKS.keys()),
        default=["삼성전자", "SK하이닉스", "현대차"],
    )

    st.subheader("🇺🇸 미국 종목 선택")
    selected_us = st.multiselect(
        "미국 주식",
        list(US_STOCKS.keys()),
        default=["Apple", "Microsoft", "NVIDIA"],
    )

    st.markdown("---")
    chart_type = st.radio("📊 차트 유형", ["정규화 비교 (100 기준)", "개별 종가 차트"])
    show_volume = st.checkbox("📦 거래량 표시 (개별 차트)", value=False)

    st.markdown("---")
    st.caption("⏱ 데이터는 10분마다 자동 갱신됩니다.")
    if st.button("🔄 데이터 새로고침"):
        st.cache_data.clear()
        st.rerun()

# ── 종목 티커 매핑 ───────────────────────────────────────
kr_tickers = {name: KOREAN_STOCKS[name] for name in selected_kr}
us_tickers = {name: US_STOCKS[name]     for name in selected_us}
all_tickers = {**kr_tickers, **us_tickers}

if not all_tickers:
    st.warning("👆 사이드바에서 종목을 하나 이상 선택해주세요!")
    st.stop()

# ── 데이터 로드 ──────────────────────────────────────────
with st.spinner("📡 데이터를 불러오는 중..."):
    ticker_list = list(all_tickers.values())
    data = load_stock_data(ticker_list, period)

# ════════════════════════════════════════════════════════
#  섹션 1 : 수익률 요약 카드
# ════════════════════════════════════════════════════════
st.markdown("## 📊 기간 수익률 요약")
st.caption(f"기준 기간: **{period_label}**")

returns = {}
for name, ticker in all_tickers.items():
    if ticker in data:
        returns[name] = calc_return(data[ticker])

if returns:
    cols = st.columns(len(returns))
    for col, (name, ret) in zip(cols, returns.items()):
        flag = "🇰🇷" if name in kr_tickers else "🇺🇸"
        with col:
            if ret is not None:
                color = "positive" if ret >= 0 else "negative"
                sign  = "+" if ret >= 0 else ""
                st.metric(
                    label=f"{flag} {name}",
                    value=f"{sign}{ret:.2f}%",
                    delta=f"{sign}{ret:.2f}%",
                )
            else:
                st.metric(label=f"{flag} {name}", value="N/A")

# ── 수익률 막대그래프 ────────────────────────────────────
st.markdown("### 📉 수익률 비교 막대그래프")
ret_df = pd.DataFrame(
    [(n, r, "🇰🇷 한국" if n in kr_tickers else "🇺🇸 미국")
     for n, r in returns.items() if r is not None],
    columns=["종목", "수익률(%)", "시장"],
)

if not ret_df.empty:
    color_map = {"🇰🇷 한국": "#1f77b4", "🇺🇸 미국": "#ff7f0e"}
    fig_bar = px.bar(
        ret_df,
        x="종목", y="수익률(%)",
        color="시장",
        color_discrete_map=color_map,
        text="수익률(%)",
        title=f"{period_label} 수익률 비교",
        template="plotly_dark",
    )
    fig_bar.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
    fig_bar.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.4)
    fig_bar.update_layout(height=420, xaxis_tickangle=-20)
    st.plotly_chart(fig_bar, use_container_width=True)

# ════════════════════════════════════════════════════════
#  섹션 2 : 가격 추이 차트
# ════════════════════════════════════════════════════════
st.markdown("## 📈 가격 추이 차트")

if chart_type == "정규화 비교 (100 기준)":
    # ── 정규화 통합 차트 ─────────────────────────────────
    fig = go.Figure()
    colors = px.colors.qualitative.Plotly
    for i, (name, ticker) in enumerate(all_tickers.items()):
        if ticker not in data:
            continue
        norm = normalize(data[ticker])
        flag = "🇰🇷" if name in kr_tickers else "🇺🇸"
        dash  = "solid" if name in kr_tickers else "dash"
        fig.add_trace(go.Scatter(
            x=norm.index, y=norm.values,
            name=f"{flag} {name}",
            line=dict(width=2, dash=dash, color=colors[i % len(colors)]),
            hovertemplate=f"<b>{name}</b><br>날짜: %{{x|%Y-%m-%d}}<br>지수: %{{y:.1f}}<extra></extra>",
        ))
    fig.add_hline(y=100, line_dash="dot", line_color="gray", opacity=0.5)
    fig.update_layout(
        title=f"정규화 수익률 추이 (시작일 = 100, {period_label})",
        xaxis_title="날짜",
        yaxis_title="지수 (시작일 = 100)",
        template="plotly_dark",
        height=550,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    # ── 개별 종목 차트 ────────────────────────────────────
    tab_names = [f"{'🇰🇷' if n in kr_tickers else '🇺🇸'} {n}" for n in all_tickers]
    tabs = st.tabs(tab_names)

    for tab, (name, ticker) in zip(tabs, all_tickers.items()):
        with tab:
            if ticker not in data:
                st.warning(f"{name} 데이터를 불러올 수 없습니다.")
                continue

            df  = data[ticker]
            ret = calc_return(df)

            # 캔들스틱
            fig2 = go.Figure()
            fig2.add_trace(go.Candlestick(
                x=df.index,
                open=df["Open"].squeeze(),
                high=df["High"].squeeze(),
                close=df["Close"].squeeze(),
                low=df["Low"].squeeze(),
                name=name,
                increasing_line_color="#00c853",
                decreasing_line_color="#ff1744",
            ))
            # 20일 이동평균
            ma20 = df["Close"].rolling(20).mean()
            fig2.add_trace(go.Scatter(
                x=ma20.index, y=ma20.squeeze(),
                name="MA20", line=dict(color="orange", width=1.5, dash="dot"),
            ))

            sign = "+" if (ret or 0) >= 0 else ""
            fig2.update_layout(
                title=f"{name} ({ticker})  |  {period_label} 수익률: {sign}{ret:.2f}%" if ret else name,
                xaxis_title="날짜",
                yaxis_title="주가",
                template="plotly_dark",
                height=480,
                xaxis_rangeslider_visible=False,
            )
            st.plotly_chart(fig2, use_container_width=True)

            # 거래량 차트
            if show_volume and "Volume" in df.columns:
                vol = df["Volume"].squeeze()
                colors_vol = ["#00c853" if c >= o else "#ff1744"
                              for c, o in zip(df["Close"].squeeze(), df["Open"].squeeze())]
                fig_vol = go.Figure(go.Bar(
                    x=df.index, y=vol,
                    marker_color=colors_vol, name="거래량",
                ))
                fig_vol.update_layout(
                    title="거래량",
                    template="plotly_dark",
                    height=220,
                    margin=dict(t=40, b=20),
                )
                st.plotly_chart(fig_vol, use_container_width=True)

# ════════════════════════════════════════════════════════
#  섹션 3 : 상관관계 히트맵
# ════════════════════════════════════════════════════════
st.markdown("## 🔗 수익률 상관관계 히트맵")

close_dict = {}
for name, ticker in all_tickers.items():
    if ticker in data:
        s = data[ticker]["Close"].squeeze()
        s.name = name
        close_dict[name] = s

if len(close_dict) >= 2:
    close_df  = pd.DataFrame(close_dict).dropna()
    returns_df = close_df.pct_change().dropna()
    corr       = returns_df.corr()

    fig_heat = go.Figure(go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale="RdBu",
        zmin=-1, zmax=1,
        text=corr.round(2).values,
        texttemplate="%{text}",
        hovertemplate="X: %{x}<br>Y: %{y}<br>상관계수: %{z:.2f}<extra></extra>",
    ))
    fig_heat.update_layout(
        title="일간 수익률 상관관계 (1 = 완전 양의 상관, -1 = 완전 음의 상관)",
        template="plotly_dark",
        height=500,
    )
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("상관관계 히트맵은 2개 이상의 종목을 선택해야 표시됩니다.")

# ════════════════════════════════════════════════════════
#  섹션 4 : 종목 기본 정보
# ════════════════════════════════════════════════════════
st.markdown("## 🏢 종목 기본 정보")

info_cols = st.columns(min(len(all_tickers), 3))
for i, (name, ticker) in enumerate(all_tickers.items()):
    with info_cols[i % 3]:
        info = load_stock_info(ticker)
        flag = "🇰🇷" if name in kr_tickers else "🇺🇸"
        with st.expander(f"{flag} {name}", expanded=False):
            mktcap = info.get("marketCap")
            st.write(f"**섹터:** {info.get('sector', 'N/A')}")
            st.write(f"**산업:** {info.get('industry', 'N/A')}")
            st.write(f"**시가총액:** "
                     f"{'${:,.0f}억'.format(mktcap/1e8) if mktcap else 'N/A'}")
            st.write(f"**52주 최고:** {info.get('fiftyTwoWeekHigh', 'N/A')}")
            st.write(f"**52주 최저:** {info.get('fiftyTwoWeekLow',  'N/A')}")
            st.write(f"**PER:** {info.get('trailingPE', 'N/A')}")
            st.write(f"**배당수익률:** "
                     f"{'{:.2%}'.format(info.get('dividendYield')) if info.get('dividendYield') else 'N/A'}")

# ── 푸터 ─────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "📌 본 웹앱은 교육 목적으로 제작되었으며 투자 권유가 아닙니다. "
    "데이터 출처: Yahoo Finance (yfinance)"
)
