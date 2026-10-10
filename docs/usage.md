# 使用指南

**简体中文** · [English](usage.en.md) · [返回首页](../README.md)

安装方式见[首页快速开始](../README.md)。VidSkim 负责获取音视频、在本地识别语音并保存 Markdown；精华由你正在使用的 AI 工具生成。

## 常用命令

```bash
vidskim setup                          # 下载并准备语音识别模型
vidskim skill                          # 输出完整 AI 操作说明
vidskim demo                           # 预览随包提供的示例
vidskim ./video.mp4
vidskim ./interview.mp3
vidskim "https://v.douyin.com/n234HvHgzN0/"
vidskim "这里粘贴完整的抖音分享文本，包括链接"
vidskim --help
vidskim --version
```

`setup` 无交互，首次下载模型可能需要几分钟。`demo` 展示预置内容，不会现场转写。`skill` 供 AI 读取，不会修改或自动安装到 AI 工具的配置中。

转写命令在 stdout 输出 JSON 素材清单，在 stderr 显示进度。清单包含来源、时长、片段数，以及以下绝对路径：

| 字段 | 内容 |
| --- | --- |
| `transcript_json` | 供 AI 读取的完整识别稿 |
| `transcript_md` | 带时间戳的原稿 Markdown |
| `summary_output` | 建议保存精华的路径，转写完成时尚未生成 |

始终使用清单返回的实际路径，标题与目录名可能不同。

## 让 AI 提炼并保存

AI 工具需要能执行本地命令、读取文件并写入结果。让它先运行 `vidskim skill`，再处理视频或分享链接。

1. 执行 `vidskim INPUT`，读取 `transcript_json`。每段包含 `id`、`start`、`end` 和 `text`。
2. 完整读取全部片段；长稿按 ID 连续分块读取后综合，不能只总结开头或工具截断后的内容。
3. 在素材目录写入 `summary.json`，保留核心观点、理由、必要例子和适用条件，去掉广告、重复与铺垫。
4. 执行 `vidskim save`，读取返回的 `summary_md` 路径。

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
vidskim save ./digests/视频标题-ID/transcript.json --from ./digests/视频标题-ID/summary.json
vidskim save ./digests/视频标题-ID/transcript.json --from ./digests/视频标题-ID/summary.json -o ./notes/focus.md
```

`-o` 仅用于 `save`，目标必须是 `.md` 文件。省略时，精华保存至输入 `transcript.json` 所在目录的 `summary.md`。命令不会覆盖输入音视频、原稿或摘要 JSON。

时间戳由引用片段生成，不能由 AI 随意填写。引用校验只确认片段存在，不能保证观点准确；识别错误也可能影响总结。需要时请核对原稿。

可在源码目录用[摘要示例](../examples/summary.json)和[对应原稿](../examples/transcript.json)试用保存命令：

```bash
vidskim save ./examples/transcript.json --from ./examples/summary.json -o ./example-digest.md
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

| 环境变量 | 用途 |
| --- | --- |
| `VIDSKIM_ASR_MODEL` | 语音识别模型，默认 `small` |
| `VIDSKIM_LANGUAGE` | 识别语言，例如 `zh`；不设置时自动检测 |
| `VIDSKIM_CACHE_DIR` | 处理缓存目录，默认 `~/.cache/vidskim` |

VidSkim 不配置或调用摘要 API。AI 工具使用它已有的模型和额度，并按其自身方式处理读取的原稿。

当前 Skill 默认生成中文精华，Markdown 固定标题也为中文。如需英文正文，可在给 AI 的请求中明确说明；`VIDSKIM_LANGUAGE` 只影响语音识别，不是摘要语言设置。

## 适用范围

适合以讲话为主的经验分享、访谈和讲解。仅存在于画面、图表或屏幕中的信息不会被自动识别。抖音解析会受作品可用性与平台变化影响。

示例与可复现结果见[验证记录](verification.md)。开发和反馈方式见[贡献指南](../CONTRIBUTING.md)。
