#Requires AutoHotkey v2.0
#SingleInstance Force

; ==============================================================================
;           멀티 AI 채팅 자동화 스크립트 (Multi AI Chat Automation Script)
; ==============================================================================
;
; 이 스크립트는 여러 AI 채팅 웹사이트에 동시에 메시지를 전송하는 GUI 컨트롤러를
; 생성합니다. PowerToys의 FancyZones와 함께 사용하는 것을 권장합니다.
;
; 최종 수정: 2025-09-25
;
; ==============================================================================
; --- [중요] 사용자 설정 (User Configuration) ---
; ==============================================================================
;
; 아래 `AiServices` 목록은 자동화할 8개 브라우저 창의 정보입니다.
; 이 스크립트가 정확하게 동작하려면, 각 항목의 정보를 사용자의 환경에 맞게
; 수정해야 합니다. (자세한 방법은 SETUP_GUIDE.md 참조)
;
; [팁] 정보 확인 방법 (AutoHotkey의 'Window Spy' 유틸리티 사용):
; 1. Window Spy를 실행하고, 제어하려는 브라우저 창을 클릭합니다.
; 2. 'Window Title' -> `winTitle` 값으로 사용합니다.
; 3. 마우스를 입력창 위로 가져간 후, 'Control Under Mouse' 섹션에서
;    'ClassNN' 값을 찾아 `inputControl` 값으로 사용합니다.
; 4. 마우스를 전송 버튼 위로 가져가 `sendControl` 값을 찾습니다.
;    만약 전송 버튼이 없거나 Enter 키로 전송하는 경우, `sendControl` 값을 비워두세요.
;
; ==============================================================================
global AiServices := [
    ; 예시: {name: "표시 이름", winTitle: "창 제목 시작", inputControl: "입력창ClassNN", sendControl: "버튼ClassNN"}
    ; 아래 값들은 예시이며, 반드시 Window Spy로 확인 후 수정해야 합니다.
    {name: "ChatGPT",  winTitle: "ChatGPT",  inputControl: "Chrome_RenderWidgetHostHWND1", sendControl: ""},
    {name: "Claude",   winTitle: "Claude",   inputControl: "Chrome_RenderWidgetHostHWND1", sendControl: ""},
    {name: "Gemini",   winTitle: "Gemini",   inputControl: "Chrome_RenderWidgetHostHWND1", sendControl: ""},
    {name: "Grok",     winTitle: "Grok",     inputControl: "Chrome_RenderWidgetHostHWND1", sendControl: ""},
    {name: "뤼튼",      winTitle: "뤼튼",      inputControl: "Chrome_RenderWidgetHostHWND1", sendControl: ""},
    {name: "DeepSeek", winTitle: "DeepSeek", inputControl: "Chrome_RenderWidgetHostHWND1", sendControl: ""},
    {name: "Copilot",  winTitle: "Copilot",  inputControl: "Chrome_RenderWidgetHostHWND1", sendControl: ""},
    {name: "Jenspark", winTitle: "Jenspark", inputControl: "Chrome_RenderWidgetHostHWND1", sendControl: ""}
]

; ==============================================================================
; --- GUI 테마 설정 (GUI Theme Settings) ---
; ==============================================================================
global currentTheme := "Dark"
global Themes := {
    "Dark": {
        Bg: "333333", Text: "FFFFFF", InputBg: "555555", GroupBg: "444444", Button: "666666"
    },
    "Light": {
        Bg: "F0F0F0", Text: "000000", InputBg: "FFFFFF", GroupBg: "E0E0E0", Button: "DDDDDD"
    }
}

; ==============================================================================
; --- GUI 생성 (GUI Creation) ---
; ==============================================================================
MyGui := Gui(, "멀티 AI 채팅 컨트롤러")
MyGui.SetFont("s10", "Segoe UI")

; --- 1. AI 서비스 선택 체크박스 ---
MyGui.Add("GroupBox", "x10 y10 w200 h255", "AI 대상 선택").Name := "TargetGroup"
for index, service in AiServices {
    yPos := 40 + (index - 1) * 26
    MyGui.Add("Checkbox", "x20 y" yPos " w180 vAiCheckbox" index, service.name).Name := "Checkbox" . index
}

; --- 2. 메인 메시지 입력란 ---
MyGui.Add("Text", "x225 y15", "메시지").Name := "MainLabel"
MyGui.Add("Edit", "x225 y40 w550 h180 vMainInput WantTab").Name := "MainInput"

; --- 3. 추가 메시지 (접미사) ---
MyGui.Add("Text", "x225 y235", "추가 메시지 (선택 시 뒤에 붙여 전송)").Name := "SuffixLabel"
MyGui.Add("Checkbox", "x225 y265 w40 vSuffixCheck1", "1:").Name := "SuffixCheck1"
MyGui.Add("Edit", "x270 y262 w505 h25 vSuffixEdit1").Name := "SuffixEdit1"
MyGui.Add("Checkbox", "x225 y298 w40 vSuffixCheck2", "2:").Name := "SuffixCheck2"
MyGui.Add("Edit", "x270 y295 w505 h25 vSuffixEdit2").Name := "SuffixEdit2"
MyGui.Add("Checkbox", "x225 y331 w40 vSuffixCheck3", "3:").Name := "SuffixCheck3"
MyGui.Add("Edit", "x270 y328 w505 h25 vSuffixEdit3").Name := "SuffixEdit3"

; --- 4. 하단 버튼 ---
SendButton := MyGui.Add("Button", "x675 y365 w100 h30 Default", "전송 (&S)").Name := "SendButton"
SendButton.OnEvent("Click", SendButton_Click)
ThemeButton := MyGui.Add("Button", "x10 y365 w100 h30", "다크/라이트").Name := "ThemeButton"
ThemeButton.OnEvent("Click", ToggleTheme)

; --- GUI 이벤트 핸들러 및 초기화 ---
MyGui.OnEvent("Close", GuiClose)
ToggleTheme(MyGui, true) ; 초기 테마 적용 (강제 라이트 모드)
MyGui.Show("w790 h410")

Return ; 스크립트의 자동 실행 부분 끝

; ==============================================================================
; --- 함수 (Functions) ---
; ==============================================================================

/**
 * GUI의 테마를 다크/라이트 모드 간에 전환합니다.
 * @param guiObj {Gui} 이 함수를 호출한 컨트롤 객체 (보통 버튼).
 * @param forceLight {Boolean} true로 설정 시, 강제로 라이트 모드를 적용합니다.
 */
ToggleTheme(guiObj, forceLight := false) {
    global currentTheme, Themes, MyGui

    if (forceLight) {
        currentTheme := "Light"
    } else {
        currentTheme := (currentTheme == "Light") ? "Dark" : "Light"
    }

    theme := Themes[currentTheme]

    ; 1. 기본 창 배경색 변경
    MyGui.BackColor := theme.Bg

    ; 2. 모든 컨트롤에 대해 테마 적용
    for name, ctrl in MyGui.Controls {
        try {
            switch ctrl.Type {
                case "Text", "Checkbox":
                    ctrl.Opt("c" . theme.Text)
                case "GroupBox":
                    ctrl.Opt("c" . theme.Text)
                    ; GroupBox는 배경색 변경을 지원하지 않음
                case "Edit":
                    ctrl.Opt("c" . theme.Text . " Background" . theme.InputBg)
                case "Button":
                     ; 버튼은 기본 테마를 따르게 하거나, 필요 시 색상 지정
                    ctrl.Opt("c" . theme.Text)
            }
        } catch as e {
            ; 색상 변경 실패 시 오류 무시 (일부 컨트롤은 지원하지 않을 수 있음)
        }
    }

    ; 테마 버튼 텍스트 업데이트 (액션을 명확하게 표시)
    MyGui.Controls["ThemeButton"].Text := (currentTheme == "Light") ? "다크 모드로" : "라이트 모드로"
}


/**
 * "전송" 버튼을 클릭했을 때 실행되는 지능형 전송 함수.
 * 이 함수는 창을 활성화하지 않고 백그라운드에서 제어합니다.
 * 1. GUI에서 데이터를 수집합니다.
 * 2. ControlSend로 지정된 입력창에 텍스트를 직접 전송합니다.
 * 3. ControlClick으로 지정된 버튼을 클릭하거나, 설정되지 않은 경우 Enter 키를 보냅니다.
 * 4. 작업 완료 후 성공/실패 결과를 보고합니다.
 */
SendButton_Click(*) {
    ; --- 1. 데이터 수집 및 유효성 검사 ---
    guiData := MyGui.Submit(false)

    finalMessage := guiData.MainInput
    if (guiData.SuffixCheck1 && Trim(guiData.SuffixEdit1) != "") {
        finalMessage .= "`n" . guiData.SuffixEdit1
    }
    if (guiData.SuffixCheck2 && Trim(guiData.SuffixEdit2) != "") {
        finalMessage .= "`n" . guiData.SuffixEdit2
    }
    if (guiData.SuffixCheck3 && Trim(guiData.SuffixEdit3) != "") {
        finalMessage .= "`n" . guiData.SuffixEdit3
    }

    selectedAiIndexes := []
    Loop AiServices.Length {
        if (guiData["AiCheckbox" . A_Index]) {
            selectedAiIndexes.Push(A_Index)
        }
    }

    if (selectedAiIndexes.Length == 0) {
        MsgBox("전송할 AI 대상을 하나 이상 선택해주세요.", "알림", "48")
        return
    }

    if (Trim(finalMessage) == "") {
        MsgBox("전송할 메인 메시지를 입력해주세요.", "알림", "48")
        return
    }

    ; --- 2. 지능형 전송 로직 실행 ---
    MyGui.Enabled := false ; 처리 중 GUI 비활성화
    SetTitleMatchMode("startswith")

    successCount := 0
    failCount := 0
    failedServices := ""

    for i in selectedAiIndexes {
        service := AiServices[i]

        if WinExist(service.winTitle) {
            ; ControlSend는 창이 비활성화 상태여도 텍스트를 보낼 수 있습니다.
            ControlSend(service.inputControl, finalMessage, service.winTitle)
            Sleep(200) ; 웹사이트가 텍스트 입력을 처리할 시간을 줌

            if (service.sendControl && Trim(service.sendControl) != "") {
                ; sendControl 값이 있으면 해당 버튼 클릭
                ControlClick(service.sendControl, service.winTitle)
            } else {
                ; sendControl 값이 없으면 입력창에 Enter 키 전송
                ControlSend(service.inputControl, "{Enter}", service.winTitle)
            }
            successCount++
            Sleep(300)
        } else {
            failCount++
            failedServices .= "- " . service.name . "`n"
        }
    }

    MyGui.Enabled := true ; GUI 다시 활성화

    ; --- 3. 결과 보고 ---
    resultMessage := "전송 완료!`n`n- 성공: " . successCount . "건`n- 실패: " . failCount . "건"
    if (failCount > 0) {
        resultMessage .= "`n`n[실패 목록]`n" . Trim(failedServices, "`n")
    }
    MsgBox(resultMessage, "전송 결과", "64")
}

/**
 * GUI 창의 닫기 버튼을 누르면 스크립트를 완전히 종료합니다.
 */
GuiClose(*) {
    ExitApp
}