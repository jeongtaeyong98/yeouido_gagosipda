import streamlit as st
import yfinance as yf

# 웹페이지 기본 설정
st.set_page_config(page_title="여의도 가고싶다 대시보드", page_icon="📈", layout="wide")

st.title("📈 Yeouido Gagosipda - 매크로 & 증시 시황판")
st.markdown("일일 증시 시황판")
st.write("---")

# 자주 찾는 종목 이름-코드 맵핑
KR_STOCKS = {
    "삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "LG에너지솔루션": "373220.KS",
    "현대차": "005380.KS", "기아": "000270.KS", "KB금융": "105560.KS",
    "네이버": "035420.KS", "NAVER": "035420.KS", "카카오": "035720.KS", "셀트리온": "068270.KS"
}

US_STOCKS = {
    "애플": "AAPL", "Apple": "AAPL", "테슬라": "TSLA", "Tesla": "TSLA",
    "엔비디아": "NVDA", "Nvidia": "NVDA", "마이크로소프트": "MSFT", "Microsoft": "MSFT",
    "구글": "GOOGL", "Google": "GOOGL", "아마존": "AMZN", "Amazon": "AMZN", "메타": "META", "Meta": "META"
}

# (1) 핵심 지표 전일 대비 계산용 함수
@st.cache_data
def get_metric(ticker):
    try:
        data = yf.download(ticker, period="5d", progress=False)
        if data.empty or len(data) < 2:
            return 0.0, 0.0, 0.0
        
        close_data = data['Close'] if 'Close' in data else data
        today = float(close_data.iloc[-1].item() if hasattr(close_data.iloc[-1], 'item') else close_data.iloc[-1])
        yesterday = float(close_data.iloc[-2].item() if hasattr(close_data.iloc[-2], 'item') else close_data.iloc[-2])
        
        diff = today - yesterday
        pct = (diff / yesterday) * 100 if yesterday != 0 else 0
        return today, diff, pct
    except Exception:
        return 0.0, 0.0, 0.0

# (2) ⭐️ 만능 개별 종목 분석기 함수
def display_stock_detail(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        hist_5d = stock.history(period="5d")
        
        if hist_5d.empty or len(hist_5d) < 2:
            st.error("데이터를 충분히 불러오지 못했습니다. 종목 코드나 이름을 다시 확인해 주세요.")
            return
            
        today_close = float(hist_5d['Close'].iloc[-1])
        yesterday_close = float(hist_5d['Close'].iloc[-2])
        diff = today_close - yesterday_close
        pct = (diff / yesterday_close) * 100 if yesterday_close != 0 else 0
        vol = int(hist_5d['Volume'].iloc[-1])
        
        is_kr = ticker_symbol.endswith('.KS') or ticker_symbol.endswith('.KQ')
        
        col1, col2 = st.columns(2)
        with col1:
            if is_kr:
                st.metric("현재가", f"{today_close:,.0f}원", f"{diff:,.0f}원 ({pct:+.2f}%)")
            else:
                st.metric("현재가", f"${today_close:,.2f}", f"${diff:,.2f} ({pct:+.2f}%)")
        with col2:
            st.metric("당일 거래량", f"{vol:,.0f}주")
            
        st.write("---")
        
        # 💡 여기가 바뀐 부분! (일봉이 맨 앞으로 왔어)
        chart_type = st.radio(
            "차트 종류 선택", 
            ["일봉 (최근 3개월)", "주봉 (최근 1년)", "월봉 (최근 5년)", "년봉 (전체)", "분봉 (오늘 5분 단위)"], 
            horizontal=True, 
            key=f"radio_{ticker_symbol}" 
        )
        
        if "분봉" in chart_type:
            df_chart = stock.history(period="1d", interval="5m")
        elif "일봉" in chart_type:
            df_chart = stock.history(period="3mo", interval="1d")
        elif "주봉" in chart_type:
            df_chart = stock.history(period="1y", interval="1wk")
        elif "월봉" in chart_type:
            df_chart = stock.history(period="5y", interval="1mo")
        else:
            df_chart = stock.history(period="max", interval="3mo")
            
        if not df_chart.empty:
            st.markdown("**📈 주가 추이**")
            st.line_chart(df_chart['Close'])
            st.markdown("**📊 거래량**")
            st.bar_chart(df_chart['Volume'])
        else:
            st.warning("해당 기간의 차트 데이터가 없습니다.")
            
    except Exception as e:
        st.error(f"데이터 처리 중 에러가 발생했습니다: {e}")

# 6개의 탭(페이지) 구성
tabs = st.tabs(["1️⃣ 핵심 지표", "2️⃣ 🇰🇷 한국 증시", "3️⃣ 🇰🇷 한국 뉴스", "4️⃣ 🇺🇸 미국 증시", "5️⃣ 🌍 글로벌 뉴스", "6️⃣ 🌏 아시아 증시"])

with tabs[0]:
    st.subheader("글로벌 핵심 매크로 & 증시 지표")
    col1, col2, col3 = st.columns(3)
    with col1:
        t, d, p = get_metric('^GSPC')
        st.metric(label="🇺🇸 S&P 500", value=f"{t:,.2f}", delta=f"{d:,.2f} ({p:+.2f}%)")
        t, d, p = get_metric('KRW=X')
        st.metric(label="💵 원/달러 환율", value=f"{t:,.2f}원", delta=f"{d:,.2f}원 ({p:+.2f}%)")
    with col2:
        t, d, p = get_metric('^IXIC')
        st.metric(label="🇺🇸 NASDAQ", value=f"{t:,.2f}", delta=f"{d:,.2f} ({p:+.2f}%)")
        t, d, p = get_metric('^TNX')
        st.metric(label="📊 미국 10년물 국채 금리", value=f"{t:,.2f}%", delta=f"{d:,.2f}%p ({p:+.2f}%)")
    with col3:
        t, d, p = get_metric('CL=F')
        st.metric(label="🛢️ WTI 원유 가격", value=f"${t:,.2f}", delta=f"${d:,.2f} ({p:+.2f}%)")

with tabs[1]:
    st.subheader("🇰🇷 한국 증시 개별 종목 검색")
    kr_input = st.text_input("종목명 또는 코드 입력 (예: SK하이닉스, 000660.KS)", "삼성전자")
    if kr_input:
        kr_ticker = KR_STOCKS.get(kr_input, kr_input)
        display_stock_detail(kr_ticker)

with tabs[2]:
    st.subheader("📰 한국 거시경제, 기업, 산업 뉴스")
    st.warning("🚧 [업데이트 예정] 조만간 네이버 뉴스 API를 연결할 공간입니다.")

with tabs[3]:
    st.subheader("🇺🇸 미국 증시 개별 종목 검색")
    us_input = st.text_input("종목명 또는 티커 입력 (예: 테슬라, TSLA)", "애플")
    if us_input:
        us_ticker = US_STOCKS.get(us_input, us_input)
        display_stock_detail(us_ticker)

with tabs[4]:
    st.subheader("🌍 전 세계 거시경제, 기업, 산업 뉴스")
    st.warning("🚧 [업데이트 예정] 해외 뉴스 API를 연동할 공간입니다.")

with tabs[5]:
    st.subheader("🌏 주요 아시아 증시 지표")
    col1, col2, col3 = st.columns(3)
    with col1:
        t, d, p = get_metric("^N225")
        st.metric(label="🇯🇵 니케이 225 (일본)", value=f"{t:,.2f}", delta=f"{d:,.2f} ({p:+.2f}%)")
    with col2:
        t, d, p = get_metric("000001.SS")
        st.metric(label="🇨🇳 상해 종합 (중국)", value=f"{t:,.2f}", delta=f"{d:,.2f} ({p:+.2f}%)")
    with col3:
        t, d, p = get_metric("^TWII")
        st.metric(label="🇹🇼 가권 지수 (대만)", value=f"{t:,.2f}", delta=f"{d:,.2f} ({p:+.2f}%)")
