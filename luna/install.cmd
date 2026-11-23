@echo off
setlocal
set "AKA_INSTALL=%TEMP%\akaaka-luna-install-%RANDOM%-%RANDOM%.ps1"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/Haccayukie/Akaaka_Steam_Patch/main/luna/install.ps1' -OutFile $env:AKA_INSTALL -TimeoutSec 30; & $env:AKA_INSTALL; if (-not $?) { exit 1 } } catch { Write-Host $_; exit 1 } finally { Remove-Item -LiteralPath $env:AKA_INSTALL -ErrorAction SilentlyContinue }"
if errorlevel 1 pause
endlocal
