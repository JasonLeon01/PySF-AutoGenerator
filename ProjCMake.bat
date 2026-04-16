@echo off

if exist build rmdir /s /q build
mkdir build
if exist result rmdir /s /q result
mkdir result\pysf
mkdir result\lib

cd build
cmake -G "Visual Studio 17 2022" -A x64 ..
cmake --build . --config Release -- /m:16

xcopy "bin\Release\*.pyd" "..\result\pysf\" /Y
xcopy "SFML\bin\Release\*.dll" "..\result\pysf\" /Y
xcopy "SFML\lib\Release\*.lib" "..\result\lib\" /Y

cd ..
xcopy /E /I /H /Y "required_libs\*.dll" "result\pysf\"

python pyFilesGen.py
