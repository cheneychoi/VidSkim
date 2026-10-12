# Advanced CLI guide

[简体中文](usage.md) · **English** · [Back to README](../README.en.md)

For everyday use, follow the [README installation and usage steps](../README.en.md) to set up the Skill, then send a link in your AI chat. This guide covers running commands directly, reading transcription output, choosing output locations, and connecting other AI tools.

The Watch2Note CLI fetches media, transcribes speech locally, and saves files. The Skill guides your existing AI through reading the complete transcript, writing a digest, and calling the CLI to save Markdown.

> This guide describes the current Watch2Note source version. The historical `v0.1.0` tag and older packages use the name VidSkim and include neither the new name nor the Skill installation options. Install from GitHub source as shown in the README.

## CLI commands

Run these commands in your system terminal. `watch2note INPUT` transcribes media; your AI writes the digest. `save` renders an existing summary JSON as Markdown without calling a model to summarize it.

```bash
watch2note setup                          # Download and prepare the speech model
watch2note setup --codex                  # Also install the Codex Skill
watch2note setup --claude                 # Also install the Claude Code Skill
watch2note skill                          # Print the complete AI workflow
watch2note demo                           # Preview a bundled example
watch2note ./video.mp4
watch2note ./interview.mp3
watch2note "https://v.douyin.com/n234HvHgzN0/"
watch2note "Paste the complete Douyin share text including its URL here"
watch2note --help
watch2note setup --help
watch2note save --help
watch2note --version
```

`setup` runs without prompts; the first model download may take a few minutes. `demo` shows prewritten content without live transcription. `skill` only prints the workflow; use `setup --codex` or `setup --claude` to install it.

### Transcription output

Transcription prints a JSON manifest to stdout and progress to stderr. The manifest includes the source, duration, segment count, and these absolute paths:

| Field | Content |
| --- | --- |
| `transcript_json` | The complete transcript for your AI to read |
| `transcript_md` | The transcript as Markdown with timestamps |
| `summary_output` | Suggested digest path; transcription does not create this file |

Always use the actual paths in the manifest; titles and directory names vary. To consume the result in a script, capture stdout while progress remains visible in your terminal:

```bash
watch2note "https://v.douyin.com/n234HvHgzN0/" > manifest.json
```

Exit codes are `0` for success, `1` for a processing failure, `2` for invalid command arguments, and `130` for cancellation. On failure, check stderr and do not treat incomplete output as a successful result.

## Understanding progress

Fetching a video and recognizing speech are separate steps. A successful download means the media is ready; Watch2Note still needs to decode audio, load the model, and recognize speech before text is available.

The CLI reports link resolution, downloading, model loading, and transcription separately. Transcription distinguishes the position in the audio from elapsed time: `02:00 / 05:49` means it has reached the two-minute point in a 5-minute-49-second recording. It does not mean two minutes have elapsed or remain. Once the transcript is ready, your AI reports summarization and saving.

The default `small` model runs on a CPU, so a video a few minutes long may also take several minutes to transcribe, depending on the device, audio, and settings. Progress updates do not make the model itself faster. Some AI clients buffer command output, so the frequency of updates in chat also depends on the client.

## Summary JSON and Markdown output

Invoking the installed Skill guides your AI through the steps below. For other AI tools, ask your AI to run `watch2note skill` first to read the workflow.

1. Run `watch2note INPUT` and read `transcript_json`. Each segment has `id`, `start`, `end`, and `text`.
2. Read every segment. Read long transcripts in consecutive ID chunks before synthesizing; do not summarize only the opening or a truncated tool response.
3. Write `summary.json` alongside the transcript. Keep key ideas, reasoning, necessary examples, and conditions; remove ads, repetition, and filler.
4. Run `watch2note save` and use the returned `summary_md` path.

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
watch2note save ./digests/video-title-ID/transcript.json --from ./digests/video-title-ID/summary.json
watch2note save ./digests/video-title-ID/transcript.json --from ./digests/video-title-ID/summary.json -o ./notes/focus.md
```

`-o` is only available for `save`; its target must be a `.md` file. Without it, the digest is saved as `summary.md` beside the input `transcript.json`. The command protects the input media, transcript, and summary JSON from being overwritten; an existing Markdown file at any other output path is replaced. On success, stdout contains `{"summary_md": "absolute path to the saved file"}`.

Timestamps come from referenced segments rather than AI guesses. Reference validation confirms that segments exist; it does not establish that the digest is accurate. Transcription errors may affect the digest, so check the transcript when needed.

From a source checkout, try saving the [example summary](../examples/summary.json) with its [matching transcript](../examples/transcript.json):

```bash
watch2note save ./examples/transcript.json --from ./examples/summary.json -o ./example-digest.md
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

Complete cached models load directly from disk. Downloads are needed only when the cache is missing or incomplete, avoiding network waits during startup.

| Environment variable | Purpose |
| --- | --- |
| `WATCH2NOTE_ASR_MODEL` | Speech model name or local model directory; default: `small` |
| `WATCH2NOTE_LANGUAGE` | Speech language, e.g. `zh`; automatically detected when unset |
| `WATCH2NOTE_CACHE_DIR` | Root directory for processing caches and speech models; default: `~/.cache/watch2note` |

Watch2Note does not configure or call a summary API. Your AI tool uses its existing model and account limits, and handles the transcript according to its own settings.

The current Skill defaults to Chinese digests, and fixed Markdown headings are also Chinese. Request English prose explicitly from your AI if needed. `WATCH2NOTE_LANGUAGE` controls speech recognition, not the digest language.

## Skill installation, upgrades, and compatibility

In your terminal, install the Skill for your AI tool and prepare the speech model:

```bash
watch2note setup --codex
# Or
watch2note setup --claude
```

If you use both tools, run `watch2note setup --codex --claude`. Running `watch2note setup` alone still only prepares the speech model; it does not install a Skill.

Running the matching `setup` command again updates a Skill installed by Watch2Note if you have not edited it. If the destination has a custom or manually edited `SKILL.md` with different content, or the Skill directory or file is a symbolic link, installation stops and reports the conflicting path; move that directory elsewhere before trying again.

| AI tool | Skill location | Enter in the AI chat input |
| --- | --- | --- |
| Codex | `~/.agents/skills/watch2note/SKILL.md` | `$watch2note https://v.douyin.com/n234HvHgzN0/` |
| Claude Code | `~/.claude/skills/watch2note/SKILL.md` | `/watch2note https://v.douyin.com/n234HvHgzN0/` |

In Codex, type `$` and select `watch2note`; the Codex CLI and IDE extension also offer `/skills`. In Claude Code, type `/watch2note`. These invocations belong in the **AI chat input**, not your system terminal. If Watch2Note does not appear after installation, start a new session or restart the client. See the [Codex Skills documentation](https://learn.chatgpt.com/docs/build-skills) and [Claude Code Skills documentation](https://code.claude.com/docs/en/skills) for the underlying conventions.

This workflow requires a local Codex session or Claude Code with local command and file access. Claude web chat does not read Skills installed on your computer. Command execution remains subject to your AI client's permissions.

Add preferences after the link, such as “Save to `./notes/ai.md`” or “Summarize in English.” Local file paths and full Douyin share text also work. Your AI follows the Skill to transcribe, read every segment, summarize, save, and return the file path.

### Command not found

If your terminal cannot find `watch2note` after installation, run `uv tool update-shell`, then open a new terminal. Restart any AI clients that were already open so they can read the updated command path.

### Migrate from VidSkim or update

Watch2Note is the new name for VidSkim. Its Python package, CLI, and Skill all use `watch2note`.

**Before running `setup`**, if you configured `VIDSKIM_*` environment variables, rename them to the corresponding `WATCH2NOTE_*` variables. The default cache is now `~/.cache/watch2note`. To reuse cached models, first set `WATCH2NOTE_CACHE_DIR` to the absolute path of your previous cache directory (by default, `.cache/vidskim` under your home directory). Existing caches are not moved or deleted automatically.

In your terminal, install the current source and run `setup` for your AI tool:

```bash
uv tool install --reinstall --python 3.12 "git+https://github.com/cheneychoi/Watch2Note.git"
watch2note setup --codex
# For Claude Code, use watch2note setup --claude instead
```

Start a new AI session and use `$watch2note` or `/watch2note`. Existing transcripts and Markdown notes remain usable; they do not need to be transcribed again.

Once the new command and Skill work, you may run `uv tool uninstall vidskim` to remove the old CLI. Old Skills are also left in place: check `~/.agents/skills/vidskim` or `~/.claude/skills/vidskim` for custom changes, keep a backup if needed, and move them out of your client's Skill directory yourself.

### Use another AI tool

For an AI tool that can run local commands but does not support Skill installation, use this request to load the same workflow:

```text
Run watch2note skill and follow its workflow for this video:
https://v.douyin.com/n234HvHgzN0/
Read the entire transcript, write a digest, save it as Markdown,
and tell me the file path.
```

## Scope

Watch2Note works best with spoken content such as interviews, explanations, and experience sharing. It does not read information that appears only in images, charts, or screen recordings. Douyin extraction depends on video availability and platform behavior.

See the [verification record](verification.md) for examples and reproducible results, and [Contributing](../CONTRIBUTING.md) for development and feedback.
