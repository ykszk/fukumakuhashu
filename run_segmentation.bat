@echo off

set SCRIPT_DIR=%~dp0src\
set SCRIPT=%SCRIPT_DIR%run_scripts.py
set OUTPUT_DIR=%SCRIPT_DIR%..\..\..\output\%~nx1
set PYTHON_DIR=%SCRIPT_DIR%..\..\python\
set PYTHON=%PYTHON_DIR%python.exe
set TOTAL_SEGMENTATOR=%PYTHON_DIR%Scripts\TotalSegmentator.exe
set INPUT=%1

echo Using Python interpreter at: %PYTHON%
echo script: %SCRIPT%
echo output: %OUTPUT_DIR%
echo input: %INPUT%

%PYTHON% %SCRIPT% --input %INPUT% --output "%OUTPUT_DIR%" --skip_existing

pause