import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import pandas as pd

st.set_page_config(page_title="여의도 가고싶다 대시보드", page_icon="📈", layout="wide")
st.title("📈 Yeouido Gagosipda - 매크로 & 증시 시황판")
st.markdown("산업정보시스템공학과 & 경영학 인사이트가 담긴 나만의 일일 대시보드")
st.write("---")

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

@st.cache_data(ttl=300)
def get_metric(ticker):
    try:
        if ticker == '^KS11':
            df = fdr.DataReader('KS11')
            close_data = df['Close'][-5:]
        elif ticker == '^KQ11':
            df = fdr.DataReader('KQ11')
            close_data = df['Close'][-5:]
        else:
            data = yf.download(ticker, period="5d", progress=False)
            if data.empty: return 0.0, 0.0, 0.0
            close_data = data['Close'] if 'Close' in data else data
            close_data = close_data.dropna()

        if len(close_data) < 2: return 0.0, 0.0, 0.0
        today = float(close_data.iloc[-1].item() if hasattr(close_data.iloc[-1], 'item') else close_data.iloc[-1])
        yesterday = float(close_data.iloc[-2].item() if hasattr(close_data.iloc[-2], 'item') else close_data.iloc[-2])
        return today, today - yesterday, ((today - yesterday) / yesterday) * 100 if yesterday != 0 else 0
    except: return 0.0, 0.0, 0.0

@st.cache_data(ttl=300)
def get_chart_data(ticker, period="3mo"):
    try:
        data = yf.download(ticker, period=period, progress=False)
        return data['Close'].dropna() if not data.empty and 'Close' in data else None
    except: return None

# 💡 검색 기간(period)을 유동적으로 설정할 수 있게 업그레이드! (기본값: 1d)
@st.cache_data(ttl=600, show_spinner=False)
def get_latest_news(keyword, limit=7, period="1d"):
    try:
        search_query = f"{keyword} when:{period}"
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(search_query)}&hl=ko&gl=KR&ceid=KR:ko"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            root = ET.fromstring(response.read())
        return [(item.find('title').text, item.find('link').text) for item in root.findall('.//item')[:limit]]
    except: return []

def display_stock_detail(ticker_symbol):
    try:
        is_kr = ticker_symbol.endswith('.KS') or ticker_symbol.endswith('.KQ')
        if is_kr:
            fdr_ticker = ticker_symbol.replace('.KS', '').replace('.KQ', '')
            df_recent = fdr.DataReader(fdr_ticker)[-5:]
            if df_recent.empty or len(df_recent) < 2: return st.error("데이터 오류")
            today_close = float(df_recent['Close'].iloc[-1])
            yesterday_close = float(df_recent['Close'].iloc[-2])
            vol = int(df_recent['Volume'].iloc[-1])
        else:
            stock = yf.Ticker(ticker_symbol)
            hist_5d = stock.history(period="5d").dropna(subset=['Close'])
            if hist_5d.empty or len(hist_5d) < 2: return st.error("데이터 오류")
            today_close = float(hist_5d['Close'].iloc[-1])
            yesterday_close = float(hist_5d['Close'].iloc[-2])
            vol = int(hist_5d['Volume'].iloc[-1])

        diff = today_close - yesterday_close
        pct = (diff / yesterday_close) * 100 if yesterday_close != 0 else 0
        
        col1, col2 = st.columns(2)
        with col1:
            if is_kr: st.metric("현재가", f"{today_close:,.0f}원", f"{diff:,.0f}원 ({pct:+.2f}%)")
            else: st.metric("현재가", f"${today_close:,.2f}", f"${diff:,.2f} ({pct:+.2f}%)")
        with col2: st.metric("당일 거래량", f"{vol:,.0f}주")
            
        st.write("---")
        chart_type = st.radio("차트 종류 선택", ["일봉", "주봉", "월봉", "년봉", "분봉"], horizontal=True, key=f"radio_{ticker_symbol}")
        
        end_date = datetime.datetime.today()
        if is_kr:
            if "분봉" in chart_type: df_chart = yf.Ticker(ticker_symbol).history(period="1d", interval="5m")
            elif "일봉" in chart_type: df_chart = fdr.DataReader(fdr_ticker, start=end_date - datetime.timedelta(days=90))
            elif "주봉" in chart_type: df_chart = fdr.DataReader(fdr_ticker, start=end_date - datetime.timedelta(days=365)).resample('W-FRI').agg({'Close':'last', 'Volume':'sum'})
            elif "월봉" in chart_type: df_chart = fdr.DataReader(fdr_ticker, start=end_date - datetime.timedelta(days=365*5)).resample('ME').agg({'Close':'last', 'Volume':'sum'})
            else: df_chart = fdr.DataReader(fdr_ticker).resample('ME').agg({'Close':'last', 'Volume':'sum'})
        else:
            stock = yf.Ticker(ticker_symbol)
            if "분봉" in chart_type: df_chart = stock.history(period="1d", interval="5m")
            elif "일봉" in chart_type: df_chart = stock.history(period="3mo", interval="1d")
            elif "주봉" in chart_type: df_chart = stock.history(period="1y", interval="1wk")
            elif "월봉" in chart_type: df_chart = stock.history(period="5y", interval="1mo")
            else: df_chart = stock.history(period="max", interval="3mo")
            
        df_chart = df_chart.dropna(subset=['Close'])
        if not df_chart.empty:
            st.line_chart(df_chart['Close'])
            st.bar_chart(df_chart['Volume'])
        else: st.warning("데이터가 없습니다.")
    except: st.error("에러 발생")

tabs = st.tabs([
    "1️⃣ 핵심 지표", "2️⃣ 🇰🇷 한국 증시", "3️⃣ 🇰🇷 한국 뉴스", "4️⃣ 🇺🇸 미국 증시", 
    "5️⃣ 🌍 글로벌 뉴스", "6️⃣ 📅 🇰🇷 한국 일정", "7️⃣ 📅 🇺🇸 미국 일정", "8️⃣ 🌏 아시아 증시"
])

with tabs[0]:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        t, d, p = get_metric('^KS11')
        st.metric("🇰🇷 KOSPI", f"{t:,.2f}", f"{d:,.2f} ({p:+.2f}%)")
        t, d, p = get_metric('CL=F')
        st.metric("🛢️ WTI 원유", f"${t:,.2f}", f"${d:,.2f} ({p:+.2f}%)")
    with col2:
        t, d, p = get_metric('^KQ11')
        st.metric("🇰🇷 KOSDAQ", f"{t:,.2f}", f"{d:,.2f} ({p:+.2f}%)")
        t, d, p = get_metric('KRW=X')
        st.metric("💵 원/달러", f"{t:,.2f}원", f"{d:,.2f}원 ({p:+.2f}%)")
    with col3:
        t, d, p = get_metric('^GSPC')
        st.metric("🇺🇸 S&P 500", f"{t:,.2f}", f"{d:,.2f} ({p:+.2f}%)")
        t, d, p = get_metric('^TNX')
        st.metric("📊 미국 10년물 금리", f"{t:,.2f}%", f"{d:,.2f}%p ({p:+.2f}%)")
    with col4:
        t, d, p = get_metric('^IXIC')
        st.metric("🇺🇸 NASDAQ", f"{t:,.2f}", f"{d:,.2f} ({p:+.2f}%)")
        t, d, p = get_metric('KR10YT=RR') 
        if t == 0.0: st.metric("📊 한국 10년물 금리", "API 연동 필요", "-")
        else: st.metric("📊 한국 10년물 금리", f"{t:,.2f}%", f"{d:,.2f}%p ({p:+.2f}%)")

with tabs[1]:
    kr_input = st.text_input("종목명/코드 입력 (예: SK하이닉스)", "삼성전자")
    if kr_input: display_stock_detail(KR_STOCKS.get(kr_input, kr_input))

with tabs[2]:
    st.subheader("📰 오늘의 한국 경제 핵심 테마 (최근 24시간)")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("### 🏦 매크로 & 무역")
        for title, link in get_latest_news("금리 OR 환율 OR 수출", limit=7, period="1d"): st.markdown(f"- [{title}]({link})")
    with col2:
        st.markdown("### 📈 증시 & 수급")
        for title, link in get_latest_news("코스피 OR 코스닥 OR 외국인순매수", limit=7, period="1d"): st.markdown(f"- [{title}]({link})")
    with col3:
        st.markdown("### 🚀 주도 산업 (AI·바이오)")
        for title, link in get_latest_news("AI반도체 OR 2차전지 OR 바이오 FDA", limit=7, period="1d"): st.markdown(f"- [{title}]({link})")
    with col4:
        st.markdown("### 🌎 글로벌 정치·외교")
        for title, link in get_latest_news("트럼프 OR 베센트 OR 케빈워시 OR 무역관세", limit=7, period="1d"): st.markdown(f"- [{title}]({link})")

with tabs[3]:
    us_input = st.text_input("종목명/티커 입력 (예: TSLA)", "애플")
    if us_input: display_stock_detail(US_STOCKS.get(us_input, us_input))

with tabs[4]:
    st.subheader("🌍 글로벌 경제 속보 (국내 주요 경제지 보도 기준)")
    st.info("💡 번역 딜레이 없이, 월가 및 로이터 통신의 주요 이슈를 다룬 국내 최신 기사를 즉시 표출합니다.")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🏦 Fed & 경제 지표")
        for title, link in get_latest_news("미국 연준 OR FOMC OR CPI OR 파월", limit=7, period="1d"): 
            st.markdown(f"- [{title}]({link})")
            
    with col2:
        st.markdown("### 📉 뉴욕 증시 & 국채")
        for title, link in get_latest_news("뉴욕증시 OR S&P500 OR 나스닥 OR 미 국채금리", limit=7, period="1d"): 
            st.markdown(f"- [{title}]({link})")
            
    with col3:
        st.markdown("### 💻 M7 & AI 반도체")
        for title, link in get_latest_news("엔비디아 OR 테슬라 OR 매그니피센트7 OR 빅테크", limit=7, period="1d"): 
            st.markdown(f"- [{title}]({link})")

# 💡 6번 탭: 한국 증시 일정 (최근 7일 기사 검색 허용)
with tabs[5]:
    st.subheader("📅 🇰🇷 한국 주요 기업 실적 및 경제지표 일정")
    st.info("💡 최근 1주일 내 보도된 한국 증시 주요 실적 발표 및 경제 일정 뉴스입니다.")
    for title, link in get_latest_news("증시 일정 OR 코스피 실적 발표 OR 금통위", limit=10, period="7d"):
        st.markdown(f"🔹 [{title}]({link})")

# 💡 7번 탭: 네가 제안한 미국 핵심 키워드 적용 (최근 7일 기사 검색 허용)
with tabs[6]:
    st.subheader("📅 🇺🇸 미국 주요 기업 실적 및 경제지표 일정")
    st.info("💡 최근 1주일 내 보도된 미국 M7 실적 및 주요 매크로 지표 일정 뉴스입니다.")
    for title, link in get_latest_news("미국 증시 일정 OR 실적 OR FOMC OR CPI OR PPI OR PCE", limit=10, period="7d"):
        st.markdown(f"🔹 [{title}]({link})")

with tabs[7]:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🇯🇵 니케이 225")
        t, d, p = get_metric("^N225")
        st.metric("일본 증시", f"{t:,.2f}", f"{d:,.2f} ({p:+.2f}%)")
    with col2:
        st.markdown("### 🇨🇳 상해 종합")
        t, d, p = get_metric("000001.SS")
        st.metric("중국 증시", f"{t:,.2f}", f"{d:,.2f} ({p:+.2f}%)")
    with col3:
        st.markdown("### 🇹🇼 가권 지수")
        t, d, p = get_metric("^TWII")
        st.metric("대만 증시", f"{t:,.2f}", f"{d:,.2f} ({p:+.2f}%)")
