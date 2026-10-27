# CSS 修复策略参考

按两种输出模式分类的完整 CSS 修复清单。所有规则使用 `!important` 以确保覆盖内联样式。

---

## 通用修复（两种模式都需要）

### 打印色彩保真

```css
* {
  -webkit-print-color-adjust: exact !important;
  print-color-adjust: exact !important;
}
```

不加此声明，Chrome 默认丢弃背景色和渐变以节省墨水。

### 动画与过渡

```css
* {
  animation: none !important;
  transition: none !important;
}
```

headless 打印不会触发滚动事件，所有入场动画（IntersectionObserver、scroll-triggered）永远不会执行。

### 滚动渐入强制可见

```css
[class*="fade"], [class*="reveal"], [class*="animate"], [class*="aos"],
[class*="appear"], [class*="enter"], [class*="visible"],
[data-aos], [data-animate], [data-reveal] {
  opacity: 1 !important;
  transform: none !important;
  visibility: visible !important;
}
```

这些 class 模式在 headless 打印中永远停留在 `opacity:0` / `transform:translateY(...)` 状态。

### 毛玻璃降级

```css
[class*="glass"], [class*="blur"], [class*="frosted"],
[style*="backdrop-filter"], [style*="backdropFilter"] {
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
}
```

`backdrop-filter: blur()` 在 PDF 输出中被 Chrome 静默丢弃。如果半透明元素下有复杂背景，需追加不透明背景：

```css
.glass, .glassmorphism, .frosted, .blur-bg {
  background: rgba(255, 255, 255, 0.88) !important;
}
```

### 固定背景修正

```css
* {
  background-attachment: scroll !important;
}
```

`background-attachment: fixed` 在 Chrome 打印中仅在首页绘制。

### 固定定位 → 绝对定位

```css
.fixed, [class*="fixed"], nav[class*="fixed"],
[style*="position: fixed"], [style*="position:fixed"] {
  position: absolute !important;
}
```

固定导航栏/指示器在每页 PDF 重复出现，转为绝对定位只出现一次。

### CJK 字体回退

```css
body {
  font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei",
               "Hiragino Sans GB", sans-serif !important;
}
```

Web font 可能不含 CJK 字形，PDF 中会显示 tofu。显式声明系统回退。

---

## 模式 A 专用：连续单页 PDF

模式 A 使用 onepage_pdf.py，脚本已注入基础修复 CSS。额外需要的修复：

### 响应式断点锁定

打印媒体查询宽度 ~741px（US Letter 默认值），`@media (max-width: N)` 中 N≥741 的规则都会在打印时意外触发：

```css
@media (max-width: 900px) {
  .card-grid { grid-template-columns: repeat(3, 1fr) !important; }
  .hero h1 { font-size: 56px !important; }
}
```

检查原 HTML 中所有 `@media (max-width: N)` 且 N≥741 的规则，为每个生成桌面值覆盖。

### vh/vw 覆盖

```css
[style*="100vh"], .hero, .fullscreen {
  height: auto !important;
  min-height: auto !important;
}
[style*="100vw"] {
  width: auto !important;
}
```

打印中 vh 解析为 bedrock 页面高度（18000px+），`min-height:100vh` → ~187 英寸。

---

## 屏幕截图级保真策略

`render_slides_cdp.py --strategy slides-raster` 和 `--strategy long-raster`
默认不注入修复 CSS。它们的目标是捕获 Chrome 屏幕模式已经绘制出来的画面，
因此应尽量避免修改页面样式。

`slides-raster` 会在临时 Chrome 会话中注入一小段隔离 CSS：当前 slide
固定到视口左上角，其他 slide 隐藏。这个行为用于避免横向 deck 或 transform
deck 重复截第一页，不会写回源 HTML。

只有在以下情况才考虑额外修改 HTML/CSS：

- 页面必须等待异步图表或动画结束：优先用 `--ready-expr`。
- slide 自动识别不准确：优先用 `--selector`。
- 页面本身需要进入“导出状态”：由页面代码提供 `body.exporting` 或
  `window.__PDF_READY`，而不是在转换脚本里大面积重写样式。

### 推荐的导出状态 CSS

如果页面作者愿意提供导出状态，可在 HTML 中自行加入：

```css
body.exporting {
  scroll-behavior: auto;
}

body.exporting * {
  caret-color: transparent;
}
```

并在页面准备好时设置：

```js
document.body.classList.add("exporting");
window.__PDF_READY = true;
```

然后转换时使用：

```bash
--ready-expr "window.__PDF_READY === true"
```

## print 向量 slide 备用策略

如果用户明确要求“slide PDF 文字可选中”，可以尝试旧式 print 分页。但这不是
“浏览器原样”路线，复杂 canvas/WebGL/backdrop-filter 可能不保真。

### @page 尺寸声明

```css
@page {
  size: {WIDTH}px {HEIGHT}px;
  margin: 0;
}
```

### 禁用滚动吸附并锁定 slide 尺寸

```css
html, body {
  scroll-snap-type: none !important;
  overflow: visible !important;
  height: auto !important;
  margin: 0 !important;
  padding: 0 !important;
}

.slide, [data-slide], section {
  width: {WIDTH}px !important;
  height: {HEIGHT}px !important;
  min-height: {HEIGHT}px !important;
  max-height: {HEIGHT}px !important;
  overflow: hidden !important;
  box-sizing: border-box !important;
  break-after: page !important;
  page-break-after: always !important;
  break-inside: avoid !important;
}

.slide:last-child, [data-slide]:last-child, section:last-child {
  break-after: auto !important;
  page-break-after: auto !important;
}
```

---

## 尺寸检测策略

### 自动检测 slide 尺寸

1. 从第一个 `.slide` 元素的 `height` CSS 计算值提取
2. 如果是 `100vh` 或百分比：
   - PC 演示默认 → 1280×720 (16:9)
   - 移动端演示默认 → 390×844 (iPhone 14 比例)
3. 从 `<meta name="viewport">` 或 body 的 width 推断
4. 最终 fallback：1280×720
5. 宽度对齐到 8px（防止 MediaBox 舍入产生空白页）

### 自动检测 slide 数量

```python
import re
count = len(re.findall(r'class=["\'][^"\']*slide[^"\']*["\']', html))
# 或更精确：用 BeautifulSoup 解析
```
