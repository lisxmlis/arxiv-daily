@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PATH=%PATH%;%ProgramFiles%\GitHub CLI"

echo ========================================
echo  arXiv Daily - 云端部署助手
echo ========================================
echo.
echo 目标：推送到 GitHub，再用 Streamlit Cloud
echo       获得固定链接 https://xxxx.streamlit.app
echo.

where gh >nul 2>&1
if errorlevel 1 (
  echo [错误] 未找到 GitHub CLI。请先安装：winget install GitHub.cli
  pause
  exit /b 1
)

gh auth status >nul 2>&1
if errorlevel 1 (
  echo 需要先登录 GitHub（浏览器会打开）...
  gh auth login -h github.com -p https -w
  if errorlevel 1 (
    echo 登录失败，请重试。
    pause
    exit /b 1
  )
)

echo.
set /p REPO_NAME=仓库名（直接回车=arxiv-daily）: 
if "%REPO_NAME%"=="" set REPO_NAME=arxiv-daily

echo.
echo 正在创建并推送 GitHub 仓库: %REPO_NAME%
git branch -M main
gh repo create %REPO_NAME% --public --source=. --remote=origin --push
if errorlevel 1 (
  echo.
  echo 若仓库已存在，尝试直接推送...
  git push -u origin main
)

for /f "delims=" %%u in ('gh repo view --json url -q .url') do set REPO_URL=%%u
echo.
echo ----------------------------------------
echo 仓库地址: %REPO_URL%
echo.
echo 下一步（约 1 分钟）：
echo 1. 浏览器将打开 Streamlit Cloud
echo 2. 用同一个 GitHub 账号登录
echo 3. New app → 选仓库 %REPO_NAME%
echo 4. Main file path 填: app.py
echo 5. Deploy 后得到固定链接
echo ----------------------------------------
echo.

start "" "https://share.streamlit.io/"
echo 完成后把你的 https://xxxx.streamlit.app 链接保存好即可长期使用。
pause
