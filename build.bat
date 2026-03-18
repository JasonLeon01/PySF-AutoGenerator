@echo off

if not exist "PySFEnv" (
    py -3.12 -m venv PySFEnv
)
call PySFEnv\Scripts\activate
pip install -r ./requirements.txt

python parse.py

call ProjCMake.bat

pause
