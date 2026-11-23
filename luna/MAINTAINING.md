# 维护预翻译

日常修改以下三个文件并提交 Git。仓库中的 GitHub Actions 会检查数据、运行测试并生成更新清单。

| 文件 | 用途 |
|---|---|
| `runtime/data.json.gz` | 单一词库，含日文、官方简繁、定稿简繁和地图 |
| `runtime/rules.json` | 相似度、上下文范围、已确认 OCR 纠错 |
| `runtime/engine.py` | 匹配算法 |

## 修改文本

使用原始文本 ID。例如以下命令只修改 ID 16806 的对应简繁定稿。

```powershell
python luna/maintainer/edit_text.py 16806 --zh "因为，这一定不是黑狐的本意。" --cht "因為，這一定不是黑狐的本意。"
python luna/maintainer/build.py
```

断行可以写为 `<br>`。简繁分别维护，不自动把简体转换为繁体。脚本不会修改游戏或之前发布的 Steam 补丁。

词库每条记录为 `[ID, 脚本文件, 日文, 官方简中, 官方繁中, 定稿简中, 定稿繁中]`。保留原始 ID，重复句不合并。地图记录为 `[日文, 官方简中, 官方繁中, 定稿简中, 定稿繁中]`。

## 发布更新

```powershell
python -m unittest discover -s luna/tests
python luna/maintainer/build.py
git add luna
git commit -m "Update pretranslation text and matching rules"
git push
```

也可以省略本地测试和构建命令，提交 `runtime` 的修改后由 GitHub Actions 自动执行。等工作流成功，再通知用户更新。构建会生成按内容命名的 `releases/<版本>/`，并更新 `manifest.json`。三个组件的 SHA256 校验都通过才切换用户缓存。保留已发布版本目录，版本内容不要原地修改。将新版本组件与清单一起提交，避免出现清单先到、文件未到的更新。

`selfbuild.py` 是稳定的加载入口，通常无需修改。它会从本仓库下载并加载 `engine.py`，因此此仓库中的匹配代码会在用户的 Luna 内运行。只有维护者可发布更新。若将来必须修改加载入口，用户需重跑安装入口。

## 原生配置

语言使用 Luna 的源语言、目标语言设置，样式与 OCR 使用 Luna 原有设置，不增加游戏专用语言选项。加载入口按 Luna 原生自定义接口约定放在 `userconfig_akaaka/selfbuild.py`。

更新源固定为 `Haccayukie/Akaaka_Steam_Patch`。发布到其他仓库时，需同时修改安装器和加载入口的 URL。用户本地的语言和样式配置不会被日常后台更新覆盖。
