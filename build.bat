@echo off

py -3.12 parse.py
if %errorlevel% neq 0 (
    echo py -3.12 parse.py Failed to parse the code
    exit /b
)

call ProjCMake.bat

pause
