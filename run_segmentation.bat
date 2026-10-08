@echo off
chcp 65001 > nul
setlocal
rem Drag and drop a .nii.gz image onto this file to run the analysis pipeline.
rem Output: %HASHU_DIR%\output\<file name without .nii.gz>\

if not defined HASHU_DIR set "HASHU_DIR=C:\hashu"
set "CODE_DIR=%HASHU_DIR%\code"
set "PYTHONUTF8=1"

if "%~1"=="" goto :usage
if exist "%~1\" goto :not_file

rem Case name = file name without .nii.gz (or .nii)
set "CASE=%~n1"
if /i "%~x1"==".gz" goto :strip_nii
if /i "%~x1"==".nii" goto :have_case
goto :not_nifti
:strip_nii
if /i not "%CASE:~-4%"==".nii" goto :not_nifti
set "CASE=%CASE:~0,-4%"
:have_case
set "OUTPUT_DIR=%HASHU_DIR%\output\%CASE%"

echo 入力: %~1
echo 結果の保存先: %OUTPUT_DIR%
echo 解析には15分から1時間ほどかかります。この画面は閉じないでください。
echo.

cd /d "%CODE_DIR%" || goto :no_code
rem SimpleITK can't open non-ASCII paths on Windows; stop early with a clear message.
uv run python -c "import sys; sys.exit(0 if all(a.isascii() for a in sys.argv[1:]) else 3)" "%~f1" "%OUTPUT_DIR%"
if errorlevel 1 goto :not_ascii
uv run python src\run_scripts.py --input "%~f1" --output "%OUTPUT_DIR%" --skip_existing
if errorlevel 1 goto :failed

echo.
echo 解析が終わりました。結果: %OUTPUT_DIR%
echo 上に「Feature extraction failed!」が出ていないか確認してください。
goto :end

:usage
echo .nii.gz ファイルをこのファイルの上にドラッグ＆ドロップしてください。
goto :end

:not_file
echo エラー: フォルダーではなく .nii.gz ファイルをドラッグ＆ドロップしてください。
echo DICOMフォルダーの場合は、先に to-niigz.bat で変換してください。
goto :end

:not_nifti
echo エラー: .nii.gz ファイルではありません: %~nx1
echo DICOMの場合は、先に to-niigz.bat で変換してください。
goto :end

:no_code
echo エラー: プログラムのフォルダーが見つかりません: %CODE_DIR%
goto :end

:not_ascii
echo エラー: ファイル名またはフォルダー名に全角文字が含まれていると解析できません。
echo ファイルを %HASHU_DIR%\input に移し、ファイル名を半角英数字（例: 001.nii.gz）に変更してから、
echo もう一度ドラッグ＆ドロップしてください。
goto :end

:failed
echo.
echo 解析が途中で止まりました。上のメッセージを確認してください。
echo 同じファイルをもう一度ドラッグ＆ドロップすると、止まったところから再開します。

:end
echo.
pause
