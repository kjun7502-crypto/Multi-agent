#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 3자 실시간 가치판단 & 투자/의사결정 센터 (Ver 2.0)
자료 조사 · 투자 분석 · 인생 및 일상 의사결정 특화
100% 완전 무료 (0원) 가동 + 결단력 있는 판정 엔진 + 보안 비밀번호 (1909)
"""

import os
import sys
import time
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


# 페이지 설정
st.set_page_config(
    page_title="AI 가치판단 & 투자·의사결정 센터 2.0",
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
        margin-bottom: 1.5rem;
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
    st.header("🎯 분석 분야 (Domain)")
    domain_type = st.selectbox(
        "분석 목적 선택:",
        [
            "📈 투자 & 자산 가치평가 (Investment & Valuation)",
            "⚖️ 인생 & 일상 중대 의사결정 (Life & Career Decision)",
            "🔍 심층 리서치 & 팩트체크 (In-depth Research)"
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
    st.subheader("💡 Ver 2.0 특장점")
    st.markdown("""
    - **100% 평생 무료:** 유료 구독 없이 0원 무제한 가동
    - **맹탕 타협 방지:** 확실한 **확신도 점수(0~100) & Action 권고**
    - **참고 자료 연동:** 뉴스, 재무 수치, 메모를 함께 첨부 가능
    """)


# 메인 헤더
st.markdown('<div class="main-header">⚖️ AI 가치판단 & 투자·의사결정 센터 (Ver 2.0)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">상승·기회 분석 (Bull Case) ⚔️ 하락·리스크 검증 (Bear Case) ⚖️ 결단력 있는 최종 판정 (Executive Verdict)</div>', unsafe_allow_html=True)

# 3 에이전트 소개 카드
col_g, col_c, col_o = st.columns(3)
with col_g:
    st.markdown("""
    <div class="card-gemini">
        <b>📈 Bull Case & Upside Analyst (Gemini)</b><br>
        <small><b>역할:</b> 상승 동력, 내재 가치, 성장 잠재력 및 긍정적 시나리오 분석</small>
    </div>
    """, unsafe_allow_html=True)

with col_c:
    st.markdown("""
    <div class="card-claude">
        <b>🛡️ Bear Case & Downside Auditor (Claude)</b><br>
        <small><b>역할:</b> 하락 위험, 고평가 거품, 규제/구조적 결함 및 최악의 시나리오 검증</small>
    </div>
    """, unsafe_allow_html=True)

with col_o:
    st.markdown("""
    <div class="card-gpt">
        <b>⚖️ Decisive Chief Advisor (ChatGPT)</b><br>
        <small><b>역할:</b> 어설픈 타협 배제, 확신도 점수 및 명확한 행동 결단(Go / No-Go) 제시</small>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 빠른 예시 선택 버튼
st.write("📌 **자주 묻는 핵심 의사결정 예시:**")
b1, b2, b3, b4 = st.columns(4)
if b1.button("📈 엔비디아/AI 주식 추가 매수"):
    st.session_state.current_topic = "현재 시점에서 엔비디아(또는 AI 반도체) 추가 매수 vs 차익 실현 관망 가치판단"
    st.rerun()
if b2.button("🏠 아파트 매수 vs 전세 유지"):
    st.session_state.current_topic = "향후 3년간 서울/수도권 주택 매수 타이밍 vs 전세 유지 후 자산 운용"
    st.rerun()
if b3.button("💼 이직(스타트업) vs 대기업 잔류"):
    st.session_state.current_topic = "대기업 안정적 잔류 vs 성장하는 스타트업 스톡옵션 이직의 기회비용과 위험도"
    st.rerun()
if b4.button("🚗 하이브리드 vs 전기차 구매"):
    st.session_state.current_topic = "2026년 현시점 신차 구매 시: 하이브리드(HEV) vs 순수전기차(EV) 실사용 경제성 비교"
    st.rerun()

# 폼(Form) 입력창
with st.form(key="debate_form", clear_on_submit=False):
    topic_input = st.text_input(
        "💬 분석하고 싶은 안건, 투자 대상, 또는 중대 의사결정 문제를 입력하세요:",
        value=st.session_state.current_topic,
        placeholder="예: 미국 고배당 ETF(SCHD) 집중 투자 vs 나스닥 성장주(QQQ) 투자 / 사이드 프로젝트 창업 타당성",
    )
    
    with st.expander("📄 [선택] 참고 자료 / 기사 내용 / 수치 메모 첨부 (없으면 비워두세요)"):
        ref_input = st.text_area(
            "분석에 반영할 기사 본문, 기업 실적, 매수 가격, 개인 상황 등을 자유롭게 붙여넣으세요:",
            value=st.session_state.current_ref_text,
            placeholder="예: 현재 평단가 120달러, 투자 기간 3년 예상 / 기사 내용: 3분기 매출 전년비 20% 증가했으나 가이던스 둔화...",
            height=100
        )

    submit_button = st.form_submit_button(f"🚀 AI 3자 실시간 심층 분석 & 최종 결단 시작 (Enter)")


# 지능형 무결점 LLM 호출 함수 (503 방지 및 자동 모델 로테이션)
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


# Ver 2.0 가치판단 & 의사결정 엔진
def run_live_debate_v2(topic: str, ref_text: str, domain: str, strict_mode: bool, api_key: str, live_container):
    debate_logs = []
    
    ref_context = f"\n[사용자 첨부 참고자료]:\n{ref_text}\n" if ref_text.strip() else ""
    
    strict_instruction = """
[판정관 지침 - 엄격성 극대화]:
- '모두의 말이 맞으니 적절히 균형을 맞추자'는 식의 안일한 중립이나 맹탕 절충안을 절대 내지 마십시오.
- 리스크 대비 기대수익(Risk/Reward)을 냉정하게 평가하여, 반드시 명확한 확신도 점수(0~100점)와 단호한 행동 결단(Strong Go / Hold / Strong No-Go)을 내리십시오.
- 치명적인 리스크가 보이면 가차 없이 '중단/철회(No-Go)'를 선언하십시오.
""" if strict_mode else ""

    # 1. 수석 조정관 개회
    with live_container:
        with st.chat_message("assistant", avatar="⚖️"):
            intro_msg = f"**[Decisive Chief Advisor]** 분석을 시작합니다.\n\n- **검토 안건:** `{topic}`\n- **분야:** `{domain.split('(')[0].strip()}`\n\n먼저 **Bull Case Analyst**, 본 안건의 상승 모멘텀, 내재 가치 및 긍정적 잠재력에 대한 1차 심층 분석을 보고하십시오."
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
{ref_context}

본 안건을 긍정적으로 평가해야 하는 핵심 근거와 상승 잠재력을 논리정연하게 분석하십시오:
1. 핵심 성장 동력 및 가치 상승 요인 (Key Catalysts & Upside Drivers)
2. 기대 수익률 및 정량적/정성적 혜택 (Expected ROI & Strategic Value)
3. 낙관적 시나리오에서의 목표 가치 및 최상의 결과 (Best-case Scenario)

프로페셔널하고 명확한 비즈니스/투자 보고서 스타일(Markdown)로 작성하십시오."""

    with live_container:
        with st.chat_message("assistant", avatar="📈"):
            with st.spinner("📈 Bull Case Analyst가 상승 가치 및 기회 요인을 분석 중입니다..."):
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
{ref_context}
앞선 상승론자(Bull Case)의 보고 내용:
"{pro_1_res}"

상승론의 맹점, 과도한 낙관론, 숨겨진 비용 및 치명적인 하방 리스크를 날카롭게 파고드십시오:
1. 비현실적 전제 및 과대평가 거품 지적 (Valuation & Reality Check)
2. 발생 가능한 최악의 시나리오 및 최대 손실폭 (Worst-case Scenario & Max Downside)
3. 외부 매크로 위기, 규제 리스크 및 실행 장벽 (Macro & Structural Traps)

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
감사팀(Bear Case)의 혹독한 비판:
"{con_1_res}"

지적된 하방 리스크를 방어하고, 리스크를 감수할 만한 '비대칭적 보상 비율(Asymmetric Risk/Reward)'과 '안전 마진(Margin of Safety)'을 제시하십시오:
1. 지적된 리스크에 대한 실질적 방어 대책 (Risk Mitigation & Hedging)
2. 안전 마진 확보 방안 및 분할/단계적 접근법 (Phased Execution)
3. 리스크 대비 기대 효익의 우위 재입증

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
상승론자의 방어안:
"{pro_2_res}"

방어안에도 불구하고 여전히 남는 '구조적 잔여 리스크'와 반드시 설정해야 할 '손절/중단 기준(Exit Trigger / Stop-loss)'을 최종 보고하십시오:
1. 여전히 해결 불가능한 핵심 결함 (Unresolved Fatal Flaws)
2. 즉각 철수/매도/중단해야 할 명확한 트리거 (Mandatory Stop-loss Triggers)
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
{ref_context}
{strict_instruction}

전체 공방 내역:
[상승론 1차]: {pro_1_res}
[하락론 1차]: {con_1_res}
[상승론 2차 방어]: {pro_2_res}
[하락론 2차 쐐기]: {con_2_res}

양측의 분석을 종합하여, 사용자가 즉시 실행할 수 있는 [최종 가치판단 & 의사결정 권고 보고서 (Final Decision Report)]를 작성하십시오.

보고서 필수 구성:
1. 📋 핵심 의사결정 요약 (Executive Decision Summary)
2. ⚖️ 상승 기대효과(Upside) vs 하방 리스크(Downside) 대조 평가
3. 🎯 **최종 결단 판정 (Final Verdict)**: [적극 추천(Strong Go) / 보류 및 조건부(Hold) / 강력 비추천(Strong No-Go)] 중 택 1
4. 🔢 **확신도 점수 (Confidence Score)**: 100점 만점 중 __점
5. 🛠️ **실행 가이드 및 분할/헤징 전략 (Action Strategy)**
6. 🚨 **반드시 지켜야 할 손절/중단 기준 (Critical Stop-loss Rule)**

어설픈 미사여구를 배제하고, 최고의 통찰이 담긴 전문가 리포트 형식(Markdown)으로 작성하십시오."""

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
        
        st.markdown("---")
        st.subheader(f"⚖️ 실시간 가치판단 심의: '{topic_input}'")
        
        live_box = st.container()
        
        try:
            debate_logs, final_verdict, pro1, con1, pro2, con2 = run_live_debate_v2(
                topic_input, ref_input, domain_type, is_strict, cur_g, live_box
            )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"decision_report_v2_{timestamp}.md"
            
            full_md = f"""# ⚖️ AI 가치판단 & 투자·의사결정 보고서 (Ver 2.0)
- **검토 안건:** {topic_input}
- **분석 분야:** {domain_type}
- **일시:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
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

            st.success(f"🎉 가치판단 심의 및 최종 결단 보고서 작성이 완료되었습니다! (파일 저장: `{filename}`)")

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
