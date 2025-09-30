using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Threading;
using SldWorks;
using SolidWorks.Interop.swconst;

namespace SolidworksStepConverter
{
    /// <summary>
    /// MainWindow.xaml에 대한 상호 작용 논리
    /// </summary>
    public partial class MainWindow : Window
    {
        private SldWorks.SldWorks swApp;
        private DispatcherTimer swStatusTimer;

        public MainWindow()
        {
            InitializeComponent();
            // 앱 시작 시 기본 테마 적용
            ApplyTheme("Theme.Default");
            // SolidWorks 상태를 주기적으로 확인할 타이머 설정
            SetupTimer();
        }

        #region SolidWorks 연동 로직

        private void SetupTimer()
        {
            swStatusTimer = new DispatcherTimer();
            swStatusTimer.Interval = TimeSpan.FromSeconds(2); // 2초마다 확인
            swStatusTimer.Tick += SwStatusTimer_Tick;
            swStatusTimer.Start();
            // 앱 시작 시 즉시 한 번 확인
            SwStatusTimer_Tick(null, null);
        }

        private void SwStatusTimer_Tick(object sender, EventArgs e)
        {
            try
            {
                // 실행 중인 SolidWorks 인스턴스에 연결 시도
                swApp = (SldWorks.SldWorks)Marshal.GetActiveObject("SldWorks.Application");

                ModelDoc2 swModel = swApp.ActiveDoc as ModelDoc2;

                if (swModel != null)
                {
                    // 파일이 열려 있으면 UI 업데이트
                    ActiveFileNameTextBlock.Text = swModel.GetPathName();
                    ConvertButton.IsEnabled = true;
                }
                else
                {
                    // 파일이 열려있지 않은 경우
                    ActiveFileNameTextBlock.Text = "SolidWorks에서 파일을 열어주세요.";
                    ConvertButton.IsEnabled = false;
                }
            }
            catch (COMException)
            {
                // SolidWorks가 실행 중이 아닌 경우
                swApp = null;
                ActiveFileNameTextBlock.Text = "SolidWorks가 실행 중이 아닙니다.";
                ConvertButton.IsEnabled = false;
            }
            catch (Exception ex)
            {
                // 기타 예외 처리
                ActiveFileNameTextBlock.Text = $"오류 발생: {ex.Message}";
                ConvertButton.IsEnabled = false;
            }
        }

        private void ConvertButton_Click(object sender, RoutedEventArgs e)
        {
            if (swApp == null)
            {
                MessageBox.Show("SolidWorks에 연결되지 않았습니다.", "오류", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            ModelDoc2 swModel = swApp.ActiveDoc as ModelDoc2;
            if (swModel == null)
            {
                MessageBox.Show("변환할 파일이 열려있지 않습니다.", "오류", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            // 어셈블리 파일인지 확인
            if (swModel.GetType() != (int)swDocumentTypes_e.swDocASSEMBLY)
            {
                MessageBox.Show("어셈블리 파일(.sldasm)만 STEP 파일로 변환할 수 있습니다.", "알림", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            string originalPath = swModel.GetPathName();
            if (string.IsNullOrEmpty(originalPath))
            {
                MessageBox.Show("파일이 저장되어 있지 않습니다. 먼저 파일을 저장해주세요.", "오류", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            // 저장할 STEP 파일 경로 생성 (원본 파일명 + .step)
            string stepFilePath = Path.ChangeExtension(originalPath, ".step");

            try
            {
                // STEP 파일로 저장 (AP214 프로토콜 사용)
                // 마지막 두 인자는 오류 및 경고를 받기 위한 변수
                int errors = 0;
                int warnings = 0;
                bool success = swModel.Extension.SaveAs(stepFilePath, (int)swSaveAsVersion_e.swSaveAsCurrentVersion, (int)swSaveAsOptions_e.swSaveAsOptions_Silent, null, ref errors, ref warnings);

                if (success)
                {
                    MessageBox.Show($"STEP 파일 변환 성공!\n저장 위치: {stepFilePath}", "성공", MessageBoxButton.OK, MessageBoxImage.Information);
                }
                else
                {
                    MessageBox.Show($"STEP 파일 변환 실패. 오류 코드: {errors}", "오류", MessageBoxButton.OK, MessageBoxImage.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"파일 저장 중 예외가 발생했습니다: {ex.Message}", "치명적 오류", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        #endregion

        #region 테마 변경 로직

        private void ApplyTheme(string themeName)
        {
            // App.xaml에 정의된 리소스 딕셔너리를 찾아 현재 창의 리소스로 설정
            var theme = (ResourceDictionary)FindResource(themeName);
            if (theme != null)
            {
                MainGrid.Resources.MergedDictionaries.Clear();
                MainGrid.Resources.MergedDictionaries.Add(theme);
            }
        }

        private void DefaultThemeButton_Click(object sender, RoutedEventArgs e)
        {
            ApplyTheme("Theme.Default");
        }

        private void SolarizedThemeButton_Click(object sender, RoutedEventArgs e)
        {
            ApplyTheme("Theme.Solarized");
        }

        private void BlackThemeButton_Click(object sender, RoutedEventArgs e)
        {
            ApplyTheme("Theme.Black");
        }

        #endregion
    }
}