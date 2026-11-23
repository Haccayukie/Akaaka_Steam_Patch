param([string]$LunaDirectory, [switch]$NoLaunch)
$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$base = 'https://raw.githubusercontent.com/Haccayukie/Akaaka_Steam_Patch/main/luna/'

if (-not $LunaDirectory) {
    Add-Type -AssemblyName System.Windows.Forms
    $picker = New-Object System.Windows.Forms.OpenFileDialog
    $picker.Title = '请选择 LunaTranslator.exe'
    $picker.Filter = 'LunaTranslator.exe|LunaTranslator.exe'
    if ($picker.ShowDialog() -ne 'OK') { exit }
    $LunaDirectory = Split-Path -LiteralPath $picker.FileName
}
$LunaDirectory = (Resolve-Path -LiteralPath $LunaDirectory).Path
$exe = Join-Path $LunaDirectory 'LunaTranslator.exe'
if (-not (Test-Path -LiteralPath $exe -PathType Leaf)) { throw '所选目录没有 LunaTranslator.exe' }
$profile = Join-Path $LunaDirectory 'userconfig_akaaka'
$cache = Join-Path $profile 'akaaka_pretranslation'
New-Item -ItemType Directory -Path $profile, $cache -Force | Out-Null
$utf8 = New-Object System.Text.UTF8Encoding($false)

function Save-Json($path, $value) {
    $text = ConvertTo-Json -InputObject $value -Depth 100
    [IO.File]::WriteAllText($path, $text, $utf8)
}

function Fetch-File($url, $path) {
    Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $path -TimeoutSec 30
}

# A separate native Luna profile preserves the user's existing translator setup.
if (-not (Test-Path -LiteralPath (Join-Path $profile 'config.json'))) {
    $original = Join-Path $LunaDirectory 'userconfig'
    if (Test-Path -LiteralPath $original) {
        Get-ChildItem -LiteralPath $original -Filter '*.json' -File | ForEach-Object {
            Copy-Item -LiteralPath $_.FullName -Destination $profile
        }
    }
}

$manifest = Invoke-RestMethod -Uri ($base + 'manifest.json') -TimeoutSec 30
$version = [string]$manifest.version
if ($version -notmatch '^[A-Za-z0-9_.-]+$') { throw '版本号无效' }
$versions = Join-Path $cache 'versions'
$destination = Join-Path $versions $version
New-Item -ItemType Directory -Path $destination -Force | Out-Null
foreach ($name in @('engine.py', 'data.json.gz', 'rules.json')) {
    $item = $manifest.files.$name
    if ($item.path -match '(^/|\.\.|:)') { throw '更新路径无效' }
    $temporary = Join-Path $destination ($name + '.tmp')
    Fetch-File ($base + $item.path) $temporary
    $actual = (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $item.sha256) { throw ('下载校验失败 ' + $name) }
    Move-Item -LiteralPath $temporary -Destination (Join-Path $destination $name) -Force
}
Save-Json (Join-Path $destination 'complete.json') @{ version = $version }
$entryTemporary = Join-Path $profile 'selfbuild.py.download'
Fetch-File ($base + 'selfbuild.py') $entryTemporary
$entryHash = (Get-FileHash -LiteralPath $entryTemporary -Algorithm SHA256).Hash.ToLowerInvariant()
if ($entryHash -ne $manifest.bootstrap_sha256) { throw '加载入口校验失败' }
Move-Item -LiteralPath $entryTemporary -Destination (Join-Path $profile 'selfbuild.py') -Force
Save-Json (Join-Path $cache 'current.json') @{ version = $version }

$configPath = Join-Path $profile 'config.json'
if (Test-Path -LiteralPath $configPath) {
    $config = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
} else { $config = [pscustomobject]@{} }
if (-not $config.PSObject.Properties['fanyi']) {
    $config | Add-Member -NotePropertyName fanyi -NotePropertyValue ([pscustomobject]@{})
}
foreach ($property in $config.fanyi.PSObject.Properties) {
    if ($property.Value.PSObject.Properties['use']) { $property.Value.use = $false }
}
$custom = [pscustomobject]@{ use = $true; type = 'other'; name = '自定义翻译'; color = '#2065D1'; lang = @{} }
$config.fanyi | Add-Member -NotePropertyName selfbuild -NotePropertyValue $custom -Force
$config | Add-Member -NotePropertyName srclang4 -NotePropertyValue 'auto' -Force
if (-not $config.PSObject.Properties['tgtlang4'] -or $config.tgtlang4 -notin @('zh', 'cht', 'ja')) {
    $config | Add-Member -NotePropertyName tgtlang4 -NotePropertyValue 'zh' -Force
}
Save-Json $configPath $config

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) '赤灯预翻译.lnk'))
$shortcut.TargetPath = $exe
$shortcut.Arguments = '--userconfig=userconfig_akaaka'
$shortcut.WorkingDirectory = $LunaDirectory
$shortcut.Save()
Write-Host '安装完成。以后使用桌面的“赤灯预翻译”打开。'
Write-Host '源语言、目标语言、OCR 和显示样式都在 Luna 原有设置里调整。'
if (-not $NoLaunch) {
    Start-Process -FilePath $exe -ArgumentList '--userconfig=userconfig_akaaka' -WorkingDirectory $LunaDirectory -WindowStyle Hidden
}
