import streamlit as st
import yfinance as yf
import pandas as pd

# 웹페이지 기본 설정
st.set_page_config(page_title="여의도 가고싶다 대시보드", page_icon="📈", layout="wide")

st.title("📈 Yeouido Gagosipda - 매크로 & 증시 대시보드")
st.markdown("산업정보시스템공학과 & 경영학 인사이트가 담긴 나만의 일일 시황판")
st.write("---")

# 야후 파이낸스 데이터 불러오기 함수
@st.cache_data
def load_data(ticker):
    data = yf.download(ticker, period="1mo")
    # 최신 yfinance 버전 대응을 위해 종가(Close)만 추출
    return data['Close'] if 'Close' in data else data

# 탭으로 화면 분리하기 (전문가 레이아웃)
tab1, tab2 = st.tabs(["🌎 글로벌 매크로 & 증시", "🇰🇷 한국 금융 지표 (API 연결 예정)"])

with tab1:
    st.subheader("1. 주요 증시 현황")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🇺🇸 S&P 500")
        sp500 = load_data('^GSPC')
        st.line_chart(sp500)

    with col2:
        st.markdown("### 🇺🇸 NASDAQ")
        nasdaq = load_data('^IXIC')
        st.line_chart(nasdaq)

    st.write("---")
    
    st.subheader("2. 핵심 매크로 지표")
    col3, col4, col5 = st.columns(3)

    with col3:
        st.markdown("### 💵 원/달러 환율")
        usdkrw = load_data('KRW=X')
        st.line_chart(usdkrw)

    with col4:
        st.markdown("### 📊 미국 10년물 국채 금리")
        tnx = load_data('^TNX')
        st.line_chart(tnx)

    with col5:
        st.markdown("### 🛢️ WTI 원유 가격")
        wti = load_data('CL=F')
        st.line_chart(wti)

with tab2:
    st.info("💡 이곳에는 조만간 한국은행(ECOS) API를 연결해 국내 기준금리, 물가지수 등의 데이터를 추가할 예정입니다.")
