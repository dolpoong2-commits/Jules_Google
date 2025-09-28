@echo off
echo ======================================================
echo  ESP32 AI 데이터 수집기 - 자동 설정 및 시작 스크립트
echo ======================================================
echo.

REM --- 1. Python 설치 확인 ---
echo [1/5] Python 설치 여부를 확인합니다...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [오류] Python이 설치되어 있지 않거나 PATH에 등록되지 않았습니다.
    echo https://www.python.org/downloads/ 에서 Python을 먼저 설치해주세요.
    echo (설치 시 "Add Python to PATH" 옵션을 반드시 체크하세요.)
    pause
    exit /b
)
echo Python이 확인되었습니다.
echo.

REM --- 2. 가상환경 생성 ---
echo [2/5] 가상환경을 설정합니다...
if not exist venv (
    echo 'venv' 가상환경 폴더를 생성합니다. 잠시 기다려주세요...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [오류] 가상환경 생성에 실패했습니다.
        pause
        exit /b
    )
)
echo 가상환경이 준비되었습니다.
echo.

REM --- 3. 의존성 라이브러리 설치 ---
echo [3/5] 필요한 라이브러리를 설치합니다 (Flask, Requests, Playwright).
call venv\Scripts\activate.bat
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [오류] 라이브러리 설치에 실패했습니다. 인터넷 연결을 확인해주세요.
    pause
    exit /b
)
echo 라이브러리 설치가 완료되었습니다.
echo.

REM --- 4. Playwright 브라우저 설치 ---
echo [4/5] Playwright에 필요한 웹 브라우저를 설치합니다.
echo 이 작업은 처음 실행 시 몇 분 정도 소요될 수 있습니다.
playwright install
if %errorlevel% neq 0 (
    echo [오류] Playwright 브라우저 설치에 실패했습니다.
    pause
    exit /b
)
echo 브라우저 설치가 완료되었습니다.
echo.

REM --- 5. 웹 애플리케이션 실행 ---
echo [5/5] 웹 애플리케이션을 시작합니다...
echo.
echo 웹 브라우저에서 http://127.0.0.1:5001 주소로 접속하세요.
echo.
echo 이 창을 닫으면 서버가 종료됩니다.
python web_scraper_ui/app.py

echo.
echo 서버가 종료되었습니다.
pause