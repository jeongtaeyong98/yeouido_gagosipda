import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import pandas as pd
from deep_translator import GoogleTranslator

# 웹페이지 기본 설정
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
        diff = today - yesterday
        pct = (diff / yesterday) * 100 if yesterday != 0 else 0
        return today, diff, pct
    except Exception:
        return 0.0, 0.0, 0.0

@st.cache_data(ttl=300)
def get_chart_data(ticker, period="3mo"):
    try:
        data = yf.download(ticker, period=period, progress=False)
        if data.empty: return None
        return data['Close'].dropna() if 'Close' in data else data.dropna()
    except:
        return None

# ⭐️ 실시간 한글 번역 기능이 추가된 뉴스 크롤러
@st.cache_data(ttl=600) 
def get_news(keyword, is_global=False, limit=20):
    try:
        if is_global: 
            url = f"https://news.google.com/rss/search?q={urllib.parse.quote(keyword)}&hl=en-US&gl=US&ceid=US:en"
        else: 
            url = f"https://news.google.com/rss/search?q={urllib.parse.quote(keyword)}&hl=ko&gl=KR&ceid=KR:ko"
            
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        news_list = []
        translator = GoogleTranslator(source='auto', target='ko')
        
        for item in root.findall('.//item')[:limit]:
            title = item.find('title').text
            link = item.find('link').text
            
            # 글로벌 뉴스일 경우 한국어로 번역 실행
            if is_global:
                try:
                    title = translator.translate(title)
                except:
                    pass # 번역 에러 시 원문 유지
                    
            news_list.append((title, link))
        return news_list
    except Exception as e:
        return []

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
        chart_type = st.radio("차트 종류 선택", ["일봉 (최근 3개월)", "주봉 (최근 1년)", "월봉 (최근 5년)", "년봉 (전체)", "분봉 (오늘 5분 단위)"], horizontal=True, key=f"radio_{ticker_symbol}")
        
        end_date = datetime.datetime.today()
        if is_kr:
            if "분봉" in chart_type:
                df_chart = yf.Ticker(ticker_symbol).history(period="1d", interval="5m")
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
            st.markdown("**📈 주가 추이**")
            st.line_chart(df_chart['Close'])
            st.markdown("**📊 거래량**")
            st.bar_chart(df_chart['Volume'])
        else: st.warning("데이터가 없습니다.")
    except Exception as e: st.error(f"에러: {e}")

# 총 8개 탭으로 구조 재편성
tabs = st.tabs([
    "1️⃣ 핵심 지표", "2️⃣ 🇰🇷 한국 증시", "3️⃣ 🇰🇷 한국 뉴스", "4️⃣ 🇺🇸 미국 증시", 
    "5️⃣ 🌍 글로벌 뉴스", "6️⃣ 📅 🇰🇷 한국 일정", "7️⃣ 📅 🇺🇸 미국 일정", "8️⃣ 🌏 아시아 증시"
])

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
        if t == 0.0: st.metric(label="📊 한국 10년물 국채 금리", value="API 연동 필요", delta="-")
        else: st.metric(label="📊 한국 10년물 국채 금리", value=f"{t:,.2f}%", delta=f"{d:,.2f}%p ({p:+.2f}%)")

with tabs[1]:
    st.subheader("🇰🇷 한국 증시 개별 종목 검색")
    kr_input = st.text_input("종목명 또는 코드 입력 (예: SK하이닉스, 000660.KS)", "삼성전자")
    if kr_input:
        kr_ticker = KR_STOCKS.get(kr_input, kr_input)
        display_stock_detail(kr_ticker)

with tabs[2]:
    st.subheader("📰 오늘의 한국 경제 핵심 테마")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🏦 매크로 & 무역")
        for title, link in get_news("금리 환율 수출", is_global=False, limit=7): st.markdown(f"- [{title}]({link})")
    with col2:
        st.markdown("### 📈 증시 & 수급")
        for title, link in get_news("코스피 외국인 기관", is_global=False, limit=7): st.markdown(f"- [{title}]({link})")
    with col3:
        st.markdown("### 🚀 주도 산업 (AI·바이오)")
        for title, link in get_news("반도체 AI FDA", is_global=False, limit=7): st.markdown(f"- [{title}]({link})")

with tabs[3]:
    st.subheader("🇺🇸 미국 증시 개별 종목 검색")
    us_input = st.text_input("종목명 또는 티커 입력 (예: 테슬라, TSLA)", "애플")
    if us_input:
        us_ticker = US_STOCKS.get(us_input, us_input)
        display_stock_detail(us_ticker)

with tabs[4]:
    st.subheader("🌍 오늘의 글로벌 경제 핵심 테마 (한글 자동번역)")
    st.info("💡 미국 매체 원문 기사 제목을 실시간으로 한글로 번역하여 표출합니다.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 🏦 Fed & 경제 지표")
        for title, link in get_news("Fed FOMC CPI PCE", is_global=True, limit=7): st.markdown(f"- [{title}]({link})")
    with col2:
        st.markdown("### 📉 뉴욕 증시 & 국채")
        for title, link in get_news("Nasdaq S&P 500 Treasury", is_global=True, limit=7): st.markdown(f"- [{title}]({link})")
    with col3:
        st.markdown("### 💻 M7 & AI 반도체")
        for title, link in get_news("Magnificent 7 AI Semiconductor", is_global=True, limit=7): st.markdown(f"- [{title}]({link})")

# 💡 6번 탭: 한국 실적 & 경제지표 일정 (프레임워크)
with tabs[5]:
    st.subheader("📅 🇰🇷 한국 주요 기업 실적 및 경제지표 일정")
    st.warning("🚧 [데이터 한계] 실시간 컨센서스 및 매출/영업이익 상세 데이터는 유료 API(에프앤가이드 등)가 필요합니다. 아래는 데이터 연동을 위한 대시보드 UI 프레임워크입니다.")
    
    kr_schedule_data = {
        "날짜": ["10/29 (예시)", "10/30 (예시)", "10/31 (예시)", "11/01 (예시)"],
        "이벤트/기업명": ["삼성전자 3분기 실적", "한국은행 금통위 의사록", "SK하이닉스 실적발표", "10월 수출입동향 발표"],
        "매출액(예상)": ["79조 원", "-", "18조 원", "-"],
        "영업이익(예상)": ["9.1조 원", "-", "6.5조 원", "-"],
        "순이익(예상)": ["8.5조 원", "-", "5.2조 원", "-"],
        "컨센서스(Surprise/Shock)": ["Shock (-10.5%)", "-", "Surprise (+5.2%)", "-"],
        "중요도": ["⭐⭐⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐"]
    }
    kr_df = pd.DataFrame(kr_schedule_data)
    st.dataframe(kr_df, use_container_width=True, hide_index=True)

# 💡 7번 탭: 미국 실적 & 경제지표 일정 (프레임워크)
with tabs[6]:
    st.subheader("📅 🇺🇸 미국 주요 기업 실적 및 경제지표 일정")
    st.warning("🚧 [데이터 한계] 미국 M7 및 경제지표 상세 결과는 유료 API(인베스팅닷컴 등) 연동 후 표출 가능합니다. 아래는 UI 프레임워크입니다.")
    
    us_schedule_data = {
        "날짜(한국시간)": ["10/30 22:30 (예시)", "10/31 05:00 (예시)", "11/01 05:00 (예시)", "11/01 21:30 (예시)"],
        "이벤트/기업명": ["미국 3분기 GDP (예비치)", "Microsoft (MSFT) 실적", "Apple (AAPL) 실적", "미국 10월 비농업 고용지수"],
        "매출/수치(예상)": ["3.0%", "$64.5B", "$94.2B", "110K"],
        "이익/수치(실제)": ["발표 대기", "발표 대기", "발표 대기", "발표 대기"],
        "컨센서스 부합 여부": ["-", "-", "-", "-"],
        "중요도": ["⭐⭐⭐", "⭐⭐⭐", "⭐⭐⭐", "⭐⭐⭐"]
    }
    us_df = pd.DataFrame(us_schedule_data)
    st.dataframe(us_df, use_container_width=True, hide_index=True)

with tabs[7]:
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
