@echo off
chcp 65001 > nul
setlocal
rem One-time setup for run_ascites.bat: unpacks the ascites model and installs the
rem ascites environment. Double-click it after saving the model archive to
rem %HASHU_DIR%\downloads\ascites_model.tar.gz, or drop the archive onto it.

if not defined HASHU_DIR set "HASHU_DIR=C:\hashu"
set "CODE_DIR=%HASHU_DIR%\code"
set "DOWNLOAD_DIR=%HASHU_DIR%\downloads"
set "MODELS_DIR=%CODE_DIR%\models"
set "TRAINER_DIR=%MODELS_DIR%\ascites_model\nnUNet_trained_models\nnUNet\3d_fullres\Task505_TCGA-OV\nnUNetTrainerV2__nnUNetPlansv2.1"
set "MODEL_URL=https://nihcc.app.box.com/s/oc81mic9k8vre30fq0eanxqp9kdwern2"
rem Windows' own tar, not another one that may be on PATH (e.g. from Git).
set "TAR=%SystemRoot%\System32\tar.exe"
set "PYTHONUTF8=1"
rem nnunet==1.7.0 depends on the deprecated "sklearn" package; lets uv install it.
set "SKLEARN_ALLOW_DEPRECATED_SKLEARN_PACKAGE_INSTALL=True"

set "ARCHIVE=%DOWNLOAD_DIR%\ascites_model.tar.gz"
if not "%~1"=="" set "ARCHIVE=%~f1"

if not exist "%CODE_DIR%\" goto :no_code
call :check_model
if not defined MISSING goto :model_ready
if not exist "%ARCHIVE%" goto :no_archive

echo モデルを展開しています（数分かかります）: %ARCHIVE%
if not exist "%MODELS_DIR%\" mkdir "%MODELS_DIR%"
"%TAR%" -xzf "%ARCHIVE%" -C "%MODELS_DIR%"
if errorlevel 1 goto :extract_failed
call :check_model
if defined MISSING goto :incomplete
echo モデルの展開が終わりました: %MODELS_DIR%\ascites_model
goto :sync

:model_ready
echo 腹水モデルはすでに展開されています: %MODELS_DIR%\ascites_model

rem Always (re)sync: quick when already installed, and retries a failed earlier install.
:sync
echo.
echo 腹水ツールの部品をインストールしています（初回は数分かかります）...
cd /d "%CODE_DIR%"
uv sync --directory ascites
if errorlevel 1 goto :sync_failed

echo.
echo 腹水ツールの準備ができました。
echo 解析済みの .nii.gz ファイルを run_ascites.bat にドラッグ＆ドロップすると、腹水を計測できます。
echo %DOWNLOAD_DIR% 内の ascites_model.tar.gz は削除してかまいません。
goto :end

rem Sets MISSING if any of the 5 fold checkpoints (or the plans file) is absent.
:check_model
set "MISSING="
if not exist "%TRAINER_DIR%\plans.pkl" set "MISSING=1"
for %%f in (0 1 2 3 4) do if not exist "%TRAINER_DIR%\fold_%%f\model_final_checkpoint.model" set "MISSING=1"
exit /b 0

:no_code
echo エラー: プログラムのフォルダーが見つかりません: %CODE_DIR%
goto :end

:no_archive
if not exist "%DOWNLOAD_DIR%\" mkdir "%DOWNLOAD_DIR%"
echo モデルファイルが見つかりません: %ARCHIVE%
echo.
echo 1. ブラウザーで開くNIHのページから ascites_model.tar.gz（約1.1 GB）をダウンロードしてください。
echo    %MODEL_URL%
echo 2. ダウンロードしたファイルを、開いたフォルダー（%DOWNLOAD_DIR%）に移してください。
echo 3. もう一度このファイル（setup_ascites_model.bat）をダブルクリックしてください。
if not defined HASHU_NO_BROWSER start "" "%MODEL_URL%"
if not defined HASHU_NO_BROWSER start "" explorer "%DOWNLOAD_DIR%"
goto :end

:extract_failed
echo.
echo エラー: モデルの展開に失敗しました。ダウンロードが途中で止まった可能性があります。
echo ファイルを削除してダウンロードし直し、もう一度実行してください: %ARCHIVE%
goto :end

:incomplete
echo.
echo エラー: 展開したモデルに足りないファイルがあります。
echo ファイルが正しい ascites_model.tar.gz か確認し、ダウンロードし直してから、もう一度実行してください。
goto :end

:sync_failed
echo.
echo エラー: 腹水ツールの部品をインストールできませんでした。インターネット接続を確認して、もう一度実行してください。
echo （モデルの展開は終わっているため、次回は部品のインストールから行います。）
goto :end

:end
echo.
pause
