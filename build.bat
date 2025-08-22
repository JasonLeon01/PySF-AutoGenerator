@echo off
python parse.py
if %errorlevel% neq 0 echo python parse.py Failed to parse the code
if exist build rmdir /s /q build
mkdir build
cd build
cmake -G "Visual Studio 17 2022" -A x64 ..
if %errorlevel% neq 0 echo cmake Failed to create project
cmake --build . --config Release -- /m:16
if %errorlevel% neq 0 echo Failed to build
cd ..
pause