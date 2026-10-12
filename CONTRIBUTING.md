# Contributing · 参与贡献

[简体中文 README](README.md) · [English README](README.en.md)

## 中文

欢迎通过 [Issue](https://github.com/cheneychoi/Watch2Note/issues) 反馈问题或建议，也欢迎提交 Pull Request。

报告问题时，请附上 Watch2Note 版本、操作系统、输入类型、执行命令、错误信息和复现步骤。分享日志前请移除私人内容；公开视频可提供链接，本地文件可用简短的可分享样例代替。

需要 Python 3.11+ 和 [uv](https://docs.astral.sh/uv/getting-started/installation/)。准备开发环境并检查改动：

```bash
git clone https://github.com/cheneychoi/Watch2Note.git
cd Watch2Note
uv sync --locked
uv run ruff check .
uv run pytest
uv build
```

提交 PR 时，请说明解决的问题、用户可见的变化及验证方式。保持改动集中；行为发生变化时补充相关测试，并同步中英文文档。

提交信息使用英文，简明描述改动，例如 `docs: add the Douyin workflow demo` 或 `fix: preserve Markdown links on Windows`。面向用户的变化请补充到 [CHANGELOG.md](CHANGELOG.md) 的 `Unreleased` 部分。

欢迎使用 AI 工具协作。请在 PR 描述中注明所用工具与协作范围，并由提交者检查代码和验证结果。

实际转写与完整 AI 流程的验证记录见 [docs/verification.md](docs/verification.md)。用户操作说明见[使用指南](docs/usage.md)。

## English

Bug reports and suggestions are welcome in [Issues](https://github.com/cheneychoi/Watch2Note/issues), as are pull requests.

For a bug report, include your Watch2Note version, operating system, input type, command, error message, and reproduction steps. Remove private content from logs. You may share a public video link or a short, shareable sample for a local file.

Development requires Python 3.11+ and [uv](https://docs.astral.sh/uv/getting-started/installation/). Use the commands above to clone the repository, install dependencies, run lint and tests, and build the package.

In your PR, describe the problem, user-visible changes, and how you checked them. Keep changes focused, add relevant tests for changed behavior, and update both language versions of the documentation.

Write commit messages in English and describe the change briefly, for example `docs: add the Douyin workflow demo` or `fix: preserve Markdown links on Windows`. Add user-facing changes to the `Unreleased` section of [CHANGELOG.md](CHANGELOG.md).

AI-assisted contributions are welcome. Identify the tool and its role in your PR, and review the code and validation results yourself.

See [docs/verification.md](docs/verification.md) for real transcription and complete AI workflow checks, or the [usage guide](docs/usage.en.md) for user instructions.
