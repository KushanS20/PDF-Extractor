@echo off
echo Starting Invoice Extractor Service...
echo.

echo 1. Starting Flask Backend...
start "Flask Backend" cmd /k "python app.py"
timeout /t 3 /nobreak >nul

echo 2. Starting Streamlit Frontend...
start "Streamlit Frontend" cmd /k "python -m streamlit run frontend.py"

echo.
echo All services are starting...
echo - Flask Backend: http://localhost:5000
echo - Streamlit Frontend: http://localhost:8501
echo.
echo Press any key to exit this script (services will continue running)
pause >nul 