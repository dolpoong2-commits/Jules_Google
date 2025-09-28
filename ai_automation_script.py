import asyncio
from playwright.async_api import async_playwright

async def get_chatgpt_response(prompt: str) -> str:
    """
    ChatGPT에 접속하여 질문에 대한 답변을 가져옵니다.
    최초 실행 시, 사용자가 수동으로 로그인해야 합니다.
    인증 정보는 user_data_dir에 저장되어 다음 실행부터 자동으로 사용됩니다.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./chatgpt_user_data",
            headless=False,  # 처음에는 GUI 환경에서 로그인 필요
        )
        page = await browser.new_page()
        try:
            await page.goto("https://chatgpt.com/")
            print("ChatGPT 페이지에 접속했습니다. 로그인이 필요한 경우 수동으로 진행해주세요.")

            # 로그인 감지 (로그인 페이지의 특정 요소 확인)
            try:
                await page.wait_for_selector('text="Log in"', timeout=5000)
                print("로그인이 감지되었습니다. 30초 동안 로그인을 기다립니다...")
                await page.wait_for_timeout(30000) # 사용자가 로그인할 시간
            except:
                print("이미 로그인된 상태일 수 있습니다.")

            # 메인 페이지 로딩 확인
            await page.wait_for_selector("#prompt-textarea", timeout=60000)
            print("ChatGPT 메인 페이지 로딩 완료.")

            # 질문 입력 및 제출
            await page.fill("#prompt-textarea", prompt)
            await page.click('button[data-testid="send-button"]')
            print(f"질문 제출: {prompt}")

            # 답변 대기 및 추출
            await page.wait_for_selector('div[data-testid*="conversation-turn"]:last-child .markdown', timeout=120000)
            print("답변 생성 중...")

            # 답변이 완전히 생성될 때까지 잠시 대기
            await asyncio.sleep(5)

            response_elements = await page.query_selector_all('div[data-testid*="conversation-turn"]:last-child .markdown')

            # 마지막 답변 블록의 텍스트를 조합
            full_response = ""
            for elem in response_elements:
                full_response += await elem.inner_text() + "\n"

            print("답변 추출 완료.")
            return full_response.strip()

        except Exception as e:
            return f"오류가 발생했습니다: {e}"
        finally:
            await browser.close()

async def get_gemini_response(prompt: str) -> str:
    """
    Gemini에 접속하여 질문에 대한 답변을 가져옵니다.
    최초 실행 시, 사용자가 수동으로 로그인해야 합니다.
    인증 정보는 user_data_dir에 저장되어 다음 실행부터 자동으로 사용됩니다.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./gemini_user_data",
            headless=False,
        )
        page = await browser.new_page()
        try:
            await page.goto("https://gemini.google.com/")
            print("Gemini 페이지에 접속했습니다. 로그인이 필요한 경우 수동으로 진행해주세요.")

            # 로그인 페이지가 나타나면 대기
            try:
                await page.wait_for_selector('a[href^="https://accounts.google.com"]', timeout=5000)
                print("로그인이 필요합니다. 30초 동안 로그인을 기다립니다...")
                await page.wait_for_timeout(30000)
            except:
                print("이미 로그인된 상태일 수 있습니다.")

            # 메인 질문 입력창 대기
            await page.wait_for_selector(".ql-editor.textarea", timeout=60000)
            print("Gemini 메인 페이지 로딩 완료.")

            # 질문 입력
            await page.click(".ql-editor.textarea")
            await page.keyboard.type(prompt)
            print(f"질문 입력: {prompt}")

            # 제출 버튼 클릭
            await page.click('button.send-button')
            print("질문 제출.")

            # 답변 로딩 대기 (프로그레스 바가 사라질 때까지)
            await page.wait_for_selector('progress-indicator.progress-bar', state='hidden', timeout=120000)
            print("답변 생성 완료.")
            await asyncio.sleep(2) # 렌더링 대기

            # 답변 추출
            response_element = await page.query_selector("response-component:last-of-type message-content")
            if response_element:
                response_text = await response_element.inner_text()
                print("답변 추출 완료.")
                return response_text.strip()
            else:
                return "답변을 찾을 수 없습니다."

        except Exception as e:
            return f"오류가 발생했습니다: {e}"
        finally:
            await browser.close()

async def get_claude_response(prompt: str) -> str:
    """
    Claude.ai에 접속하여 질문에 대한 답변을 가져옵니다.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./claude_user_data",
            headless=False,
        )
        page = await browser.new_page()
        try:
            await page.goto("https://claude.ai/")
            print("Claude 페이지에 접속했습니다. 로그인이 필요한 경우 수동으로 진행해주세요.")

            try:
                await page.wait_for_selector('text="Continue with email"', timeout=5000)
                print("로그인이 필요합니다. 30초 동안 로그인을 기다립니다...")
                await page.wait_for_timeout(30000)
            except:
                print("이미 로그인된 상태일 수 있습니다.")

            # 메인 입력창 대기
            editor_selector = 'div[contenteditable="true"]'
            await page.wait_for_selector(editor_selector, timeout=60000)
            print("Claude 메인 페이지 로딩 완료.")

            # 질문 입력
            await page.fill(editor_selector, prompt)
            print(f"질문 입력: {prompt}")

            # 제출 버튼 클릭
            await page.click('button[aria-label="Send Message"]')
            print("질문 제출.")

            # 답변 로딩 대기 (stop 버튼이 사라질 때까지)
            stop_button_selector = 'button[aria-label="Stop generating"]'
            await page.wait_for_selector(stop_button_selector, state='visible', timeout=10000)
            print("답변 생성 중...")
            await page.wait_for_selector(stop_button_selector, state='hidden', timeout=120000)
            print("답변 생성 완료.")

            await asyncio.sleep(2) # 렌더링 대기

            # 답변 추출
            response_elements = await page.query_selector_all("div[data-is-response='true']")
            if response_elements:
                last_response = response_elements[-1]
                response_text = await last_response.inner_text()
                print("답변 추출 완료.")
                return response_text.strip()
            else:
                return "답변을 찾을 수 없습니다."

        except Exception as e:
            return f"오류가 발생했습니다: {e}"
        finally:
            await browser.close()


async def get_copilot_response(prompt: str) -> str:
    """
    Microsoft Copilot에 접속하여 질문에 대한 답변을 가져옵니다.
    Shadow DOM 구조 때문에 locator를 사용하여 요소를 찾습니다.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./copilot_user_data",
            headless=False,
        )
        page = await browser.new_page()
        try:
            await page.goto("https://copilot.microsoft.com/")
            print("Copilot 페이지에 접속했습니다. 로그인이 필요한 경우 수동으로 진행해주세요.")

            # 로그인 확인
            try:
                await page.wait_for_selector('a:has-text("Sign in")', timeout=5000)
                print("로그인이 필요합니다. 30초 동안 로그인을 기다립니다...")
                await page.wait_for_timeout(30000)
            except:
                print("이미 로그인된 상태일 수 있습니다.")

            # Shadow DOM 내의 입력창 대기
            search_box_locator = page.locator('cib-serp').locator('cib-action-bar').locator('cib-text-input').locator('#searchbox')
            await search_box_locator.wait_for(timeout=60000)
            print("Copilot 메인 페이지 로딩 완료.")

            # 질문 입력 및 제출
            await search_box_locator.fill(prompt)
            print(f"질문 입력: {prompt}")

            submit_button_locator = page.locator('cib-serp').locator('cib-action-bar').locator('button[aria-label="Submit"]')
            await submit_button_locator.click()
            print("질문 제출.")

            # 답변 로딩 대기
            await page.wait_for_selector('cib-chat-turn[state="complete"]', timeout=120000)
            print("답변 생성 완료.")
            await asyncio.sleep(3) # 렌더링 대기

            # 답변 추출
            last_turn = page.locator('cib-chat-turn').last()
            response_groups = last_turn.locator('cib-message-group[source="bot"]')

            full_response = ""
            for i in range(await response_groups.count()):
                group = response_groups.nth(i)
                message_parts = group.locator("cib-message-part")
                for j in range(await message_parts.count()):
                     full_response += await message_parts.nth(j).inner_text() + "\n"

            print("답변 추출 완료.")
            return full_response.strip() if full_response else "답변을 찾을 수 없습니다."

        except Exception as e:
            return f"오류가 발생했습니다: {e}"
        finally:
            await browser.close()


async def get_wrtn_response(prompt: str) -> str:
    """
    뤼튼(Wrtn)에 접속하여 질문에 대한 답변을 가져옵니다.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./wrtn_user_data",
            headless=False,
        )
        page = await browser.new_page()
        try:
            await page.goto("https://wrtn.io/chat")
            print("뤼튼 페이지에 접속했습니다. 로그인이 필요한 경우 수동으로 진행해주세요.")

            try:
                await page.wait_for_selector('a:has-text("로그인")', timeout=5000)
                print("로그인이 필요합니다. 30초 동안 로그인을 기다립니다...")
                await page.wait_for_timeout(30000)
            except:
                print("이미 로그인된 상태일 수 있습니다.")

            # 메인 입력창 대기
            textarea_selector = 'textarea[placeholder*="에게 무엇이든 물어보세요"]'
            await page.wait_for_selector(textarea_selector, timeout=60000)
            print("뤼튼 메인 페이지 로딩 완료.")

            # 질문 입력 및 제출
            await page.fill(textarea_selector, prompt)
            print(f"질문 입력: {prompt}")

            # textarea 부모의 형제 button 클릭
            submit_button = page.locator(f'xpath=//textarea[@placeholder="뤼튼에게 무엇이든 물어보세요"]/../following-sibling::button')
            await submit_button.click()
            print("질문 제출.")

            # 답변 로딩 대기 (재생성 버튼이 나타날 때까지)
            await page.wait_for_selector('button:has-text("다시 생성")', timeout=120000)
            print("답변 생성 완료.")
            await asyncio.sleep(2)

            # 답변 추출
            response_elements = await page.query_selector_all('div[class^="ChatBubble_content"]')
            if response_elements:
                # 마지막 답변 element의 텍스트를 가져옴
                last_response_text = await response_elements[-1].inner_text()
                print("답변 추출 완료.")
                return last_response_text.strip()
            else:
                return "답변을 찾을 수 없습니다."

        except Exception as e:
            return f"오류가 발생했습니다: {e}"
        finally:
            await browser.close()


async def get_grok_response(prompt: str) -> str:
    """
    Grok에 접속하여 질문에 대한 답변을 가져옵니다.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./grok_user_data",
            headless=False,
        )
        page = await browser.new_page()
        try:
            await page.goto("https://grok.x.ai/") # Grok URL은 x.ai 도메인을 사용할 수 있습니다.
            print("Grok 페이지에 접속했습니다. 로그인이 필요한 경우 수동으로 진행해주세요.")

            try:
                # X 로그인 버튼 확인
                await page.wait_for_selector('button:has-text("Sign in with X")', timeout=5000)
                print("로그인이 필요합니다. 30초 동안 로그인을 기다립니다...")
                await page.wait_for_timeout(30000)
            except:
                print("이미 로그인된 상태일 수 있습니다.")

            # 메인 입력창 대기
            textarea_selector = 'textarea[placeholder*="Ask Grok"]'
            await page.wait_for_selector(textarea_selector, timeout=60000)
            print("Grok 메인 페이지 로딩 완료.")

            # 질문 입력 및 제출
            await page.fill(textarea_selector, prompt)
            print(f"질문 입력: {prompt}")

            await page.keyboard.press("Enter")
            print("질문 제출.")

            # 답변 로딩 대기
            await page.wait_for_selector('div[data-testid="conversation-turn-1"]', timeout=120000)
            print("답변 생성 중...")

            # 답변이 끝났는지 확인하는 로직 (예: 특정 요소가 사라지거나, 새로운 프롬프트 창이 활성화될 때까지)
            # 여기서는 마지막 답변 블록이 나타난 후 잠시 대기하는 방식으로 단순화
            await asyncio.sleep(5)
            print("답변 생성 완료.")

            # 답변 추출
            # Grok의 UI는 동적일 수 있어, 가장 마지막에 생성된 대화 블록을 선택
            response_elements = await page.query_selector_all('div[data-testid^="conversation-turn-"]')
            if response_elements:
                # 마지막 turn에서 답변 부분만 추출
                last_turn = response_elements[-1]
                answer_element = await last_turn.query_selector('div > div > div:nth-child(2)')
                if answer_element:
                    response_text = await answer_element.inner_text()
                    print("답변 추출 완료.")
                    return response_text.strip()

            return "답변을 찾을 수 없습니다."

        except Exception as e:
            return f"오류가 발생했습니다: {e}"
        finally:
            await browser.close()


async def get_genspark_response(prompt: str) -> str:
    """
    GenSpark에 접속하여 질문에 대한 답변을 가져옵니다.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir="./genspark_user_data",
            headless=False,
        )
        page = await browser.new_page()
        try:
            await page.goto("https://www.genspark.ai/")
            print("GenSpark 페이지에 접속했습니다. 로그인이 필요한 경우 수동으로 진행해주세요.")

            # GenSpark는 별도 로그인이 필요 없을 수 있음.
            # 메인 입력창 대기
            textarea_selector = 'textarea[placeholder*="Ask me anything"]'
            await page.wait_for_selector(textarea_selector, timeout=60000)
            print("GenSpark 메인 페이지 로딩 완료.")

            # 질문 입력 및 제출
            await page.fill(textarea_selector, prompt)
            print(f"질문 입력: {prompt}")

            await page.keyboard.press("Enter")
            print("질문 제출.")

            # 답변 페이지(Sparkpage) 로딩 대기
            # Sparkpage의 특정 컨테이너가 나타날 때까지 기다립니다.
            await page.wait_for_selector('div[class*="sparkpage_main"]', timeout=180000)
            print("Sparkpage 생성 완료.")
            await asyncio.sleep(5) # 콘텐츠 렌더링 대기

            # 답변 추출
            # Sparkpage는 복잡한 구조를 가질 수 있으므로, 메인 콘텐츠 영역의 텍스트를 추출
            main_content = await page.query_selector('div[class*="sparkpage_main"]')
            if main_content:
                response_text = await main_content.inner_text()
                print("답변 추출 완료.")
                return response_text.strip()
            else:
                return "Sparkpage 콘텐츠를 찾을 수 없습니다."

        except Exception as e:
            return f"오류가 발생했습니다: {e}"
        finally:
            await browser.close()


async def main():
    # 사용자로부터 질문을 입력받습니다.
    test_prompt = input("모든 AI에게 물어볼 질문을 입력하세요: ")
    if not test_prompt:
        test_prompt = "인공지능이 미래 사회에 미칠 영향에 대해 긍정적인 측면과 부정적인 측면을 모두 설명해줘."
        print(f"입력이 없어 기본 질문으로 실행합니다: {test_prompt}")

    all_responses = {}
    AIs_to_run = {
        "ChatGPT": get_chatgpt_response,
        "Gemini": get_gemini_response,
        "Claude": get_claude_response,
        "Copilot": get_copilot_response,
        "Wrtn": get_wrtn_response,
        "Grok": get_grok_response,
        "GenSpark": get_genspark_response,
    }

    for name, func in AIs_to_run.items():
        print(f"--- {name} 테스트 시작 ---")
        try:
            # 각 AI 함수에 프롬프트를 전달하여 실행
            answer = await func(test_prompt)
            all_responses[name] = answer
            print(f"\n[{name} 답변 요약]\n{answer[:200]}...") # 답변이 길 수 있으므로 요약 출력
        except Exception as e:
            error_message = f"!!! {name}에서 심각한 오류 발생: {e}"
            all_responses[name] = error_message
            print(error_message)
        finally:
            print("--------------------------\n")

    # 최종 결과 파일로 저장
    output_filename = "ai_responses.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(f"질문: {test_prompt}\n\n")
        for ai_name, response in all_responses.items():
            f.write(f"--- {ai_name} ---\n")
            f.write(response)
            f.write("\n\n" + "="*50 + "\n\n")

    print(f"모든 AI의 답변을 '{output_filename}' 파일에 저장했습니다.")


if __name__ == "__main__":
    asyncio.run(main())