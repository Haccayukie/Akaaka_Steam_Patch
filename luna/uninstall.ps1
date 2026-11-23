param(
    [string]$LunaDirectory,
    [string]$StateDirectory = (Join-Path $env:LOCALAPPDATA 'AkaakaLunaOCR'),
    [string]$DesktopDirectory = ([Environment]::GetFolderPath('Desktop')),
    [switch]$Unattended
)
$ErrorActionPreference = 'Stop'
$statePath = Join-Path $StateDirectory 'installation.json'
$recorded = $null
if (Test-Path -LiteralPath $statePath -PathType Leaf) {
    $recorded = [string](Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json).luna_directory
}
if (-not $LunaDirectory -or -not (Test-Path -LiteralPath (Join-Path $LunaDirectory 'LunaTranslator.exe') -PathType Leaf)) {
    $LunaDirectory = $recorded
}
if (-not $LunaDirectory -or -not (Test-Path -LiteralPath (Join-Path $LunaDirectory 'LunaTranslator.exe') -PathType Leaf)) {
    if ($Unattended) { throw '找不到 Luna，请重新选择安装位置。' }
    Add-Type -AssemblyName System.Windows.Forms
    $picker = New-Object System.Windows.Forms.OpenFileDialog
    $picker.Title = '请选择要卸载赤灯预翻译的 LunaTranslator.exe'
    $picker.Filter = 'LunaTranslator.exe|LunaTranslator.exe'
    if ($picker.ShowDialog() -ne 'OK') { return }
    $LunaDirectory = Split-Path -LiteralPath $picker.FileName
}
$LunaDirectory = (Resolve-Path -LiteralPath $LunaDirectory).Path.TrimEnd('\')
$exe = Join-Path $LunaDirectory 'LunaTranslator.exe'
if (Get-Process -Name 'LunaTranslator' -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exe }) {
    throw '请先完全退出 Luna，再运行卸载。'
}
if (-not $Unattended) {
    Add-Type -AssemblyName System.Windows.Forms
    $answer = [Windows.Forms.MessageBox]::Show("卸载赤灯预翻译？`n将删除赤灯专用设置、下载的译文和启动入口。`nLuna 本体、原来的设置、OCR 模型和词典会保留。", '卸载赤灯预翻译', 'YesNo', 'Question')
    if ($answer -ne 'Yes') { return }
}
# Every recursive target is an exact named child, checked against its parent.
function Remove-OwnedChild($parent, $name, [switch]$Recurse) {
    $parentFull = [IO.Path]::GetFullPath($parent).TrimEnd('\')
    $target = [IO.Path]::GetFullPath((Join-Path $parentFull $name))
    if ([IO.Path]::GetDirectoryName($target) -ne $parentFull) { throw '卸载路径检查失败' }
    if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse:$Recurse -Force }
}
$profile = Join-Path $LunaDirectory 'userconfig_akaaka'
if (Test-Path -LiteralPath $profile) {
    if (-not (Test-Path -LiteralPath (Join-Path $profile 'selfbuild.py')) -and
        -not (Test-Path -LiteralPath (Join-Path $profile 'akaaka_pretranslation/current.json'))) {
        throw '此文件夹缺少赤灯安装标记，已停止卸载。'
    }
    Remove-OwnedChild $LunaDirectory 'userconfig_akaaka' -Recurse
}
Remove-OwnedChild $LunaDirectory 'Start_Akaaka_Luna_OCR.cmd'
Remove-OwnedChild $LunaDirectory 'Uninstall_Akaaka_Luna_OCR.cmd'
$shortcutPath = Join-Path $DesktopDirectory '赤灯预翻译.lnk'
if (Test-Path -LiteralPath $shortcutPath -PathType Leaf) {
    $shell = New-Object -ComObject WScript.Shell
    $link = $shell.CreateShortcut($shortcutPath)
    if ($link.TargetPath -eq $exe -and $link.Arguments -eq '--userconfig=userconfig_akaaka') {
        Remove-OwnedChild $DesktopDirectory '赤灯预翻译.lnk'
    }
}
# Leave a different Luna installation's saved startup location intact.
if ($recorded -and [IO.Path]::GetFullPath($recorded).TrimEnd('\') -eq $LunaDirectory) {
    if ([IO.Path]::GetFileName([IO.Path]::GetFullPath($StateDirectory).TrimEnd('\')) -ne 'AkaakaLunaOCR') {
        throw '安装记录路径检查失败'
    }
    Remove-OwnedChild (Split-Path -Parent $StateDirectory) 'AkaakaLunaOCR' -Recurse
}
Write-Host '赤灯预翻译已卸载。Luna 本体和原来的设置已保留。'
if (-not $Unattended) { [Windows.Forms.MessageBox]::Show('卸载完成。需要使用时，可重新运行安装 CMD。', '赤灯预翻译') | Out-Null }
