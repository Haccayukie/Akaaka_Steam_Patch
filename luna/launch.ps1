param(
    [string]$StateDirectory = (Join-Path $env:LOCALAPPDATA 'AkaakaLunaOCR'),
    [switch]$NoLaunch
)
$ErrorActionPreference = 'Stop'
$statePath = Join-Path $StateDirectory 'installation.json'
if (-not (Test-Path -LiteralPath $statePath -PathType Leaf)) { exit 2 }
try {
    $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
    $directory = [string]$state.luna_directory
    $exe = Join-Path $directory 'LunaTranslator.exe'
    $profile = Join-Path $directory 'userconfig_akaaka'
    if (-not (Test-Path -LiteralPath $exe -PathType Leaf) -or
        -not (Test-Path -LiteralPath (Join-Path $profile 'selfbuild.py') -PathType Leaf) -or
        -not (Test-Path -LiteralPath (Join-Path $profile 'akaaka_pretranslation/current.json') -PathType Leaf)) {
        exit 2
    }
    if ($NoLaunch) { Write-Output $exe; exit 0 }
    Start-Process -FilePath $exe -ArgumentList '--userconfig=userconfig_akaaka' -WorkingDirectory $directory -WindowStyle Hidden
    exit 0
} catch {
    Write-Host $_
    exit 1
}
