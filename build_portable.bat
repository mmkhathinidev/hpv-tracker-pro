@echo off
echo Building HPV Tracker Pro portable application...
if exist dist\HPV_Tracker_Pro rmdir /s /q dist\HPV_Tracker_Pro
python -m PyInstaller -y hpv_tracker_pro.spec
if %ERRORLEVEL% EQU 0 (
    echo Copying deployment assets...
    copy README_DEPLOYMENT.md dist\HPV_Tracker_Pro\ >nul
    xcopy /E /I /Y icons dist\HPV_Tracker_Pro\icons >nul
    xcopy /E /I /Y config dist\HPV_Tracker_Pro\config >nul
    echo.
    echo ==============================================
    echo Build successful! Portable app located at:
    echo %~dp0dist\HPV_Tracker_Pro\HPV_Tracker_Pro.exe
    echo ==============================================
) else (
    echo Build failed with error code %ERRORLEVEL%.
)
