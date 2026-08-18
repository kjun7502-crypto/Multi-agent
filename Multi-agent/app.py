#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI 3자 실시간 끝장 토론 & 종합 판정 웹 애플리케이션
Google Gemini, Anthropic Claude, OpenAI ChatGPT 페르소나 협업 토론 플랫폼
보안 비밀번호 인증 잠금 (Password: 1909) + 클라우드 및 모바일 완벽 호환
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
    # 1. 로컬 환경 변수 (.env)
    env_val = os.getenv(key_name) or (os.getenv(fallback_key_name) if fallback_key_name else None)
    if env_val and "your_" not in env_val:
        return env_val.strip()
    # 2. Streamlit Cloud Secrets
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
    page_title="AI 3자 실시간 끝장 토론실",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 반응형 커스텀 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
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
    div[data-testid="stFormSubmitButton"] button:hover {
        background-color: #1D4ED8 !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""
if "debate_history" not in st.session_state:
    st.session_state.debate_history = None


# 🔐 비밀번호 인증 게이트
AUTH_PASSWORD = "1909"

if not st.session_state.authenticated:
    st.markdown('<div class="main-header">🔒 AI 3자 토론실 보안 인증</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">본 시스템은 인가된 사용자만 접근할 수 있습니다. 비밀번호를 입력해주세요.</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("auth_form"):
            password_input = st.text_input("🔑 접속 비밀번호", type="password", placeholder="비밀번호 4자리를 입력하세요")
            auth_submit = st.form_submit_button("🔓 토론실 입장하기")

            if auth_submit:
                if password_input == AUTH_PASSWORD:
                    st.session_state.authenticated = True
                    st.success("✔ 인증에 성공했습니다! 토론실로 입장합니다...")
                    st.rerun()
                else:
                    st.error("❌ 비밀번호가 올바르지 않습니다. 다시 입력해주세요.")
    st.stop()


# --- 인증 완료 후 메인 서비스 화면 ---

# 사이드바
with st.sidebar:
    st.header("👤 사용자 인증 완료")
    st.success("🟢 로그인 상태: **인증됨 (1909)**")
    
    if st.button("🔒 로그아웃"):
        st.session_state.authenticated = False
        st.session_state.debate_history = None
        st.rerun()

    st.markdown("---")
    st.subheader("💡 활용 팁")
    st.markdown("""
    - 질문만 입력하고 **Enter**를 치면 실시간 3자 토론이 시작됩니다.
    - 토론 대화록과 최종 판정서는 **.md 파일로 다운로드**할 수 있습니다.
    """)


# 메인 헤더
st.markdown('<div class="main-header">🎙️ AI 3자 실시간 끝장 토론 & 종합 판정실</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Google Gemini (찬성/기회) ⚔️ Anthropic Claude (비판/리스크) ⚖️ OpenAI ChatGPT (사회자 판정)</div>', unsafe_allow_html=True)

# 3 에이전트 소개 카드
col_g, col_c, col_o = st.columns(3)
with col_g:
    st.markdown("""
    <div class="card-gemini">
        <b>🟢 Agent 1: Google Gemini</b><br>
        <small><b>역할:</b> 찬성 & 기회 요인 옹호자 (Proponent)</small><br>
        <span style="color:#166534; font-size:0.85rem;">최신 데이터, 통계 지표, 긍정적 기대 효과, 기회 요인을 바탕으로 강력한 찬성 논리를 구축합니다.</span>
    </div>
    """, unsafe_allow_html=True)

with col_c:
    st.markdown("""
    <div class="card-claude">
        <b>🔴 Agent 2: Anthropic Claude</b><br>
        <small><b>역할:</b> 비판적 레드팀 검증관 (Red Team)</small><br>
        <span style="color:#991B1B; font-size:0.85rem;">낙관론의 맹점, 예상 부작용, 숨겨진 비용, 현실적 리스크를 집요하게 파고들어 반대 논리를 전개합니다.</span>
    </div>
    """, unsafe_allow_html=True)

with col_o:
    st.markdown("""
    <div class="card-gpt">
        <b>🔵 Agent 3: OpenAI ChatGPT</b><br>
        <small><b>역할:</b> 수석 사회자 & 종합 판정관 (Moderator)</small><br>
        <span style="color:#1E40AF; font-size:0.85rem;">양측 주장의 논리성과 타당성을 공정하게 검증하여 실현 가능한 타협안 및 최종 판정서를 작성합니다.</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# 빠른 예시 선택
st.write("🔥 **빠른 예시 질문 선택:**")
b1, b2, b3, b4 = st.columns(4)
if b1.button("🍽️ 탕수육: 부먹 vs 찍먹"):
    st.session_state.current_topic = "탕수육은 부먹이야 찍먹이야"
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
        placeholder="예: 탕수육은 부먹이야 찍먹이야 / 트럼프 정부와 한국 경제 / 주 4일제 도입 의무화",
    )
    submit_button = st.form_submit_button("🚀 AI 실시간 끝장 토론 & 종합 판정 시작 (Enter)")


# 지능형 무결점 LLM 호출 함수 (503 트래픽 과부하 방지 및 자동 모델 로테이션)
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


# 4단계 멀티턴(Multi-turn) 실시간 끝장 토론 엔진
def run_live_debate(topic: str, api_key: str, live_container):
    debate_logs = []

    # 1. 사회자(ChatGPT) 토론 개회
    with live_container:
        with st.chat_message("assistant", avatar="⚖️"):
            intro_msg = f"토론을 시작하겠습니다. 오늘의 주제는 **'{topic}'** 입니다. 먼저 찬성/기회 옹호 측(Google Gemini), 입론을 시작해 주십시오."
            st.markdown(f"**[수석 사회자 / OpenAI ChatGPT]**\n\n{intro_msg}")
    debate_logs.append({
        "speaker": "⚖️ 수석 사회자 (OpenAI ChatGPT)",
        "role": "Moderator",
        "content": intro_msg
    })

    # 2. Gemini 1차 입론
    prompt_pro_1 = f"""당신은 Google Gemini 기반의 데이터 분석가이자 '찬성 및 기회 옹호자(Proponent)'입니다.
토론 주제: '{topic}'
사회자의 요청에 따라, 이 주제에 대한 강력한 1차 찬성/긍정 입론을 발표하세요.
- 데이터, 통계 지표, 긍정적 기대 효과, 기회 요인을 3가지 핵심 포인트로 논리 정연하게 개진하세요.
- 구어체 토론 어투(예: "존경하는 사회자님, 그리고 반대 측 패널 여러분...")를 섞어 생생한 발언문 형식(Markdown)으로 작성하세요."""

    with live_container:
        with st.chat_message("assistant", avatar="🟢"):
            with st.spinner("🟢 Gemini가 1차 찬성 입론을 발표하는 중..."):
                pro_1_res = call_gemini_api(prompt_pro_1, api_key, temperature=0.7)
            st.markdown(f"**[찬성측 / Google Gemini]**\n\n{pro_1_res}")
    debate_logs.append({
        "speaker": "🟢 찬성측 (Google Gemini)",
        "role": "Proponent",
        "content": pro_1_res
    })

    # 3. Claude 1차 반박
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
                con_1_res = call_gemini_api(prompt_con_1, api_key, temperature=0.8)
            st.markdown(f"**[반대측 / Anthropic Claude Red Team]**\n\n{con_1_res}")
    debate_logs.append({
        "speaker": "🔴 반대측 (Anthropic Claude Red Team)",
        "role": "Challenger",
        "content": con_1_res
    })

    # 4. Gemini 2차 재반론
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
                pro_2_res = call_gemini_api(prompt_pro_2, api_key, temperature=0.7)
            st.markdown(f"**[찬성측 / Google Gemini 재반론]**\n\n{pro_2_res}")
    debate_logs.append({
        "speaker": "🟢 찬성측 (Google Gemini 재반론)",
        "role": "Proponent",
        "content": pro_2_res
    })

    # 5. Claude 2차 최종 반론
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
                con_2_res = call_gemini_api(prompt_con_2, api_key, temperature=0.8)
            st.markdown(f"**[반대측 / Anthropic Claude 최종 반박]**\n\n{con_2_res}")
    debate_logs.append({
        "speaker": "🔴 반대측 (Anthropic Claude 최종 반박)",
        "role": "Challenger",
        "content": con_2_res
    })

    # 6. ChatGPT 수석 사회자 최종 판정
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
                verdict_res = call_gemini_api(prompt_final, api_key, temperature=0.3)
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
        st.error("⚠️ Google Gemini API 키가 필요합니다.")
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
