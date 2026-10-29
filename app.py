import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import pandas as pd
import json

st.set_page_config(page_title="TY Dashboard", page_icon="📈", layout="wide")

with st.sidebar:
    st.markdown("### 🔑 시스템 설정")
    api_key = st.text_input("Gemini API Key", type="password")
    st.markdown("---")
    st.markdown("### 📝 모닝 미팅 메모")
    if 'memo' not in st.session_state:
        st.session_state.memo = ""
    st.session_state.memo = st.text_area("오늘의 핵심 투자 아이디어", st.session_state.memo, height=300)
    if st.button("메모 저장"):
        st.success("메모가 임시 저장되었습니다.")

st.title("📈 TY_HTS - 매크로 & 증시 시황판")
st.markdown("일일 대시보드")
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

@st.cache_data(ttl=86400, show_spinner=False)
def get_krx_mapping():
    try:
        df = fdr.StockListing('KRX')
        return dict(zip(df['Name'], df['Code']))
    except:
        return {}

krx_mapping = get_krx_mapping()

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
            if data.empty: 
                return 0.0, 0.0, 0.0
            close_data = data['Close'] if 'Close' in data else data
            close_data = close_data.dropna()

        if len(close_data) < 2: 
            return 0.0, 0.0, 0.0
        today = float(close_data.iloc[-1].item() if hasattr(close_data.iloc[-1], 'item') else close_data.iloc[-1])
        yesterday = float(close_data.iloc[-2].item() if hasattr(close_data.iloc[-2], 'item') else close_data.iloc[-2])
        return today, today - yesterday, ((today - yesterday) / yesterday) * 100 if yesterday != 0 else 0
    except:
        return 0.0, 0.0, 0.0

@st.cache_data(ttl=600, show_spinner=False)
def get_latest_news(keyword, limit=7, period="1d"):
    try:
        search_query = f"{keyword} when:{period}"
        url = f"https://news.google.com/rss/search?q={urllib.parse.quote(search_query)}&hl=ko&gl=KR&ceid=KR:ko"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            root = ET.fromstring(response.read())
        return [(item.find('title').text, item.find('link').text) for item in root.findall('.//item')[:limit]]
    except:
        return []

def display_stock_detail(ticker_symbol):
    try:
        is_kr = ticker_symbol.endswith('.KS') or ticker_symbol.endswith('.KQ')
        if is_kr:
            fdr_ticker = ticker_symbol.replace('.KS', '').replace('.KQ', '')
            df_recent = fdr.DataReader(fdr_ticker)[-5:]
            if df_recent.empty or len(df_recent) < 2: 
                return st.error("해당 종목을 찾을 수 없습니다.")
            today_close = float(df_recent['Close'].iloc[-1])
            yesterday_close = float(df_recent['Close'].iloc[-2])
            vol = int(df_recent['Volume'].iloc[-1])
        else:
            stock = yf.Ticker(ticker_symbol)
            hist_5d = stock.history(period="5d").dropna(subset=['Close'])
            if hist_5d.empty or len(hist_5d) < 2: 
                return st.error("해당 티커를 찾을 수 없습니다.")
            today_close = float(hist_5d['Close'].iloc[-1])
            yesterday_close = float(hist_5d['Close'].iloc[-2])
            vol = int(hist_5d['Volume'].iloc[-1])

        diff = today_close - yesterday_close
        pct = (diff / yesterday_close) * 100 if yesterday_close != 0 else 0
        
        col1, col2 = st.columns(2)
        with col1:
            if is_kr: 
                st.metric("현재가", f"{today_close:,.0f}원", f"{diff:,.0f}원 ({pct:+.2f}%)")
            else: 
                st.metric("현재가", f"${today_close:,.2f}", f"${diff:,.2f} ({pct:+.2f}%)")
        with col2: 
            st.metric("당일 거래량", f"{vol:,.0f}주")
            
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
        else: 
            st.warning("해당 기간의 데이터가 없습니다.")
    except:
        st.error("종목 데이터를 불러오는 중 에러가 발생했습니다.")

tabs = st.tabs([
    "🤖 AI 매크로 데스크", "1️⃣ 핵심 지표", "2️⃣ 🇰🇷 한국 증시", "3️⃣ 🇰🇷 한국 뉴스", 
    "4️⃣ 🇺🇸 미국 증시", "5️⃣ 🌍 글로벌 뉴스", "6️⃣ 📅 🇰🇷 한국 일정", "7️⃣ 📅 🇺🇸 미국 일정", "8️⃣ 🌏 아시아 증시"
])

with tabs[0]:
    st.subheader("🤖 일일 시황 브리핑 & 인스타그램 피드 초안 생성기")
    
    if st.button("🚀 오늘의 매크로 분석 및 피드 초안 생성", type="primary"):
        if not api_key:
            st.error("좌측 사이드바에 Gemini API Key를 입력해주세요.")
        else:
            with st.status("🔍 데이터를 수집하고 분석하는 중입니다...", expanded=True) as status:
                try:
                    st.write("⏳ 1단계: 데이터 수집 중...")
                    k_t, k_d, k_p = get_metric('^KS11')
                    s_t, s_d, s_p = get_metric('^GSPC')
                    krw_t, krw_d, krw_p = get_metric('KRW=X')
                    st.write("✅ 1단계 완료!")
                    
                    st.write("⏳ 2단계: 뉴스 크롤링 중...")
                    kr_news = get_latest_news("금리 OR 환율 OR 코스피 OR 외국인", limit=3)
                    global_news = get_latest_news("뉴욕증시 OR 연준 OR 트럼프 OR 빅테크", limit=3)
                    st.write("✅ 2단계 완료!")
                    
                    st.write("⏳ 3단계: AI 서버 다이렉트 통신 중...")
                    news_text = "한국 이슈:\n" + "\n".join([n[0] for n in kr_news]) + "\n\n글로벌 이슈:\n" + "\n".join([n[0] for n in global_news])
                    metric_text = f"KOSPI: {k_t:,.2f} ({k_p:+.2f}%), S&P 500: {s_t:,.2f} ({s_p:+.2f}%), 원/달러 환율: {krw_t:,.2f}원"
                    
                    prompt = f"""
당신은 여의도 증권사 리서치센터의 수석 애널리스트이자 PB입니다.
오늘의 증시 지표와 최신 뉴스를 바탕으로 두 가지를 작성해주세요.

[데이터]
{metric_text}
[뉴스]
{news_text}

[양식]
1. 오늘의 매크로 & 시황 3줄 요약
2. 인스타그램 피드 텍스트 초안 (친근하게, 질문 유도, 필수 해시태그 #TY_HTS #증시시황 #매크로분석 #여의도입성)
"""
                    
                    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                    headers = {'Content-Type': 'application/json'}
                    data = {"contents": [{"parts": [{"text": prompt}]}]}
                    
                    req = urllib.request.Request(api_url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
                    
                    with urllib.request.urlopen(req, timeout=15) as response:
                        result_json = json.loads(response.read().decode('utf-8'))
                        ai_text = result_json['candidates'][0]['content']['parts'][0]['text']
                        
                    st.write("✅ 3단계 완료!")
                    status.update(label="🎉 분석 성공!", state="complete", expanded=False)
                    st.success("✅ AI 분석 완료!")
                    st.text_area("📋 생성된 피드 초안", ai_text, height=400)
                        
                except Exception as e:
                    status.update(label="❌ 에러 발생", state="error", expanded=True)
                    st.error(f"상세 에러 내용: {e}")

with tabs[1]:
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
        st.metric("📊 미국 10년물 금리", f"{t:,.2f}%", f"{d:,.2f}%p ({p:+.2
