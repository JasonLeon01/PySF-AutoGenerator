@echo off

if not exist "output\build" (
    echo output\build not found. Please run build.bat first.
    exit /b 1
)

if exist output\result rmdir /s /q output\result
mkdir output\result\pysf
mkdir output\result\lib

xcopy "output\build\bin\Release\*.pyd" "output\result\pysf\" /Y
if errorlevel 1 exit /b %errorlevel%

if exist "output\build\SFML\bin\Release" (
    xcopy "output\build\SFML\bin\Release\*.dll" "output\result\pysf\" /Y
)

if exist "output\build\SFML\lib\Release" (
    xcopy "output\build\SFML\lib\Release\*.lib" "output\result\lib\" /Y
)

xcopy /E /I /H /Y "required_libs\*.dll" "output\result\pysf\"

if not exist "PySFEnv\Scripts\activate.bat" (
    echo PySFEnv not found. Please run init.bat first.
    exit /b 1
)
call PySFEnv\Scripts\activate

python pyFilesGen.py
