import streamlit as st
import yfinance as yf
import FinanceDataReader as fdr
import datetime
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import pandas as pd
import json
import requests
import time

st.set_page_config(page_title="TY Dashboard", page_icon="📈", layout="wide")

with st.sidebar:
    st.markdown("### 🔑 시스템 설정")
    api_key = st.text_input("Gemini API Key", type="password", help="발급받은 구글 Gemini API 키를 입력하세요.")
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

def generate_ai_desk_summary(prompt: str, key: str) -> tuple:
    # 에러 메시지 지시대로 신규 유저용 최신 모델(3.8-flash)로 완전 고정
    target_model = "gemini-3.8-flash"
    gen_url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(gen_url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                return text, target_model
                
            elif response.status_code == 503:
                if attempt < max_retries - 1:
                    time.sleep(2) # 서버 폭주 시 2초 대기 후 재시도
                    continue
                else:
                    raise Exception("구글 서버 트래픽 폭주(503). 잠시 후 다시 시도해주세요.")
                    
            else:
                raise Exception(f"생성 에러 ({response.status_code}): {response.text}")
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            raise Exception("API 응답 시간이 초과되었습니다.")
            
    raise Exception("시황 요약을 불러오는 데 실패했습니다.")

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
            elif "월봉" in chart_type: df_chart = fdr.DataReader(fdr_ticker, start=end_date - datetime.timedelta(days
