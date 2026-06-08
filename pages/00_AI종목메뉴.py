import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ── 페이지 설정 ──────────────────────────────────────────
st.set_page_config(
    page_title="AI 관련주 대시보드",
    page_icon="🤖",
    layout="wide",
)

# ── 스타일 ───────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        text-align: center;
        font-size: 2.8rem;
        font-weight: bold;
        background: linear-gradient(90deg, #7B2FFF, #00C9FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        text-align: center;
        color: #aaa;
        font-size: 1.05rem;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        margin-top: 1.5rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ── AI 관련 종목 딕셔너리 ────────────────────────────────
AI_STOCKS = {
    # 반도체 / 하드웨어
    "NVIDIA":            {"ticker": "NVDA",     "category": "⚙️ 반도체/HW", "desc": "AI GPU 시장 압도적 1위"},
    "AMD":               {"ticker": "AMD",      "category": "⚙️ 반도체/HW", "desc": "AI GPU·CPU 경쟁자"},
    "Intel":             {"ticker": "INTC",     "category": "⚙️ 반도체/HW", "desc": "AI 가속기 Gaudi 개발"},
    "TSMC":              {"ticker": "TSM",      "category": "⚙️ 반도체/HW", "desc": "AI 칩 핵심 파운드리"},
    "Broadcom":          {"ticker": "AVGO",     "category": "⚙️ 반도체/HW", "desc": "AI 네트워킹 칩 선두"},
    "삼성전자":           {"ticker": "005930.KS","category": "⚙️ 반도체/HW", "desc": "HBM·AI 메모리 공급"},
    "SK하이닉스":         {"ticker": "000660.KS","category": "⚙️ 반도체/HW", "desc": "HBM3E AI 메모리 1위"},

    # 클라우드 / 플랫폼
    "Microsoft":         {"ticker": "MSFT",     "category": "☁️ 클라우드", "desc": "OpenAI 파트너·Azure AI"},
    "Alphabet(Google)":  {"ticker": "GOOGL",    "category": "☁️ 클라우드", "desc": "Gemini·TPU·Google Cloud"},
    "Amazon":            {"ticker": "AMZN",     "category": "☁️ 클라우드", "desc": "AWS AI 서비스 최대"},
    "Meta":              {"ticker": "META",     "category": "☁️ 클라우드", "desc": "LLaMA·AI 인프라 투자"},
    "Oracle":            {"ticker": "ORCL",     "category": "☁️ 클라우드", "desc": "AI 클라우드 급성장"},

    # AI 소프트웨어
    "Palantir":          {"ticker": "PLTR",     "category": "🧠 AI 소프트웨어", "desc": "기업용 AI 플랫폼"},
    "Salesforce":        {"ticker": "CRM",      "category": "🧠 AI 소프트웨어", "desc": "AI CRM·Einstein"},
    "ServiceNow":        {"ticker": "NOW",      "category": "🧠 AI 소프트웨어", "desc": "AI 업무 자동화"},
    "C3.ai":             {"ticker": "AI",       "category": "🧠 AI 소프트웨어", "desc": "순수 AI 기업용 SaaS"},

    # 데이터센터 / 인프라
    "Dell Technologies": {"ticker": "DELL",     "category": "🏗️ 데이터센터", "desc": "AI 서버·인프라 공급"},
    "Super Micro":       {"ticker": "SMCI",     "category": "🏗️ 데이터센터", "desc": "AI 서버 급성장"},
    "Vertiv":            {"ticker": "VRT",      "category": "🏗️ 데이터센터", "desc": "AI 데이터센터 냉각"},
    "Eaton":             {"ticker": "ETN",      "category": "🏗️ 데이터센터", "desc": "데이터센터 전력 공급"},

    # 한국 AI 관련주
    "네이버(NAVER)":      {"ticker": "035420.KS","category": "🇰🇷 한국 AI",  "desc": "HyperCLOVA X LLM"},
    "카카오":             {"ticker": "035720.KS","category": "🇰🇷 한국 AI",  "desc": "카카오 AI 서비스"},
    "한미반도체":         {"ticker": "042700.KS","category": "🇰🇷 한국 AI",  "desc": "HBM 본딩 장비 독점"},
}

PERIOD_MAP = {
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "1년":   "1y",
    "2년":   "2y",
}

CATEGORIES = sorted(set(v["category"] for v in AI_STOCKS.values()))

# ── 데이터 로드 함수 ─────────────────────────────────────
@st.cache_data(ttl=600)
def load_data(tickers: list, period: str) -> dict:
    result = {}
    for ticker in tickers:
        try:
            df = yf.download(ticker, period=period,
                             progress=False, auto_adjust=True)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if not df.empty:
                result[ticker] = df
        except Exception:
            pass
    return result

@st.cache_data(ttl=600)
def load_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info
    except Exception:
        return {}

def calc_return(df: pd.DataFrame) -> float:
    if df is None or df.empty:
        return None
    c = df["Close"].dropna()
    if len(c) < 2:
        return None
    return float((c.iloc[-1] / c.iloc[0] - 1) * 100)

def normalize(df: pd.DataFrame) -> pd.Series:
    c = df["Close"].dropna()
    return c / c.iloc[0] * 100

# ════════════════════════════════════════════════════════
#  헤더
# ════════════════════════════════════════════════════════
st.markdown('<p class="main-title">🤖 AI 관련주 대시보드</p>',
            unsafe_allow_html=True)
st.markdown(
    '<p class="sub-title">'
    '반도체 · 클라우드 · AI 소프트웨어 · 데이터센터 · 한국 AI 종목 한눈에 비교'
    '</p>',
    unsafe_allow_html=True,
)

# ── 사이드바 ─────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")

    period_label = st.selectbox("📅 분석 기간",
                                list(PERIOD_MAP.keys()), index=2)
    period = PERIOD_MAP[period_label]

    st.markdown("---")
    st.subheader("🗂️ 카테고리 필터")
    selected_cats = st.multiselect(
        "카테고리 선택",
        CATEGORIES,
        default=CATEGORIES,
    )

    st.markdown("---")
    st.subheader("🔍 개별 종목 선택")
    filtered_names = [
        n for n, v in AI_STOCKS.items()
        if v["category"] in selected_cats
    ]
    selected_names = st.multiselect(
        "종목 선택",
        filtered_names,
        default=filtered_names[:10],
    )

    st.markdown("---")
    chart_type = st.radio(
        "📊 메인 차트 유형",
        ["정규화 비교 (100 기준)", "개별 캔들스틱"],
    )
    show_volume = st.checkbox("📦 거래량 표시", value=False)

    st.markdown("---")
    st.caption("⏱ 데이터 10분마다 자동 갱신")
    if st.button("🔄 새로고침"):
        st.cache_data.clear()
        st.rerun()

# ── 선택 종목 확인 ───────────────────────────────────────
if not selected_names:
    st.warning("👆 사이드바에서 종목을 하나 이상 선택해주세요!")
    st.stop()

selected_stocks = {n: AI_STOCKS[n] for n in selected_names}
ticker_map      = {n: v["ticker"] for n, v in selected_stocks.items()}

# ── 데이터 로드 ──────────────────────────────────────────
with st.spinner("📡 AI 관련주 데이터 수집 중..."):
    data = load_data(list(ticker_map.values()), period)

if not data:
    st.error("❌ 데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.")
    st.stop()

# ════════════════════════════════════════════════════════
#  섹션 1 : KPI 수익률 카드
# ════════════════════════════════════════════════════════
st.markdown("## 📊 기간 수익률 현황")
st.caption(f"기준 기간 : **{period_label}**")

returns = {}
for name, ticker in ticker_map.items():
    if ticker in data:
        returns[name] = calc_return(data[ticker])

# 수익률 순 정렬
sorted_returns = sorted(
    [(n, r) for n, r in returns.items() if r is not None],
    key=lambda x: x[1], reverse=True,
)

cols = st.columns(min(len(sorted_returns), 6))
for i, (name, ret) in enumerate(sorted_returns):
    with cols[i % 6]:
        sign  = "+" if ret >= 0 else ""
        cat   = selected_stocks[name]["category"].split()[0]
        st.metric(
            label=f"{cat} {name}",
            value=f"{sign}{ret:.1f}%",
            delta=f"{sign}{ret:.1f}%",
        )

# ════════════════════════════════════════════════════════
#  섹션 2 : 수익률 막대 + 산점도 (2열)
# ════════════════════════════════════════════════════════
st.markdown("## 📉 수익률 비교")
col_left, col_right = st.columns(2)

# ── 막대그래프 ───────────────────────────────────────────
with col_left:
    ret_df = pd.DataFrame(
        [
            {
                "종목": n,
                "수익률(%)": r,
                "카테고리": selected_stocks[n]["category"],
                "색상": "#00c853" if r >= 0 else "#ff1744",
            }
            for n, r in sorted_returns
        ]
    )
    fig_bar = px.bar(
        ret_df,
        x="수익률(%)", y="종목",
        color="카테고리",
        orientation="h",
        text="수익률(%)",
        title=f"{period_label} 수익률 랭킹",
        template="plotly_dark",
        height=500,
    )
    fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_bar.add_vline(x=0, line_dash="dash", line_color="white", opacity=0.4)
    fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig_bar, use_container_width=True)

# ── 카테고리별 평균 수익률 ───────────────────────────────
with col_right:
    cat_avg = (
        ret_df.groupby("카테고리")["수익률(%)"]
        .mean()
        .reset_index()
        .sort_values("수익률(%)", ascending=False)
    )
    fig_cat = px.bar(
        cat_avg,
        x="카테고리", y="수익률(%)",
        color="수익률(%)",
        color_continuous_scale="RdYlGn",
        text="수익률(%)",
        title=f"카테고리별 평균 수익률 ({period_label})",
        template="plotly_dark",
        height=500,
    )
    fig_cat.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_cat.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.4)
    fig_cat.update_layout(xaxis_tickangle=-20, coloraxis_showscale=False)
    st.plotly_chart(fig_cat, use_container_width=True)

# ════════════════════════════════════════════════════════
#  섹션 3 : 가격 추이 차트
# ════════════════════════════════════════════════════════
st.markdown("## 📈 가격 추이")

if chart_type == "정규화 비교 (100 기준)":
    colors = px.colors.qualitative.Plotly + px.colors.qualitative.Dark24
    fig_norm = go.Figure()

    for i, (name, ticker) in enumerate(ticker_map.items()):
        if ticker not in data:
            continue
        try:
            norm = normalize(data[ticker])
            cat  = selected_stocks[name]["category"].split()[0]
            fig_norm.add_trace(go.Scatter(
                x=norm.index,
                y=norm.values,
                name=f"{cat} {name}",
                line=dict(width=2, color=colors[i % len(colors)]),
                hovertemplate=(
                    f"<b>{name}</b><br>"
                    "날짜: %{x|%Y-%m-%d}<br>"
                    "지수: %{y:.1f}<extra></extra>"
                ),
            ))
        except Exception:
            pass

    fig_norm.add_hline(y=100, line_dash="dot",
                       line_color="gray", opacity=0.5)
    fig_norm.update_layout(
        title=f"정규화 수익률 추이 (시작일 = 100, {period_label})",
        xaxis_title="날짜",
        yaxis_title="지수",
        template="plotly_dark",
        height=580,
        hovermode="x unified",
        legend=dict(orientation="v", x=1.01, y=1),
    )
    st.plotly_chart(fig_norm, use_container_width=True)

else:
    # ── 개별 캔들스틱 탭 ────────────────────────────────
    tab_labels = [
        f"{selected_stocks[n]['category'].split()[0]} {n}"
        for n in selected_names
        if ticker_map[n] in data
    ]
    valid_names = [n for n in selected_names if ticker_map[n] in data]
    tabs = st.tabs(tab_labels)

    for tab, name in zip(tabs, valid_names):
        ticker = ticker_map[name]
        df     = data[ticker]
        ret    = calc_return(df)

        with tab:
            try:
                fig_c = go.Figure()
                fig_c.add_trace(go.Candlestick(
                    x=df.index,
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    name=name,
                    increasing_line_color="#00c853",
                    decreasing_line_color="#ff1744",
                ))
                # 이동평균선
                for window, color, dash in [
                    (20, "orange",  "dot"),
                    (60, "cyan",    "dash"),
                ]:
                    ma = df["Close"].rolling(window).mean()
                    fig_c.add_trace(go.Scatter(
                        x=ma.index, y=ma.values,
                        name=f"MA{window}",
                        line=dict(color=color, width=1.5, dash=dash),
                    ))

                sign  = "+" if (ret or 0) >= 0 else ""
                title = (
                    f"{name} ({ticker})  |  "
                    f"{period_label} 수익률: {sign}{ret:.2f}%"
                    if ret else name
                )
                fig_c.update_layout(
                    title=title,
                    template="plotly_dark",
                    height=500,
                    xaxis_rangeslider_visible=False,
                )
                st.plotly_chart(fig_c, use_container_width=True)

                # 거래량
                if show_volume and "Volume" in df.columns:
                    vol_colors = [
                        "#00c853" if c >= o else "#ff1744"
                        for c, o in zip(df["Close"], df["Open"])
                    ]
                    fig_v = go.Figure(go.Bar(
                        x=df.index, y=df["Volume"],
                        marker_color=vol_colors,
                        name="거래량",
                    ))
                    fig_v.update_layout(
                        title="거래량",
                        template="plotly_dark",
                        height=220,
                        margin=dict(t=40, b=20),
                    )
                    st.plotly_chart(fig_v, use_container_width=True)

            except Exception as e:
                st.error(f"❌ {name} 차트 오류: {e}")

# ════════════════════════════════════════════════════════
#  섹션 4 : 상관관계 히트맵
# ════════════════════════════════════════════════════════
st.markdown("## 🔗 수익률 상관관계 히트맵")

close_dict = {}
for name, ticker in ticker_map.items():
    if ticker in data:
        try:
            s = data[ticker]["Close"].squeeze()
            s.name = name
            close_dict[name] = s
        except Exception:
            pass

if len(close_dict) >= 2:
    corr = pd.DataFrame(close_dict).dropna().pct_change().dropna().corr()
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
        title="일간 수익률 상관관계",
        template="plotly_dark",
        height=550,
    )
    st.plotly_chart(fig_heat, use_container_width=True)
else:
    st.info("💡 2개 이상 종목을 선택하면 히트맵이 표시됩니다.")

# ════════════════════════════════════════════════════════
#  섹션 5 : 종목 카드 (기업 정보)
# ════════════════════════════════════════════════════════
st.markdown("## 🏢 종목 기업 정보")

card_cols = st.columns(3)
for i, (name, meta) in enumerate(selected_stocks.items()):
    ticker = meta["ticker"]
    info   = load_info(ticker)
    with card_cols[i % 3]:
        with st.expander(
            f"{meta['category'].split()[0]} **{name}**  —  {meta['desc']}",
            expanded=False,
        ):
            mktcap = info.get("marketCap")
            div    = info.get("dividendYield")
            st.write(f"**티커:** `{ticker}`")
            st.write(f"**섹터:** {info.get('sector',   'N/A')}")
            st.write(f"**산업:** {info.get('industry', 'N/A')}")
            st.write(
                f"**시가총액:** "
                f"{'${:,.0f}억'.format(mktcap/1e8) if mktcap else 'N/A'}"
            )
            st.write(f"**52주 최고:** {info.get('fiftyTwoWeekHigh', 'N/A')}")
            st.write(f"**52주 최저:** {info.get('fiftyTwoWeekLow',  'N/A')}")
            st.write(f"**PER:** {info.get('trailingPE', 'N/A')}")
            st.write(
                f"**배당수익률:** "
                f"{'{:.2%}'.format(div) if div else 'N/A'}"
            )

# ── 푸터 ─────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "📌 본 대시보드는 교육 목적으로 제작되었으며 투자 권유가 아닙니다. "
    "데이터 출처: Yahoo Finance (yfinance)"
)
