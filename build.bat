@echo off

py -3.10 parse.py
if %errorlevel% neq 0 (
    echo py -3.10 parse.py Failed to parse the code
    exit /b
)

call ProjCMake.bat

pause
