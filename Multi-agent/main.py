#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Multi-Agent Debate and Synthesis CLI System
Cooperative AI debate system powered by:
- Google Gemini (Data-Driven Proponent)
- Anthropic Claude (Critical Challenger / Red Team)
- OpenAI ChatGPT (Chief Synthesizer / Moderator)
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Rich 라이브러리 (CLI 터미널 UI 강화)
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.table import Table
    from rich import print as rprint
except ImportError:
    print("Error: 'rich' 라이브러리가 설치되지 않았습니다. 'pip install -r requirements.txt'를 실행하세요.")
    sys.exit(1)

# CrewAI 라이브러리
try:
    from crewai import Agent, Crew, Process, Task, LLM
except ImportError:
    print("Error: 'crewai' 라이브러리가 설치되지 않았습니다. 'pip install -r requirements.txt'를 실행하세요.")
    sys.exit(1)


# 1. 환경 변수 로드 및 검증
def validate_environment(console: Console) -> bool:
    load_dotenv()

    # Google API Key 처리 (GOOGLE_API_KEY 또는 GEMINI_API_KEY)
    google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if google_key and not os.getenv("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = google_key
    if google_key and not os.getenv("GEMINI_API_KEY"):
        os.environ["GEMINI_API_KEY"] = google_key

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    keys_status = {
        "Google Gemini (GOOGLE_API_KEY)": bool(google_key and "your_google_key" not in google_key),
        "Anthropic Claude (ANTHROPIC_API_KEY)": bool(anthropic_key and "your_anthropic_key" not in anthropic_key),
        "OpenAI ChatGPT (OPENAI_API_KEY)": bool(openai_key and "your_openai_key" not in openai_key),
    }

    table = Table(title="[bold cyan]🔑 API 키 설정 상태 점검[/bold cyan]", show_header=True, header_style="bold magenta")
    table.add_column("모델 / 공급자", style="dim")
    table.add_column("상태", justify="center")

    all_valid = True
    for provider, is_valid in keys_status.items():
        if is_valid:
            table.add_row(provider, "[bold green]✔ 로드 완료 (Valid)[/bold green]")
        else:
            table.add_row(provider, "[bold red]✘ 미설정 (Missing)[/bold red]")
            all_valid = False

    console.print(table)
    return all_valid


# 2. LLM 인스턴스 초기화
def create_llm_instances():
    """Gemini, Claude, GPT 3개 모델 인스턴스를 초기화합니다."""
    # Google Gemini
    gemini_llm = LLM(
        model="gemini/gemini-1.5-flash",
        temperature=0.7,
        api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    )

    # Anthropic Claude
    claude_llm = LLM(
        model="anthropic/claude-3-5-sonnet-20241022",
        temperature=0.7,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

    # OpenAI ChatGPT
    openai_llm = LLM(
        model="openai/gpt-4o-mini",
        temperature=0.5,
        api_key=os.getenv("OPENAI_API_KEY")
    )

    return gemini_llm, claude_llm, openai_llm


# 3. 에이전트(Agent) 정의
def create_agents(gemini_llm, claude_llm, openai_llm):
    """찬성, 반대, 종합 판정 3개 에이전트를 정의합니다."""

    # Agent 1: Data-Driven Proponent (Gemini)
    proponent = Agent(
        role="Data-Driven Proponent & Strategic Researcher",
        goal="주제에 대해 최신 통계, 실증 데이터, 논리적 근거 및 긍정적 기대 효과를 바탕으로 강력한 찬성 논리를 구축한다.",
        backstory="""당신은 데이터와 실증적 증거를 기반으로 혁신과 변화의 긍정적 가치를 입증하는 전문 전략 분석가입니다.
Google Gemini의 방대한 지식과 최신 데이터 분석 역량을 활용하여 찬성 입장을 객관적이고 설득력 있게 대변합니다.""",
        llm=gemini_llm,
        verbose=True,
        memory=False,
    )

    # Agent 2: Critical Challenger / Red Team (Claude)
    challenger = Agent(
        role="Critical Challenger & Red Team Risk Analyst",
        goal="찬성 측 주장의 논리적 허점, 숨겨진 비용, 윤리적/법적/현실적 리스크 및 부작용을 집요하게 분석하여 강력한 반대 논리를 개진한다.",
        backstory="""당신은 시스템의 취약점과 낙관론 뒤에 숨겨진 치명적 결함을 파헤치는 최고의 레드팀 분석가입니다.
Anthropic Claude의 깊이 있는 논리 추론과 비판적 사고력을 바탕으로, 현실 세계에서의 잠재적 부작용과 현실적 한계를 날카롭게 지적합니다.""",
        llm=claude_llm,
        verbose=True,
        memory=False,
    )

    # Agent 3: Chief Synthesizer / Moderator (OpenAI ChatGPT)
    synthesizer = Agent(
        role="Chief Synthesizer & Impartial Debate Moderator",
        goal="찬성 측과 반대 측의 모든 주장을 엄격히 대조·평가하고, 오류를 배제하여 실행 가능한 타협안과 최종 판정 보고서를 도출한다.",
        backstory="""당신은 수십 년간 국가 정책 및 기업 분쟁을 조율해 온 최고 권위의 중재자이자 수석 판정관입니다.
편향 없이 양측의 핵심 논점을 가치 중립적으로 분석하고, 현실적으로 실현 가능한 최적의 타협안과 최종 결론을 명확히 제시합니다.""",
        llm=openai_llm,
        verbose=True,
        memory=False,
    )

    return proponent, challenger, synthesizer


# 4. 태스크(Task) 정의
def create_tasks(proponent, challenger, synthesizer, topic: str):
    """순차적으로 실행될 3개의 토론/분석 태스크를 정의합니다."""

    # Task 1: 긍정 논리 및 매력적인 추천 분석
    proponent_task = Task(
        description=f"""주제/질문: '{topic}'
이 주제에 대해 긍정적이고 매력적인 분석/추천/찬성 보고서를 작성하세요.
- 질문이 맛집/여행/제품 추천인 경우: 실제 매력적인 장소나 아이템 3~4곳 추천, 대표 메뉴/특징, 분위기, 인기 비결 상세 서술
- 질문이 찬반 토론인 경우: 핵심 찬성 논거 3~4가지 명시, 데이터/통계, 긍정적 기대 효과 서술
- 전문적이고 정돈된 Markdown 서식으로 작성하세요.""",
        expected_output="데이터 기반의 찬성 논거, 실증 사례 또는 구체적인 추천 리스트가 담긴 보고서 (Markdown 형식)",
        agent=proponent,
    )

    # Task 2: 비판적 반박 및 현실 검증 (리스크 분석)
    challenger_task = Task(
        description=f"""주제/질문: '{topic}'
앞선 찬성/추천 에이전트(Proponent)가 제시한 내용을 면밀히 분석하고, 비판적 현실 검증(Reality Check) 보고서를 작성하세요.
- 질문이 맛집/추천인 경우: 웨이팅 시간, 비싼 가격, 예약 난이도, 주차 문제, 소음/호불호 등 실제 겪을 수 있는 단점과 주의점 분석
- 질문이 찬반 토론인 경우: 찬성 측 주장의 맹점 지적, 예상되는 부작용, 숨겨진 비용, 현실적 한계 분석
- 전문적이고 정돈된 Markdown 서식으로 작성하세요.""",
        expected_output="현실적 한계, 리스크, 단점, 주의사항이 상세히 담긴 비판 보고서 (Markdown 형식)",
        agent=challenger,
    )

    # Task 3: 종합 대조, 상황별 맞춤 가이드 및 최종 판정 보고서
    synthesizer_task = Task(
        description=f"""주제/질문: '{topic}'
찬성/추천 에이전트(Gemini)와 비판 에이전트(Claude)가 제시한 모든 내용을 종합하여, 사용자에게 가장 유용한 최종 판정 및 맞춤 가이드 보고서를 작성하세요.

보고서에는 반드시 다음 섹션이 포함되어야 합니다:
1. 📌 주제 개요 및 핵심 요약
2. 🟢 긍정/추천 핵심 요약 (Gemini)
3. 🔴 비판/주의사항 핵심 요약 (Claude)
4. ⚖️ 쟁점별 비교 대조 및 현실적 평가
5. 🎯 상황별 맞춤 추천 및 팁 (예: 이런 분은 A, 저런 분은 B)
6. 🏆 최종 종합 판정 및 결론 (Final Verdict)""",
        expected_output="양측 분석 비교, 상황별 맞춤 팁, 최종 판정이 포함된 종합 보고서 (Markdown 형식)",
        agent=synthesizer,
    )

    return [proponent_task, challenger_task, synthesizer_task]


# 5. 결과 파일 저장 함수
def save_debate_result(topic: str, result_content: str, console: Console) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"debate_result_{timestamp}.md"

    file_header = f"""# 🏛️ 멀티 에이전트 찬반 토론 및 종합 판정 보고서

- **토론 주제:** {topic}
- **일시:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **참여 에이전트:**
  - 🟢 **찬성 (Proponent):** Google Gemini (`gemini/gemini-1.5-flash`)
  - 🔴 **반대 (Red Team):** Anthropic Claude (`anthropic/claude-3-5-sonnet-20241022`)
  - 🔵 **종합 판정 (Moderator):** OpenAI ChatGPT (`openai/gpt-4o-mini`)

---

"""
    full_content = file_header + result_content

    with open(filename, "w", encoding="utf-8") as f:
        f.write(full_content)

    console.print(Panel(f"[bold green]✔ 토론 결과가 파일로 성공적으로 저장되었습니다:[/bold green]\n[cyan]{filename}[/cyan]", border_style="green"))
    return filename


# 6. 메인 실행 루프
def main():
    console = Console()

    # 인트로 배너
    banner_text = """[bold yellow]Multi-Agent AI Debate & Synthesis CLI[/bold yellow]
[cyan]Google Gemini[/cyan] (찬성) ⚔️ [red]Anthropic Claude[/red] (반대) ⚖️ [blue]OpenAI ChatGPT[/blue] (종합 판정)"""
    console.print(Panel(banner_text, border_style="bold blue", padding=(1, 2)))

    # 환경 변수 검증
    if not validate_environment(console):
        console.print(Panel(
            "[bold red]경고:[/bold red] 일부 필수 API 키가 누락되었거나 템플릿 기본값입니다.\n"
            "[yellow].env[/yellow] 파일에 [bold]OPENAI_API_KEY[/bold], [bold]ANTHROPIC_API_KEY[/bold], [bold]GOOGLE_API_KEY[/bold]를 입력해주세요.",
            border_style="red"
        ))
        user_choice = console.input("\n[yellow]계속 진행하시겠습니까? (API 호출 시 오류가 발생할 수 있습니다) [y/N]: [/yellow]").strip().lower()
        if user_choice not in ["y", "yes"]:
            console.print("[dim]프로그램을 종료합니다.[/dim]")
            sys.exit(0)

    # LLM 및 Agent 초기화
    try:
        console.print("\n[dim]🧠 에이전트 및 LLM 인스턴스를 초기화하는 중...[/dim]")
        gemini_llm, claude_llm, openai_llm = create_llm_instances()
        proponent, challenger, synthesizer = create_agents(gemini_llm, claude_llm, openai_llm)
    except Exception as e:
        console.print(f"[bold red]에이전트 초기화 실패:[/bold red] {e}")
        sys.exit(1)

    while True:
        console.print("\n" + "=" * 80)
        topic = console.input("\n[bold green]💬 찬반 토론 주제를 입력하세요[/bold green] (종료: 'q' 또는 'exit'):\n[bold cyan]👉 [/bold cyan]").strip()

        if not topic:
            console.print("[yellow]주제를 입력해주세요.[/yellow]")
            continue

        if topic.lower() in ["q", "exit", "quit", "종료"]:
            console.print("[bold yellow]프로그램을 종료합니다. 감사합니다![/bold yellow]")
            break

        console.print(Panel(f"[bold white]토론 주제:[/bold white] [bold cyan]{topic}[/bold cyan]", border_style="cyan"))

        # 태스크 구성
        tasks = create_tasks(proponent, challenger, synthesizer, topic)

        # Crew 파이프라인 조립
        debate_crew = Crew(
            agents=[proponent, challenger, synthesizer],
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
        )

        # 파이프라인 실행
        try:
            with console.status("[bold green]🤖 3개 모델이 토론 및 종합 판정을 수행 중입니다...[/bold green]", spinner="dots"):
                crew_output = debate_crew.kickoff()

            result_str = str(crew_output)

            # 터미널에 마크다운 스타일로 최종 결과 출력
            console.print("\n" + "=" * 80)
            console.print(Panel("[bold green]🏆 최종 종합 판정 및 분석 보고서[/bold green]", border_style="bold green"))
            console.print(Markdown(result_str))
            console.print("=" * 80 + "\n")

            # 파일 저장
            save_debate_result(topic, result_str, console)

        except Exception as e:
            console.print(f"\n[bold red]❌ 토론 파이프라인 실행 중 오류 발생:[/bold red] {e}")
            console.print("[dim]API 키 유효성 및 네트워크 연결 상태를 확인해주세요.[/dim]")


if __name__ == "__main__":
    main()
