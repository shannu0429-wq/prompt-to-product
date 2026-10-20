@echo off
title Prompt to Product - AI Web Challenge Live Server
echo ===================================================================
echo     Prompt to Product - AI Web Challenge
echo     Organized by SSRS Group of Companies
echo ===================================================================
echo.
echo [1/2] Starting Flask application with MySQL...
start /b python run.py
timeout /t 3 /nobreak > nul
echo.
echo [2/2] Connecting Cloudflare Public Live HTTPS Tunnel...
echo.
echo Your public live HTTPS link will appear below:
echo ===================================================================
"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:5000
pause
