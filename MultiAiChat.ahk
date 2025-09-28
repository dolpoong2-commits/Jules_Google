#Requires AutoHotkey v2.0
#SingleInstance Force

; ==============================================================================
;           멀티 AI 채팅 컨트롤러 - v7 (오류 수정 최종)
; ==============================================================================

; --- 기본 설정 ---
global IniFile := A_ScriptDir . "\settings.ini"
global ChatCoordinates := [], ChatCount := 8, currentTheme := "Sunrising"
global Themes := {
    "Sunrising": { Bg: "FFF2E6", Text: "5C3D2E", InputBg: "FFFFFF", ButtonBg: "FFDAB9" },
    "Dark":      { Bg: "2B2B2B", Text: "EAEAEA", InputBg: "3C3F41", ButtonBg: "4A4A4A" },
    "Light":     { Bg: "F5F5F5", Text: "000000", InputBg: "FFFFFF", ButtonBg: "E0E0E0" },
    "Retro":     { Bg: "C8B499", Text: "3A2F2F", InputBg: "EAE0D1", ButtonBg: "B4A28A" },
    "Cyberpunk": { Bg: "0D0221", Text: "00FFCC", InputBg: "261447", ButtonBg: "261447" },
    "Minimalism":{ Bg: "FFFFFF", Text: "000000", InputBg: "F0F0F0", ButtonBg: "E0E0E0" }
}
global Scenario := [], AdvConvGui := "", SettingsGui := ""
global ContinueConversation := true, originalClipboard := ""

; ==============================================================================
; --- 메인 GUI 생성 ---
; ==============================================================================
MyGui := Gui(, "멀티 AI 채팅 컨트롤러")
MyGui.SetFont("s10", "Segoe UI")
MyGui.Add("GroupBox", "x10 y10 w200 h350", "대상 선택").Name := "TargetGroup"
Loop 8 {
    yPos := 40 + (A_Index - 1) * 28
    MyGui.Add("Checkbox", "x25 y" yPos " w170 vAiCheckbox" . A_Index, "채팅창 " . A_Index).Name := "Checkbox" . A_Index
}
MyGui.Add("Button", "x25 y290 w170 h30", "모두 선택").OnEvent("Click", SelectAllCheckboxes)
MyGui.Add("Button", "x25 y325 w170 h30", "모두 해제").OnEvent("Click", DeselectAllCheckboxes)
MyGui.Add("Text", "x230 y15", "메인 메시지").Name := "MainLabel"
MyGui.Add("Edit", "x230 y40 w550 h150 vMainInput WantTab").Name := "MainInput"
MyGui.Add("Text", "x230 y205", "추가 메시지").Name := "SuffixLabel"
MyGui.Add("Checkbox", "x230 y235 w40 vSuffixCheck1", "1:").Name := "SuffixCheck1"
MyGui.Add("Edit", "x275 y232 w505 h25 vSuffixEdit1").Name := "SuffixEdit1"
MyGui.Add("Checkbox", "x230 y268 w40 vSuffixCheck2", "2:").Name := "SuffixCheck2"
MyGui.Add("Edit", "x275 y265 w505 h25 vSuffixEdit2").Name := "SuffixEdit2"
MyGui.Add("Checkbox", "x230 y301 w40 vSuffixCheck3", "3:").Name := "SuffixCheck3"
MyGui.Add("Edit", "x275 y298 w505 h25 vSuffixEdit3").Name := "SuffixEdit3"
MyGui.Add("Button", "x230 y365 w100 h30", "좌표 설정").OnEvent("Click", SetupCoordinates)
MyGui.Add("Button", "x335 y365 w100 h30", "고급 대화").OnEvent("Click", ShowAdvancedConversationGui)
MyGui.Add("Button", "x440 y365 w70 h30", "설정").OnEvent("Click", ShowSettingsGui)
MyGui.Add("Text", "x520 y372", "테마:").Name := "ThemeLabel"
themeList := ""
for themeName in Themes.OwnKeys()
    themeList .= themeName . "|"
MyGui.Add("DropDownList", "x565 y368 w100 vSelectedTheme Choose1", RTrim(themeList, "|")).OnEvent("Change", ApplyTheme)
MyGui.Add("Text", "x675 y372", "상태:").Name := "StatusLabel"
MyGui.Add("Text", "x720 y372 w55 h20", "불러오는 중...").Name := "StatusValue"
MyGui.Add("Button", "x730 y365 w65 h30 Default", "전송(&S)").OnEvent("Click", SendButton_Click)
MyGui.OnEvent("Close", GuiClose)

LoadSettings()
UpdateChatCheckboxes()
ApplyTheme()
MyGui.Show("w800 h410")
Return

; ==============================================================================
; --- 함수 (Functions) ---
; ==============================================================================

; --- 설정 및 GUI 업데이트 함수 ---
LoadSettings() {
    global IniFile, ChatCount, ChatCoordinates
    ChatCount := IniRead(IniFile, "Settings", "ChatCount", 8)
    ChatCoordinates := []
    Loop ChatCount {
        x := IniRead(IniFile, "Coordinates", "X" . A_Index, "")
        y := IniRead(IniFile, "Coordinates", "Y" . A_Index, "")
        if (x != "" && y != "")
            ChatCoordinates.Push({x: x, y: y})
    }
    UpdateStatus()
}
SaveSettings() {
    global IniFile, SettingsGui, ChatCount
    guiData := SettingsGui.Submit()
    newChatCount := guiData.ChatCount
    IniWrite(newChatCount, IniFile, "Settings", "ChatCount")
    ChatCount := newChatCount
    SettingsGui.Destroy()
    MsgBox("설정이 저장되었습니다. 메인 창에 반영됩니다.", "알림", 64)
    UpdateChatCheckboxes()
    UpdateStatus()
}
UpdateChatCheckboxes() {
    global MyGui, ChatCount
    Loop 8 {
        checkbox := MyGui.Controls["Checkbox" . A_Index]
        if (A_Index <= ChatCount)
            checkbox.Show()
        else
            checkbox.Hide()
    }
}
UpdateStatus() {
    global ChatCoordinates, MyGui, currentTheme, ChatCount
    try {
        statusText := MyGui.Controls["StatusValue"]
        if (ChatCoordinates.Length == ChatCount) {
            statusText.Text := "준비 완료"
            statusText.Opt("c" . (currentTheme == "Light" ? "009900" : (currentTheme == "Dark" || currentTheme == "Cyberpunk" ? "33FF33" : "006400")))
        } else {
            statusText.Text := "좌표 설정 필요"
            statusText.Opt("c" . (currentTheme == "Light" ? "DD0000" : (currentTheme == "Dark" || currentTheme == "Cyberpunk" ? "FF5555" : "B22222")))
        }
    }
}
ShowSettingsGui(*) {
    global SettingsGui, ChatCount
    SettingsGui := Gui(, "설정")
    SettingsGui.SetFont("s10", "Segoe UI")
    SettingsGui.Add("Text", "x10 y15", "사용할 채팅창 개수:")
    ddl := SettingsGui.Add("DropDownList", "x10 y40 w100 vChatCount", "1|2|3|4|5|6|7|8")
    ddl.Value := ChatCount
    SettingsGui.Add("Button", "x140 y90 w80 h30 Default", "저장").OnEvent("Click", SaveSettings)
    SettingsGui.Add("Button", "x230 y90 w80 h30", "취소").OnEvent("Click", (*) => SettingsGui.Destroy())
    SettingsGui.OnEvent("Close", (*) => SettingsGui.Destroy())
    SettingsGui.Show("w330 h140")
}

; --- 좌표 설정 함수 ---
SetupCoordinates(*) {
    global ChatCount, IniFile
    MyGui.Hide()
    Sleep(300)
    CoordMode "Mouse", "Screen"
    tempCoords := []
    Loop ChatCount {
        ToolTip("채팅창 " . A_Index . "의 입력창을 클릭하세요...",,, 1)
        KeyWait "LButton", "D"
        MouseGetPos &x, &y
        tempCoords.Push({x: x, y: y})
        ToolTip()
        KeyWait "LButton", "U"
        Sleep(200)
    }
    Loop tempCoords.Length {
        coord := tempCoords[A_Index]
        IniWrite(coord.x, IniFile, "Coordinates", "X" . A_Index)
        IniWrite(coord.y, IniFile, "Coordinates", "Y" . A_Index)
    }
    LoadSettings()
    MyGui.Show()
    MsgBox(ChatCount . "개의 좌표 설정이 완료되었습니다!", "알림", "64")
}

; --- 일반 메시지 전송 함수 ---
SendButton_Click(*) {
    global ChatCoordinates, MyGui, ChatCount
    guiData := MyGui.Submit(false)
    finalMessage := guiData.MainInput
    if (guiData.SuffixCheck1 && Trim(guiData.SuffixEdit1) != "")
        finalMessage .= "`n" . guiData.SuffixEdit1
    if (guiData.SuffixCheck2 && Trim(guiData.SuffixEdit2) != "")
        finalMessage .= "`n" . guiData.SuffixEdit2
    if (guiData.SuffixCheck3 && Trim(guiData.SuffixEdit3) != "")
        finalMessage .= "`n" . guiData.SuffixEdit3
    selectedIndexes := []
    Loop ChatCount {
        if (guiData["AiCheckbox" . A_Index])
            selectedIndexes.Push(A_Index)
    }
    if (selectedIndexes.Length == 0) {
        MsgBox("전송할 AI 대상을 하나 이상 선택해주세요.", "알림", 48)
        return
    }
    if (Trim(finalMessage) == "") {
        MsgBox("전송할 메인 메시지를 입력해주세요.", "알림", 48)
        return
    }
    if (ChatCoordinates.Length < ChatCount) {
        MsgBox("좌표가 모두 설정되지 않았습니다. '좌표 설정' 버튼을 눌러 " . ChatCount . "개의 좌표를 모두 설정해주세요.", "설정 오류", 16)
        return
    }
    MyGui.Enabled := false
    CoordMode "Mouse", "Screen"
    MouseGetPos &originalX, &originalY
    originalClipboard := A_Clipboard
    A_Clipboard := finalMessage
    ClipWait 1
    for i in selectedIndexes {
        coord := ChatCoordinates[i]
        Click(coord.x, coord.y)
        Sleep(100)
        Send("^v")
        Sleep(100)
        Send("{Enter}")
        Sleep(300)
    }
    A_Clipboard := originalClipboard
    MouseMove(originalX, originalY, 0)
    MyGui.Enabled := true
    MsgBox(selectedIndexes.Length . "개의 채팅창에 전송을 시도했습니다.", "전송 완료", "64")
}

; --- 고급 대화 모드 관련 함수 ---
ShowAdvancedConversationGui(*) {
    global AdvConvGui, Scenario, ChatCount
    AdvConvGui := Gui(, "고급 대화 모드 설정")
    AdvConvGui.SetFont("s10", "Segoe UI")
    AdvConvGui.Add("Text", "x10 y15", "대화 시나리오 (실행 순서):")
    AdvConvGui.Add("ListBox", "x10 y40 w250 h200 vSelectedStep").Name := "ScenarioList"
    AdvConvGui.Add("Button", "x10 y250 w55 h30", "추가").OnEvent("Click", AddScenarioStep)
    AdvConvGui.Add("Button", "x75 y250 w55 h30", "수정").OnEvent("Click", ModifyScenarioStep)
    AdvConvGui.Add("Button", "x140 y250 w55 h30", "삭제").OnEvent("Click", DeleteScenarioStep)
    AdvConvGui.Add("Button", "x205 y250 w25 h30", "▲").OnEvent("Click", (*) => MsgBox("기능 구현 예정"))
    AdvConvGui.Add("Button", "x235 y250 w25 h30", "▼").OnEvent("Click", (*) => MsgBox("기능 구현 예정"))
    AdvConvGui.Add("Text", "x280 y15", "첫 질문 (1단계에서 사용할 메시지):")
    AdvConvGui.Add("Edit", "x280 y40 w300 h100 vFirstQuestion WantTab")
    AdvConvGui.Add("Text", "x280 y155", "시나리오 반복 횟수:")
    AdvConvGui.Add("Edit", "x280 y180 w80 vLoopCount", "1")
    AdvConvGui.Add("Button", "x10 y300 w120 h30", "시나리오 저장").OnEvent("Click", (*) => MsgBox("기능 구현 예정"))
    AdvConvGui.Add("Button", "x140 y300 w120 h30", "시나리오 불러오기").OnEvent("Click", (*) => MsgBox("기능 구현 예정"))
    AdvConvGui.Add("Button", "x480 y300 w100 h30 Default", "대화 시작").OnEvent("Click", StartAdvancedConversation)
    AdvConvGui.Add("Button", "x370 y300 w100 h30", "취소").OnEvent("Click", (*) => AdvConvGui.Destroy())
    AdvConvGui.OnEvent("Close", (*) => AdvConvGui.Destroy())
    UpdateScenarioDisplay()
    AdvConvGui.Show("w600 h350")
}
AddScenarioStep(*) { ShowStepEditorGui() }
ModifyScenarioStep(*) {
    global AdvConvGui
    guiData := AdvConvGui.Submit(false)
    if (guiData.SelectedStep == 0) {
        MsgBox("수정할 단계를 목록에서 선택하세요.", "알림", 48)
        return
    }
    ShowStepEditorGui(guiData.SelectedStep)
}
DeleteScenarioStep(*) {
    global AdvConvGui, Scenario
    guiData := AdvConvGui.Submit(false)
    if (guiData.SelectedStep == 0) {
        MsgBox("삭제할 단계를 목록에서 선택하세요.", "알림", 48)
        return
    }
    Scenario.RemoveAt(guiData.SelectedStep)
    UpdateScenarioDisplay()
}
ShowStepEditorGui(stepIndex := -1) {
    global Scenario, ChatCount
    isEditMode := stepIndex != -1
    title := isEditMode ? "단계 수정" : "단계 추가"
    StepEditorGui := Gui(, title)
    StepEditorGui.SetFont("s10", "Segoe UI")
    chatList := ""
    Loop ChatCount
        chatList .= "AI " . A_Index . "|"
    chatList := RTrim(chatList, "|")
    StepEditorGui.Add("Text", "x10 y15", "보내는 AI (From):")
    fromDdl := StepEditorGui.Add("DropDownList", "x10 y40 w150 vFromAi Choose1", chatList)
    StepEditorGui.Add("Text", "x180 y15", "받는 AI (To):")
    toDdl := StepEditorGui.Add("DropDownList", "x180 y40 w150 vToAi Choose1", chatList)
    if (isEditMode) {
        fromDdl.Value := "AI " . Scenario[stepIndex].from
        toDdl.Value := "AI " . Scenario[stepIndex].to
    }
    StepEditorGui.Add("Button", "x100 y90 w70 h30 Default", "확인").OnEvent("Click", (ctrl, *) => {
        data := StepEditorGui.Submit()
        fromAiNum := SubStr(data.FromAi, 4)
        toAiNum := SubStr(data.ToAi, 4)
        if (fromAiNum == toAiNum) {
            MsgBox("보내는 AI와 받는 AI는 달라야 합니다.", "오류", 16)
            return
        }
        newStep := { from: fromAiNum, to: toAiNum }
        if (isEditMode)
            Scenario[stepIndex] := newStep
        else
            Scenario.Push(newStep)
        UpdateScenarioDisplay()
        StepEditorGui.Destroy()
    })
    StepEditorGui.Add("Button", "x180 y90 w70 h30", "취소").OnEvent("Click", (*) => StepEditorGui.Destroy())
    StepEditorGui.Show("w340 h140")
}
UpdateScenarioDisplay() {
    global AdvConvGui, Scenario
    if !AdvConvGui.Hwnd
        return
    listBox := AdvConvGui.Controls["ScenarioList"]
    listBox.Delete()
    if (Scenario.Length == 0) {
        listBox.Add("(비어있음) '추가' 버튼으로 단계를 만드세요.")
    } else {
        For index, step in Scenario {
            listBox.Add(index . "단계: AI " . step.from . " -> AI " . step.to)
        }
    }
}
StartAdvancedConversation(*) {
    global ChatCoordinates, MyGui, AdvConvGui, Scenario, ContinueConversation, originalClipboard, ChatCount
    advGuiData := AdvConvGui.Submit(false)
    loopCount := advGuiData.LoopCount
    currentMessage := advGuiData.FirstQuestion
    if (Scenario.Length == 0) {
        MsgBox("대화 시나리오에 최소 1개 이상의 단계를 추가해야 합니다.", "설정 오류", 16)
        return
    }
    if !(IsInteger(loopCount) && loopCount > 0) {
        MsgBox("반복 횟수는 0보다 큰 숫자여야 합니다.", "설정 오류", 16)
        return
    }
    if (Trim(currentMessage) == "") {
        MsgBox("첫 질문을 입력해주세요.", "설정 오류", 16)
        return
    }
    if (ChatCoordinates.Length < ChatCount) {
        MsgBox("좌표가 모두 설정되지 않았습니다. '좌표 설정' 버튼을 눌러 " . ChatCount . "개의 좌표를 모두 설정해주세요.", "설정 오류", 16)
        return
    }
    MyGui.Hide()
    AdvConvGui.Destroy()
    Sleep(300)
    CoordMode "Mouse", "Screen"
    originalClipboard := A_ClipboardAll
    ContinueConversation := true
    Hotkey "~Esc", EscToExit, "On"
    Loop loopCount {
        if !ContinueConversation
            break
        loopNum := A_Index
        For stepNum, step in Scenario {
            if !ContinueConversation
                break 2
            fromAiIndex := step.from
            ToolTip("반복 " . loopNum . "/" . loopCount . " | 단계 " . stepNum . "/" . Scenario.Length . " | AI " . fromAiIndex . "에게 전송 중...`n(Esc 키로 중단)",,, 2)
            coord := ChatCoordinates[fromAiIndex]
            Click(coord.x, coord.y)
            Sleep(100)
            A_Clipboard := currentMessage
            ClipWait(1)
            Send("^v")
            Sleep(100)
            Send("{Enter}")
            ToolTip("반복 " . loopNum . "/" . loopCount . " | 단계 " . stepNum . "/" . Scenario.Length . " | AI " . fromAiIndex . " 답변 대기 중...`n(Esc 키로 중단)",,, 2)
            lastClipboard := currentMessage
            captureSuccess := false
            Loop 6 {
                if !ContinueConversation
                    break 2
                Sleep(5000)
                Click(coord.x, coord.y)
                Sleep(100)
                A_Clipboard := ""
                Send("^a")
                Sleep(200)
                Send("^c")
                ClipWait(1)
                if (A_Clipboard != "" && A_Clipboard != lastClipboard) {
                    currentMessage := A_Clipboard
                    captureSuccess := true
                    break
                }
            }
            if !captureSuccess {
                RestoreAndShowGui("AI " . fromAiIndex . "의 답변을 캡처하는 데 실패하여 대화를 중단합니다.")
                return
            }
        }
    }
    RestoreAndShowGui("고급 대화 모드가 완료되었습니다.")
}
EscToExit(*) {
    global ContinueConversation
    ContinueConversation := false
}
RestoreAndShowGui(msg) {
    global originalClipboard
    ToolTip()
    Hotkey("~Esc", EscToExit, "Off")
    A_Clipboard := originalClipboard
    MyGui.Show()
    MsgBox(msg, "알림", 64)
}

; --- 테마 및 기타 UI 함수 ---
ApplyTheme(*) {
    global currentTheme, Themes, MyGui
    guiData := MyGui.Submit(false)
    currentTheme := guiData.SelectedTheme ? guiData.SelectedTheme : currentTheme
    theme := Themes[currentTheme]
    MyGui.BackColor := theme.Bg
    for name, ctrl in MyGui.Controls {
        try {
            switch ctrl.Type {
                case "Text", "Checkbox", "GroupBox":
                    ctrl.Opt("c" . theme.Text)
                case "Edit":
                    ctrl.Opt("c" . theme.Text . " Background" . theme.InputBg)
                case "Button", "DropDownList":
                    ctrl.Opt("c" . theme.Text)
            }
        } catch {}
    }
    UpdateStatus()
}
SelectAllCheckboxes(*) {
    global ChatCount
    Loop ChatCount
        MyGui.Controls["Checkbox" . A_Index].Value := 1
}
DeselectAllCheckboxes(*) {
    global ChatCount
    Loop ChatCount
        MyGui.Controls["Checkbox" . A_Index].Value := 0
}
GuiClose(*) { ExitApp }