# SolidWorks All-in-One Platform (v1.4 - Full Pipeline Prototype)

본 프로젝트는 SolidWorks 파일을 기반으로 STEP 변환, AI 렌더링, 광학 시뮬레이션을 수행하는 올인원 플랫폼의 프로토타입입니다. 현재 버전은 **변환, 렌더링, 광학 분석**이라는 3대 핵심 기능의 전체 파이프라인 골격을 모두 구현했습니다.

## 1. 주요 기능 및 아키텍처

- **동적 파이프라인:** 사용자가 UI에서 원본 파일을 변환하면, 생성된 중간 포맷 파일(`.obj`)이 **다음 렌더링 또는 광학 분석 작업의 입력으로 자동으로 사용**됩니다.
- **플랫폼별 변환 워커:** Windows에서는 실제 C# 워커(.exe)를, Linux/macOS에서는 `.obj` 파일을 생성하는 Python 시뮬레이터를 호출합니다.
- **다중 워커 연동:** 렌더링(Blender) 및 광학 분석(시뮬레이터)을 위한 별도의 API 엔드포인트, Celery 태스크, 워커 스크립트가 모두 구현되어 있습니다.
- **동적 프로필 선택:** 사용자가 UI에서 렌더링 및 광학 분석 프로필을 직접 선택하고, 이 설정이 각 작업에 정확히 반영됩니다.
- **비동기 작업 처리 (시뮬레이션):** Celery "eager" 모드를 사용하여, Redis 없이도 비동기 작업 흐름을 테스트할 수 있는 안정적인 구조를 갖추었습니다.

## 2. 설치 및 실행 방법

프로젝트를 실행하기 위해 **총 2개의 터미널**이 필요합니다.

### 2.1. 사전 요구사항

- [Node.js](https://nodejs.org/) (v20 LTS 권장)
- [Python](https://www.python.org/) (v3.11+ 권장)
- **Blender:** 렌더링 기능을 완전히 사용하려면, `blender` 명령어가 시스템 PATH에 등록되어 있어야 합니다.
- **(Windows 전용)** .NET Framework 4.8 개발 도구 및 SolidWorks 2017

### 2.2. 실행 순서

#### 단계 1: 오케스트레이터 (백엔드) 실행 (터미널 1)
1.  `pip install -r orchestrator/requirements.txt`로 의존성을 설치합니다.
2.  `uvicorn orchestrator.main:app --host 127.0.0.1 --port 8000` 명령어로 서버를 시작합니다.

#### 단계 2: UI (프론트엔드) 실행 (터미널 2)
1.  `npm install --prefix ./ui-electron`으로 의존성을 설치합니다.
2.  `npm start --prefix ./ui-electron` 명령어로 UI 애플리케이션을 실행합니다.

### 2.3. 동작 확인
이 시스템은 두 가지 주요 파이프라인(`Convert -> Render` 및 `Convert -> Optics`)을 지원합니다.

1.  **[1. Select File]** 버튼을 눌러 원본 `.SLDASM` 또는 `.SLDPRT` 파일을 선택합니다.
2.  **[2. Request STEP Conversion]** 버튼을 클릭합니다. 잠시 후, UI에 생성된 `.obj` 파일의 경로가 표시됩니다.

**렌더링 파이프라인 테스트:**
1.  **[3. Select Render Profile]** 드롭다운 메뉴에서 원하는 렌더링 품질을 선택합니다.
2.  **[4. Request Render]** 버튼을 클릭합니다.
3.  (환경에 따라) 작업이 성공 또는 예상된 실패로 완료되는지 확인합니다.

**광학 분석 파이프라인 테스트:**
1.  **[5. Select Optics Profile]** 드롭다운 메뉴에서 원하는 분석 프로필을 선택합니다.
2.  **[6. Request Optics Analysis]** 버튼을 클릭합니다.
3.  작업이 성공적으로 완료되고, UI에 상태가 표시되는지 확인합니다.

## 3. C# 워커 빌드 및 사용 (Windows 전용)

Windows에서 실제 변환 워커를 사용하려면, 이전 버전에 명시된 대로 `.NET` 프로젝트를 빌드해야 합니다.

## 4. 현재 상태 및 한계점
- **워커는 모두 시뮬레이션:** `convert`, `render`, `optics`의 모든 워커가 실제 작업을 수행하는 대신, **가짜(dummy) 결과 파일을 생성하는 시뮬레이션**으로 동작합니다.
- **Celery 동기 모드:** Redis가 없는 환경의 제약을 우회하기 위해 `task_always_eager=True` 모드로 동작하므로, 실제 비동기/병렬 처리는 이루어지지 않습니다.

## 5. 향후 개발 계획 (로드맵)
- **실제 워커 구현:** 현재 시뮬레이션으로 동작하는 모든 워커(`convert`, `render`, `optics`)를 실제 SolidWorks, Blender, LuxCore 등의 API를 사용하는 코드로 완성합니다.
- **통합 파이프라인 엔드포인트 구현:** `convert` -> `render` -> `optics` 작업을 순차적으로 실행하는 통합 파이프라인 API(`/jobs/pipeline`)를 구현합니다.
- **UI 기능 고도화:** 3D 뷰어에 단면, 측정 등 고급 기능을 추가하고, 작업 결과를 UI에 직접 시각화합니다.
- **운영 환경 전환:** Redis를 사용하는 실제 비동기 아키텍처로 전환하고, PostgreSQL과 같은 운영 수준 데이터베이스를 도입합니다.