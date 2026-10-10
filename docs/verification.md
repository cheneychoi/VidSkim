# 首版实际验证

验证日期：2026-10-10。环境：macOS、本地 faster-whisper `small`、CPU `int8`。精华由调用 CLI 的 AI 模型生成，没有额外摘要 API。

## 抖音分享链接完整流程

| 输入 | 实际时长 | 识别片段 | 全稿读取 | 精华 | 结果 |
|---|---:|---:|---|---:|---|
| [分享短链](https://v.douyin.com/n234HvHgzN0/)，ID `7616660340146752819` | 348.996 秒 | 165 | 0–84、85–164 | 5 条 | 下载、转写、总结、Markdown 保存成功 |
| [公开视频](https://www.douyin.com/video/7611489793444171048) | 23.638 秒 | 13 | 0–12 | 3 条 | 下载、转写、总结、Markdown 保存成功 |

两条样例都通过 CLI 获取真实媒体，校验视频和音轨可解码，再遍历模型的全部识别结果。AI 阅读全稿后写入 `summary.json`，实际执行 `vidskim save`，退出码为 `0`。保存后重新读取 Markdown，确认精华、由真实片段生成的时间戳和原稿链接。

24 秒样例还使用新构建的 wheel，在独立依赖环境和新的处理缓存里重新下载、转写，再用安装包的 `save` 成功保存。该轮使用已经下载的本地 `small` 模型目录。

[查看实际生成的长视频精华](../examples/douyin-digest.md) · [机器可读验证记录](verification.json)

## 下载修复

原有路径从移动分享页的 `_ROUTER_DATA` 取媒体详情。本次实际响应中，分享页有路由信息，却没有 `videoInfoRes`，因此单靠解析 HTML 不能取得视频。

移动端 Feed 入口的思路参考 [media-parser 源码](https://github.com/ucmao/media-parser/blob/main/src/parsers/douyin_parser.py)。VidSkim 使用独立的 HTTPX 实现：优先请求主、备用移动节点，只接受 `aweme_id` 与请求完全相同的作品；未匹配时再回退分享页。当前成功样例没有使用用户 Cookie、登录会话或签名库。

另一个 [公开短链](https://v.douyin.com/mXosMBsOHF0/) 解析到 `7643403242492550139`，但两个移动节点都只返回无关推荐，分享页也缺详情。这种情况明确失败，不会转写推荐视频，也不会用发布描述冒充讲话。未匹配本身不能说明作品已删除或私密。

## 自动化与本地输入

- 119 项自动化测试通过，Ruff 检查通过。包含 ID 匹配、备用节点、分享页回退、权限拒绝、媒体解码、缓存复用、跨盘 Markdown 保存和中文管道输出。
- 已构建 wheel 和源码包，随包 Skill 与 demo 可读取。
- [原创合成口播视频](../examples/sample.mp4) 的 162 秒本地输入也完成真实识别、全稿阅读和 Markdown 保存，[结果在这里](../examples/verified/summary.md)。

GitHub Actions 已配置 Linux、macOS、Windows 及 Python 3.11 / 3.12 检查；[远程 CI 结果](https://github.com/cheneychoi/VidSkim/actions)以实际运行记录为准。公开视频存在识别错字；未测准确率或性能基准。本次结果证明这些具体样例的流程可用，不代表全部链接和环境都可用。

## 复现

在项目目录把下面的请求交给能执行命令、读写本地文件的 AI 工具：

```text
先运行 uv run vidskim skill，按流程处理：
https://v.douyin.com/n234HvHgzN0/
完整读取全部转写稿，用你当前的模型整理精华，调用 save 保存 Markdown。
```

同一输入的有效缓存会被复用。首次执行需要下载本地模型，公开视频是否仍可访问取决于平台当时返回的数据。
