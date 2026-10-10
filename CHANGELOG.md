# Changelog

Notable user-facing changes are recorded here. Entries under `Unreleased` are prepared for the next release.

## Unreleased

### Added

- Links to this changelog and the commit history.
- English commit message guidance and documentation of AI-assisted contributions.

### Changed

- Simplified both READMEs around the motivation, three-step setup, usage, and output.
- Simplified the README license section and added a brief note about reference and learning use.

## 0.1.0

### Added

- Local audio and video transcription with faster-whisper, including timestamped Markdown and JSON transcripts.
- Douyin video URLs, short share links, and full share text as inputs.
- A bundled AI workflow available through `vidskim skill`: the calling AI reads the complete transcript and prepares the digest using its existing model.
- `vidskim save` to validate transcript references and export a digest as Markdown, including an optional output location.
- `vidskim setup` to prepare the speech recognition model and `vidskim demo` to preview a bundled note.
- Reuse of valid transcripts for repeated inputs, with completed transcripts retained for resuming the AI workflow.
- Chinese and English documentation, local-video and Douyin digest examples, and an MIT license.
- CI checks on Linux, macOS, and Windows.
