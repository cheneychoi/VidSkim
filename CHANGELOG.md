# Changelog

Notable user-facing changes are recorded here. Entries under `Unreleased` are prepared for the next release.

## Unreleased

### Added

- `watch2note setup --codex` and `watch2note setup --claude` to install a personal Skill and prepare the speech model in one step.
- Direct AI invocation with `$watch2note` in Codex and `/watch2note` in Claude Code, plus bilingual setup and upgrade instructions.
- Progress reporting that separates processing stages, audio position, and elapsed time.
- Links to this changelog and the commit history.
- English commit message guidance and documentation of AI-assisted contributions.

### Changed

- Renamed the project to Watch2Note (视频拾记), with a matching repository, Python package, CLI, and Skill name.
- Renamed configuration variables to `WATCH2NOTE_*` and the default cache directory to `~/.cache/watch2note`; added migration instructions for VidSkim users.
- Load a complete cached speech model locally, avoiding a network check on each run.
- Made the installed Skill the primary way to start a complete transcription-to-Markdown workflow.
- Made both READMEs focus on Skill installation, invocation, and the resulting notes; moved detailed CLI usage to bilingual advanced guides.
- Reframed both READMEs around keeping useful ideas, revisiting the source, and developing personal understanding, with a transcript-backed excerpt and a clearly labeled reflection example.
- Simplified the README license section and added a brief note about reference and learning use.

## 0.1.0 · VidSkim (legacy release)

Published under the former name VidSkim. The historical tag and packages use that name and do not include the changes listed under `Unreleased`.

### Added

- Local audio and video transcription with faster-whisper, including timestamped Markdown and JSON transcripts.
- Douyin video URLs, short share links, and full share text as inputs.
- A bundled AI workflow available through `vidskim skill`: the calling AI reads the complete transcript and prepares the digest using its existing model.
- `vidskim save` to validate transcript references and export a digest as Markdown, including an optional output location.
- `vidskim setup` to prepare the speech recognition model and `vidskim demo` to preview a bundled note.
- Reuse of valid transcripts for repeated inputs, with completed transcripts retained for resuming the AI workflow.
- Chinese and English documentation, local-video and Douyin digest examples, and an MIT license.
- CI checks on Linux, macOS, and Windows.
