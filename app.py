import streamlit as st
import yfinance as yf

# 웹페이지 기본 설정
st.set_page_config(page_title="여의도 가고싶다 대시보드", page_icon="📈", layout="wide")

st.title("📈 Yeouido Gagosipda - 매크로 & 증시 시황판")
st.markdown("산업정보시스템공학과 & 경영학 인사이트가 담긴 나만의 일일 대시보드")
st.write("---")

# 야후 파이낸스 데이터 불러오기 함수
@st.cache_data
def load_data(ticker):
    data = yf.download(ticker, period="1mo")
    return data['Close'] if 'Close' in data else data

# 6개의 탭(페이지)으로 화면 완벽 분리
tabs = st.tabs([
    "1️⃣ 핵심 지표", 
    "2️⃣ 🇰🇷 한국 증시", 
    "3️⃣ 🇰🇷 한국 뉴스", 
    "4️⃣ 🇺🇸 미국 증시", 
    "5️⃣ 🌍 글로벌 뉴스", 
    "6️⃣ 🌏 아시아 증시"
])

# ==========================================
# 1페이지: 대표 지표들 (S&P500, 나스닥, 원유, 금리, 환율)
# ==========================================
with tabs[0]:
    st.subheader("글로벌 핵심 매크로 & 증시 지표")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🇺🇸 S&P 500")
        st.line_chart(load_data('^GSPC'))
        st.markdown("### 💵 원/달러 환율")
        st.line_chart(load_data('KRW=X'))

    with col2:
        st.markdown("### 🇺🇸 NASDAQ")
        st.line_chart(load_data('^IXIC'))
        st.markdown("### 📊 미국 10년물 국채 금리")
        st.line_chart(load_data('^TNX'))

    with col3:
        st.markdown("### 🛢️ WTI 원유 가격")
        st.line_chart(load_data('CL=F'))

# ==========================================
# 2페이지: 한국 증시 종목 탐색기
# ==========================================
with tabs[1]:
    st.subheader("🇰🇷 한국 증시 개별 종목 검색")
    st.info("💡 수많은 종목을 한 번에 띄우면 느려집니다. 원하는 종목 코드를 입력해 바로 확인하세요!")
    
    # 검색창 만들기 (기본값: 삼성전자)
    kr_search = st.text_input("한국 종목코드 입력 (코스피는 .KS, 코스닥은 .KQ)", "005930.KS")
    if kr_search:
        st.line_chart(load_data(kr_search))

# ==========================================
# 3페이지: 한국 경제/산업 뉴스 (틀 구축)
# ==========================================
with tabs[2]:
    st.subheader("📰 한국 거시경제, 기업, 산업 뉴스")
    st.warning("🚧 [업데이트 예정] 조만간 네이버 뉴스 API를 연결하여 '반도체', '금리', '증시' 관련 최신 뉴스가 자동 크롤링될 공간입니다.")

# ==========================================
# 4페이지: 미국 증시 종목 탐색기
# ==========================================
with tabs[3]:
    st.subheader("🇺🇸 미국 증시 개별 종목 검색")
    
    # 검색창 만들기 (기본값: 애플)
    us_search = st.text_input("미국 티커 입력 (예: AAPL, TSLA, NVDA)", "AAPL")
    if us_search:
        st.line_chart(load_data(us_search))

# ==========================================
# 5페이지: 글로벌 경제/산업 뉴스 (틀 구축)
# ==========================================
with tabs[4]:
    st.subheader("🌍 전 세계 거시경제, 기업, 산업 뉴스")
    st.warning("🚧 [업데이트 예정] 조만간 해외 뉴스 API를 연동하여 글로벌 시황 및 연준(Fed) 관련 주요 뉴스가 뜰 공간입니다.")

# ==========================================
# 6페이지: 아시아 주요 증시 (중국, 일본, 대만)
# ==========================================
with tabs[5]:
    st.subheader("🌏 주요 아시아 증시 지표")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🇯🇵 니케이 225 (일본)")
        st.line_chart(load_data("^N225"))
        
    with col2:
        st.markdown("### 🇨🇳 상해 종합 (중국)")
        st.line_chart(load_data("000001.SS"))
        
    with col3:
        st.markdown("### 🇹🇼 가권 지수 (대만)")
        st.line_chart(load_data("^TWII"))
