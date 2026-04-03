# 网页阅读

通用网页、微信公众号、RSS。

## 通用网页 (Jina Reader) — 默认

```bash
# 读取任意网页内容
curl -s "https://r.jina.ai/URL"

# 示例
curl -s "https://r.jina.ai/https://example.com/article"
```

**适用场景**: 大多数网页可以直接用 Jina Reader 读取。

## 反爬模式 (Scrapling StealthyFetcher)

用于 Cloudflare 保护或主动拦截机器人的网站。

### Python API

```python
from agent_reach.channels.web import WebChannel

ch = WebChannel()

# 方法1: 使用 stealth 参数
content = ch.read("https://protected-site.com", stealth=True)

# 方法2: 使用便捷方法
content = ch.read_stealth("https://protected-site.com")
```

### CLI 检测

```bash
# 检查 stealth 模式是否可用
agent-reach doctor
# 查看 "网页 (反爬)" 和 "网页 (浏览器)" 状态
```

**适用场景**:
- Cloudflare 保护的网站
- 返回 403/验证码的页面
- UAE 政府门户（自动触发）

## 自动回退策略

WebChannel 采用四级回退：

1. **Tier 1**: Jina Reader（最快，无浏览器）
2. **Tier 2**: Scrapling Fetcher（伪装 headers）
3. **Tier 3**: StealthyFetcher（Camoufox，Cloudflare 绕过）
4. **Tier 4**: Lightpanda CDP（最快浏览器，可选）

如果 Jina Reader 失败，会自动尝试后续方案，无需手动干预。

## Lightpanda 浏览器（服务器/VPS 推荐）

Lightpanda 是一个开源 headless 浏览器（Zig 编写），比 Chrome 快 11 倍，内存占用少 9 倍。

### 自动启动

如果 Docker 可用，`agent-reach install` 会自动启动 Lightpanda 容器：

```bash
# 容器配置
镜像：lightpanda/browser:nightly
CDP 端口：9222
遥测：默认禁用（隐私保护）
```

### 手动启动

```bash
docker run -d --name lightpanda -p 9222:9222 -e LIGHTPANDA_DISABLE_TELEMETRY=true lightpanda/browser:nightly
```

### 环境变量

```bash
# 自定义 Lightpanda 地址（默认: ws://localhost:9222）
export LIGHTPANDA_URL=ws://localhost:9222

# 禁用遥测（默认: true）
export LIGHTPANDA_DISABLE_TELEMETRY=true
```

### 注意事项

- Lightpanda 在 Termux/ARM Android 上不可用，自动使用 Camoufox 回退
- 端口 9222 仅内部使用，不对外暴露
- 仍处于 beta 阶段（~95% 兼容性）
- 如果 Lightpanda 连接失败，自动回退到 StealthyFetcher

## 特殊站点：UAE 政府门户

以下站点**自动使用 stealth 模式**（无需手动指定）：

| 站点 | 域名 | 说明 |
|-----|------|------|
| MOHRE | mohre.gov.ae | 阿联酋人力资源部 |
| FTA | tax.gov.ae | 联邦税务局 |
| DED | ded.ae, dubaided.gov.ae | 迪拜经济发展部 |
| ADCB | adbc.gov.ae | 阿布扎比商业中心 |

```python
# 这些 URL 会自动触发 stealth 模式
ch.read("https://www.mohre.gov.ae")  # 自动 stealth
```

## Web Reader (MCP)

```bash
# 读取网页内容 (Markdown 格式)
mcporter call 'web-reader.webReader(url: "https://example.com")'

# 保留图片
mcporter call 'web-reader.webReader(url: "https://example.com", retain_images: true)'

# 纯文本格式
mcporter call 'web-reader.webReader(url: "https://example.com", return_format: "text")'
```

**适用场景**: 需要更精确控制输出格式时使用。

## 微信公众号 / WeChat Articles

### 搜索公众号文章（通过 Exa）

```bash
# 搜索微信公众号文章
mcporter call 'exa.web_search_exa(query: "搜索关键词", numResults: 5, includeDomains: ["mp.weixin.qq.com"])'
```

### 阅读公众号文章全文（通过 Exa）

```bash
# 抓取文章全文
mcporter call 'exa.crawling_exa(urls: ["https://mp.weixin.qq.com/s/ARTICLE_ID"], maxCharacters: 10000)'
```

### 可选：Camoufox 阅读（反爬更强）

```bash
cd ~/.agent-reach/tools/wechat-article-for-ai && python3 main.py "https://mp.weixin.qq.com/s/ARTICLE_ID"
```

> **注意**: Jina Reader 无法读取微信文章（被 CAPTCHA 拦截），推荐用 Exa。

## RSS (feedparser)

```python
python3 -c "
import feedparser
for e in feedparser.parse('FEED_URL').entries[:5]:
    print(f'{e.title} — {e.link}')
"
```

**适用场景**: 订阅博客、新闻源、播客等 RSS feed。

## 选择指南

| 场景 | 推荐工具 |
|-----|---------|
| 通用网页 | Jina Reader (`curl r.jina.ai`) |
| Cloudflare/反爬 | Scrapling StealthyFetcher (`stealth=True`) |
| 需要图片/格式控制 | web-reader MCP |
| 微信公众号 | Exa (搜索+阅读) / Camoufox (可选阅读) |
| RSS 订阅 | feedparser |
| 微博/知乎等 | Jina Reader |
| UAE 政府门户 | 自动 stealth 模式 |
