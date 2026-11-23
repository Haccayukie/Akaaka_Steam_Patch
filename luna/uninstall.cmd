@echo off
setlocal
set "AKA_UNINSTALL=%TEMP%\akaaka-luna-uninstall-%RANDOM%-%RANDOM%.ps1"
set "AKA_LUNA_HINT=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; try { $cached=Join-Path $env:LOCALAPPDATA 'AkaakaLunaOCR\uninstall.ps1'; if (Test-Path -LiteralPath $cached) { Copy-Item -LiteralPath $cached -Destination $env:AKA_UNINSTALL } else { Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/Haccayukie/Akaaka_Steam_Patch/main/luna/uninstall.ps1' -OutFile $env:AKA_UNINSTALL -TimeoutSec 30 }; & $env:AKA_UNINSTALL -LunaDirectory $env:AKA_LUNA_HINT; if (-not $?) { exit 1 } } catch { Write-Host $_; Read-Host 'Press Enter to close'; exit 1 } finally { Remove-Item -LiteralPath $env:AKA_UNINSTALL -ErrorAction SilentlyContinue }"
