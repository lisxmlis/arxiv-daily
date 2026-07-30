@echo off
cd /d "%~dp0"
echo Installing dependencies...
python -m pip install -r requirements.txt
echo.
echo Starting arXiv Daily (本机 + 局域网)...
echo 本机:     http://localhost:8501
echo 局域网:   用同 Wi-Fi 设备访问本机 IP:8501
echo.
echo 若需办公室/通勤远程访问，请改用 run_remote.bat
echo.
python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --browser.gatherUsageStats false
pause
