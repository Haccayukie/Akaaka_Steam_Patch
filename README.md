# 赤灯 Steam 完全汉化补丁 v1.0.0

[下载完整补丁 v1.0.0（含简繁攻略）](https://github.com/Haccayukie/Akaaka_Steam_Patch/releases/download/v1.0.0/Akaaka_Steam_Patch_v1.0.0.zip) · [发布页与校验文件](https://github.com/Haccayukie/Akaaka_Steam_Patch/releases/tag/v1.0.0)

## 下载包内文件

```text
Akaaka_Steam_Patch_v1.0.0/
├─ PatchData/
│  ├─ payload/
│  ├─ install.sh
│  ├─ installer.ps1
│  ├─ installer.py
│  ├─ manifest.json
├─ 游戏攻略/
│  ├─ 简体/
│  ├─ 繁體/
├─ 【SteamDeck掌机用】1_安装补丁_v1.0.0.desktop
├─ 【SteamDeck掌机用】2_还原补丁_v1.0.0.desktop
├─ 【WindowsPC用】1_Steam安装补丁_v1.0.0.cmd
├─ 【WindowsPC用】2_Steam还原补丁_v1.0.0.cmd
├─ 使用说明.txt
├─ 赤灯汉化成员列表.png
```

[查看完整文件清单](FILES.md)。以下是下载包内容的预览；安装请下载并完整解压上方补丁包。

适用于《赤红灯火妖魅行 缀/あかやあかしやあやかしの 綴/赤与灯皆有诡异 缀》Steam 版，包含简体中文与繁体中文。
Windows 与 SteamDeck 共用一套补丁文件。

## Windows
完整下载并解压，双击 “【WindowsPC用】1_Steam安装补丁_v1.0.0.cmd”，按提示选择游戏目录。安装后从 Steam 启动游戏，在设置中选择简体中文或繁体中文。

## SteamDeck
在桌面模式完整解压，运行 “【SteamDeck掌机用】1_安装补丁_v1.0.0.desktop”。若无法双击执行，在本文件夹打开终端运行 “bash ./PatchData/install.sh”。

Steam 游戏属性的启动选项填入：

```text
WINEDLLOVERRIDES="winhttp.dll=n,b" %command%
```

返回游戏模式从 Steam 启动，游戏内选择中文。

## 攻略
攻略位于 “游戏攻略/简体” 和 “游戏攻略/繁體”，简体版打开 “[赤灯·缀]全事件攻略.html”，繁體版開啟 “[赤燈·綴]全事件攻略.html”。

## 更新与还原
更新时重新运行对应平台的新版安装入口。还原请运行对应的“一键还原补丁”入口；SteamDeck 还需清除上述启动选项。保留游戏目录中的 “.akaaka-fanpatch” 原版备份。

补丁不含游戏本体。完整安装注意事项请阅读“使用说明.txt”。

PatchData 为安装组件文件夹，请完整保留，无须打开或单独运行其中的文件。
