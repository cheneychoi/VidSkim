# Watch2Note · 视频拾记

Keep the ideas. Take your thinking further.

Watch2Note turns a Douyin link or local audio/video into a readable Markdown note through your existing AI tool. The CLI fetches media and transcribes speech locally; the Skill guides Codex or Claude Code through reading the complete transcript, writing a digest, and saving it.

## Current source version

- Repository: [cheneychoi/Watch2Note](https://github.com/cheneychoi/Watch2Note).
- Python package, CLI, and Skill: `watch2note`.
- Local transcription with timestamps, validated transcript references, Markdown export, and reusable transcription caches.
- Personal Skill installation for Codex and Claude Code, with progress reporting during processing.
- Bilingual installation instructions and examples in the [README](README.en.md).

Install the current source in your terminal:

```bash
uv tool install --python 3.12 "git+https://github.com/cheneychoi/Watch2Note.git"
watch2note setup --codex
# Or: watch2note setup --claude
```

In your AI chat, invoke `$watch2note VIDEO_LINK` in Codex or `/watch2note VIDEO_LINK` in Claude Code. Python is managed by uv, and the speech model downloads on first setup. No separate summary API key is needed.

## Historical v0.1.0 version

The historical [v0.1.0 tag](https://github.com/cheneychoi/Watch2Note/tree/v0.1.0) and older installation packages use the name VidSkim. That version uses the `vidskim` command and does not include the Watch2Note rename or native Skill installation options. Install the current source from `main` to use Watch2Note.

The rename is available from the current source; it has not been published as a new GitHub Release. For existing installations, follow the [migration guide](docs/usage.en.md#migrate-from-vidskim-or-update). See the [changelog](CHANGELOG.md) for changes and the [verification record](docs/verification.md) for completed checks.

Speech recognition and summaries can contain errors. The retained transcript supports checking; information that appears only in video frames is not read. Douyin extraction depends on video availability and platform behavior.

This project is intended for reference and learning.
