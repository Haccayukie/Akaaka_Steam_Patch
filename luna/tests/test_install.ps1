$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$testRoot = Join-Path (Get-Location).Path ('test-launch-' + [Guid]::NewGuid().ToString('N').Substring(0, 8))
$directory = Join-Path $testRoot 'Luna Test'
$env:LOCALAPPDATA = Join-Path $testRoot 'AppData'
New-Item -ItemType Directory -Path $directory -Force | Out-Null
[IO.File]::WriteAllText((Join-Path $directory 'LunaTranslator.exe'), '')
function Invoke-RestMethod { param($Uri, $TimeoutSec) Get-Content -LiteralPath (Join-Path $root 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json }
function Invoke-WebRequest {
    param([switch]$UseBasicParsing, $Uri, $OutFile, $TimeoutSec)
    $relative = $Uri.Substring($Uri.IndexOf('/main/luna/') + 11)
    Copy-Item -LiteralPath (Join-Path $root $relative) -Destination $OutFile
}
& (Join-Path $root 'install.ps1') -LunaDirectory $directory -NoLaunch -NoDesktopShortcut
$state = Join-Path $env:LOCALAPPDATA 'AkaakaLunaOCR'
$launcher = Join-Path $root 'launch.ps1'
& powershell.exe -NoProfile -File $launcher -StateDirectory $state -NoLaunch
if ($LASTEXITCODE -ne 0) { throw 'Installed launcher failed' }
if (-not (Test-Path -LiteralPath (Join-Path $directory 'Start_Akaaka_Luna_OCR.cmd'))) { throw 'Folder launcher missing' }
if (-not (Test-Path -LiteralPath (Join-Path $state 'launch.ps1'))) { throw 'Cached launcher missing' }
& powershell.exe -NoProfile -File $launcher -StateDirectory (Join-Path $testRoot 'missing') -NoLaunch
if ($LASTEXITCODE -ne 2) { throw 'Missing installation did not request setup' }
Rename-Item -LiteralPath (Join-Path $directory 'LunaTranslator.exe') -NewName 'moved.exe'
& powershell.exe -NoProfile -File $launcher -StateDirectory $state -NoLaunch
if ($LASTEXITCODE -ne 2) { throw 'Moved executable did not request setup' }
Write-Host 'PASS: installation, cached launch, folder launch, missing state, moved executable'
# The last child intentionally returns 2 for a moved executable. Do not let
# GitHub's PowerShell wrapper treat that expected result as the test outcome.
$global:LASTEXITCODE = 0
exit 0
