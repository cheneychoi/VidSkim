<h1 align="center">Watch2Note · 视频拾记</h1>

<p align="center"><b>把内容留下，把思考展开。</b></p>

<p align="center">
  <strong>简体中文</strong> | <a href="README.en.md">English</a>
</p>

Watch2Note（视频拾记）是一个用于 **Codex 和 Claude Code 的视频精华 Skill**。给它一个抖音链接或本地音视频，让 AI 把观点、理由与例子整理成一篇可读的 Markdown 笔记。无需另配摘要 API Key。

## 收藏了很多视频，后来都看了吗？

一段访谈，一次经验分享，一个让你停下来想了想的观点。总想着以后看，却一直没时间。等到再次需要其中的内容，又得拖着进度条从头找。

Watch2Note 帮你先把内容留下：去掉重复和铺垫，保留观点背后的理由与例子，整理成几分钟能读完的精华。想深入的地方，按时间戳回看；值得记住的内容，留在自己的笔记库里。

**从别人的分享，到自己的理解。** 有了可以回顾、核对和补充的笔记，你可以把新观点与已有的知识联系起来，沿着新的问题继续思考。

## 快速开始

**给它一个链接，留下内容精华。** 安装一次，之后在 AI 聊天中调用即可。

> **环境要求：** macOS、Linux 或 Windows，已安装 [uv](https://docs.astral.sh/uv/getting-started/installation/) 和 [Git](https://git-scm.com/downloads)，以及能执行本地命令、读写文件的 AI 工具，例如 Codex 或 Claude Code。

### 第一步：安装 Watch2Note

在终端运行：

```bash
uv tool install --python 3.12 "git+https://github.com/cheneychoi/Watch2Note.git"
```

`uv` 会在需要时准备 Python。安装完成后，再按下一步将 Watch2Note 接入你使用的 AI 工具。

### 第二步：接入你用的 AI

在终端运行对应的一条命令，安装 Skill 并准备语音识别模型：

```bash
watch2note setup --codex    # Codex
watch2note setup --claude   # Claude Code
```

首次需要下载语音模型，完成后会显示 Skill 的调用方式。之后模型在本地运行，无需 GPU。安装后若找不到 Skill，重开会话或重启 AI 工具。

### 第三步：输入 Skill 和视频链接

在 **Codex 聊天输入框**中输入 `$`，选择 `watch2note`，后面接上链接：

```text
$watch2note https://v.douyin.com/n234HvHgzN0/
```

在 **Claude Code 聊天输入框**中输入：

```text
/watch2note https://v.douyin.com/n234HvHgzN0/
```

以上内容输入在 AI 聊天中，无需在终端运行。也可以把链接换成本地文件路径，如 `./video.mp4`、`./interview.mp3`，或抖音的整段分享文本。

AI 会自动完成 **获取视频 → 转写原稿 → 提炼精华 → 保存笔记**，最后返回 Markdown 文件链接。想放进自己的笔记文件夹，在链接后再加一句“保存到 `./notes/video.md`”即可。

从旧版本升级、命令找不到或使用其他 AI 工具，见[进阶指南](docs/usage.md)。

## 你会得到什么

**观点、理由、例子，整理成一篇可读的笔记。** 每篇笔记包含一句话概括、核心观点和精简正文，保留理解一个观点所需的上下文。

下面摘自[一份实际生成的抖音视频笔记](examples/douyin-digest.md)：

> **一句话看懂**
>
> 视频认为，AI 普及不必然缩小人与人的差距，专业认知、具体提问和筛选结果的能力会影响工具带来的收益。
>
> **核心观点 · 01:31、01:42**
>
> 同一套 AI，使用方式可能差很大。视频对比泛泛描述、反复生成的新手，与给出具体专业条件、筛选方案并继续加工的视觉总监，强调专业经验仍参与结果形成。

**想深入的地方，按时间戳回看。** 核心观点附有原稿对应的时间戳，完整转写原稿也会保留，方便核对。更多示例：[本地视频精华](examples/verified/summary.md) · [带时间戳的原稿](examples/verified/transcript.md)。

**留下值得记住的观点。** 笔记保存为 Markdown，可放进 Obsidian 或普通笔记文件夹。默认位置为 `digests/视频标题-ID/summary.md`，也可以在请求中指定保存位置。

语音识别在本地完成，总结使用你正在使用的 AI 工具及其模型、额度。Watch2Note 处理音轨，不读取只存在于画面中的图表或文字。

## 从一篇笔记，继续思考

读完上面的笔记，你可以打开自己已有的相关记录，补上联想和问题。例如，在自己的「如何向 AI 提问」笔记里继续写下：

> **个人延伸示例 · 由你继续补充**
>
> **已有的经验：** 我给 AI 的任务越具体，得到的回答通常越贴近实际需要。
>
> **这次的理解：** 除了描述任务，我还需要知道如何判断一个回答是否有用。
>
> **新的问题：** 在我的工作里，哪些判断最需要经验？下一次提问前，我可以先写清哪些评价标准？

Watch2Note 提供有原稿可核对的笔记；这些联系与问题，由你结合自己的知识和经历继续展开，也可以交给正在使用的 AI 一起讨论。

**连接已有的知识，形成自己的理解。**

**沿着新的问题，继续思考。**

**视频拾记 · 把内容留下，把思考展开。**

## 常见问题

| 问题 | 说明 |
|------|------|
| 第一次运行为什么比较慢？ | 首次需要下载语音模型；转写耗时取决于视频长度和设备性能。 |
| 处理中会显示进度吗？ | 会分别报告解析、下载、模型加载和转写阶段，再由 AI 总结并保存。音频处理位置与实际耗时分开显示；聊天中的更新频率也取决于 AI 客户端。 |
| 抖音链接无法解析？ | 作品可用性和平台变化可能影响解析。有本地音视频时，可以直接处理文件。 |
| 只生成了原稿，没有精华？ | 直接运行转写命令只生成原稿。在 AI 中调用 Watch2Note Skill，或让它继续整理已有原稿并保存。 |
| 中途中断，需要从头来吗？ | 已完成的原稿会保留，让 AI 接着整理即可。同一输入与设置的有效转写缓存也会复用。 |

## 进阶用法

Watch2Note 保留 CLI，供 Skill 调用，也方便在终端或脚本中使用。完整命令、Markdown 导出、模型设置及缓存说明见[进阶 CLI 指南](docs/usage.md)。日常使用只需在 AI 中调用 Skill。

## 参与项目

欢迎[反馈问题](https://github.com/cheneychoi/Watch2Note/issues)或[参与改进](CONTRIBUTING.md)。[更新记录](CHANGELOG.md) · [提交历史](https://github.com/cheneychoi/Watch2Note/commits/main/)。

感谢 [faster-whisper](https://github.com/SYSTRAN/faster-whisper) 提供本地语音识别能力，以及 [media-parser](https://github.com/ucmao/media-parser) 提供抖音移动 Feed 入口的参考。

## 许可证

[MIT](LICENSE)

本项目供参考与学习使用。
