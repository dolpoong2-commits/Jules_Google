# SolidWorks STEP 변환기: 빌드 및 실행 가이드

이 문서는 제공된 소스 코드(`MainWindow.xaml`, `MainWindow.xaml.cs`)를 사용하여 실제 Windows 데스크톱 애플리케이션(.exe)을 만드는 방법을 안내합니다.

---

### 1단계: 개발 환경 준비 (Visual Studio 설치)

C# 코드를 컴파일하고 실행 파일을 만들려면 **Visual Studio**라는 Microsoft의 무료 개발 도구가 필요합니다.

1.  **[Visual Studio Community 다운로드 페이지](https://visualstudio.microsoft.com/ko/vs/community/)**로 이동합니다.
2.  'Community 2022' 버전을 다운로드하여 설치 프로그램을 실행합니다.
3.  '워크로드' 선택 화면이 나타나면, **'.NET 데스크톱 개발'** 항목을 반드시 체크하고 '설치' 버튼을 누릅니다. (다른 항목은 필요 없습니다.)

![.NET 데스크톱 개발 워크로드 선택](https://i.imgur.com/E4V2n2E.png)

---

### 2단계: 새 프로젝트 생성

1.  Visual Studio 2022를 실행합니다.
2.  시작 화면에서 **'새 프로젝트 만들기'**를 선택합니다.
3.  프로젝트 템플릿 검색창에 `WPF`를 입력하고, **'WPF 애플리케이션'** (C# 언어) 템플릿을 선택한 후 '다음'을 누릅니다.
4.  **프로젝트 이름**을 `SolidworksStepConverter`로 지정하고 '다음'을 누릅니다.
5.  **프레임워크**는 추천되는 버전(예: .NET 6.0 또는 .NET 8.0)을 그대로 두고 **'만들기'** 버튼을 누릅니다.

---

### 3단계: 소스 코드 추가

프로젝트가 생성되면 기본 파일들이 만들어집니다. 이제 이 파일들을 우리가 만든 코드로 교체합니다.

1.  **MainWindow.xaml 교체**:
    *   Visual Studio 오른쪽의 '솔루션 탐색기'에서 `MainWindow.xaml` 파일을 더블클릭하여 엽니다.
    *   기존 내용을 모두 지우고, 제가 제공한 `MainWindow.xaml` 파일의 전체 코드를 복사하여 붙여넣습니다.

2.  **MainWindow.xaml.cs 교체**:
    *   '솔루션 탐색기'에서 `MainWindow.xaml` 항목 옆의 작은 화살표를 클릭하여 `MainWindow.xaml.cs`를 표시합니다.
    *   `MainWindow.xaml.cs` 파일을 더블클릭하여 엽니다.
    *   기존 내용을 모두 지우고, 제가 제공한 `MainWindow.xaml.cs` 파일의 전체 코드를 복사하여 붙여넣습니다.

---

### 4단계: SolidWorks API 참조 추가 (가장 중요!)

우리 코드는 SolidWorks와 통신해야 하므로, 관련 API 라이브러리 파일을 프로젝트에 연결해주어야 합니다.

1.  '솔루션 탐색기'에서 **'종속성'** (또는 '참조') 항목을 마우스 오른쪽 버튼으로 클릭하고 **'프로젝트 참조 추가'**를 선택합니다.
2.  왼쪽 메뉴에서 **'찾아보기'**를 선택하고, 오른쪽 아래의 **'찾아보기...'** 버튼을 클릭합니다.
3.  SolidWorks가 설치된 폴더로 이동합니다. 보통 아래 경로 중 하나에 있습니다.
    *   `C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS`
4.  해당 폴더에서 아래 **두 개의 파일**을 찾아서 선택(Ctrl 키를 누른 채 클릭)하고 '추가' 버튼을 누릅니다.
    *   `SldWorks.dll`
    *   `SolidWorks.Interop.swconst.dll`
5.  '참조 관리자' 창으로 돌아오면, 방금 추가한 두 파일이 체크되어 있는지 확인하고 '확인'을 누릅니다.
6.  **속성 변경**:
    *   다시 '솔루션 탐색기'의 '종속성 > 어셈블리'에서 방금 추가한 `SldWorks`를 선택합니다.
    *   마우스 오른쪽 버튼을 클릭하여 '속성'을 선택합니다.
    *   속성 창에서 **'Interop 형식 포함'** 옵션을 **'아니요'** 또는 **'False'**로 변경합니다.
    *   `SolidWorks.Interop.swconst`에 대해서도 동일하게 'Interop 형식 포함'을 '아니요(False)'로 변경합니다. 이 작업을 하지 않으면 빌드 시 오류가 발생할 수 있습니다.

---

### 5단계: 프로그램 빌드 및 실행

모든 준비가 끝났습니다. 이제 코드를 컴파일하여 실행 파일을 만들 차례입니다.

1.  Visual Studio 상단 메뉴에서 **'빌드' > '솔루션 빌드'**를 클릭합니다. (단축키: `Ctrl+Shift+B`)
2.  창 하단의 '출력' 창에 `빌드 성공` 메시지가 나타나면 성공입니다.
3.  프로젝트 폴더 안의 아래 경로로 이동하면 실행 파일이 만들어져 있습니다.
    *   `[내 문서]\Source\Repos\SolidworksStepConverter\bin\Debug\netX.0-windows\`
    *   (위 경로의 `netX.0-windows` 부분은 .NET 버전에 따라 다를 수 있습니다.)
4.  해당 폴더에 있는 **`SolidworksStepConverter.exe`** 파일을 더블클릭하면 직접 만든 프로그램이 실행됩니다.

이제 SolidWorks를 실행하고 어셈블리 파일을 연 상태에서 프로그램을 사용해 보세요!