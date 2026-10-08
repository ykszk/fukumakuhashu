@echo off
chcp 65001 > nul
setlocal
rem Drag and drop a DICOM folder onto this file to convert it to .nii.gz.
rem Output: %HASHU_DIR%\dcm2niix\<folder name>.nii.gz (one file per series).
rem The user then moves the series to analyze into %HASHU_DIR%\input.

if not defined HASHU_DIR set "HASHU_DIR=C:\hashu"
set "CODE_DIR=%HASHU_DIR%\code"
set "DCM2NIIX_DIR=%HASHU_DIR%\dcm2niix"
set "INPUT_DIR=%HASHU_DIR%\input"
set "PYTHONUTF8=1"

if "%~1"=="" goto :usage
if not exist "%~1\" goto :not_folder

cd /d "%CODE_DIR%" || goto :no_code
uv run python src\convert_dicom.py "%~1" "%DCM2NIIX_DIR%"
if errorlevel 1 goto :failed

if not exist "%INPUT_DIR%\" mkdir "%INPUT_DIR%"
echo.
echo 変換が終わりました。保存先: %DCM2NIIX_DIR%
echo 解析するシリーズのファイルを1つ選び、%INPUT_DIR% に移してください。
echo 必要なら、ファイル名を短い症例名（例: 001.nii.gz）に変更してください。
if not defined HASHU_NO_BROWSER start "" explorer "%DCM2NIIX_DIR%"
goto :end

:usage
echo DICOMフォルダーをこのファイルの上にドラッグ＆ドロップしてください。
goto :end

:not_folder
echo エラー: フォルダーではありません: %~1
echo DICOMファイルが入っているフォルダーをドラッグ＆ドロップしてください。
goto :end

:no_code
echo エラー: プログラムのフォルダーが見つかりません: %CODE_DIR%
goto :end

:failed
echo.
echo 変換できませんでした。上のメッセージを確認してください。

:end
echo.
pause
