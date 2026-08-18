#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 3자 실시간 가치판단 & 투자·의사결정 센터
실시간 글로벌 매크로 지표(환율/금리/증시) + 실시간 개별 주가 + 오늘자 핫뉴스 100% 무료 연동
출처 및 산출근거 의무화 + 결단력 있는 판정 엔진 + 보안 비밀번호 (1909)
"""

import os
import sys
import time
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

# 로컬 환경 변수 로드
load_dotenv()

# Google GenAI 공식 SDK 임포트
try:
    from google import genai
    from google.genai import types
except ImportError:
    st.error("Google GenAI SDK가 설치되지 않았습니다. 'pip install google-genai'를 실행해주세요.")
    st.stop()

# 실시간 금융 데이터 (yfinance)
try:
    import yfinance as yf
except ImportError:
    yf = None


# Streamlit secrets 및 환경 변수 통합 조회 헬퍼
def get_api_key(key_name: str, fallback_key_name: str = None) -> str:
    env_val = os.getenv(key_name) or (os.getenv(fallback_key_name) if fallback_key_name else None)
    if env_val and "your_" not in env_val:
        return env_val.strip()
    try:
        if key_name in st.secrets:
            return str(st.secrets[key_name]).strip()
        if fallback_key_name and fallback_key_name in st.secrets:
            return str(st.secrets[fallback_key_name]).strip()
    except Exception:
        pass
    return ""


# 🌐 실시간 글로벌 매크로 핵심 지표 캐싱 수집기 (1분 캐싱)
@st.cache_data(ttl=60)
def fetch_global_macro_indicators():
    """환율, 코스피, S&P500, 나스닥, 미국 10년물 국채금리 실시간 데이터를 수집합니다."""
    macro_symbols = {
        "원/달러 환율": ("KRW=X", "원", "{:,.1f}"),
        "KOSPI": ("^KS11", "pt", "{:,.1f}"),
        "S&P 500": ("^GSPC", "pt", "{:,.1f}"),
        "NASDAQ": ("^IXIC", "pt", "{:,.1f}"),
        "미국 10년물 금리": ("^TNX", "%", "{:.2f}"),
    }
    data = {}
    if not yf:
        return data

    for name, (sym, unit, fmt) in macro_symbols.items():
        try:
            t = yf.Ticker(sym)
            h = t.history(period="5d")
            if not h.empty:
                curr = h['Close'].iloc[-1]
                prev = h['Close'].iloc[-2] if len(h) > 1 else curr
                chg = ((curr - prev) / prev) * 100
                val_str = fmt.format(curr) + unit
                delta_str = f"{chg:+.2f}%"
                data[name] = {"val": val_str, "delta": delta_str, "num": curr, "chg": chg}
        except Exception:
            pass
    return data


# 📰 실시간 최신 뉴스(Live News RSS) 무료 수집기
def fetch_live_news(query: str, max_items: int = 5) -> str:
    """구글 뉴스 RSS를 통해 오늘자 실시간 주요 언론사 뉴스 헤드라인을 수집합니다."""
    clean_q = re.sub(r'[^\w\s가-힣a-zA-Z0-9]', ' ', query)
    words = clean_q.split()[:4]
    search_term = " ".join(words) if words else query

    encoded_q = urllib.parse.quote(search_term)
    url = f"https://news.google.com/rss/search?q={encoded_q}&hl=ko&gl=KR&ceid=KR:ko"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            news_items = []
            for item in root.findall(".//item")[:max_items]:
                title = item.find("title").text if item.find("title") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                if title:
                    news_items.append(f"- [{pub_date[:16]}] {title}")

            if news_items:
                return "\n[📰 오늘자 실시간 주요 언론사 핫뉴스 (Live News Headlines)]\n" + "\n".join(news_items) + "\n"
    except Exception:
        pass
    return ""


# 📊 실시간 시장 주가(Live Stock Price) 자동 수집기
KNOWN_TICKERS = {
    "삼성전자": "005930.KS",
    "삼전": "005930.KS",
    "sk하이닉스": "000660.KS",
    "하이닉스": "000660.KS",
    "현대차": "005380.KS",
    "현대자동차": "005380.KS",
    "기아": "000270.KS",
    "lg에너지솔루션": "373220.KS",
    "카카오": "035720.KS",
    "네이버": "035420.KS",
    "naver": "035420.KS",
    "엔비디아": "NVDA",
    "nvda": "NVDA",
    "테슬라": "TSLA",
    "tsla": "TSLA",
    "애플": "AAPL",
    "aapl": "AAPL",
    "마이크로소프트": "MSFT",
    "msft": "MSFT",
    "알파벳": "GOOGL",
    "구글": "GOOGL",
    "비트코인": "BTC-USD",
    "btc": "BTC-USD",
    "이더리움": "ETH-USD",
    "eth": "ETH-USD",
}

def fetch_live_market_data(query: str) -> str:
    """질문에 포함된 종목명을 감지하여 실시간 실제 주가 데이터를 추출합니다."""
    if not yf:
        return ""
    
    query_lower = query.lower()
    detected_tickers = []
    
    for name, ticker in KNOWN_TICKERS.items():
        if name in query_lower and ticker not in detected_tickers:
            detected_tickers.append(ticker)
            
    if not detected_tickers:
        words = re.findall(r'\b[A-Z]{2,5}\b', query)
        for w in words:
            if w in ["NVDA", "TSLA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "QQQ", "SPY", "SCHD", "SOXX"]:
                if w not in detected_tickers:
                    detected_tickers.append(w)

    if not detected_tickers:
        return ""

    market_report = ["\n[⚡ 실시간 실제 금융 시장 시세 데이터 (Live Market Fact)]"]
    for sym in detected_tickers[:3]:
        try:
            t = yf.Ticker(sym)
            info = t.info
            hist = t.history(period="5d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                change_pct = ((current_price - prev_price) / prev_price) * 100
                
                currency = "KRW(원)" if sym.endswith(".KS") else "USD($)"
                price_str = f"{current_price:,.0f}원" if currency.startswith("KRW") else f"${current_price:,.2f}"
                
                high_52 = info.get("fiftyTwoWeekHigh", "N/A")
                low_52 = info.get("fiftyTwoWeekLow", "N/A")
                trailing_pe = info.get("trailingPE", "N/A")
                price_to_book = info.get("priceToBook", "N/A")
                
                line = f"- **{sym}**: 현재 실제 주가 = **{price_str}** (전일대비: {change_pct:+.2f}%)"
                if high_52 != "N/A" and low_52 != "N/A":
                    line += f" | 52주 최고: {high_52} / 최저: {low_52}"
                if trailing_pe != "N/A":
                    line += f" | PER: {trailing_pe:.1f}배" if isinstance(trailing_pe, (int, float)) else f" | PER: {trailing_pe}"
                if price_to_book != "N/A":
                    line += f" | PBR: {price_to_book:.2f}배" if isinstance(price_to_book, (int, float)) else f" | PBR: {price_to_book}"
                
                market_report.append(line)
        except Exception:
            pass

    if len(market_report) > 1:
        return "\n".join(market_report) + "\n"
    return ""


# 페이지 설정
st.set_page_config(
    page_title="AI 가치판단 & 투자·의사결정 센터",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 세련된 의사결정 센터 커스텀 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    .card-gemini {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #10B981;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    .card-claude {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #EF4444;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    .card-gpt {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #3B82F6;
        padding: 12px;
        border-radius: 6px;
        margin-bottom: 10px;
    }
    div[data-testid="stFormSubmitButton"] button {
        width: 100% !important;
        background-color: #0F172A !important;
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        padding: 0.75rem 1rem !important;
        border-radius: 6px !important;
        border: none !important;
    }
    div[data-testid="stFormSubmitButton"] button:hover {
        background-color: #1E293B !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""
if "current_ref_text" not in st.session_state:
    st.session_state.current_ref_text = ""
if "debate_history" not in st.session_state:
    st.session_state.debate_history = None


# 🔐 비밀번호 인증 게이트
AUTH_PASSWORD = "1909"

if not st.session_state.authenticated:
    st.markdown('<div class="main-header">🔒 AI 가치판단 센터 보안 인증</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">본 시스템은 개인화된 의사결정 지원 도구입니다. 접근 비밀번호를 입력해주세요.</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("auth_form"):
            password_input = st.text_input("🔑 접속 비밀번호", type="password", placeholder="비밀번호 4자리를 입력하세요")
            auth_submit = st.form_submit_button("🔓 의사결정실 입장하기")

            if auth_submit:
                if password_input == AUTH_PASSWORD:
                    st.session_state.authenticated = True
                    st.success("✔ 인증에 성공했습니다! 입장합니다...")
                    st.rerun()
                else:
                    st.error("❌ 비밀번호가 올바르지 않습니다.")
    st.stop()


# --- 인증 완료 후 메인 서비스 화면 ---

# 사이드바
with st.sidebar:
    st.header("🏢 의사결정 제어 콘솔")
    st.success("🟢 로그인 상태: **인증됨 (1909)**")
    
    st.markdown("---")
    st.header("🎯 분석 목적 (Domain)")
    domain_type = st.selectbox(
        "분야 선택:",
        [
            "📈 투자 & 자산 가치평가 (Live Stock & Macro)",
            "⚖️ 인생 & 일상 중대 의사결정 (Life & Career Decision)",
            "🔍 심층 리서치 & 팩트체크 (Live News Fact-check)"
        ],
        index=0
    )

    st.markdown("---")
    st.header("⚡ 판정 성향 설정")
    strictness = st.radio(
        "사회자 판정 강도:",
        ["🔥 결단력 극대화 (어설픈 타협 배제 / 단호한 판정)", "⚖️ 균형 잡힌 타협안 중심"],
        index=0
    )
    
    if st.button("🔒 로그아웃"):
        st.session_state.authenticated = False
        st.session_state.debate_history = None
        st.rerun()

    st.markdown("---")
    st.subheader("💡 시스템 특징")
    st.markdown("""
    - **🌐 글로벌 매크로 지표:** 환율·증시·금리 실시간 연동
    - **📊 실제 실시간 주가:** 야후 파이낸스 자동 주입
    - **📰 오늘자 핫뉴스:** 언론사 헤드라인 팩트체크
    - **100% 평생 무료:** 0원 유지
    """)


# 메인 헤더
st.markdown('<div class="main-header">⚖️ AI 가치판단 & 투자·의사결정 센터</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">실시간 매크로 지표 🌐 & 실제 시세 📊 & 당일 핫뉴스 📰 기반 | 3자 끝장 심의 및 결단 판정</div>', unsafe_allow_html=True)

# 🌐 실시간 글로벌 매크로 미니 대시보드
macro_data = fetch_global_macro_indicators()
if macro_data:
    cols = st.columns(len(macro_data))
    for col, (name, d) in zip(cols, macro_data.items()):
        col.metric(label=name, value=d["val"], delta=d["delta"])
    st.markdown("---")

# 3 에이전트 소개 카드
col_g, col_c, col_o = st.columns(3)
with col_g:
    st.markdown("""
    <div class="card-gemini">
        <b>📈 Bull Case & Upside Analyst (Gemini)</b><br>
        <small><b>역할:</b> 실시간 시세/뉴스/매크로 기반 상승 촉매, 내재 가치 및 긍정 시나리오 분석</small>
    </div>
    """, unsafe_allow_html=True)

with col_c:
    st.markdown("""
    <div class="card-claude">
        <b>🛡️ Bear Case & Downside Auditor (Claude)</b><br>
        <small><b>역할:</b> 최신 악재, 금리/환율 매크로 압박, 밸류 거품 및 최악의 하락 시나리오 검증</small>
    </div>
    """, unsafe_allow_html=True)

with col_o:
    st.markdown("""
    <div class="card-gpt">
        <b>⚖️ Decisive Chief Advisor (ChatGPT)</b><br>
        <small><b>역할:</b> 실시간 팩트 대조, 확신도 점수(0~100) 및 명확한 행동 결단(Go/No-Go) 제시</small>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 빠른 예시 선택 버튼
st.write("📌 **실시간 시세 & 뉴스 연동 테스트 안건:**")
b1, b2, b3, b4 = st.columns(4)
if b1.button("📊 삼성전자 vs SK하이닉스"):
    st.session_state.current_topic = "현재 실제 주가 및 최신 뉴스 기준: 삼성전자 vs SK하이닉스 추가 매수 및 밸류에이션 비교"
    st.rerun()
if b2.button("📈 엔비디아 vs 테슬라"):
    st.session_state.current_topic = "엔비디아(NVDA) vs 테슬라(TSLA) 실시간 시세 및 최신 뉴스 반영 투자 가치판단"
    st.rerun()
if b3.button("🏠 아파트 매수 vs 전세 유지"):
    st.session_state.current_topic = "현재 금리 및 거시 환경 기준: 서울/수도권 주택 매수 타이밍 vs 전세 유지"
    st.rerun()
if b4.button("💼 이직(스타트업) vs 대기업 잔류"):
    st.session_state.current_topic = "대기업 안정적 잔류 vs 성장하는 스타트업 스톡옵션 이직의 기회비용과 위험도"
    st.rerun()

# 폼(Form) 입력창
with st.form(key="debate_form", clear_on_submit=False):
    topic_input = st.text_input(
        "💬 분석하고 싶은 기업, 투자 안건, 또는 중대 의사결정 문제를 입력하세요:",
        value=st.session_state.current_topic,
        placeholder="예: 삼성전자 vs SK하이닉스 추가 매수 가치판단 / 엔비디아(NVDA) 고점 논란 분석",
    )
    
    with st.expander("📄 [선택] 내 개인 상황 / 평단가 메모 첨부 (작성 시 맞춤 전략 산출)"):
        ref_input = st.text_area(
            "본인 평단가, 투자 비중, 보유 현금, 목표 기간 등을 한 줄 적어주시면 훨씬 정밀한 핀셋 전략이 나옵니다:",
            value=st.session_state.current_ref_text,
            placeholder="예: 삼성전자 평단가 72,000원 비중 40% 보유 중 / 투자 기간 1년 목표...",
            height=80
        )

    submit_button = st.form_submit_button(f"🚀 실시간 팩트(매크로+주가+뉴스) 수집 & AI 3자 결단 시작 (Enter)")


# 지능형 무결점 LLM 호출 함수
def call_gemini_api(prompt: str, api_key: str, temperature: float = 0.7) -> str:
    client = genai.Client(api_key=api_key)
    candidate_models = [
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.7-flash",
        "gemini-flash-latest"
    ]
    last_err = None
    for model_name in candidate_models:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                    )
                )
                if response and response.text:
                    return response.text
            except Exception as e:
                last_err = e
                time.sleep(0.7)
    raise last_err if last_err else RuntimeError("API 응답 생성 실패")


# 가치판단 & 의사결정 엔진
def run_live_debate_engine(topic: str, ref_text: str, live_data: str, live_news: str, macro_summary: str, domain: str, strict_mode: bool, api_key: str, live_container):
    debate_logs = []
    
    data_context = ""
    if macro_summary.strip():
        data_context += f"\n{macro_summary}\n"
    if live_data.strip():
        data_context += f"\n{live_data}\n"
    if live_news.strip():
        data_context += f"\n{live_news}\n"
    if ref_text.strip():
        data_context += f"\n[사용자 개인 상황 및 첨부자료]:\n{ref_text}\n"
        
    source_instruction = """
[데이터 정확성 및 출처/근거 명시 지침]:
- 제공된 [실시간 글로벌 매크로 환경], [실시간 주가 시세], [오늘자 핫뉴스]를 반드시 100% 최우선 팩트 기준으로 인용하여 토론하십시오.
- 사용자 개인 상황(평단가, 비중)이 제공된 경우 이를 반드시 전략에 1:1로 반영하십시오.
- 모든 핵심 수치(타겟가, PER/PBR, 손절선)를 제시할 때는 '산출 근거 및 기준 지표'를 함께 명시하십시오.
"""

    strict_instruction = """
[판정관 지침 - 엄격성 극대화]:
- '모두의 말이 맞으니 적절히 균형을 맞추자'는 식의 안일한 중립이나 맹탕 절충안을 절대 내지 마십시오.
- 리스크 대비 기대수익(Risk/Reward)을 냉정하게 평가하여, 반드시 명확한 확신도 점수(0~100점)와 단호한 행동 결단(Strong Go / Hold / Strong No-Go)을 내리십시오.
- 치명적인 리스크가 보이면 가차 없이 '중단/철회(No-Go)'를 선언하십시오.
""" if strict_mode else ""

    # 1. 수석 조정관 개회
    with live_container:
        with st.chat_message("assistant", avatar="⚖️"):
            intro_msg = f"**[Decisive Chief Advisor]** 분석을 시작합니다.\n\n- **검토 안건:** `{topic}`\n- **분야:** `{domain.split('(')[0].strip()}`\n\n먼저 **Bull Case Analyst**, 실시간 매크로/시세 및 최신 뉴스 팩트에 기반하여 상승 모멘텀과 내재 가치 분석을 보고하십시오."
            st.markdown(intro_msg)
    debate_logs.append({
        "speaker": "⚖️ Decisive Chief Advisor (수석 조정관)",
        "role": "Moderator",
        "content": intro_msg
    })

    # 2. Bull Case (Gemini) 1차 긍정/상승 가치 분석
    prompt_pro_1 = f"""당신은 최고 투자/전략 분석가이자 '상승 및 가치 옹호관(Bull Case & Upside Analyst)'입니다.
안건: '{topic}'
분야: '{domain}'
{data_context}
{source_instruction}

제공된 실시간 매크로 환경, 주가, 최신 뉴스를 적극 반영하여, 본 안건을 긍정적으로 평가해야 하는 핵심 근거와 상승 잠재력을 논리정연하게 분석하십시오:
1. 실제 현재 가격/지표 대비 상승 여력 (Current Price vs Upside Target with Metrics)
2. 최신 뉴스 및 매크로 수혜 요인 기반 성장 촉매 (Key Catalysts & Growth Drivers)
3. 정량적/정성적 산출 근거 (Data & Valuation Rationale)

프로페셔널하고 명확한 비즈니스/투자 보고서 스타일(Markdown)로 작성하십시오."""

    with live_container:
        with st.chat_message("assistant", avatar="📈"):
            with st.spinner("📈 Bull Case Analyst가 실시간 시세 및 최신 뉴스 기반 상승 가치를 분석 중입니다..."):
                pro_1_res = call_gemini_api(prompt_pro_1, api_key, temperature=0.6)
            st.markdown(f"**[Bull Case & Upside Analyst / 기회 및 상승 가치 분석]**\n\n{pro_1_res}")
    debate_logs.append({
        "speaker": "📈 Bull Case Analyst (상승·기회 분석)",
        "role": "Proponent",
        "content": pro_1_res
    })

    # 3. Bear Case (Claude) 1차 하락/리스크 검증
    prompt_con_1 = f"""당신은 엄격한 리스크 감사관이자 '하락 및 위기 검증관(Bear Case & Downside Auditor)'입니다.
안건: '{topic}'
분야: '{domain}'
{data_context}
{source_instruction}
앞선 상승론자(Bull Case)의 보고 내용:
"{pro_1_res}"

제공된 매크로 환경(환율/금리), 실시간 주가와 최신 뉴스 이면에 있는 악재, 맹점, 숨겨진 비용 및 치명적인 하방 리스크를 날카롭게 파고드십시오:
1. 실제 현재 주가 기준 밸류에이션 거품 및 고평가 리스크 (Valuation & Reality Check)
2. 최신 뉴스/매크로에서 드러난 위기 요인 및 최악의 손실 시나리오 (Worst-case Scenario & Max Downside Floor)
3. 환율/금리 부담, 실적 둔화 등 구체적 위기 근거 (Downside Risk Factors)

객관적이고 뼈아픈 리스크 감사 보고서 스타일(Markdown)로 작성하십시오."""

    with live_container:
        with st.chat_message("assistant", avatar="🛡️"):
            with st.spinner("🛡️ Bear Case Auditor가 하방 리스크 및 함정을 검증 중입니다..."):
                con_1_res = call_gemini_api(prompt_con_1, api_key, temperature=0.7)
            st.markdown(f"**[Bear Case & Downside Auditor / 하락 리스크 및 함정 검증]**\n\n{con_1_res}")
    debate_logs.append({
        "speaker": "🛡️ Bear Case Auditor (하락·위기 검증)",
        "role": "Challenger",
        "content": con_1_res
    })

    # 4. Bull Case 2차 방어 및 리스크 완화책
    prompt_pro_2 = f"""당신은 Bull Case Analyst입니다.
안건: '{topic}'
{data_context}
감사팀(Bear Case)의 혹독한 비판:
"{con_1_res}"

지적된 하방 리스크를 방어하고, 리스크를 감수할 만한 '비대칭적 보상 비율(Asymmetric Risk/Reward)'과 '안전 마진(Margin of Safety)'을 제시하십시오:
1. 지적된 리스크에 대한 실질적 방어 대책 및 밸류에이션 바닥 지지선 (Valuation Floor Support)
2. 안전 마진 확보 방안 및 분할/단계적 매수 접근법 (Phased Strategy)
3. 근거 지표 기반의 기대수익비 우위 입증

설득력 있는 현실적 보완 보고서(Markdown)로 작성하십시오."""

    with live_container:
        with st.chat_message("assistant", avatar="📈"):
            with st.spinner("📈 Bull Case Analyst가 리스크 방어책 및 안전마진을 제시 중입니다..."):
                pro_2_res = call_gemini_api(prompt_pro_2, api_key, temperature=0.6)
            st.markdown(f"**[Bull Case Analyst / 리스크 방어 및 안전마진 제시]**\n\n{pro_2_res}")
    debate_logs.append({
        "speaker": "📈 Bull Case Analyst (방어 및 안전마진)",
        "role": "Proponent",
        "content": pro_2_res
    })

    # 5. Bear Case 2차 최종 쐐기 및 손절/중단 기준
    prompt_con_2 = f"""당신은 Bear Case Auditor입니다.
안건: '{topic}'
{data_context}
상승론자의 방어안:
"{pro_2_res}"

방어안에도 불구하고 여전히 남는 '구조적 잔여 리스크'와 반드시 설정해야 할 '손절/중단 기준(Exit Trigger / Stop-loss)'을 최종 보고하십시오:
1. 여전히 해결 불가능한 핵심 결함 (Unresolved Fatal Flaws)
2. 실제 가격 기준 즉각 손절/매도/철회해야 할 구체적 가격/조건 (Mandatory Stop-loss Triggers)
3. 잔여 위험도 최종 스코어링

단호하고 날카로운 최종 의견(Markdown)으로 작성하십시오."""

    with live_container:
        with st.chat_message("assistant", avatar="🛡️"):
            with st.spinner("🛡️ Bear Case Auditor가 손절 기준 및 잔여 리스크를 정리 중입니다..."):
                con_2_res = call_gemini_api(prompt_con_2, api_key, temperature=0.7)
            st.markdown(f"**[Bear Case Auditor / 필수 손절 기준 및 잔여 결함]**\n\n{con_2_res}")
    debate_logs.append({
        "speaker": "🛡️ Bear Case Auditor (손절 기준 & 잔여 결함)",
        "role": "Challenger",
        "content": con_2_res
    })

    # 6. Decisive Advisor 최종 결단 판정서
    prompt_final = f"""당신은 최고 수석 의사결정관이자 가치판단 총괄관(Decisive Chief Advisor)입니다.
안건: '{topic}'
분야: '{domain}'
{data_context}
{strict_instruction}

전체 공방 내역:
[상승론 1차]: {pro_1_res}
[하락론 1차]: {con_1_res}
[상승론 2차 방어]: {pro_2_res}
[하락론 2차 쐐기]: {con_2_res}

양측의 분석과 실시간 데이터(매크로+실제 시세+최신 뉴스+사용자 상황)를 종합하여, 사용자가 즉시 실행할 수 있는 [최종 가치판단 & 의사결정 권고 보고서 (Final Decision Report)]를 작성하십시오.

보고서 필수 구성:
1. 📋 **핵심 의사결정 요약 (Executive Decision Summary)**
2. 📊 **실제 시세 및 밸류에이션 비교표 (Actual Valuation Table)**: 현재 실제가, 목표가, 밸류에이션 바닥, R:R 비율
3. 🎯 **최종 결단 판정 (Final Verdict)**: [적극 추천(Strong Go) / 보류 및 조건부(Hold) / 강력 비추천(Strong No-Go)] 중 택 1
4. 🔢 **확신도 점수 (Confidence Score)**: 100점 만점 중 __점
5. 🛠️ **사용자 맞춤 실행 가이드 (Action Strategy)**: 사용자 평단가/비중에 맞춘 분할 매매 및 헤징
6. 🚨 **반드시 지켜야 할 손절/중단 기준 (Critical Stop-loss Rule)**
7. 📚 **핵심 지표 산출 근거 및 데이터 출처 (Data Sources & Rationale)**

최고의 통찰과 실전 투자/의사결정에 즉시 활용할 수 있는 명확한 전문가 리포트 형식(Markdown)으로 작성하십시오."""

    with live_container:
        with st.chat_message("assistant", avatar="⚖️"):
            with st.spinner("⚖️ Decisive Advisor가 확신도 점수와 최종 결단 판정서를 작성 중입니다..."):
                verdict_res = call_gemini_api(prompt_final, api_key, temperature=0.3)
            st.markdown(f"**[Final Decision Report / 최종 가치판단 및 결단 보고서]**\n\n{verdict_res}")
    debate_logs.append({
        "speaker": "⚖️ Decisive Chief Advisor (최종 결단 보고서)",
        "role": "Moderator",
        "content": verdict_res
    })

    return debate_logs, verdict_res, pro_1_res, con_1_res, pro_2_res, con_2_res


# 실행 처리
if submit_button:
    cur_g = get_api_key("GOOGLE_API_KEY", "GEMINI_API_KEY")

    if not cur_g:
        st.error("⚠️ Google Gemini API 키가 필요합니다. Secrets 설정을 확인해주세요.")
    elif not topic_input.strip():
        st.warning("⚠️ 분석할 안건이나 의사결정 주제를 입력해주세요!")
    else:
        st.session_state.current_topic = topic_input
        st.session_state.current_ref_text = ref_input
        is_strict = "결단력" in strictness
        
        # 1. 글로벌 매크로 요약
        macro_summary = "[🌐 실시간 글로벌 매크로 시장 환경]\n" + "\n".join([f"- {k}: {v['val']} ({v['delta']})" for k, v in macro_data.items()]) if macro_data else ""
        
        # 2. 실시간 실제 금융 시장 데이터 자동 조회
        live_market_data = fetch_live_market_data(topic_input)
        
        # 3. 오늘자 실시간 주요 언론사 뉴스 자동 조회
        live_news_data = fetch_live_news(topic_input)
        
        st.markdown("---")
        st.subheader(f"⚖️ 실시간 팩트체크 & 가치판단 심의: '{topic_input}'")
        
        if live_market_data:
            st.info(live_market_data)
        if live_news_data:
            with st.expander("📰 [실시간 수집된 오늘자 핫뉴스 헤드라인 확인]", expanded=False):
                st.markdown(live_news_data)
        
        live_box = st.container()
        
        try:
            debate_logs, final_verdict, pro1, con1, pro2, con2 = run_live_debate_engine(
                topic_input, ref_input, live_market_data, live_news_data, macro_summary, domain_type, is_strict, cur_g, live_box
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"decision_report_{timestamp}.md"
            
            full_md = f"""# ⚖️ AI 가치판단 & 투자·의사결정 보고서
- **검토 안건:** {topic_input}
- **분석 분야:** {domain_type}
- **일시:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{macro_summary}
{live_market_data}
{live_news_data}
- **참여 패널:** 📈 Bull Case (Gemini) | 🛡️ Bear Case (Claude) | ⚖️ Decisive Advisor (ChatGPT)

---

## 🏆 [최종 가치판단 및 행동 결단 권고안]
{final_verdict}

---

## 📋 [실시간 가치판단 심의 전말 (Full Dialogue)]

### 📈 1. 상승 및 기회 가치 분석 (Bull Case)
{pro1}

### 🛡️ 2. 하락 및 리스크 감사 (Bear Case)
{con1}

### 📈 3. 리스크 방어 및 안전마진 제시
{pro2}

### 🛡️ 4. 필수 손절 기준 및 잔여 결함
{con2}
"""
            with open(filename, "w", encoding="utf-8") as f:
                f.write(full_md)

            st.session_state.debate_history = {
                "topic": topic_input,
                "logs": debate_logs,
                "final_verdict": final_verdict,
                "full_md": full_md,
                "filename": filename
            }

            st.success(f"🎉 실시간 매크로+시세+뉴스 반영 및 최종 결단 보고서 작성이 완료되었습니다! (파일 저장: `{filename}`)")

        except Exception as e:
            st.error(f"❌ 분석 진행 중 오류 발생: {str(e)}")


# 영구 탭 렌더링
if st.session_state.debate_history:
    data = st.session_state.debate_history
    
    st.markdown("---")
    st.success(f"🎯 **심의 완료 안건:** {data['topic']} (파일 자동 저장: `{data['filename']}`)")

    tab_report, tab_chat, tab_raw = st.tabs([
        "🏆 최종 결단 보고서 (Decision Report)",
        "💬 실시간 심의 회의록 (Full Meeting Logs)",
        "💾 전체 보고서 다운로드 (.md)"
    ])

    with tab_report:
        st.markdown(data["final_verdict"])

    with tab_chat:
        st.markdown("### 🗣️ Bull Case vs Bear Case 실시간 공방 회의록")
        for log in data["logs"]:
            if "Advisor" in log["speaker"]:
                avatar = "⚖️"
            elif "Bull" in log["speaker"]:
                avatar = "📈"
            else:
                avatar = "🛡️"
                
            with st.chat_message(log["role"], avatar=avatar):
                st.markdown(f"**[{log['speaker']}]**\n\n{log['content']}")

    with tab_raw:
        st.markdown("### 📄 전체 통합 보고서 전문")
        st.code(data["full_md"], language="markdown")
        st.download_button(
            label="📥 전체 결단 보고서 (.md) 다운로드",
            data=data["full_md"],
            file_name=data["filename"],
            mime="text/markdown",
            type="primary"
        )
