@echo off

if exist build rmdir /s /q build
mkdir build
if exist result rmdir /s /q result
mkdir result\pysf
mkdir result\lib
cd build

cmake -G "Visual Studio 17 2022" -A x64 ..
if %errorlevel% neq 0 (
    echo cmake Failed to create project
    exit /b
)

cmake --build . --config Release -- /m:16
if %errorlevel% neq 0 (
    echo Failed to build
    exit /b
)

copy "Release\pysf.pyd" "..\result\pysf\"
if %errorlevel% neq 0 (
    echo Failed to copy pysf
    exit /b
)

xcopy "SFML\bin\Release\*.dll" "..\result\pysf\" /Y
if %errorlevel% neq 0 (
    echo Failed to copy dependencies
    exit /b
)

xcopy "SFML\lib\Release\*.lib" "..\result\lib\" /Y
if %errorlevel% neq 0 (
    echo Failed to copy dependencies
    exit /b
)

cd ..

xcopy /E /I /H /Y "required_libs\*.dll" "result\pysf\"
if %errorlevel% neq 0 (
    echo Failed to copy DLLs, exiting...
    exit /b
)

py -3.10 pyFilesGen.py
if %errorlevel% neq 0 (
    echo py -3.10 pyFilesGen.py Failed to generate python files
    exit /b
)

cd result\pysf
py -3.10 -m pybind11_stubgen --output-dir=. pysf.sf
IF %ERRORLEVEL% NEQ 0 (
    echo pybind11_stubgen failed, exiting...
    exit /b %ERRORLEVEL%
)

robocopy "pysf\sf" "." /E /MOVE >nul
rmdir "pysf" 2>nul

pause
