---
name: agent-reach
description: >
  Give your AI agent eyes to see the entire internet.
  17 platforms via CLI, MCP, curl, and Python scripts.
  Zero config for 8 channels.

  【路由方式】SKILL.md 包含路由表和常用命令，复杂场景需按需阅读对应分类的 references/*.md。
  分类：search / social (小红书/抖音/微博/推特/B站/V2EX/Reddit) / career(LinkedIn) / dev(github) / web(网页/文章/公众号/RSS) / video(YouTube/B站/播客).

  Use when user asks to search, read, or interact on any supported platform,
  shares a URL, or asks to search the web.
triggers:
  - search: 搜/查/找/search/搜索/查一下/帮我搜
  - social:
    - 小红书: xiaohongshu/xhs/小红书/红书
    - 抖音: douyin/抖音
    - Twitter: twitter/推特/x.com/推文
    - 微博: weibo/微博
    - B站: bilibili/b站/哔哩哔哩
    - V2EX: v2ex
    - Reddit: reddit
  - career: 招聘/职位/求职/linkedin/领英/找工作
  - dev: github/代码/仓库/gh/issue/pr/分支/commit
  - web: 网页/链接/文章/公众号/微信文章/rss/读一下/打开这个
  - video: youtube/视频/播客/字幕/小宇宙/转录/yt
  - finance: 雪球/股票/stock/xueqiu/行情/基金
metadata:
  openclaw:
    homepage: https://github.com/Panniantong/Agent-Reach
---

# Agent Reach — 路由器

17 平台工具集合。根据用户意图选择对应分类。

## 路由表

| 用户意图 | 分类 | 详细文档 |
|---------|------|---------|
| 网页搜索/代码搜索 | search | [references/search.md](references/search.md) |
| 小红书/抖音/微博/推特/B站/V2EX/Reddit | social | [references/social.md](references/social.md) |
| 招聘/职位/LinkedIn | career | [references/career.md](references/career.md) |
| GitHub/代码 | dev | [references/dev.md](references/dev.md) |
| 网页/文章/公众号/RSS | web | [references/web.md](references/web.md) |
| YouTube/B站/播客字幕 | video | [references/video.md](references/video.md) |

## 零配置快速命令

```bash
# Exa 网页搜索
mcporter call 'exa.web_search_exa(query: "query", numResults: 5)'

# 通用网页阅读（默认 Jina Reader）
curl -s "https://r.jina.ai/URL"

# GitHub 搜索
gh search repos "query" --sort stars --limit 10

# Twitter 搜索
twitter search "query" --limit 10

# YouTube/B站字幕
yt-dlp --write-sub --skip-download -o "/tmp/%(id)s" "URL"

# Reddit 搜索
rdt search "query" --limit 10

# Reddit 读帖 + 评论
rdt read POST_ID

# V2EX 热门
curl -s "https://www.v2ex.com/api/topics/hot.json" -H "User-Agent: agent-reach/1.0"
```

## 网页阅读策略

### 默认模式（Jina Reader）

大多数网页直接使用 Jina Reader（免费、无需配置）：

```bash
curl -s "https://r.jina.ai/https://example.com/article"
```

### 反爬模式（Stealth）

对于 Cloudflare 保护或主动拦截机器人的网站，使用 Scrapling StealthyFetcher：

```python
from agent_reach.channels.web import WebChannel

ch = WebChannel()
# 强制使用 stealth 模式
content = ch.read("https://protected-site.com", stealth=True)
# 或使用便捷方法
content = ch.read_stealth("https://protected-site.com")
```

### 自动回退

如果 Jina Reader 失败，会自动尝试 Scrapling Fetcher，最后尝试 StealthyFetcher。

### Lightpanda 浏览器（服务器/VPS 推荐）

Lightpanda 是一个开源 headless 浏览器（Zig 编写），比 Chrome 快 11 倍，内存占用少 9 倍。

**自动启动**：如果 Docker 可用，`agent-reach install` 会自动启动 Lightpanda 容器：
- 镜像：`lightpanda/browser:nightly`
- CDP 端口：`9222`
- 遥测：默认禁用（隐私保护）

**注意**：
- Lightpanda 在 Termux/ARM Android 上不可用，自动使用 Camoufox 回退
- 端口 9222 仅内部使用，不对外暴露
- 仍处于 beta 阶段（~95% 兼容性）

### 特殊站点：UAE 政府门户

以下站点总是自动使用 stealth 模式（无需手动指定）：
- MOHRE (mohre.gov.ae) — 阿联酋人力资源部
- FTA (tax.gov.ae) — 联邦税务局
- DED (ded.ae, dubaided.gov.ae) — 迪拜经济发展部
- ADCB (adbc.gov.ae) — 阿布扎比商业中心

## 环境检查

```bash
# 检查可用 channel
agent-reach doctor

# 查看所有 MCP 服务
mcporter_list_servers()
```

## 工作区规则

**不要在 agent workspace 创建文件。** 使用 `/tmp/` 存放临时输出，`~/.agent-reach/` 存放持久数据。

## 详细文档

根据用户需求，阅读对应的详细文档：

- [搜索工具](references/search.md) — Exa AI 搜索
- [社交媒体](references/social.md) — 小红书, 抖音, Twitter, B站, V2EX, Reddit
- [职场招聘](references/career.md) — LinkedIn
- [开发工具](references/dev.md) — GitHub CLI
- [网页阅读](references/web.md) — Jina Reader, 微信公众号, RSS
- [视频播客](references/video.md) — YouTube, B站, 小宇宙

## 配置渠道

如果某个 channel 需要配置，获取安装指南：
https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md

用户只需提供 cookies，其他配置由 agent 完成。
