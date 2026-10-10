<h1 align="center">VidSkim</h1>

<p align="center"><b>Long video. Short read.</b></p>

<p align="center">
  <a href="README.md">简体中文</a> | <strong>English</strong>
</p>

## Why VidSkim?

You save an interview or a useful talk to watch later. Later rarely comes. When you want to find one idea again, you're back to scrubbing through the video. The saved list keeps growing, but little of it makes its way into your notes.

VidSkim makes that easier: give your existing AI a video link or a local file. It reads the content, removes repetition and filler, and keeps the ideas, reasoning, and useful examples. Read the digest in a few minutes, then use timestamps to revisit anything that interests you.

The result is Markdown you can keep in Obsidian or any notes folder. Find it again when you need it, or hand it to your AI to explore further. **Turn “watch later” into something you can read now.**

## Quick start

> **Requirements:** macOS, Linux, or Windows; [uv](https://docs.astral.sh/uv/getting-started/installation/) and [Git](https://git-scm.com/downloads); and an AI tool that can run local commands and read/write files, such as Codex or Claude Code.

### Step 1: Install

```bash
uv tool install --python 3.12 "git+https://github.com/cheneychoi/VidSkim.git"
vidskim setup
```

`uv` prepares Python if needed. `setup` downloads the speech recognition model on first use. Transcription then runs locally, with no GPU required.

### Step 2: Give your AI a video

Paste this into your AI tool, replacing the link with the video you want to read:

```text
Run vidskim skill and follow its workflow for this video:
https://v.douyin.com/n234HvHgzN0/

Read the entire transcript, write a digest I can read in a few minutes,
and save it as Markdown. Tell me the saved file path.
```

You can also use a local file path, such as `./video.mp4` or `./interview.mp3`, or paste the full Douyin share text.

### Step 3: Open your notes

Your AI returns the saved file path. By default, the digest is at `digests/video-title-ID/summary.md`, alongside timestamped transcripts. To use your own notes folder, add “Save it to `./notes/video.md`” to your request.

The bundled workflow defaults to Chinese. You can ask your AI for an English digest; exported section headings are currently Chinese.

## Usage

Usually, you just give your AI the task. It reads the instructions through `vidskim skill` and uses these commands:

```bash
vidskim skill                              # Read the AI workflow
vidskim ./video.mp4                         # Transcribe local audio or video
vidskim "https://v.douyin.com/n234HvHgzN0/"  # Transcribe Douyin; full share text also works
vidskim demo                               # Preview a bundled note
vidskim --help                             # Show command help
```

After transcription, your AI reads the transcript, writes `summary.json`, and runs this in the video's output folder:

```bash
vidskim save transcript.json --from summary.json
```

Append `-o ./notes/video.md` to choose where to save the digest. See the [user guide](docs/usage.en.md) for all options and file formats.

## Output

Each video gets a folder containing the digest and its source transcripts:

```text
digests/video-title-ID/
├── summary.md         # The digest you read
├── summary.json       # Content prepared by your AI
├── transcript.md      # Timestamped transcript
└── transcript.json    # Transcript for your AI to read
```

Each digest contains **a one-sentence overview, key takeaways, and a concise narrative**. Takeaways include timestamps from the transcript so you can revisit the source. This excerpt is translated from an actual output:

> **In one sentence**
>
> The video argues that broader access to AI does not necessarily close the gap between people: domain knowledge, specific questions, and the ability to evaluate results all shape its value.

Read the full examples: [Douyin digest](examples/douyin-digest.md) · [Local video digest](examples/verified/summary.md). Both are in Chinese.

## How it works

1. VidSkim reads a local file or fetches a video from a Douyin share link.
2. faster-whisper transcribes the audio locally into a complete timestamped transcript.
3. Your AI reads the entire transcript and writes the ideas, reasoning, and useful examples to `summary.json`.
4. `vidskim save` checks the referenced transcript segments and exports Markdown.

**No separate summary API key is needed.** Summarization uses your existing AI tool, model, and account limits. VidSkim processes audio; it does not read charts or text that appear only on screen.

## Configuration

The defaults work out of the box. To adjust them, set these environment variables:

| Variable | Purpose | Default |
|----------|---------|---------|
| `VIDSKIM_ASR_MODEL` | Speech recognition model | `small` |
| `VIDSKIM_LANGUAGE` | Transcription language, such as `zh` | Auto-detect |
| `VIDSKIM_CACHE_DIR` | Processing cache directory | `~/.cache/vidskim` |

## FAQ

| Question | Answer |
|----------|--------|
| Why is the first run slow? | It needs to download the speech model. Transcription time depends on video length and your hardware. |
| Why does a Douyin link fail? | Video availability and platform changes can affect extraction. If you have a local audio/video file, process that instead. |
| Why did I get a transcript but no digest? | The transcription command only creates transcripts. Ask your AI to follow `vidskim skill` to summarize and save. |
| Do I need to start over after an interruption? | Completed transcripts remain available. Ask your AI to continue from them. A valid transcription cache is also reused for the same input and settings. |

## Contributing

[Feedback](https://github.com/cheneychoi/VidSkim/issues) and [contributions](CONTRIBUTING.md#english) are welcome. [Changelog](CHANGELOG.md) · [Commit history](https://github.com/cheneychoi/VidSkim/commits/main/).

Thanks to [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for local speech recognition and [media-parser](https://github.com/ucmao/media-parser) for the Douyin mobile Feed entry point reference.

## License

[MIT](LICENSE)

This project is intended for reference and learning.
