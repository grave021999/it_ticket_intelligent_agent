# IT Ticket AI System - Complete Startup Script
# Run this in PowerShell: .\START_ALL.ps1

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Starting IT Ticket AI System" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Change to script directory
Set-Location $PSScriptRoot

Write-Host "[1/5] Starting A2A Server..." -ForegroundColor Yellow
Start-Process python -ArgumentList "a2a_protocol/real_a2a_server.py"
Start-Sleep -Seconds 2

Write-Host "[2/5] Starting MCP Server..." -ForegroundColor Yellow
Start-Process python -ArgumentList "mcp_server/real_mcp_server.py"
Start-Sleep -Seconds 2

Write-Host "[3/5] Starting Analytics Agent..." -ForegroundColor Yellow
Start-Process python -ArgumentList "agents/real_analytics_agent.py"
Start-Sleep -Seconds 2

Write-Host "[4/5] Starting Main Agent..." -ForegroundColor Yellow
Start-Process python -ArgumentList "agents/real_main_agent.py"
Start-Sleep -Seconds 2

Write-Host "[5/5] Starting Full Agent App UI..." -ForegroundColor Yellow
Start-Process streamlit -ArgumentList "run ui/full_agent_app.py"
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ALL SERVICES STARTED!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Services running on:" -ForegroundColor White
Write-Host "  - A2A Server:        ws://localhost:9090" -ForegroundColor Gray
Write-Host "  - MCP Server:        ws://localhost:8080" -ForegroundColor Gray
Write-Host "  - Analytics Agent:   Connected" -ForegroundColor Gray
Write-Host "  - Main Agent:        Connected" -ForegroundColor Gray
Write-Host "  - Full Agent App:    http://localhost:8501" -ForegroundColor Gray
Write-Host ""
Write-Host "Verifying services..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
python check_services.py
Write-Host ""
Write-Host "The Full Agent App should open in your browser automatically." -ForegroundColor Cyan
Write-Host "If not, navigate to: http://localhost:8501" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop all services, run: Get-Process python,streamlit | Stop-Process -Force" -ForegroundColor Yellow
Write-Host ""
