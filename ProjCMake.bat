@echo off
setlocal EnableExtensions

cd /d "%~dp0"

if not exist output (
    echo output not found. Please run build.bat to generate bindings first.
    exit /b 1
)

set "PYSF_PYTHON_EXECUTABLE=%CD%\PySFEnv\Scripts\python.exe"
if not exist "%PYSF_PYTHON_EXECUTABLE%" (
    echo PySFEnv Python not found: %PYSF_PYTHON_EXECUTABLE%
    exit /b 1
)

xcopy /E /I /Y "include" "output\include\" > nul
if errorlevel 1 exit /b %errorlevel%
xcopy /E /I /Y "src" "output\src\" > nul
if errorlevel 1 exit /b %errorlevel%

if exist output\SFML rmdir /s /q output\SFML
robocopy "SFML" "output\SFML" /E /XD .git > nul
if %errorlevel% GEQ 8 exit /b %errorlevel%

if exist output\build rmdir /s /q output\build
mkdir output\build

cd output\build
cmake -G "Visual Studio 17 2022" -A x64 -DPython3_EXECUTABLE="%PYSF_PYTHON_EXECUTABLE%" ..
if errorlevel 1 exit /b %errorlevel%

cmake --build . --config Release --target pysf --parallel
if errorlevel 1 exit /b %errorlevel%

cd ..\..

endlocal
exit /b 0
