<h1 align="center">VidSkim</h1>

<p align="center"><b>视频太长，读精华就好。</b></p>

<p align="center">
  <strong>简体中文</strong> | <a href="README.en.md">English</a>
</p>

## 为什么做 VidSkim？

收藏了一个访谈、一段经验分享，觉得值得看，却一直没空点开。等到想找其中某个观点，又得拖着进度条从头翻。收藏夹越积越多，真正留下来的内容却很少。

VidSkim 想让这件事简单一点：把视频链接或本地文件交给你正在使用的 AI，让它读完内容，去掉重复和铺垫，留下观点、理由和必要的例子。几分钟读完一份精华，感兴趣的地方再按时间戳回看。

整理好的内容保存为 Markdown，放进 Obsidian 或普通笔记文件夹都可以。想回顾时能找到，想接着思考时也能直接交给 AI。**把“以后再看”变成一篇现在就能读的笔记。**

## 快速开始

> **环境要求：** macOS、Linux 或 Windows，已安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) 和 [Git](https://git-scm.com/downloads)，以及能执行本地命令、读写文件的 AI 工具，例如 Codex 或 Claude Code。

### 第一步：安装

```bash
uv tool install --python 3.12 "git+https://github.com/cheneychoi/VidSkim.git"
vidskim setup
```

`uv` 会在需要时准备 Python。`setup` 首次下载语音识别模型，之后在本地运行，无需 GPU。

### 第二步：把视频交给 AI

在 AI 工具里粘贴下面这段话，把链接换成你想看的视频：

```text
先运行 vidskim skill，按其中流程处理这个视频：
https://v.douyin.com/n234HvHgzN0/

完整阅读内容，提炼成几分钟能读完的精华，保存为 Markdown。
告诉我保存路径。
```

也可以换成本地文件路径，例如 `./video.mp4`、`./interview.mp3`，或直接粘贴抖音的整段分享文本。

### 第三步：打开笔记

AI 会返回保存路径。默认精华位于 `digests/视频标题-ID/summary.md`，同目录保留带时间戳的原稿。想直接放进自己的笔记文件夹，在请求里加一句“保存到 `./notes/video.md`”即可。

## 使用方法

通常只需要把需求交给 AI。它会通过 `vidskim skill` 读取处理说明，并使用以下命令：

```bash
vidskim skill                              # 读取 AI 处理流程
vidskim ./video.mp4                         # 转写本地音视频
vidskim "https://v.douyin.com/n234HvHgzN0/"  # 转写抖音视频，也支持完整分享文本
vidskim demo                               # 预览内置笔记示例
vidskim --help                             # 查看命令帮助
```

转写完成后，AI 读取原稿并写好 `summary.json`，再在素材目录执行：

```bash
vidskim save transcript.json --from summary.json
```

指定保存位置时，在命令末尾加上 `-o ./notes/video.md`。完整参数和文件格式见[使用指南](docs/usage.md)。

## 输出效果

每个视频对应一个文件夹，精华和原稿放在一起：

```text
digests/视频标题-ID/
├── summary.md         # 最后阅读的精华
├── summary.json       # AI 整理的内容
├── transcript.md      # 带时间戳的原稿
└── transcript.json    # 供 AI 读取的原稿
```

精华由**一句话概括、核心观点和精简正文**组成。观点附有来自原稿的时间戳，方便回看。下面是一段实际输出：

> **一句话看懂**
>
> 视频认为，AI 普及不必然缩小人与人的差距，专业认知、具体提问和筛选结果的能力会影响工具带来的收益。

查看完整示例：[抖音视频精华](examples/douyin-digest.md) · [本地视频精华](examples/verified/summary.md)。

## 工作原理

1. VidSkim 读取本地文件，或从抖音分享链接获取视频。
2. 使用 faster-whisper 在本地识别语音，生成带时间戳的完整原稿。
3. 你的 AI 阅读全部原稿，提炼观点、理由和必要例子，写入 `summary.json`。
4. `vidskim save` 校验引用的原稿片段，再导出 Markdown。

**无需另配摘要 API Key。** 总结使用你正在使用的 AI 工具及其模型、额度。VidSkim 处理音轨，不读取只存在于画面中的图表或文字。

## 配置

默认配置即可使用。需要调整时，通过环境变量设置：

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `VIDSKIM_ASR_MODEL` | 语音识别模型 | `small` |
| `VIDSKIM_LANGUAGE` | 语音识别语言，例如 `zh` | 自动检测 |
| `VIDSKIM_CACHE_DIR` | 处理缓存目录 | `~/.cache/vidskim` |

## 常见问题

| 问题 | 说明 |
|------|------|
| 第一次运行为什么比较慢？ | 首次需要下载语音模型；转写耗时取决于视频长度和设备性能。 |
| 抖音链接无法解析？ | 作品可用性和平台变化可能影响解析。有本地音视频时，可以直接处理文件。 |
| 只生成了原稿，没有精华？ | 转写命令只生成原稿。让 AI 按 `vidskim skill` 的说明继续总结并保存。 |
| 中途中断，需要从头来吗？ | 已完成的原稿会保留，让 AI 接着整理即可。同一输入与设置的有效转写缓存也会复用。 |

## 参与项目

欢迎[反馈问题](https://github.com/cheneychoi/VidSkim/issues)或[参与改进](CONTRIBUTING.md)。[更新记录](CHANGELOG.md) · [提交历史](https://github.com/cheneychoi/VidSkim/commits/main/)。

感谢 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 提供本地语音识别能力，以及 [media-parser](https://github.com/ucmao/media-parser) 提供抖音移动 Feed 入口的参考。

## 许可证

[MIT](LICENSE)

本项目供参考与学习使用。
