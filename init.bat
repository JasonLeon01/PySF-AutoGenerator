@echo off

if not exist "versions.conf" (
    echo versions.conf not found.
    exit /b 1
)

for /f "usebackq eol=# tokens=1,* delims==" %%A in ("versions.conf") do (
    set "%%A=%%B"
)

if "%SFML_VERSION%"=="" (
    echo SFML_VERSION not set in versions.conf.
    exit /b 1
)

if "%PYTHON_VERSION%"=="" (
    echo PYTHON_VERSION not set in versions.conf.
    exit /b 1
)

set "SFML_ARCHIVE=SFML-%SFML_VERSION%.zip"
if not exist "SFML" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri 'https://github.com/SFML/SFML/archive/refs/tags/%SFML_VERSION%.zip' -OutFile '%SFML_ARCHIVE%'"
    if errorlevel 1 exit /b 1

    powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%SFML_ARCHIVE%' -DestinationPath '.' -Force"
    if errorlevel 1 exit /b 1

    if exist "SFML-%SFML_VERSION%" ren "SFML-%SFML_VERSION%" SFML
    if not exist "SFML" (
        echo Failed to prepare SFML directory.
        exit /b 1
    )
    del "%SFML_ARCHIVE%"
)

if not exist "PySFEnv" (
    py -%PYTHON_VERSION% -m venv PySFEnv
)
call PySFEnv\Scripts\activate
pip install -r requirements.txt
