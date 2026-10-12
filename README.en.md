<h1 align="center">Watch2Note</h1>

<p align="center"><b>Keep the ideas. Take your thinking further.</b></p>

<p align="center">
  <a href="README.md">简体中文</a> | <strong>English</strong>
</p>

Watch2Note (视频拾记) is a **video digest Skill for Codex and Claude Code**. Give it a Douyin link or a local audio/video file, and let your AI turn the ideas, reasoning, and examples into a readable Markdown note. No separate summary API key is needed.

## All those saved videos. Did you ever watch them?

An interview, a useful talk, an idea that made you pause. You save it for later, but never quite find the time. When you need the content again, you're back to scrubbing through the video.

Watch2Note helps you keep the content first. It removes repetition and filler while preserving the reasoning and examples behind each idea, giving you a digest you can read in a few minutes. Use timestamps to revisit anything that interests you, and keep the ideas worth remembering in your notes.

**From someone else's perspective to your own understanding.** With a note you can revisit, check, and add to, you can connect new ideas to what you already know and follow the questions they raise.

## Quick start

**Give it a link. Keep the ideas.** Set it up once, then invoke it in your AI chat.

> **Requirements:** macOS, Linux, or Windows; [uv](https://docs.astral.sh/uv/getting-started/installation/) and [Git](https://git-scm.com/downloads); and an AI tool that can run local commands and read/write files, such as Codex or Claude Code.

### Step 1: Install Watch2Note

Run in your terminal:

```bash
uv tool install --python 3.12 "git+https://github.com/cheneychoi/Watch2Note.git"
```

`uv` prepares Python if needed. After installation, connect Watch2Note to your AI tool in the next step.

### Step 2: Connect your AI tool

Run the matching command in your terminal to install the Skill and prepare the speech recognition model:

```bash
watch2note setup --codex    # Codex
watch2note setup --claude   # Claude Code
```

The speech model downloads on first use. Once setup finishes, it shows how to invoke the Skill. The model then runs locally, with no GPU required. If the Skill does not appear, start a new session or restart your AI tool.

### Step 3: Enter the Skill and a video link

In the **Codex chat input**, type `$`, choose `watch2note`, and add the link:

```text
$watch2note https://v.douyin.com/n234HvHgzN0/
```

In the **Claude Code chat input**, enter:

```text
/watch2note https://v.douyin.com/n234HvHgzN0/
```

Enter these requests in your AI chat, not in your terminal. You can replace the link with a local file path, such as `./video.mp4` or `./interview.mp3`, or the full Douyin share text.

Your AI handles **fetching the video → transcribing → summarizing → saving the note**, then returns a link to the Markdown file. To use your own notes folder, add “Save it to `./notes/video.md`” after the video link.

The bundled workflow defaults to Chinese. You can ask your AI for an English digest; exported section headings are currently Chinese.

See the [advanced guide](docs/usage.en.md) for upgrades, missing commands, and other AI tools.

## What you get

**Ideas, reasoning, and examples in one readable note.** Each digest contains a one-sentence overview, key takeaways, and a concise narrative, keeping the context you need to understand an idea.

The following excerpt is translated from [an actual Douyin video note](examples/douyin-digest.md):

> **In one sentence**
>
> The video argues that broader access to AI does not necessarily close the gap between people: domain knowledge, specific questions, and the ability to evaluate results all shape its value.
>
> **Key takeaway · 01:31, 01:42**
>
> People can use the same AI in very different ways. The video contrasts a beginner who gives broad prompts and keeps generating images with a visual director who supplies specific professional requirements, selects a result, and develops it further. The example illustrates how expertise still shapes the outcome.

**Want to go deeper? Revisit the source at its timestamp.** Key takeaways carry timestamps from the transcript, and the complete transcript is retained for checking. More examples: [local video digest](examples/verified/summary.md) · [timestamped transcript](examples/verified/transcript.md). The examples are in Chinese.

**Keep the ideas worth remembering.** Notes are saved as Markdown for Obsidian or any notes folder. The default location is `digests/video-title-ID/summary.md`; you can also request a specific destination.

Speech recognition runs locally. Summarization uses your existing AI tool, model, and account limits. Watch2Note processes audio; it does not read charts or text that appear only on screen.

## Where the note takes you next

After reading that note, you can open related notes you already have and add your own connections and questions. For example, you might continue a note titled “How I ask AI for help” with:

> **Personal reflection example · for you to develop**
>
> **What I already noticed:** The more specific my request, the more useful the AI's answer tends to be.
>
> **What this adds:** Describing the task is only part of it. I also need to know how to judge whether an answer is useful.
>
> **What I want to explore:** Which judgments in my work depend most on experience? What criteria could I write down before my next request?

Watch2Note provides a note you can check against the transcript. You build on it with your own knowledge and experience, and can discuss those connections and questions with your existing AI.

**Connect them to what you know. Make sense of them for yourself.**

**Follow the new questions. Keep thinking.**

**Watch2Note · Keep the ideas. Take your thinking further.**

## FAQ

| Question | Answer |
|----------|--------|
| Why is the first run slow? | It needs to download the speech model. Transcription time depends on video length and your hardware. |
| Can I see progress? | Link resolution, downloading, model loading, and transcription are reported separately, followed by AI summarization and saving. Audio position and elapsed time are shown separately; chat update frequency also depends on your AI client. |
| Why does a Douyin link fail? | Video availability and platform changes can affect extraction. If you have a local audio/video file, process that instead. |
| Why did I get a transcript but no digest? | The transcription command only creates transcripts. Invoke the Watch2Note Skill in your AI tool, or ask it to summarize and save an existing transcript. |
| Do I need to start over after an interruption? | Completed transcripts remain available. Ask your AI to continue from them. A valid transcription cache is also reused for the same input and settings. |

## Advanced usage

Watch2Note retains a CLI for the Skill to call and for direct use in terminals or scripts. See the [advanced CLI guide](docs/usage.en.md) for all commands, Markdown export, model settings, and caching. For everyday use, invoke the Skill in your AI tool.

## Contributing

[Feedback](https://github.com/cheneychoi/Watch2Note/issues) and [contributions](CONTRIBUTING.md#english) are welcome. [Changelog](CHANGELOG.md) · [Commit history](https://github.com/cheneychoi/Watch2Note/commits/main/).

Thanks to [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for local speech recognition and [media-parser](https://github.com/ucmao/media-parser) for the Douyin mobile Feed entry point reference.

## License

[MIT](LICENSE)

This project is intended for reference and learning.
