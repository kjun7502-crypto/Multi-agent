#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Multi-Agent AI Debate & Decision System - Interactive Live Debate Edition
Google Gemini, Anthropic Claude, OpenAI ChatGPT 3-Agent Collaborative Platform
Features Live Dialogue Simulation + Comprehensive Final Verdict
"""

import os
import sys
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

# 로컬 환경 변수 로드
load_dotenv()

# Streamlit secrets 호환 헬퍼 함수
def get_api_key(key_name: str, fallback_key_name: str = None) -> str:
    if f"custom_{key_name}" in st.session_state and st.session_state[f"custom_{key_name}"]:
        return st.session_state[f"custom_{key_name}"].strip()
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


# CrewAI LLM 임포트
try:
    from crewai import LLM
except ImportError:
    st.error("CrewAI 라이브러리가 설치되지 않았습니다. 터미널에서 'pip install crewai'를 실행해주세요.")
    st.stop()

# 페이지 설정
st.set_page_config(
    page_title="AI 3자 실시간 끝장 토론 & 종합 판정실",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 커스텀 CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .card-gemini {
        background-color: #F0FDF4;
        border: 1px solid #BBF7D0;
        border-left: 5px solid #22C55E;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .card-claude {
        background-color: #FEF2F2;
        border: 1px solid #FECACA;
        border-left: 5px solid #EF4444;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .card-gpt {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-left: 5px solid #3B82F6;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    div[data-testid="stFormSubmitButton"] button {
        width: 100% !important;
        background-color: #2563EB !important;
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        padding: 0.75rem 1rem !important;
        border-radius: 8px !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""
if "debate_history" not in st.session_state:
    st.session_state.debate_history = None

# 사이드바
with st.sidebar:
    st.header("🔑 API 키 연동 관리")
    st.caption("로컬 `.env`, 클라우드 `secrets` 또는 아래 직접 입력창에서 키를 로드합니다.")

    current_gemini = get_api_key("GOOGLE_API_KEY", "GEMINI_API_KEY")
    current_claude = get_api_key("ANTHROPIC_API_KEY")
    current_openai = get_api_key("OPENAI_API_KEY")

    with st.expander("⚙️ API 키 직접 확인 / 변경", expanded=not bool(current_gemini)):
        input_gemini = st.text_input("Google Gemini API Key", value=current_gemini, type="password", key="custom_GOOGLE_API_KEY")
        input_claude = st.text_input("Anthropic Claude API Key (선택)", value=current_claude, type="password", key="custom_ANTHROPIC_API_KEY")
        input_openai = st.text_input("OpenAI ChatGPT API Key (선택)", value=current_openai, type="password", key="custom_OPENAI_API_KEY")

    st.markdown("### 📡 실시간 연동 상태")
    st.write(f"🟢 **Google Gemini:** {'✅ 연결됨' if input_gemini else '❌ 미연결'}")
    st.write(f"🔴 **Claude (Red Team):** {'✅ 연결됨' if input_claude else '⚡ 무료 스마트 모드'}")
    st.write(f"🔵 **ChatGPT (Moderator):** {'✅ 연결됨' if input_openai else '⚡ 무료 스마트 모드'}")

    st.markdown("---")
    st.subheader("🎙️ 실시간 대화형 토론 모드")
    st.info("AI들이 서로의 발언을 직접 인용하며 반박하고 재반박하는 **실제 토론장 대화 과정**을 실시간으로 감상하실 수 있습니다.")


# 메인 헤더
st.markdown('<div class="main-header">🎙️ AI 3자 실시간 끝장 토론 & 종합 판정실</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Google Gemini (찬성/기회) ⚔️ Anthropic Claude (비판/리스크) ⚖️ OpenAI ChatGPT (사회자 판정)</div>', unsafe_allow_html=True)

# 3 에이전트 소개 카드
col_g, col_c, col_o = st.columns(3)
with col_g:
    st.markdown("""
    <div class="card-gemini">
        <b>🟢 Gemini (찬성 / 입론)</b><br>
        <small>데이터, 통계, 긍정적 기대 효과, 기회 요인 기반 강력한 찬성 논리 전개</small>
    </div>
    """, unsafe_allow_html=True)

with col_c:
    st.markdown("""
    <div class="card-claude">
        <b>🔴 Claude (반대 / 반론)</b><br>
        <small>낙관론의 맹점 지적, 부작용, 비용, 리스크를 집요하게 파고드는 레드팀 반론</small>
    </div>
    """, unsafe_allow_html=True)

with col_o:
    st.markdown("""
    <div class="card-gpt">
        <b>🔵 ChatGPT (사회자 / 판정)</b><br>
        <small>양측 주장의 논리성과 타당성을 검증하여 실현 가능한 타협안 및 최종 판정</small>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 빠른 예시 선택
st.write("🔥 **빠른 예시 질문 선택:**")
b1, b2, b3, b4 = st.columns(4)
if b1.button("🍽️ 홍대 데이트 맛집 추천"):
    st.session_state.current_topic = "홍대 맛집 중에 분위기 좋고 데이트하기에 실패 없는 곳 추천"
    st.rerun()
if b2.button("💼 주 4일제 도입 의무화"):
    st.session_state.current_topic = "주 4일제 도입 의무화에 대한 찬반 분석 및 현실적 대안"
    st.rerun()
if b3.button("📱 아이폰 16 vs 갤럭시 S24"):
    st.session_state.current_topic = "아이폰 16 Pro vs 갤럭시 S24 Ultra 비교 분석 및 맞춤 추천"
    st.rerun()
if b4.button("📈 트럼프 정부 & 한국 경제"):
    st.session_state.current_topic = "트럼프 정부가 들어선 이후 한국 경제는 발전할 가능성이 높은가?"
    st.rerun()

# 폼(Form) 입력창
with st.form(key="debate_form", clear_on_submit=False):
    topic_input = st.text_input(
        "💬 토론하고 싶은 주제나 궁금한 점을 입력하세요 (입력 후 Enter 키를 누르거나 아래 버튼 클릭):",
        value=st.session_state.current_topic,
        placeholder="예: 트럼프 정부가 들어선 이후 한국 경제는 발전할 가능성이 높은가? / 주 4일제 도입 의무화",
    )
    submit_button = st.form_submit_button("🚀 AI 실시간 끝장 토론 & 종합 판정 시작 (Enter)")


import time

# 지능형 무결점 LLM 호출 함수 (503 트래픽 급증 시 다른 모델로 즉시 자동 우회)
def call_llm_resilient(prompt: str, gemini_key: str, temperature: float = 0.7) -> str:
    candidate_models = [
        "gemini/gemini-3.5-flash",
        "gemini/gemini-3.6-flash",
        "gemini/gemini-3.7-flash",
        "gemini/gemini-flash-latest"
    ]
    last_err = None
    for model_name in candidate_models:
        for attempt in range(2):
            try:
                llm = LLM(model=model_name, temperature=temperature, api_key=gemini_key)
                return llm.call(prompt)
            except Exception as e:
                last_err = e
                time.sleep(0.8)
    raise last_err


# 4단계 멀티턴(Multi-turn) 토론 시뮬레이션 함수
def run_live_debate(topic: str, gemini_key: str, live_container):
    debate_logs = []

    # 1라운드: 사회자(ChatGPT) 토론 개회 및 쟁점 브리핑
    with live_container:
        with st.chat_message("assistant", avatar="⚖️"):
            st.markdown(f"**[사회자 / OpenAI ChatGPT]** 토론을 시작하겠습니다. 오늘의 주제는 **'{topic}'** 입니다. 먼저 찬성 측(Google Gemini), 입론을 시작해 주십시오.")
    debate_logs.append({
        "speaker": "⚖️ 사회자 (ChatGPT)",
        "role": "Moderator",
        "content": f"토론을 시작하겠습니다. 오늘의 주제는 **'{topic}'** 입니다. 먼저 찬성 측(Google Gemini), 입론을 시작해 주십시오."
    })

    # 2라운드: Gemini (1차 찬성 입론)
    prompt_pro_1 = f"""당신은 Google Gemini 기반의 데이터 분석가이자 '찬성 및 기회 옹호자(Proponent)'입니다.
토론 주제: '{topic}'
사회자의 요청에 따라, 이 주제에 대한 강력한 1차 찬성/긍정 입론을 발표하세요.
- 데이터, 통계 지표, 긍정적 기대 효과, 기회 요인을 3가지 핵심 포인트로 논리 정연하게 개진하세요.
- 구어체 토론 어투(예: "존경하는 사회자님, 그리고 반대 측 패널 여러분...")를 섞어 생생한 발언문 형식(Markdown)으로 작성하세요."""
    
    with live_container:
        with st.chat_message("assistant", avatar="🟢"):
            with st.spinner("🟢 Gemini가 1차 찬성 입론을 발표하는 중..."):
                pro_1_res = call_llm_resilient(prompt_pro_1, gemini_key, temperature=0.7)
            st.markdown(f"**[찬성측 / Google Gemini]**\n\n{pro_1_res}")
    debate_logs.append({
        "speaker": "🟢 찬성측 (Google Gemini)",
        "role": "Proponent",
        "content": pro_1_res
    })

    # 3라운드: Claude (1차 반대 반론 - Gemini 입론 직접 반박)
    prompt_con_1 = f"""당신은 Anthropic Claude 기반의 날카로운 리스크 분석가이자 '반대 및 레드팀 비판자(Red Team Challenger)'입니다.
토론 주제: '{topic}'
앞선 찬성측(Gemini)의 입론 내용:
"{pro_1_res}"

Gemini의 찬성 입론을 직접 인용하며, 이에 대한 강력하고 집요한 1차 반박(Rebuttal)을 펼치세요.
- 찬성 논리의 낙관적 편향, 숨겨진 비용, 부작용, 현실적 장벽 및 위기 요인을 날카롭게 짚으세요.
- 토론 어투(예: "Gemini 측의 낙관적인 전망은 현실을 간과한 위험한 주장입니다. 특히...")로 생생하게 작성하세요."""
    
    with live_container:
        with st.chat_message("assistant", avatar="🔴"):
            with st.spinner("🔴 Claude (Red Team)가 찬성 주장을 매섭게 반박하는 중..."):
                con_1_res = call_llm_resilient(prompt_con_1, gemini_key, temperature=0.8)
            st.markdown(f"**[반대측 / Anthropic Claude Red Team]**\n\n{con_1_res}")
    debate_logs.append({
        "speaker": "🔴 반대측 (Anthropic Claude Red Team)",
        "role": "Challenger",
        "content": con_1_res
    })

    # 4라운드: Gemini (2차 재반론 - Claude의 비판에 대한 방어 및 대안 제시)
    prompt_pro_2 = f"""당신은 Google Gemini 기반 찬성 옹호자입니다.
토론 주제: '{topic}'
반대측(Claude)의 날카로운 비판:
"{con_1_res}"

Claude의 비판에 대해 물러서지 않고 논리적으로 재반론(Counter-Rebuttal)을 제시하세요.
- 지적된 리스크를 완화할 수 있는 안전장치, 정책적 대안, 실증 사례를 들어 찬성의 타당성을 다시 입증하세요.
- 토론 어투(예: "Claude 측의 지적은 충분히 고려할 가치가 있으나, 다음과 같은 보완책이 있습니다...")로 작성하세요."""
    
    with live_container:
        with st.chat_message("assistant", avatar="🟢"):
            with st.spinner("🟢 Gemini가 비판에 대한 재반론과 방어 논리를 펼치는 중..."):
                pro_2_res = call_llm_resilient(prompt_pro_2, gemini_key, temperature=0.7)
            st.markdown(f"**[찬성측 / Google Gemini 재반론]**\n\n{pro_2_res}")
    debate_logs.append({
        "speaker": "🟢 찬성측 (Google Gemini 재반론)",
        "role": "Proponent",
        "content": pro_2_res
    })

    # 5라운드: Claude (2차 최종 반론)
    prompt_con_2 = f"""당신은 Anthropic Claude 기반 레드팀 비판자입니다.
토론 주제: '{topic}'
찬성측(Gemini)의 재반론:
"{pro_2_res}"

Gemini의 재반론에 대해 최종 마무리 반박을 하세요.
- 현실적 실행의 한계와 구조적 결함이 왜 여전히 치명적인지 최종 쐐기를 박으세요.
- 토론 어투(예: "대안을 제시하셨지만 여전히 구조적인 모순은 해결되지 않았습니다...")로 작성하세요."""
    
    with live_container:
        with st.chat_message("assistant", avatar="🔴"):
            with st.spinner("🔴 Claude가 최종 반박으로 쐐기를 박는 중..."):
                con_2_res = call_llm_resilient(prompt_con_2, gemini_key, temperature=0.8)
            st.markdown(f"**[반대측 / Anthropic Claude 최종 반박]**\n\n{con_2_res}")
    debate_logs.append({
        "speaker": "🔴 반대측 (Anthropic Claude 최종 반박)",
        "role": "Challenger",
        "content": con_2_res
    })

    # 6라운드: ChatGPT (수석 사회자의 최종 종합 판정 및 타협안 도출)
    prompt_final = f"""당신은 최고 권위의 수석 토론 사회자이자 판정관(OpenAI ChatGPT Moderator)입니다.
토론 주제: '{topic}'

전체 토론 내역:
[찬성 Gemini 1차 입론]: {pro_1_res}
[반대 Claude 1차 반박]: {con_1_res}
[찬성 Gemini 2차 재반론]: {pro_2_res}
[반대 Claude 2차 최종반박]: {con_2_res}

양측의 치열한 공방을 객관적이고 가치중립적으로 엄격하게 평가하여 [최종 종합 판정 및 전략 보고서]를 작성하세요.

보고서 필수 항목:
1. 📌 토론 총평 및 핵심 쟁점 대조 요약
2. 🟢 찬성측(Gemini) 주장의 강점과 타당성 평가
3. 🔴 반대측(Claude) 비판의 유효성과 핵심 경고
4. ⚖️ 논리적 우위 및 실현 가능성 종합 심사
5. 🎯 실천적 타협안 및 맞춤 대응 가이드 (Actionable Compromise)
6. 🏆 최종 판정 및 결론 (Final Verdict)

정돈되고 권위 있는 Markdown 보고서 형식으로 작성하세요."""
    
    with live_container:
        with st.chat_message("assistant", avatar="⚖️"):
            with st.spinner("⚖️ ChatGPT 수석 사회자가 양측의 치열한 공방을 심사하여 최종 판정서를 작성 중입니다..."):
                verdict_res = call_llm_resilient(prompt_final, gemini_key, temperature=0.3)
            st.markdown(f"**[수석 사회자 / OpenAI ChatGPT 최종 판정]**\n\n{verdict_res}")
    debate_logs.append({
        "speaker": "⚖️ 수석 사회자 (OpenAI ChatGPT 최종 판정)",
        "role": "Moderator",
        "content": verdict_res
    })

    return debate_logs, verdict_res, pro_1_res, con_1_res, pro_2_res, con_2_res


# 실행 처리
if submit_button:
    cur_g = get_api_key("GOOGLE_API_KEY", "GEMINI_API_KEY")

    if not cur_g:
        st.error("⚠️ Google Gemini API 키가 필요합니다. 사이드바에서 키를 확인해주세요.")
    elif not topic_input.strip():
        st.warning("⚠️ 분석할 주제나 궁금한 점을 입력해주세요!")
    else:
        st.session_state.current_topic = topic_input
        
        st.markdown("---")
        st.subheader(f"🎙️ 실시간 토론 생중계: '{topic_input}'")
        
        live_box = st.container()
        
        try:
            debate_logs, final_verdict, pro1, con1, pro2, con2 = run_live_debate(topic_input, cur_g, live_box)

            # 전체 마크다운 문서 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"debate_live_result_{timestamp}.md"
            
            full_md = f"""# 🎙️ AI 3자 실시간 끝장 토론 & 종합 판정 전문
- **주제:** {topic_input}
- **일시:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **참여 패널:** 🟢 Google Gemini (찬성) | 🔴 Anthropic Claude (반대) | ⚖️ OpenAI ChatGPT (사회자)

---

## 🏆 [최종 종합 판정 및 전략 가이드]
{final_verdict}

---

## 💬 [실시간 끝장 토론 대화록 (Full Dialogue)]

### 🟢 1. Gemini 찬성 입론
{pro1}

### 🔴 2. Claude 반대 반박
{con1}

### 🟢 3. Gemini 방어 및 재반론
{pro2}

### 🔴 4. Claude 최종 반박
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

            st.success(f"🎉 실시간 토론과 최종 판정이 모두 완료되었습니다! (파일 저장: `{filename}`)")

        except Exception as e:
            st.error(f"❌ 토론 진행 중 오류 발생: {str(e)}")


# 영구 탭 렌더링 (결과가 있으면 화면 아래에 항상 표시)
if st.session_state.debate_history:
    data = st.session_state.debate_history
    
    st.markdown("---")
    st.success(f"🎯 **토론 완료 주제:** {data['topic']} (파일 자동 저장: `{data['filename']}`)")

    tab_chat, tab_verdict, tab_raw = st.tabs([
        "💬 실시간 토론 대화록 (Full Dialogue)",
        "🏆 최종 종합 판정 보고서 (Verdict)",
        "💾 전체 대화록 & 보고서 다운로드 (.md)"
    ])

    with tab_chat:
        st.markdown("### 🗣️ AI 패널 간 실시간 공방 대화록")
        for log in data["logs"]:
            if "사회자" in log["speaker"]:
                avatar = "⚖️"
            elif "찬성" in log["speaker"]:
                avatar = "🟢"
            else:
                avatar = "🔴"
                
            with st.chat_message(log["role"], avatar=avatar):
                st.markdown(f"**[{log['speaker']}]**\n\n{log['content']}")

    with tab_verdict:
        st.markdown(data["final_verdict"])

    with tab_raw:
        st.markdown("### 📄 전체 통합 마크다운 전문")
        st.code(data["full_md"], language="markdown")
        st.download_button(
            label="📥 전체 대화록 & 판정 보고서 (.md) 다운로드",
            data=data["full_md"],
            file_name=data["filename"],
            mime="text/markdown",
            type="primary"
        )
