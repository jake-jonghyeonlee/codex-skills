# HTML to PDF

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-2.0.0-green.svg)
![Author](https://img.shields.io/badge/author-Dr.CS-orange.svg)
![Claude](https://img.shields.io/badge/Claude-Skill-purple.svg)

<div align="center">

### 高保真 HTML 转 PDF 工具 | HTML to PDF Fidelity Skill

**以浏览器屏幕渲染为第一参照，兼顾截图级保真、文本可选中和正式文档输出**

[快速开始](#快速开始) • [核心特性](#核心特性) • [策略选择](#策略选择) • [质量审计](#质量审计)

</div>

---

## 项目简介

**HTML to PDF** 是一个面向 Claude Code / Claude Skills 的 HTML 转 PDF 工具，专门解决“Chrome 浏览器里看起来很好，导出 PDF 后却变形”的问题。

本 Skill 不再把 HTML 转 PDF 简化为单一路线，而是根据用户目标提供三种策略：

- **屏幕截图级保真**：最大程度还原浏览器渲染后的原始画面。
- **屏幕向量尝试**：尽量接近屏幕布局，同时保留文字可复制能力。
- **print 向量长页**：适合正式报告、文章、长图 PDF 和较小文件体积。

### 核心价值

- **先选择再执行**：调用时默认先给用户 1/2/3 策略建议，确认后再转换。
- **最高视觉还原**：CDP 屏幕模式截图，保留 canvas、WebGL、backdrop-filter、复杂 CSS。
- **长页与演示兼容**：连续网页可生成单页长 PDF，翻页演示可生成一 slide 一页 PDF。
- **文本层保留路线**：在用户需要复制、检索文本时，提供 screen-vector 和 print-vector 两条方案。
- **审计后修复**：已修复 slide-raster 重复截第一页的问题，并通过纵向/横向 slide 像素级验证。

---

## 项目数据

| 维度 | 数据 |
| --- | --- |
| **当前版本** | v2.0.0 |
| **转换策略** | 3 种：slides/long raster、screen vector、print vector |
| **核心脚本** | 2 个：CDP 屏幕保真脚本 + onepage print 长页脚本 |
| **参考文档** | 3 个：CSS 修复、渲染机理、使用示例 |
| **默认交互** | 先给策略选择建议，再按用户选择执行 |
| **截图默认格式** | PNG + DPR 2 |
| **支持页面类型** | 翻页演示、横向 deck、连续长页、报告/文章 |
| **验证覆盖** | 语法检查、纵向 slide、横向 slide、长页 raster、screen-vector |

---

## 核心特性

### 1. 策略选择优先

调用 skill 时，除非用户明确要求“直接执行某策略”，否则必须先给选择建议：

```text
我看这个 HTML 更像【翻页演示/连续长页】。如果目标是尽量还原浏览器里的原始画面，我建议选 1。

1. 屏幕截图级保真（推荐）：最像浏览器画面，保留 canvas/WebGL/backdrop-filter/复杂 CSS；文字不可选中，文件较大。
2. 屏幕向量尝试：文字可选中，使用 screen media 打 PDF；视觉通常接近浏览器，但复杂滤镜/分页仍可能有差异。
3. 打印向量长页：文字可选中、体积较小、适合报告/文章；会进入 print pipeline，不保证和浏览器屏幕完全一致。

请回复 1/2/3 或策略名，我再执行。
```

### 2. 屏幕截图级保真

`render_slides_cdp.py` 使用 Chrome DevTools Protocol 在 **screen mode** 下渲染页面：

- 等待 `document.readyState`、`document.fonts.ready`、图片解码和双 RAF。
- 支持 `--ready-expr` 等待页面自定义导出状态。
- `slides-raster` 会临时隔离当前 slide，避免横向 deck 或 transform deck 重复截第一页。
- `long-raster` 会分块截取长页面，拼成单页连续 PDF。

### 3. 文本可选中路线

当用户强调“文字可复制、可检索、不要截图”时：

- 优先尝试 `screen-vector`：设置 `Emulation.setEmulatedMedia(media="screen")` 后调用 `Page.printToPDF`。
- 如果 screen-vector 视觉差异明显，改用 `onepage_pdf.py` 的 print-vector 长页路线。
- 如果用户最终仍以视觉原样为第一目标，应回到 raster 策略。

### 4. print 长页稳定输出

`onepage_pdf.py` 保留 onepage-pdf 的核心方法：

- 先渲染到超大 bedrock 页面。
- 使用 PyMuPDF 测量真实内容底部。
- 重写 MediaBox/CropBox 裁剪成单页连续 PDF。
- 支持替换脱敏、禁止词泄露检测和 extra CSS 修复。

### 5. 故障定位清晰

Skill 内置常见问题分类：

- 截图策略：DPR、PNG/JPEG、slide selector、lazy image、异步图表。
- screen-vector：PDF backend 与屏幕渲染差异。
- print-vector：741px 打印媒体查询、`vh/vw`、毛玻璃降级、背景丢失。

---

## 策略选择

| 用户目标 | 推荐策略 | 命令策略名 | 文本可选中 | 视觉还原 |
| --- | --- | --- | --- | --- |
| 浏览器原样、最高还原、复杂视觉 | 屏幕截图级保真 | `slides-raster` / `long-raster` | 否 | 最高 |
| 尽量接近屏幕，同时文字可复制 | 屏幕向量尝试 | `screen-vector` | 通常是 | 中高 |
| 正式报告、长页、体积小、文本层 | print 向量长页 | `onepage_pdf.py` | 是 | 中 |

### 选择原则

- 用户说“像浏览器里看到的一样”“高度还原”“原样”：推荐策略 1。
- 用户说“文字可复制”“可搜索”“不要截图”：推荐策略 2。
- 用户说“长图 PDF”“正式报告 PDF”“体积小”：推荐策略 3。
- 用户同时要求“最高还原”和“文字可选中”时，必须说明二者存在取舍，让用户选择。

---

## 核心架构

```text
┌─────────────────────────────────────────────────────────────┐
│                         HTML to PDF                          │
│                           v2.0.0                              │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
      ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
      │ 策略 1     │    │ 策略 2     │    │ 策略 3     │
      │ Screen     │    │ Screen     │    │ Print      │
      │ Raster     │    │ Vector     │    │ Vector     │
      └───────────┘    └───────────┘    └───────────┘
            │                 │                 │
      ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
      │ CDP 截图   │    │ CDP PDF    │    │ Chrome CLI │
      │ slide/long │    │ screen CSS │    │ print CSS  │
      └───────────┘    └───────────┘    └───────────┘
            │                 │                 │
      ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
      │ 最高视觉   │    │ 文本可选   │    │ 长页稳定   │
      │ 不可选字   │    │ 可能差异   │    │ 可选文本   │
      └───────────┘    └───────────┘    └───────────┘
```

### 文件关系

```text
html-to-pdf/
├── SKILL.md                         # Skill 主规则：先推荐策略，再执行
├── README.md                        # 本文件
├── scripts/
│   ├── render_slides_cdp.py          # CDP 屏幕保真与 screen-vector
│   └── onepage_pdf.py                # print-vector 单页长 PDF
└── references/
    ├── css-fixes.md                  # CSS 修复策略
    ├── mechanics.md                  # Chrome/PDF 渲染机理
    └── examples.md                   # 完整命令示例
```

---

## 快速开始

### 安装依赖

```bash
pip install pymupdf websocket-client
```

需要本机安装 Chrome 或 Edge。macOS 默认检测路径：

```text
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
```

### 方式1：翻页演示，最高视觉还原

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/render_slides_cdp.py \
  slides.html \
  -o output/slides.pdf \
  --strategy slides-raster \
  --width 1280 --height 720 \
  --dpr 2 \
  --format png
```

### 方式2：连续长页，浏览器原样长 PDF

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/render_slides_cdp.py \
  report.html \
  -o output/report-screen.pdf \
  --strategy long-raster \
  --width 1280 --height 900 \
  --dpr 2 \
  --format png \
  --tile-height 4096
```

### 方式3：文字可复制，尽量接近屏幕

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/render_slides_cdp.py \
  report.html \
  -o output/report-screen-vector.pdf \
  --strategy screen-vector \
  --width 1280 --height 900
```

### 方式4：正式报告，print 向量长页

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/onepage_pdf.py \
  report.html \
  -o output/report-print-vector.pdf \
  --width 1280
```

---

## 参数说明

### CDP 屏幕保真脚本

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `--strategy` | `slides-raster` | `auto` / `slides-raster` / `long-raster` / `screen-vector` |
| `--width` | 1280 | 浏览器视口宽度 |
| `--height` | 720 | 浏览器视口高度 |
| `--dpr` | 2 | 截图设备像素比；文字细节不够锐时升到 3 |
| `--format` | png | 截图格式；文字/线条多用 PNG，照片多可用 JPEG |
| `--quality` | 92 | JPEG 质量，PNG 忽略 |
| `--selector` | 自动 | 指定 slide 选择器，例如 `.slide` |
| `--ready-expr` | 无 | 页面自定义就绪表达式 |
| `--tile-height` | 4096 | 长页截图分块高度 |

### onepage print 长页脚本

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `--width` | 1280 | 页面设计宽度 px，自动对齐 8px |
| `--bedrock` | 18000 | 初始超大页面高度 |
| `--padding` | 32 | 内容底部留白 px |
| `--crop` | vector | 内容检测方式：vector 或 pixel |
| `--extra-css` | 无 | 注入 print 修复 CSS |
| `--replace` | 无 | 文本替换 JSON，用于脱敏 |
| `--forbid` | 无 | 禁止词检查，防止泄露 |

---

## 使用场景

### 场景1：网页 PPT 导出分享

**需求**：把 scroll-snap 或横向 deck 导出为每页一张 PDF，要求和浏览器显示一致。

**推荐**：

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/render_slides_cdp.py \
  deck.html -o deck.pdf \
  --strategy slides-raster \
  --width 1280 --height 720 \
  --dpr 2 --format png \
  --selector ".slide"
```

### 场景2：长网页生成“长图 PDF”

**需求**：网页报告有复杂背景、毛玻璃、canvas 图表，希望 PDF 看起来和浏览器一致。

**推荐**：

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/render_slides_cdp.py \
  report.html -o report-long.pdf \
  --strategy long-raster \
  --width 1280 --height 900 \
  --dpr 2 --format png
```

### 场景3：法律/财务报告正式归档

**需求**：文字可复制、可检索，文件体积不要太大，视觉允许按 print CSS 微调。

**推荐**：

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/onepage_pdf.py \
  report.html -o report-vector.pdf \
  --width 1280 \
  --extra-css /tmp/onepage-fixes.css
```

### 场景4：异步图表或动画页面

**需求**：页面需要等 ECharts、Three.js、异步数据或自定义渲染完成后再导出。

页面侧设置：

```js
window.__PDF_READY = true;
```

转换时等待：

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/render_slides_cdp.py \
  dashboard.html -o dashboard.pdf \
  --strategy long-raster \
  --ready-expr "window.__PDF_READY === true"
```

---

## 文档导航

| 文档 | 说明 |
| --- | --- |
| [SKILL.md](SKILL.md) | Skill 主入口，包含调用流程和策略选择规则 |
| [render_slides_cdp.py](scripts/render_slides_cdp.py) | CDP 屏幕截图级保真与 screen-vector 实现 |
| [onepage_pdf.py](scripts/onepage_pdf.py) | print-vector 单页长 PDF 实现 |
| [CSS 修复策略](references/css-fixes.md) | print CSS 常见差异和修复方式 |
| [渲染机理](references/mechanics.md) | Chrome print/CDP/PDF 的关键机制 |
| [使用示例](references/examples.md) | 三种策略的完整命令示例 |

---

## 质量审计

### 已完成检查

| 检查项 | 结果 |
| --- | --- |
| Python 语法检查 | 通过 |
| CLI `--help` 参数解析 | 通过 |
| `slides-raster` 纵向 slide | 通过，3 页分别截到红/绿/蓝 |
| `slides-raster` 横向 flex deck | 通过，3 页分别截到红/绿/蓝 |
| `long-raster` 连续长页 | 通过，输出 1 页长 PDF |
| `screen-vector` 向量输出 | 通过，输出 1 页 PDF |
| 文档一致性 | 已同步 SKILL、README、examples、mechanics、css-fixes |

### 审计中修复的问题

1. **slide-raster 重复截第一页**

   原因：CDP screenshot clip 固定在文档坐标 `(0,0)`，滚动或切换 slide 后仍可能截第一页。

   修复：slide-raster 改为临时隔离当前 slide，将其固定到视口左上角，并隐藏其他 slide 后截图。

2. **横向 deck 截图不稳定**

   原因：横向 flex/transform deck 不一定能通过滚动进入当前视口。

   修复：不再依赖横向滚动或 transform 状态，统一使用 slide isolation 捕获。

3. **加载等待不充分**

   原因：只靠固定 sleep 可能早于字体、图片或异步渲染完成。

   修复：等待 `document.readyState`、字体、图片解码、双 RAF，并支持 `--ready-expr`。

### 剩余取舍

- raster 策略是最高视觉保真，但文字不可选中。
- screen-vector 保留文本层，但仍可能受 Chrome PDF backend 限制。
- print-vector 最适合正式文档，但不等同于浏览器屏幕渲染。

---

## 高级使用技巧

### 技巧1：提高文字锐度

```bash
--dpr 3 --format png
```

DPR 越高，文字越锐，文件也越大。

### 技巧2：控制文件体积

```bash
--format jpeg --quality 92
```

适合照片多、纯文本少的页面。文字和细线多时优先 PNG。

### 技巧3：修正 slide 自动识别

```bash
--selector ".slide"
```

如果页面中有 `.slides-container`、`.slide-track` 等容器被误判，务必指定真正的一页元素。

### 技巧4：处理 print 断点坍塌

`onepage_pdf.py` 进入 print pipeline 后，`@media (max-width: 1024px)` 之类规则可能被触发。用 `--extra-css` 锁定桌面布局：

```css
@media (max-width: 1024px) {
  .report-layout {
    grid-template-columns: repeat(3, 1fr) !important;
  }
}
```

### 技巧5：脱敏与泄露检测

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/onepage_pdf.py \
  confidential.html -o public.pdf \
  --replace /tmp/subs.json \
  --forbid /tmp/forbid.txt
```

---

## FAQ

### Q1：为什么不默认用向量 PDF？

**A：** 因为 Chrome 的 PDF 输出管线不等于浏览器屏幕渲染。`backdrop-filter`、WebGL、canvas、复杂 filter、3D transform 等效果可能丢失或变化。用户要求“浏览器原样”时，截图策略更可靠。

### Q2：截图 PDF 的文字为什么不能复制？

**A：** raster 策略把浏览器画面作为图片写入 PDF，视觉保真优先，没有文本层。如果需要文字可复制，应选择 screen-vector 或 print-vector。

### Q3：slide-raster 会修改我的 HTML 文件吗？

**A：** 不会。slide isolation 只注入到临时 Chrome 会话里，用于截图时固定当前 slide，不写回源文件。

### Q4：为什么文件很大？

**A：** PNG + DPR 2/3 会保留大量像素细节。可以改用 JPEG，或降低 DPR：

```bash
--format jpeg --quality 92 --dpr 2
```

### Q5：长页 PDF 在 Acrobat 打不开怎么办？

**A：** 旧 Acrobat 对页面高度有 14400pt 兼容限制。超长单页可以改为分页输出，或用 Chrome/Firefox/PDFium/微信等查看器。

---

## 路线图

### v2.0.0 已完成

- 三策略体系：screen-raster、screen-vector、print-vector。
- 默认先给用户策略选择建议。
- 新增 `long-raster` 连续长页截图 PDF。
- `slides-raster` 支持 slide isolation，修复重复截第一页问题。
- 增强资源等待：readyState、fonts、images、RAF、ready expression。
- README、SKILL、examples、mechanics、css-fixes 全量同步。

### v2.1.0 计划

- 自动生成浏览器截图与 PDF 渲染图的差异对比报告。
- 增加多页长文分页 raster 输出。
- 为常见 slide 框架增加专用 selector preset。
- 增加文件体积预算和自动 PNG/JPEG 选择。

---

## 许可证

MIT License

`onepage_pdf.py` 基于 [xntj-ai/onepage-pdf](https://github.com/xntj-ai/onepage-pdf) 方法论扩展。

---

## 免责声明

本 Skill 生成的 PDF 受 Chrome、系统字体、GPU/headless 环境、页面自身加载逻辑和 PDF 查看器能力影响。截图策略以视觉还原为优先，但不提供文本层；向量策略保留文本层，但不保证与浏览器屏幕完全一致。正式归档前应人工抽检关键页面。

---

## 作者

**作者**：Dr.CS

**用途**：Claude Code / Claude Skills 中的 HTML 高保真 PDF 导出工作流。
