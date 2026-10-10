# VidSkim 0.1.0

没时间看完整视频？让你正在使用的 AI 读完，把精华保存为 Markdown。

## 首版功能

- 接受本地音视频、抖音分享短链和完整分享文本。
- 在本地使用 faster-whisper 转写，保留完整原稿和真实时间戳。
- 随包提供 AI Skill，让当前模型阅读全稿、提炼观点，不配置另一套摘要 API。
- 校验精华引用的段落编号，保存适合个人知识库的 Markdown。
- 复用有效识别缓存，失败后可接着完成总结。
- 提供中英文 README、使用示例、MIT 许可和 GitHub Actions 配置。

## 发布验证

119 项测试与 Ruff 检查通过。实际完成 348.996 秒抖音分享短链、23.638 秒公开抖音视频和 162 秒本地合成口播的转写、AI 总结及 Markdown 保存。新构建的 wheel 也完成真实链接处理与保存。[完整验证记录](docs/verification.md)。

抖音数据接口可能变化，未返回目标视频时会明确失败；纯画面、图表和屏幕内容尚不识别。视频识别和摘要可能有错误，可通过保留的原稿核对。

## GitHub 发布材料

- 仓库名：`VidSkim`
- 简介：让你的 AI 快速读完视频，把精华保存为 Markdown。支持本地音视频和抖音分享链接。
- 建议 Topics：`python`、`cli`、`video-transcription`、`whisper`、`markdown`、`ai-tools`、`douyin`
- 首次版本：`v0.1.0`
- 发布附件：`dist/vidskim-0.1.0-py3-none-any.whl`、`dist/vidskim-0.1.0.tar.gz`

源码仓库：[cheneychoi/VidSkim](https://github.com/cheneychoi/VidSkim)。发布附件可通过 `uv build` 在本地生成；GitHub Release 与 PyPI 尚未发布。[查看远程 CI 结果](https://github.com/cheneychoi/VidSkim/actions)。
