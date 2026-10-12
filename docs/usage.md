# 进阶 CLI 指南

**简体中文** · [English](usage.en.md) · [返回首页](../README.md)

日常使用只需按[首页的安装和使用步骤](../README.md)接入 Skill，然后在 AI 聊天中发送链接。本页供需要手动运行命令、读取转写结果、控制保存位置或接入其他 AI 工具的用户参考。

Watch2Note（视频拾记）的 CLI 负责获取音视频、本地语音识别和文件保存；Skill 让你正在使用的 AI 读取完整原稿、生成精华，再调用 CLI 保存 Markdown。

> 本指南对应 Watch2Note 当前源码版本。历史 `v0.1.0` 标签和旧安装包使用 VidSkim 名称，不包含新名称及 Skill 安装参数。请按首页从 GitHub 源码安装。

## CLI 命令

以下命令在系统终端运行。`watch2note INPUT` 负责转写，精华由调用它的 AI 生成；`save` 将已有摘要 JSON 写成 Markdown，不会自行调用模型总结。

```bash
watch2note setup                          # 下载并准备语音识别模型
watch2note setup --codex                  # 同时安装 Codex Skill
watch2note setup --claude                 # 同时安装 Claude Code Skill
watch2note skill                          # 输出完整 AI 操作说明
watch2note demo                           # 预览随包提供的示例
watch2note ./video.mp4
watch2note ./interview.mp3
watch2note "https://v.douyin.com/n234HvHgzN0/"
watch2note "这里粘贴完整的抖音分享文本，包括链接"
watch2note --help
watch2note setup --help
watch2note save --help
watch2note --version
```

`setup` 无交互，首次下载模型可能需要几分钟。`demo` 展示预置内容，不会现场转写。`skill` 只输出处理说明；安装入口是 `setup --codex` 或 `setup --claude`。

### 转写输出

转写命令在 stdout 输出 JSON 素材清单，在 stderr 显示进度。清单包含来源、时长、片段数，以及以下绝对路径：

| 字段 | 内容 |
| --- | --- |
| `transcript_json` | 供 AI 读取的完整识别稿 |
| `transcript_md` | 带时间戳的原稿 Markdown |
| `summary_output` | 建议保存精华的路径，转写完成时尚未生成 |

始终使用清单返回的实际路径，标题与目录名可能不同。需要脚本读取结果时，可单独保存 stdout，进度仍显示在终端：

```bash
watch2note "https://v.douyin.com/n234HvHgzN0/" > manifest.json
```

成功退出码为 `0`，处理失败为 `1`，命令参数错误为 `2`，用户取消为 `130`。失败时查看 stderr，不要把未完成的输出当成成功结果。

## 怎样看进度

获取视频和识别语音是不同的步骤。视频已下载成功，表示素材已就绪；还需要解码音频、加载模型并识别，才能得到文字。

CLI 会报告链接解析、下载、模型加载和转写阶段。转写会区分音频处理位置与实际已耗时，例如 `02:00 / 05:49` 表示处理到一段 5 分 49 秒音频的第 2 分钟，不代表任务刚开始两分钟，也不是预计还需两分钟。原稿完成后，由 AI 继续报告正在总结和保存。

默认 `small` 模型在 CPU 上运行，几分钟的视频也可能需要几分钟转写，取决于设备、音频和识别设置。进度提示不会提高模型本身的速度。AI 客户端可能在命令执行期间缓冲日志，因此聊天中的更新频率也取决于客户端。

## 摘要 JSON 与 Markdown 保存

调用已安装的 Skill 后，AI 会执行以下流程。使用其他 AI 工具时，让它先运行 `watch2note skill` 读取说明。

1. 执行 `watch2note INPUT`，读取 `transcript_json`。每段包含 `id`、`start`、`end` 和 `text`。
2. 完整读取全部片段；长稿按 ID 连续分块读取后综合，不能只总结开头或工具截断后的内容。
3. 在素材目录写入 `summary.json`，保留核心观点、理由、必要例子和适用条件，去掉广告、重复与铺垫。
4. 执行 `watch2note save`，读取返回的 `summary_md` 路径。

摘要 JSON 结构：

```json
{
  "overview": "一句话概括最重要的信息。",
  "points": [
    {"text": "一条核心观点及必要解释。", "segment_ids": [0, 1]},
    {"text": "另一条核心观点。", "segment_ids": [2]}
  ],
  "body": "把观点、理由和必要例子串成一篇顺畅的精简正文。"
}
```

`overview`、`body` 和每条 `text` 必须是非空字符串。`points` 接受 1—5 条；`segment_ids` 必须为非空整数数组，引用当前原稿中实际存在的 ID。上面的编号仅演示结构。

```bash
watch2note save ./digests/视频标题-ID/transcript.json --from ./digests/视频标题-ID/summary.json
watch2note save ./digests/视频标题-ID/transcript.json --from ./digests/视频标题-ID/summary.json -o ./notes/focus.md
```

`-o` 仅用于 `save`，目标必须是 `.md` 文件。省略时，精华保存至输入 `transcript.json` 所在目录的 `summary.md`。命令不会覆盖输入音视频、原稿或摘要 JSON；若目标处已有其他同名 Markdown，会替换该文件。成功后 stdout 返回 `{"summary_md": "保存文件的绝对路径"}`。

时间戳由引用片段生成，不能由 AI 随意填写。引用校验只确认片段存在，不能保证观点准确；识别错误也可能影响总结。需要时请核对原稿。

可在源码目录用[摘要示例](../examples/summary.json)和[对应原稿](../examples/transcript.json)试用保存命令：

```bash
watch2note save ./examples/transcript.json --from ./examples/summary.json -o ./example-digest.md
```

## 文件位置与恢复

默认输出位于运行命令时的当前目录：

```text
digests/
└── 视频标题-ID/
    ├── transcript.json
    ├── transcript.md
    ├── summary.json     # AI 生成
    └── summary.md       # save 生成
```

`save -o` 只改变精华的位置，识别原稿仍留在原处。精华末尾链接到输入 JSON 同目录的 `transcript.md`，若缺失则链接到 `transcript.json`；通常使用相对链接，Windows 跨盘保存时使用绝对文件链接。整理笔记时，请保留原稿并注意移动文件后链接是否仍然有效。

总结中断时，已完成的原稿仍可继续使用。让 AI 读取现有原稿、完成 `summary.json` 并运行 `save`，无需重新识别。同一输入与识别设置再次转写时，会复用有效缓存。

处理缓存按 7 天、最多 20 个项目清理，清理在处理输入时进行；语音模型缓存独立管理。长期保存请保留 `digests` 中的文件或自行指定的 Markdown。

抖音链接解析失败时，可将已取得的本地音视频文件交给同一条命令处理。

## 模型与设置

默认使用 faster-whisper 的 `small` 模型，以 CPU `int8` 运行，无需 CUDA。PyAV 负责音频解码，通常无需另外安装 FFmpeg。

模型文件已完整缓存时，直接从本地加载；仅在缓存缺失或不完整时下载，减少启动时的网络等待。

| 环境变量 | 用途 |
| --- | --- |
| `WATCH2NOTE_ASR_MODEL` | 语音识别模型名称或本地模型目录，默认 `small` |
| `WATCH2NOTE_LANGUAGE` | 识别语言，例如 `zh`；不设置时自动检测 |
| `WATCH2NOTE_CACHE_DIR` | 处理缓存与语音模型的根目录，默认 `~/.cache/watch2note` |

Watch2Note 不配置或调用摘要 API。AI 工具使用它已有的模型和额度，并按其自身方式处理读取的原稿。

当前 Skill 默认生成中文精华，Markdown 固定标题也为中文。如需英文正文，可在给 AI 的请求中明确说明；`WATCH2NOTE_LANGUAGE` 只影响语音识别，不是摘要语言设置。

## Skill 安装、升级与兼容

在终端为你使用的 AI 工具安装 Skill，同时准备语音识别模型：

```bash
watch2note setup --codex
# 或
watch2note setup --claude
```

同时使用两个工具时，运行 `watch2note setup --codex --claude`。只运行 `watch2note setup` 仍然仅准备语音模型，不安装 Skill。

再次运行对应的 `setup` 命令，会更新由 Watch2Note 安装且未被手工修改的 Skill。若目标位置的 `SKILL.md` 是内容不同的自定义或手工修改版本，或 Skill 目录或文件是符号链接，安装会停止并显示冲突路径；请先将该目录移到其他位置，再重试。

| AI 工具 | Skill 安装位置 | 聊天输入框中的用法 |
| --- | --- | --- |
| Codex | `~/.agents/skills/watch2note/SKILL.md` | `$watch2note https://v.douyin.com/n234HvHgzN0/` |
| Claude Code | `~/.claude/skills/watch2note/SKILL.md` | `/watch2note https://v.douyin.com/n234HvHgzN0/` |

在 Codex 中先输入 `$` 并选择 `watch2note`；Codex CLI 和 IDE 扩展也可以通过 `/skills` 选择。Claude Code 则在输入框键入 `/watch2note`。这些是 **AI 聊天中的调用方式**，不要粘贴到系统终端执行。安装后若列表中没有 Watch2Note，重开会话或重启客户端。相关机制见 [Codex Skills 文档](https://learn.chatgpt.com/docs/build-skills)与 [Claude Code Skills 文档](https://code.claude.com/docs/en/skills)。

这里指能执行本机命令、读写文件的 Codex 本地会话和 Claude Code；Claude 网页聊天不会读取本机安装的 Skill。AI 执行命令时仍遵循你为客户端设置的权限。

链接后面可以直接追加要求，例如“保存到 `./notes/ai.md`”或“用英文总结”。本地文件路径和抖音的完整分享文本也可以作为输入。AI 会按 Skill 完成转写、阅读全部原稿、总结和保存，最后给出文件路径。

### 找不到 watch2note 命令

安装完成后，如果终端提示找不到 `watch2note`，运行 `uv tool update-shell`，然后重新打开终端。已打开的 AI 客户端也需要重启，以读取更新后的命令路径。

### 从 VidSkim 迁移或更新

Watch2Note 是 VidSkim 的新名称，Python 包、CLI 和 Skill 统一使用 `watch2note`。

**运行 `setup` 前**，若设置过 `VIDSKIM_*` 环境变量，请改为对应的 `WATCH2NOTE_*`。默认缓存目录现为 `~/.cache/watch2note`；如需复用旧模型缓存，请先将 `WATCH2NOTE_CACHE_DIR` 设为原来缓存目录的绝对路径（默认是用户目录下的 `.cache/vidskim`）。旧缓存不会被自动搬移或删除。

在终端安装当前源码，并为你使用的 AI 工具运行 `setup`：

```bash
uv tool install --reinstall --python 3.12 "git+https://github.com/cheneychoi/Watch2Note.git"
watch2note setup --codex
# 使用 Claude Code 时，改为 watch2note setup --claude
```

重开 AI 会话后，改用 `$watch2note` 或 `/watch2note`。已有的原稿与 Markdown 笔记可以继续使用，无需重新转写。

确认新命令和 Skill 可用后，可选择运行 `uv tool uninstall vidskim` 卸载旧 CLI。旧 Skill 也不会自动删除：先检查 `~/.agents/skills/vidskim` 或 `~/.claude/skills/vidskim` 中有无自定义内容，需要时保留备份，再自行移出客户端的 Skill 目录。

### 使用其他 AI 工具

不支持 Skill 安装、但能运行本地命令的 AI 工具，可以用以下请求读取同一份流程说明：

```text
运行 watch2note skill，按其中流程处理这个视频：
https://v.douyin.com/n234HvHgzN0/
完整阅读原稿，提炼精华并保存 Markdown，告诉我文件路径。
```

## 适用范围

适合以讲话为主的经验分享、访谈和讲解。仅存在于画面、图表或屏幕中的信息不会被自动识别。抖音解析会受作品可用性与平台变化影响。

示例与可复现结果见[验证记录](verification.md)。开发和反馈方式见[贡献指南](../CONTRIBUTING.md)。
