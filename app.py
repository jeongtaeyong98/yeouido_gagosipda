import streamlit as st
import yfinance as yf

# 웹페이지 기본 설정
st.set_page_config(page_title="여의도 가고싶다 대시보드", page_icon="📈", layout="wide")

st.title("📈 Yeouido Gagosipda - 매크로 & 증시 시황판")
st.markdown("산업정보시스템공학과 & 경영학 인사이트가 담긴 나만의 일일 대시보드")
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

# (1) 핵심 지표 전일 대비 계산용 함수 (nan 제거 기능 추가)
@st.cache_data
def get_metric(ticker):
    try:
        data = yf.download(ticker, period="5d", progress=False)
        if data.empty:
            return 0.0, 0.0, 0.0
        
        close_data = data['Close'] if 'Close' in data else data
        close_data = close_data.dropna() # 💡 핵심 해결책: nan(빈칸) 데이터 걸러내기
        
        if len(close_data) < 2:
            return 0.0, 0.0, 0.0
            
        today = float(close_data.iloc[-1].item() if hasattr(close_data.iloc[-1], 'item') else close_data.iloc[-1])
        yesterday = float(close_data.iloc[-2].item() if hasattr(close_data.iloc[-2], 'item') else close_data.iloc[-2])
        
        diff = today - yesterday
        pct = (diff / yesterday) * 100 if yesterday != 0 else 0
        return today, diff, pct
    except Exception:
        return 0.0, 0.0, 0.0

# (2) 미니 차트 데이터 불러오기 함수 (아시아 증시용)
@st.cache_data
def get_chart_data(ticker, period="3mo"):
    try:
        data = yf.download(ticker, period=period, progress=False)
        if data.empty: return None
        close_data = data['Close'] if 'Close' in data else data
        return close_data.dropna() # 💡 차트에서도 nan 제거
    except:
        return None

# (3) ⭐️ 만능 개별 종목 분석기 함수 (nan 제거 기능 추가)
def display_stock_detail(ticker_symbol):
    try:
        stock = yf.Ticker(ticker_symbol)
        hist_5d = stock.history(period="5d")
        
        if hist_5d.empty:
            st.error("데이터를 충분히 불러오지 못했습니다. 종목 코드나 이름을 다시 확인해 주세요.")
            return
            
        hist_5d = hist_5d.dropna(subset=['Close']) # 💡 개별 종목에서도 nan 제거
        
        if len(hist_5d) < 2:
            st.error("최근 거래일 데이터가 부족합니다.")
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
            
        df_chart = df_chart.dropna(subset=['Close'])
            
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

# ==========================================
# 1페이지: 핵심 지표
# ==========================================
with tabs[0]:
    st.subheader("글로벌 핵심 매크로 & 증시 지표")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        t, d, p = get_metric('^KS11')
        st.metric(label="🇰🇷 KOSPI", value=f"{t:,.2f}", delta=f"{d:,.2f} ({p:+.2f}%)")
        t, d, p = get_metric('CL=F')
        st.metric(label="🛢️ WTI 원유 가격", value=f"${t:,.2f}", delta=f"${d:,.2f} ({p:+.2f}%)")
        
    with col2:
        t, d, p = get_metric('^KQ11')
        st.metric(label="🇰🇷 KOSDAQ", value=f"{t:,.2f}", delta=f"{d:,.2f} ({p:+.2f}%)")
        t, d, p = get_metric('KRW=X')
        st.metric(label="💵 원/달러 환율", value=f"{t:,.2f}원", delta=f"{d:,.2f}원 ({p:+.2f}%)")

    with col3:
        t, d, p = get_metric('^GSPC')
        st.metric(label="🇺🇸 S&P 500", value=f"{t:,.2f}", delta=f"{d:,.2f} ({p:+.2f}%)")
        t, d, p = get_metric('^TNX')
        st.metric(label="📊 미국 10년물 국채 금리", value=f"{t:,.2f}%", delta=f"{d:,.2f}%p ({p:+.2f}%)")

    with col4:
        t, d, p = get_metric('^IXIC')
        st.metric(label="🇺🇸 NASDAQ", value=f"{t:,.2f}", delta=f"{d:,.2f} ({p:+.2f}%)")
        
        t, d, p = get_metric('KR10YT=RR') 
        if t == 0.0:
            st.metric(label="📊 한국 10년물 국채 금리", value="API 연동 필요", delta="-")
        else:
            st.metric(label="📊 한국 10년물 국채 금리", value=f"{t:,.2f}%", delta=f"{d:,.2f}%p ({p:+.2f}%)")

# ==========================================
# 2페이지: 한국 증시
# ==========================================
with tabs[1]:
    st.subheader("🇰🇷 한국 증시 개별 종목 검색")
    kr_input = st.text_input("종목명 또는 코드 입력 (예: SK하이닉스, 000660.KS)", "삼성전자")
    if kr_input:
        kr_ticker = KR_STOCKS.get(kr_input, kr_input)
        display_stock_detail(kr_ticker)

# ==========================================
# 3페이지: 한국 경제 뉴스
# ==========================================
with tabs[2]:
    st.subheader("📰 한국 거시경제, 기업, 산업 뉴스")
    st.warning("🚧 [업데이트 예정] 조만간 네이버 뉴스 API를 연결할 공간입니다.")

# ==========================================
# 4페이지: 미국 증시
# ==========================================
with tabs[3]:
    st.subheader("🇺🇸 미국 증시 개별 종목 검색")
    us_input = st.text_input("종목명 또는 티커 입력 (예: 테슬라, TSLA)", "애플")
    if us_input:
        us_ticker = US_STOCKS.get(us_input, us_input)
        display_stock_detail(us_ticker)

# ==========================================
# 5페이지: 글로벌 경제 뉴스
# ==========================================
with tabs[4]:
    st.subheader("🌍 전 세계 거시경제, 기업, 산업 뉴스")
    st.warning("🚧 [업데이트 예정] 해외 뉴스 API를 연동할 공간입니다.")

# ==========================================
# 6페이지: 아시아 증시
# ==========================================
with tabs[5]:
    st.subheader("🌏 주요 아시아 증시 지표 (최근 3개월 흐름)")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🇯🇵 니케이 225")
        t, d, p = get_metric("^N225")
        st.metric(label="일본 증시", value=f"{t:,.2f}", delta=f"{d:,.2f} ({p:+.2f}%)")
        chart_data = get_chart_data("^N225")
        if chart_data is not None: st.line_chart(chart_data)
        
    with col2:
        st.markdown("### 🇨🇳 상해 종합")
        t, d, p = get_metric("000001.SS")
        st.metric(label="중국 증시", value=f"{t:,.2f}", delta=f"{d:,.2f} ({p:+.2f}%)")
        chart_data = get_chart_data("000001.SS")
        if chart_data is not None: st.line_chart(chart_data)
        
    with col3:
        st.markdown("### 🇹🇼 가권 지수")
        t, d, p = get_metric("^TWII")
        st.metric(label="대만 증시", value=f"{t:,.2f}", delta=f"{d:,.2f} ({p:+.2f}%)")
        chart_data = get_chart_data("^TWII")
        if chart_data is not None: st.line_chart(chart_data)
