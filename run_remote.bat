@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo  arXiv Daily - 远程访问模式
echo ========================================
echo.
echo 说明：会启动本机服务，并用 Cloudflare 临时隧道
echo       生成一个公网 HTTPS 链接，手机/办公室可打开。
echo       本机需保持开机，关闭本窗口即断开远程。
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo [错误] 未找到 Python，请先安装并加入 PATH。
  pause
  exit /b 1
)

if not exist "tools" mkdir tools
set "CF=tools\cloudflared.exe"

if not exist "%CF%" (
  echo 正在下载 cloudflared ...
  powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'tools\cloudflared.exe'"
  if not exist "%CF%" (
    echo [错误] cloudflared 下载失败，请检查网络后重试。
    pause
    exit /b 1
  )
  echo 下载完成。
  echo.
)

echo [1/2] 启动 arXiv Daily ...
start "arXiv Daily (Streamlit)" /min cmd /c "cd /d ""%~dp0"" && python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --browser.gatherUsageStats false"

echo 等待服务就绪...
timeout /t 6 /nobreak >nul

echo [2/2] 启动公网隧道...
echo.
echo ----------------------------------------
echo 下方会出现一行 https://xxxx.trycloudflare.com
echo 用手机/办公室浏览器打开该链接即可。
echo 链接每次启动会变；关掉本窗口即停止远程。
echo ----------------------------------------
echo.

"%CF%" tunnel --url http://127.0.0.1:8501

echo.
echo 隧道已结束。正在尝试关闭本机 Streamlit ...
taskkill /FI "WINDOWTITLE eq arXiv Daily (Streamlit)*" /F >nul 2>&1
pause
