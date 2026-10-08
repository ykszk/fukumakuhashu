@echo off
chcp 65001 > nul
setlocal
rem Drag and drop a case's .nii.gz (or its output folder) onto this file to run
rem ascites segmentation on that case. Needs the main analysis to have run first.
rem Output: %HASHU_DIR%\output\<case name>\ascites.nii.gz

if not defined HASHU_DIR set "HASHU_DIR=C:\hashu"
set "CODE_DIR=%HASHU_DIR%\code"
set "MODEL_DIR=%CODE_DIR%\models\ascites_model"
set "PYTHONUTF8=1"
rem nnunet==1.7.0 depends on the deprecated "sklearn" package; lets `uv run` install it.
set "SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=True"

if "%~1"=="" goto :usage

rem Case name = folder name, or file name without .nii.gz (or .nii)
if exist "%~1\" goto :from_folder
set "CASE=%~n1"
if /i "%~x1"==".gz" goto :strip_nii
if /i "%~x1"==".nii" goto :have_case
goto :not_nifti
:strip_nii
if /i not "%CASE:~-4%"==".nii" goto :not_nifti
set "CASE=%CASE:~0,-4%"
goto :have_case
:from_folder
set "CASE=%~nx1"
:have_case
set "CASE_DIR=%HASHU_DIR%\output\%CASE%"
set "INPUT=%CASE_DIR%\abdomen_cropped.nii.gz"
set "OUTPUT=%CASE_DIR%\ascites.nii.gz"

if not exist "%CODE_DIR%\" goto :no_code
if not exist "%MODEL_DIR%\" goto :no_model
if not exist "%INPUT%" goto :no_main
if exist "%OUTPUT%" goto :already_done

echo 症例: %CASE%
echo 結果の保存先: %OUTPUT%
echo 腹水の計測には時間がかかります。この画面は閉じないでください。
echo.

cd /d "%CODE_DIR%"
rem SimpleITK can't open non-ASCII paths on Windows; stop early with a clear message.
uv run python -c "import sys; sys.exit(0 if sys.argv[1].isascii() else 3)" "%OUTPUT%"
if errorlevel 1 goto :not_ascii
uv run --directory ascites python predict_ascites.py --input "%INPUT%" --output "%OUTPUT%"
if errorlevel 1 goto :failed
if not exist "%OUTPUT%" goto :failed

echo.
echo 腹水の計測が終わりました。結果: %OUTPUT%
goto :end

:usage
echo 解析済みの .nii.gz ファイル（または結果フォルダー）をこのファイルの上にドラッグ＆ドロップしてください。
goto :end

:not_nifti
echo エラー: .nii.gz ファイルではありません: %~nx1
goto :end

:no_code
echo エラー: プログラムのフォルダーが見つかりません: %CODE_DIR%
goto :end

:no_model
echo エラー: 腹水モデルが見つかりません: %MODEL_DIR%
echo 先に setup_ascites_model.bat をダブルクリックして、腹水モデルを準備してください。
goto :end

:no_main
echo エラー: この症例のメイン解析の結果が見つかりません: %INPUT%
echo 先に同じファイルを run_segmentation.bat にドラッグ＆ドロップして、解析を終わらせてください。
goto :end

:already_done
echo この症例の腹水の計測はすでに終わっています: %OUTPUT%
echo やり直す場合は、このファイルを削除してから、もう一度ドラッグ＆ドロップしてください。
goto :end

:not_ascii
echo エラー: ファイル名またはフォルダー名に全角文字が含まれていると計測できません。
echo ファイル名を半角英数字（例: 001.nii.gz）に変更してから、解析からやり直してください。
goto :end

:failed
echo.
echo 腹水の計測が途中で止まりました。上のメッセージを確認してください。

:end
echo.
pause
