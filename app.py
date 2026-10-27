import streamlit as st
import yfinance as yf
import pandas as pd
import datetime

# 웹페이지 기본 설정
st.set_page_config(page_title="여의도 가고싶다 대시보드", page_icon="📈", layout="wide")

st.title("📈 Yeouido Gagosipda - 매크로 & 증시 대시보드")
st.markdown("산업정보시스템공학과 & 경영학 인사이트가 담긴 나만의 일일 시황판")

st.write("---")

st.subheader("미국 주요 증시 실시간 현황")

# 야후 파이낸스 데이터 불러오기 함수
@st.cache_data
def load_data(ticker):
    data = yf.download(ticker, period="1mo")
    return data

# 컬럼을 2개로 나누어서 배치
col1, col2 = st.columns(2)

with col1:
    st.markdown("### S&P 500")
    sp500 = load_data('^GSPC')
    st.line_chart(sp500['Close'])

with col2:
    st.markdown("### NASDAQ")
    nasdaq = load_data('^IXIC')
    st.line_chart(nasdaq['Close'])

st.info("💡 앞으로 이곳에 환율, 금리, 원자재 및 경제 뉴스 데이터가 추가될 예정입니다.")
