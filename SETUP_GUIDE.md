# 멀티 AI 채팅 환경 설정 가이드 (v2)

이 문서는 PowerToys와 AutoHotkey를 사용하여 멀티 AI 채팅 환경을 구축하고, 스크립트를 개인 환경에 맞게 설정하는 방법을 안내합니다.

---

## 1. 기본 프로그램 설치

### 1.1. PowerToys 설치 (화면 분할용)
1.  Windows의 **Microsoft Store**에서 `PowerToys`를 검색하여 설치합니다.
2.  PowerToys 설정 > **FancyZones** > **레이아웃 편집기 시작**으로 갑니다.
3.  **"+ 새 레이아웃 만들기"**를 눌러 원하는 분할(예: 8분할) 레이아웃을 만들고 저장합니다.
4.  `Shift` 키를 누른 채 브라우저 창을 끌어다 놓아 8개의 AI 채팅창을 배치합니다.

### 1.2. AutoHotkey 설치 (스크립트 실행용)
1.  [AutoHotkey 공식 웹사이트](https://www.autohotkey.com/)에서 **v2.0 이상 버전**을 다운로드하여 설치합니다.
2.  바탕화면이나 원하는 폴더에 `MultiAiChat.ahk` 라는 이름으로 스크립트 파일을 생성합니다.
3.  이후 단계에서 제공될 코드를 이 파일에 복사하여 붙여넣습니다.

---

## 2. `MultiAiChat.ahk` 스크립트 설정하기 (매우 중요!)

이 스크립트는 각 AI 채팅 사이트의 **창 정보**와 **컨트롤 정보**를 알아야 정확하게 동작합니다. 아래 가이드를 따라 스크립트 상단의 `AiServices` 목록을 반드시 수정해야 합니다.

### Window Spy 사용 방법

**Window Spy**는 AutoHotkey를 설치하면 함께 제공되는, 창과 컨트롤 정보를 확인하는 강력한 도구입니다.
-   **실행 방법**: 시작 메뉴에서 `Window Spy`를 검색하여 실행하거나, 실행 중인 AutoHotkey 스크립트의 트레이 아이콘을 더블클릭합니다.

### 단계별 정보 확인 및 설정

`MultiAiChat.ahk` 파일을 열고, `AiServices` 목록의 각 항목을 아래 순서대로 수정합니다.

```autohotkey
; 예시: {name: "표시 이름", winTitle: "창 제목 시작", inputControl: "입력창ClassNN", sendControl: "버튼ClassNN"}
{name: "ChatGPT",  winTitle: "ChatGPT",  inputControl: "Chrome_RenderWidgetHostHWND1", sendControl: ""},
```

1.  **`winTitle` (창 제목) 확인:**
    -   정보를 확인할 브라우저 창을 클릭합니다.
    -   Window Spy 창의 상단 `Window Title, Class and Process` 섹션에서 `ahk_exe chrome.exe` 와 같은 정보 바로 위에 있는 **창 제목**을 확인합니다.
    -   이 제목의 시작 부분을 복사하여 `winTitle` 값으로 붙여넣습니다. (예: `ChatGPT - Google Chrome` -> `"ChatGPT"`)

2.  **`inputControl` (입력창 정보) 확인:**
    -   브라우저 창에서 **메시지를 입력하는 텍스트 영역** 위로 마우스 커서를 가져갑니다. (클릭하지 마세요)
    -   Window Spy 창의 중간 `Control Under Mouse Position` 섹션을 봅니다.
    -   `ClassNN` 필드에 있는 값 (예: `Chrome_RenderWidgetHostHWND1`)을 복사하여 `inputControl` 값으로 붙여넣습니다.

3.  **`sendControl` (전송 버튼 정보) 확인:**
    -   브라우저 창에서 **메시지 전송 버튼** 위로 마우스 커서를 가져갑니다.
    -   Window Spy의 `ClassNN` 필드에 있는 값을 복사하여 `sendControl` 값으로 붙여넣습니다.
    -   **만약 전송 버튼이 없거나, 그냥 Enter 키로 메시지를 보내는 사이트라면?** -> 이 `sendControl` 값을 **빈 따옴표(`""`)**로 남겨두세요. 스크립트가 알아서 Enter 키를 보냅니다.

**모든 8개 서비스에 대해 이 과정을 반복하여 설정을 완료해주세요.** 설정이 정확하지 않으면 스크립트가 제대로 동작하지 않습니다.

---

## 3. 스크립트 실행 및 종료

-   **실행**: 설정이 완료된 `MultiAiChat.ahk` 파일을 더블클릭하여 실행합니다.
-   **종료**: 작업 표시줄 트레이 아이콘 영역의 녹색 'H' 아이콘을 마우스 오른쪽 버튼으로 클릭하고 `Exit`를 선택합니다.