import asyncio
import os
import re
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, BrowserContext, Page

# --- 설정 및 전역 변수 ---
USER_DATA_DIR = "./unified_ai_profile"  # 통합 프로필 경로

# --- AI별 답변 수집 함수들 ---

async def get_chatgpt_response(context: BrowserContext, prompt: str) -> str:
    """ChatGPT 답변 수집"""
    page = await context.new_page()
    try:
        await page.goto("https://chatgpt.com/")
        print("[ChatGPT] 접속 완료")

        # 로그인 감지 및 대기 (최초 1회만 필요하지만 안전을 위해)
        try:
            # 로그아웃 상태일 때 'Log in' 버튼이 보일 수 있음
            if await page.locator('text="Log in"').is_visible(timeout=3000):
                print("[ChatGPT] 로그인 필요! 45초 대기합니다. 직접 로그인해주세요.")
                await page.wait_for_timeout(45000)
        except:
            pass

        # 메인 입력창 대기
        await page.wait_for_selector("#prompt-textarea", timeout=60000)

        # 질문 입력
        await page.fill("#prompt-textarea", prompt)
        # 전송 버튼 클릭
        await page.click('button[data-testid="send-button"]')
        print(f"[ChatGPT] 질문 전송: {prompt[:30]}...")

        # 답변 대기: 'Stop generating' 버튼이 나타났다가 사라질 때까지, 혹은 Send 버튼이 다시 활성화될 때까지
        # ChatGPT는 답변 중일 때 stop 버튼이 보임
        try:
            # 먼저 응답 시작 대기 (Stop 버튼이 보이거나, 턴이 추가되거나)
            await page.wait_for_selector('button[data-testid="stop-button"]', timeout=10000)
        except:
            # 아주 짧은 답변이라 순식간에 끝났을 수도 있음
            pass

        # 완료 대기 (Stop 버튼이 사라짐 = 생성 완료)
        await page.wait_for_selector('button[data-testid="stop-button"]', state='hidden', timeout=120000)

        # 추가 대기 (렌더링)
        await asyncio.sleep(2)

        # 답변 추출
        response_elements = await page.query_selector_all('div[data-testid*="conversation-turn"]:last-child .markdown')
        full_response = ""
        for elem in response_elements:
            full_response += await elem.inner_text() + "\n"

        return full_response.strip()

    except Exception as e:
        return f"[ChatGPT 오류] {e}"
    finally:
        await page.close()

async def get_gemini_response(context: BrowserContext, prompt: str) -> str:
    """Gemini 답변 수집"""
    page = await context.new_page()
    try:
        await page.goto("https://gemini.google.com/")
        print("[Gemini] 접속 완료")

        try:
            if await page.locator('a[href^="https://accounts.google.com"]').is_visible(timeout=3000):
                 print("[Gemini] 로그인 필요! 45초 대기합니다.")
                 await page.wait_for_timeout(45000)
        except:
            pass

        # 입력창
        await page.wait_for_selector(".ql-editor.textarea", timeout=60000)

        # 입력
        await page.click(".ql-editor.textarea")
        await page.keyboard.type(prompt)
        await page.click('button.send-button')
        print(f"[Gemini] 질문 전송: {prompt[:30]}...")

        # 답변 대기: progress bar가 사라질 때까지
        await page.wait_for_selector('progress-indicator.progress-bar', state='hidden', timeout=120000)
        await asyncio.sleep(3)

        # 답변 추출
        response_element = await page.query_selector("response-component:last-of-type message-content")
        if response_element:
            return (await response_element.inner_text()).strip()
        return "답변을 찾을 수 없습니다."

    except Exception as e:
        return f"[Gemini 오류] {e}"
    finally:
        await page.close()

async def get_claude_response(context: BrowserContext, prompt: str) -> str:
    """Claude 답변 수집"""
    page = await context.new_page()
    try:
        await page.goto("https://claude.ai/")
        print("[Claude] 접속 완료")

        # 로그인 체크 로직은 생략(접속되면 바로 진행)

        # 입력창
        editor_selector = 'div[contenteditable="true"]'
        await page.wait_for_selector(editor_selector, timeout=60000)

        await page.fill(editor_selector, prompt)
        await page.click('button[aria-label="Send Message"]')
        print(f"[Claude] 질문 전송: {prompt[:30]}...")

        # 답변 완료 대기: Stop generating 버튼 사라짐
        stop_btn = 'button[aria-label="Stop generating"]'
        try:
            await page.wait_for_selector(stop_btn, state='visible', timeout=10000)
        except:
            pass
        await page.wait_for_selector(stop_btn, state='hidden', timeout=120000)
        await asyncio.sleep(2)

        # 답변 추출
        response_elements = await page.query_selector_all("div[data-is-response='true']")
        if response_elements:
            return (await response_elements[-1].inner_text()).strip()
        return "답변을 찾을 수 없습니다."

    except Exception as e:
        return f"[Claude 오류] {e}"
    finally:
        await page.close()

async def get_copilot_response(context: BrowserContext, prompt: str) -> str:
    """Copilot 답변 수집"""
    page = await context.new_page()
    try:
        await page.goto("https://copilot.microsoft.com/")
        print("[Copilot] 접속 완료")

        # Shadow DOM 입력창
        search_box = page.locator('cib-serp').locator('cib-action-bar').locator('cib-text-input').locator('#searchbox')
        await search_box.wait_for(timeout=60000)

        await search_box.fill(prompt)
        submit_btn = page.locator('cib-serp').locator('cib-action-bar').locator('button[aria-label="Submit"]')
        await submit_btn.click()
        print(f"[Copilot] 질문 전송: {prompt[:30]}...")

        # 답변 완료 대기
        await page.wait_for_selector('cib-chat-turn[state="complete"]', timeout=120000)
        await asyncio.sleep(2)

        # 답변 추출
        last_turn = page.locator('cib-chat-turn').last()
        response_groups = last_turn.locator('cib-message-group[source="bot"]')

        full_res = ""
        count = await response_groups.count()
        for i in range(count):
            parts = response_groups.nth(i).locator("cib-message-part")
            p_count = await parts.count()
            for j in range(p_count):
                full_res += await parts.nth(j).inner_text() + "\n"

        return full_res.strip() if full_res else "답변 없음"

    except Exception as e:
        return f"[Copilot 오류] {e}"
    finally:
        await page.close()

async def get_wrtn_response(context: BrowserContext, prompt: str) -> str:
    """Wrtn 답변 수집"""
    page = await context.new_page()
    try:
        await page.goto("https://wrtn.io/chat")
        print("[Wrtn] 접속 완료")

        textarea = 'textarea[placeholder*="에게 무엇이든 물어보세요"]'
        await page.wait_for_selector(textarea, timeout=60000)

        await page.fill(textarea, prompt)

        # 버튼 클릭
        submit_btn = page.locator(f'xpath=//textarea[@placeholder="뤼튼에게 무엇이든 물어보세요"]/../following-sibling::button')
        if not await submit_btn.is_visible():
            # 플레이스홀더가 다를 경우 대비 일반적인 형제 버튼 찾기
             submit_btn = page.locator('button[data-testid="chat-input-send-button"]')

        await submit_btn.click()
        print(f"[Wrtn] 질문 전송: {prompt[:30]}...")

        # 답변 완료 대기 (다시 생성 or 복사 버튼 등)
        # 뤼튼은 '다시 생성' 버튼이 뜨면 완료된 것
        await page.wait_for_selector('button:has-text("다시 생성")', timeout=120000)
        await asyncio.sleep(2)

        # 답변 추출
        bubbles = await page.query_selector_all('div[class^="ChatBubble_content"]')
        if bubbles:
            return (await bubbles[-1].inner_text()).strip()
        return "답변 없음"

    except Exception as e:
        return f"[Wrtn 오류] {e}"
    finally:
        await page.close()

async def get_grok_response(context: BrowserContext, prompt: str) -> str:
    """Grok 답변 수집"""
    page = await context.new_page()
    try:
        await page.goto("https://grok.x.ai/")
        print("[Grok] 접속 완료")

        # 입력창
        textarea = 'textarea[placeholder*="Ask Grok"]'
        await page.wait_for_selector(textarea, timeout=60000)

        await page.fill(textarea, prompt)
        await page.keyboard.press("Enter")
        print(f"[Grok] 질문 전송: {prompt[:30]}...")

        # 대기 (임시: 15초 sleep + 요소 확인)
        await asyncio.sleep(5)
        # Grok의 응답 완료 시그널은 명확치 않아 약간의 sleep을 섞음
        await page.wait_for_selector('div[data-testid^="conversation-turn-"]', timeout=120000)
        # 추가 대기
        await asyncio.sleep(10)

        # 답변 추출
        turns = await page.query_selector_all('div[data-testid^="conversation-turn-"]')
        if turns:
            last_turn = turns[-1]
            # Grok 구조상 봇 답변 위치 찾기
            # 보통 2번째 child div가 텍스트
            ans_elem = await last_turn.query_selector('div > div > div:nth-child(2)')
            if ans_elem:
                return (await ans_elem.inner_text()).strip()
            # 못 찾으면 전체 텍스트
            return (await last_turn.inner_text()).strip()
        return "답변 없음"

    except Exception as e:
        return f"[Grok 오류] {e}"
    finally:
        await page.close()

async def get_genspark_response(context: BrowserContext, prompt: str) -> str:
    """GenSpark 답변 수집"""
    page = await context.new_page()
    try:
        await page.goto("https://www.genspark.ai/")
        print("[GenSpark] 접속 완료")

        textarea = 'textarea[placeholder*="Ask me anything"]'
        await page.wait_for_selector(textarea, timeout=60000)

        await page.fill(textarea, prompt)
        await page.keyboard.press("Enter")
        print(f"[GenSpark] 질문 전송: {prompt[:30]}...")

        # Sparkpage 로딩 대기
        await page.wait_for_selector('div[class*="sparkpage_main"]', timeout=180000)
        await asyncio.sleep(5)

        main_content = await page.query_selector('div[class*="sparkpage_main"]')
        if main_content:
            return (await main_content.inner_text()).strip()
        return "답변 없음"

    except Exception as e:
        return f"[GenSpark 오류] {e}"
    finally:
        await page.close()


# --- 핵심 로직: 토론 라운드 실행 ---

async def run_discussion_round(context: BrowserContext, ai_map: Dict, prompt: str) -> Dict[str, str]:
    """
    모든 AI에게 동시에 질문을 던지고 답변을 수집합니다 (병렬 처리).
    """
    print(f"\n🚀 토론 시작! 질문: {prompt}\n")

    tasks = []
    ai_names = []

    for name, func in ai_map.items():
        ai_names.append(name)
        tasks.append(func(context, prompt))

    # 병렬 실행
    results = await asyncio.gather(*tasks)

    # 결과 매핑
    response_map = {}
    for name, res in zip(ai_names, results):
        response_map[name] = res
        print(f"✅ {name} 답변 수신 완료 ({len(res)}자)")

    return response_map

def save_responses_to_file(filename: str, prompt: str, responses: Dict[str, str]):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Question: {prompt}\n\n")
        for name, res in responses.items():
            f.write(f"--- {name} ---\n{res}\n\n{'='*50}\n\n")
    print(f"💾 결과 저장 완료: {filename}")


# --- 메인 실행 함수 ---

async def main():
    # 1. 브라우저 컨텍스트 시작 (통합 프로필)
    print("🌐 브라우저를 실행하고 통합 프로필을 로드합니다...")
    async with async_playwright() as p:
        # headless=False여야 로그인이 유지되고 봇 탐지 회피 유리
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 720}
        )

        # AI 함수 매핑
        ai_functions = {
            "ChatGPT": get_chatgpt_response,
            "Gemini": get_gemini_response,
            "Claude": get_claude_response,
            "Copilot": get_copilot_response,
            "Wrtn": get_wrtn_response,
            "Grok": get_grok_response,
            "GenSpark": get_genspark_response
        }

        # 2. 사용자 입력
        topic = input("\n🎤 토론 주제를 입력하세요: ")
        if not topic.strip():
            topic = "인공지능이 인간의 창의성을 대체할 수 있을까?"
            print(f"   (기본 주제로 진행합니다: {topic})")

        # 3. 1차 토론 (Parallel)
        round1_responses = await run_discussion_round(browser, ai_functions, topic)
        save_responses_to_file("round_1_responses.txt", topic, round1_responses)

        # 4. 사회자(ChatGPT)에게 요약 및 후속 질문 요청
        print("\n🤔 ChatGPT가 1차 토론을 분석하고 있습니다...")
        summary_prompt = (
            "다음은 7개 AI가 나눈 토론 내용입니다:\n\n"
            + str(round1_responses)[:3000] + "\n..."  # 길이 제한
            + "\n\n이 내용을 바탕으로 1) 핵심 쟁점 3줄 요약, 2) 토론을 심화시킬 수 있는 날카로운 후속 질문 3가지를 추천해줘."
            + "형식은 [요약] ... [질문1] ... [질문2] ... [질문3] ... 으로 해줘."
        )

        # ChatGPT 단독 호출 (사회자 역할)
        moderator_res = await get_chatgpt_response(browser, summary_prompt)
        print("\n" + "="*20 + " 📝 1차 토론 분석 " + "="*20)
        print(moderator_res)
        print("="*60)

        # 5. 사용자 선택 (후속 질문)
        print("\n👉 2차 토론을 위한 질문을 선택하세요 (1, 2, 3) 또는 직접 입력하세요.")
        choice = input("선택: ")

        next_question = choice # 기본값: 직접 입력
        # 간단한 파싱 (실제로는 정규식 등으로 더 정교하게 할 수 있음)
        if choice in ["1", "2", "3"]:
            # ChatGPT 응답에서 질문 텍스트 추출 시도 (단순화된 로직)
            lines = moderator_res.split('\n')
            q_candidates = [l for l in lines if "질문" in l or "?" in l]
            if len(q_candidates) >= int(choice):
                next_question = q_candidates[int(choice)-1]
                print(f"선택된 질문: {next_question}")
            else:
                print("질문을 찾지 못해 입력값을 그대로 사용합니다.")

        # 6. 2차 토론 (Parallel)
        round2_responses = await run_discussion_round(browser, ai_functions, next_question)
        save_responses_to_file("round_2_responses.txt", next_question, round2_responses)

        # 7. 최종 기획안 생성 (테마 선택)
        print("\n🎯 최종 결과물 생성을 위한 테마를 선택하세요.")
        themes = ["사업 기획서", "기술 명세서", "교육 커리큘럼", "마케팅 전략", "정책 제안서", "연구 보고서", "블로그 포스팅", "유튜브 스크립트", "SF 소설 시놉시스", "철학적 에세이"]
        for i, t in enumerate(themes):
            print(f"{i+1}. {t}")

        t_choice = input("번호 입력: ")
        try:
            selected_theme = themes[int(t_choice)-1]
        except:
            selected_theme = "종합 보고서"

        print(f"\n📄 '{selected_theme}' 형식으로 최종 문서를 생성합니다...")

        final_prompt = (
            f"지금까지의 1차, 2차 토론 내용을 바탕으로 '{selected_theme}'를 작성해줘.\n"
            f"주제: {topic}\n"
            f"심화 논의: {next_question}\n"
            f"참고 내용(2차 토론 요약): {str(round2_responses)[:3000]}..."
        )

        final_doc = await get_chatgpt_response(browser, final_prompt)

        with open("final_project_plan.txt", "w", encoding="utf-8") as f:
            f.write(f"주제: {topic}\n테마: {selected_theme}\n\n")
            f.write(final_doc)

        print("\n✨ 모든 과정이 완료되었습니다! 'final_project_plan.txt'를 확인하세요.")

        # 브라우저 종료는 context manager가 처리

if __name__ == "__main__":
    asyncio.run(main())
