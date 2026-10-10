# Usage guide

[简体中文](usage.md) · **English** · [Back to README](../README.en.md)

See the [README quick start](../README.en.md) for installation. VidSkim fetches media, transcribes speech locally, and saves Markdown. The AI tool you already use writes the digest.

## Commands

```bash
vidskim setup                          # Download and prepare the speech model
vidskim skill                          # Print the complete AI workflow
vidskim demo                           # Preview a bundled example
vidskim ./video.mp4
vidskim ./interview.mp3
vidskim "https://v.douyin.com/n234HvHgzN0/"
vidskim "Paste the complete Douyin share text including its URL here"
vidskim --help
vidskim --version
```

`setup` runs without prompts; the first model download may take a few minutes. `demo` shows prewritten content without live transcription. `skill` provides instructions for your AI to read; it does not change or install itself into your AI tool's configuration.

Transcription prints a JSON manifest to stdout and progress to stderr. The manifest includes the source, duration, segment count, and these absolute paths:

| Field | Content |
| --- | --- |
| `transcript_json` | The complete transcript for your AI to read |
| `transcript_md` | The transcript as Markdown with timestamps |
| `summary_output` | Suggested digest path; transcription does not create this file |

Always use the actual paths in the manifest; titles and directory names vary.

## Summarize and save with your AI

Your AI tool needs local command execution, file reading, and file writing. Ask it to run `vidskim skill` before processing a file or share link.

1. Run `vidskim INPUT` and read `transcript_json`. Each segment has `id`, `start`, `end`, and `text`.
2. Read every segment. Read long transcripts in consecutive ID chunks before synthesizing; do not summarize only the opening or a truncated tool response.
3. Write `summary.json` alongside the transcript. Keep key ideas, reasoning, necessary examples, and conditions; remove ads, repetition, and filler.
4. Run `vidskim save` and use the returned `summary_md` path.

Summary JSON format:

```json
{
  "overview": "The most important idea in one sentence.",
  "points": [
    {"text": "A key idea and its explanation.", "segment_ids": [0, 1]},
    {"text": "Another key idea.", "segment_ids": [2]}
  ],
  "body": "A readable narrative connecting the ideas, reasoning, and examples."
}
```

`overview`, `body`, and each `text` must be nonempty strings. `points` accepts 1–5 entries. Each `segment_ids` must be a nonempty array of integers referring to existing IDs in the input transcript. The IDs above only illustrate the format.

```bash
vidskim save ./digests/video-title-ID/transcript.json --from ./digests/video-title-ID/summary.json
vidskim save ./digests/video-title-ID/transcript.json --from ./digests/video-title-ID/summary.json -o ./notes/focus.md
```

`-o` is only available for `save`; its target must be a `.md` file. Without it, the digest is saved as `summary.md` beside the input `transcript.json`. The command protects the input media, transcript, and summary JSON from being overwritten.

Timestamps come from referenced segments rather than AI guesses. Reference validation confirms that segments exist; it does not establish that the digest is accurate. Transcription errors may affect the digest, so check the transcript when needed.

From a source checkout, try saving the [example summary](../examples/summary.json) with its [matching transcript](../examples/transcript.json):

```bash
vidskim save ./examples/transcript.json --from ./examples/summary.json -o ./example-digest.md
```

## Files and recovery

Default output is written under your current working directory:

```text
digests/
└── video-title-ID/
    ├── transcript.json
    ├── transcript.md
    ├── summary.json     # Written by your AI
    └── summary.md       # Written by save
```

`save -o` only changes the digest location; transcripts stay where they were generated. The digest links to `transcript.md` beside the input JSON, or to `transcript.json` if the Markdown is missing. Links are usually relative; saving across drives on Windows uses an absolute file link. Keep the transcript and check the link if you move files later.

If summarization is interrupted, completed transcripts remain usable. Ask your AI to read the existing transcript, finish `summary.json`, and run `save` without transcribing again. Repeating transcription with the same input and speech settings reuses a valid cache.

Processing caches are pruned to 7 days and at most 20 items when an input is processed; speech model downloads are managed separately. For long-term storage, keep the files in `digests` or your chosen Markdown location.

If Douyin extraction fails, pass an available local audio or video file to the same command.

## Model and settings

The default faster-whisper model is `small`, running on CPU with `int8` computation; CUDA is not required. PyAV decodes audio, so a separate FFmpeg installation is generally unnecessary.

| Environment variable | Purpose |
| --- | --- |
| `VIDSKIM_ASR_MODEL` | Speech recognition model; default: `small` |
| `VIDSKIM_LANGUAGE` | Speech language, e.g. `zh`; automatically detected when unset |
| `VIDSKIM_CACHE_DIR` | Processing cache directory; default: `~/.cache/vidskim` |

VidSkim does not configure or call a summary API. Your AI tool uses its existing model and account limits, and handles the transcript according to its own settings.

The current Skill defaults to Chinese digests, and fixed Markdown headings are also Chinese. Request English prose explicitly from your AI if needed. `VIDSKIM_LANGUAGE` controls speech recognition, not the digest language.

## Scope

VidSkim works best with spoken content such as interviews, explanations, and experience sharing. It does not read information that appears only in images, charts, or screen recordings. Douyin extraction depends on video availability and platform behavior.

See the [verification record](verification.md) for examples and reproducible results, and [Contributing](../CONTRIBUTING.md) for development and feedback.
