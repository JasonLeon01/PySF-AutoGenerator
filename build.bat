@echo off

python parse.py
if %errorlevel% neq 0 (
    echo python parse.py Failed to parse the code
    exit /b
)

if exist build rmdir /s /q build
mkdir build
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

cd ..

python pyFilesGen.py
if %errorlevel% neq 0 (
    echo python pyFilesGen.py Failed to generate python files
    exit /b
)

xcopy /E /I /H /Y required_dlls\* result\pysf\
if %errorlevel% neq 0 (
    echo Failed to copy DLLs, exiting...
    exit /b
)

cd build\Release

xcopy /Y pysf.pyd ..\..\result\pysf\
if %errorlevel% neq 0 (
    echo Failed to copy pysf.pyd, exiting...
    exit /b
)

python -m pybind11_stubgen --output-dir=. pysf
IF %ERRORLEVEL% NEQ 0 (
    echo pybind11_stubgen failed, exiting...
    exit /b %ERRORLEVEL%
)

xcopy /E /I /H pysf\sf\* ..\..\result\pysf\
rmdir /S /Q pysf

pause
