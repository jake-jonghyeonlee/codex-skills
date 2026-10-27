# 使用示例

## 调用前的选择建议

默认先读取 HTML 后给出选择，不要直接转换。只有用户明确指定策略并要求直接执行时，才跳过确认。

```text
我看这个 HTML 更像【翻页演示】。如果目标是尽量还原浏览器里的原始画面，我建议选 1。

1. 屏幕截图级保真（推荐）：最像浏览器画面，保留 canvas/WebGL/backdrop-filter/复杂 CSS；文字不可选中，文件较大。
2. 屏幕向量尝试：文字可选中，使用 screen media 打 PDF；视觉通常接近浏览器，但复杂滤镜/分页仍可能有差异。
3. 打印向量长页：文字可选中、体积较小、适合报告/文章；会进入 print pipeline，不保证和浏览器屏幕完全一致。

请回复 1/2/3 或策略名，我再执行。
```

## 策略 1A：翻页演示 -> 多页截图 PDF

适合 scroll-snap、section slide、PPT、横向/纵向 deck。最高视觉还原，文字不可选中。

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/render_slides_cdp.py \
  slides.html \
  -o output/slides-screen.pdf \
  --strategy slides-raster \
  --width 1280 --height 720 \
  --dpr 2 \
  --format png
```

如果自动 slide 检测不准：

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/render_slides_cdp.py \
  slides.html \
  -o output/slides-screen.pdf \
  --strategy slides-raster \
  --width 1280 --height 720 \
  --selector ".slide" \
  --dpr 2 \
  --format png
```

照片很多、PDF 太大时：

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/render_slides_cdp.py \
  slides.html \
  -o output/slides-screen-small.pdf \
  --strategy slides-raster \
  --width 1280 --height 720 \
  --dpr 2 \
  --format jpeg \
  --quality 92
```

## 策略 1B：连续长页 -> 单页截图 PDF

适合“和浏览器原样一致”的网页长图 PDF。

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/render_slides_cdp.py \
  report.html \
  -o output/report-screen-long.pdf \
  --strategy long-raster \
  --width 1280 --height 900 \
  --dpr 2 \
  --format png \
  --tile-height 4096
```

如果页面有异步图表，HTML 可在渲染完成时设置：

```js
window.__PDF_READY = true;
```

然后调用：

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/render_slides_cdp.py \
  dashboard.html \
  -o output/dashboard.pdf \
  --strategy long-raster \
  --width 1440 --height 1000 \
  --ready-expr "window.__PDF_READY === true"
```

## 策略 2：screen-media 向量 PDF

适合“文字可复制，同时尽量接近浏览器屏幕布局”。它不是截图级保真。

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/render_slides_cdp.py \
  report.html \
  -o output/report-screen-vector.pdf \
  --strategy screen-vector \
  --width 1280 --height 900
```

如果输出视觉差异明显，改用策略 1B；如果用户更重视文本层和体积，改用策略 3。

## 策略 3：print 向量连续长页 PDF

适合正式报告、文章、需要文本可选中、体积较小的 PDF。

```bash
python3 ~/.claude/skills/html-to-pdf/scripts/onepage_pdf.py \
  report.html \
  -o output/report-print-vector.pdf \
  --width 1280
```

含毛玻璃、移动端断点、`100vh` 等 print 风险时，先生成修复 CSS：

```bash
cat > /tmp/onepage-fixes.css << 'CSSEOF'
.glass-card {
  backdrop-filter: none !important;
  -webkit-backdrop-filter: none !important;
  background: rgba(255, 255, 255, 0.92) !important;
}

@media (max-width: 1024px) {
  .report-layout { grid-template-columns: repeat(3, 1fr) !important; }
}

.hero, .fullscreen {
  height: auto !important;
  min-height: auto !important;
}
CSSEOF

python3 ~/.claude/skills/html-to-pdf/scripts/onepage_pdf.py \
  report.html \
  -o output/report-print-vector.pdf \
  --width 1280 \
  --extra-css /tmp/onepage-fixes.css
```

## 验证

```python
import pymupdf

doc = pymupdf.open("output/report-screen-long.pdf")
print(f"页数: {doc.page_count}")
for i in range(min(3, doc.page_count)):
    rect = doc[i].rect
    print(f"第{i+1}页: {rect.width:.0f}x{rect.height:.0f}pt")
    doc[i].get_pixmap(dpi=72).save(f"/tmp/pdf-check-{i+1}.png")
doc.close()
```

检查重点：

- 页面数量是否符合预期。
- 首屏/前 3 页是否与浏览器截图一致。
- 没有空白页、底部截断、图片缺失、文字错位。
- 截图策略下文字不可选中是预期结果。
