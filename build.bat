@echo off

if not exist "versions.conf" (
    echo versions.conf not found.
    exit /b 1
)

for /f "usebackq eol=# tokens=1,* delims==" %%A in ("versions.conf") do (
    set "%%A=%%B"
)

if not exist "PySFEnv\Scripts\activate.bat" (
    echo PySFEnv not found. Please run init.bat first.
    exit /b 1
)
call PySFEnv\Scripts\activate

python parse.py
if errorlevel 1 exit /b %errorlevel%

call ProjCMake.bat
