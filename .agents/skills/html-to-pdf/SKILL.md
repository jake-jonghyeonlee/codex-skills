---
name: html-to-pdf
description: |
  [KO] PDF로 변환·PDF로 내보내기·HTML이나 슬라이드를 PDF로·인쇄용 PDF를 만들 때.
  Convert an HTML page or HTML slide deck into a PDF with a local Chrome/Edge (no network).
  Pick the strategy from the user's goal:
  - pixel-faithful / "exactly like the browser" -> CDP screenshot PDF (slides-raster, long-raster)
  - selectable text, close to screen rendering -> CDP screen-media vector PDF (screen-vector)
  - formal document, text layer, small file, one continuous page -> Chrome print vector PDF (onepage)
  Triggers: "PDF로 내보내기", "PDF로 변환", "HTML을 PDF로", "슬라이드를 PDF로", "export PDF",
  "html to pdf", "print to pdf", "one-page PDF", "long-page PDF", "multi-page PDF".
---

# HTML to PDF — screenshot-faithful or vector-text

Two routes, three strategies. Decide first what the user really wants:

- **Maximum visual fidelity**: the PDF should look like the browser screen.
- **Selectable text**: text must be copyable/searchable (text layer).
- **Formal printed document**: accept print CSS semantics; stable pagination or one long page; smaller file.

## Ask before converting (unless the user already chose)

Do not run a conversion blindly. Read the HTML, classify it (slide deck vs continuous page), then offer a
short choice and wait. Skip the question only when the user named the strategy in the same message and
said to proceed without asking.

Suggested wording:

```text
이 HTML은 [슬라이드 덱 / 연속 긴 페이지]로 보입니다. 브라우저 화면 그대로가 목표라면 1번을 권합니다.

1. 화면 캡처 수준 (권장): 브라우저와 가장 비슷. canvas/WebGL/backdrop-filter/복잡한 CSS 유지. 글자 선택 불가, 파일 큼.
2. 화면 벡터 시도: 글자 선택 가능. screen media로 PDF 출력. 대체로 비슷하지만 필터/페이지 나눔이 다를 수 있음.
3. 인쇄 벡터 긴 페이지: 글자 선택 가능, 파일 작음, 보고서/문서용. print 파이프라인을 타므로 화면과 완전히 같지는 않음.

1/2/3 또는 전략 이름으로 답해 주세요.
```

Mapping from stated goals:

- "browser look / as-is / screenshot-level / visual fidelity" -> recommend **strategy 1**.
- "copyable text / searchable / text layer / not a screenshot" -> recommend **strategy 2**, fall back to **3** if the result differs visibly.
- "long-page PDF / no page breaks / formal report / small file" -> recommend **strategy 3**; if visual fidelity is also stressed, recommend **1B**.

## Step 1: read the HTML and classify it

**Slide-deck signals** (any one is enough):
- `scroll-snap-type` present.
- 2+ elements matching `.slide` / `[class*="slide"]` / `[data-slide]` / `<section>` / `.page`.
- Many elements sized about `100vw` x `100vh`.
- `<title>` / `<meta>` mentions slide, PPT, presentation, 발표, 演示.
- Reveal.js / Impress.js markers.

**Continuous-page signals**:
- No explicit slide container.
- `<article>` / `<main>` / `.content` flows downward.
- Page height far exceeds the viewport.

## Environment

- Python 3.12 with `pymupdf` and `websocket-client` installed (see `requirements-skills.txt` at the repo root).
- A local Chrome, Edge or Chromium. The scripts probe the usual Windows (`C:\Program Files\Google\Chrome\...`,
  `...\Microsoft\Edge\Application\msedge.exe`), macOS and Linux locations; pass `--chrome PATH` to override.
- No network is used: the scripts talk only to `127.0.0.1:<port>` of the Chrome they launched.
- Run the scripts with the repo-relative path shown below (this skill lives in `.agents/skills/html-to-pdf`).
  On Windows CMD/PowerShell use `python`; `python3` may resolve to the Microsoft Store stub.

## Strategy 1: CDP screenshot PDF (screen-faithful)

Default recommendation for "make it look like the browser". It does not enter print media: Chrome renders in
screen mode, waits for fonts/images, screenshots, and the script assembles a PDF. For slide decks it
temporarily isolates the current slide at the viewport origin so horizontal decks, scroll-snap or transform
state cannot repeat page 1.

Pros: closest to the browser; keeps canvas, WebGL, backdrop-filter, CSS filter, complex backgrounds.
Cons: text is not selectable; larger files; very long pages may exceed old Acrobat's 14400 pt limit.

### 1A. slide deck -> multi-page screenshot PDF

```bash
python .agents/skills/html-to-pdf/scripts/render_slides_cdp.py "{input.html}" \
  -o "{output.pdf}" --strategy slides-raster --width 1280 --height 720 --dpr 2 --format png
```

| option | default | meaning |
|---|---|---|
| `--width` / `--height` | 1280 / 720 | viewport in px (use 1920x1080 for html-ppt / frontend-slides decks) |
| `--dpr` | 2 | device pixel ratio; raise to 3 for sharper small text |
| `--format` | png | png for text/lines, jpeg to shrink photo-heavy decks |
| `--quality` | 92 | JPEG quality |
| `--selector` | auto | slide selector, e.g. `.slide` / `[data-slide]` |
| `--ready-expr` | — | JS readiness expression, e.g. `window.__PDF_READY === true` |

Notes: isolation happens only inside the temporary Chrome session; the source HTML is never modified.
If a background lives only inside another slide, move it into each slide or use the page's own export mode.

### 1B. continuous page -> single long-page screenshot PDF

```bash
python .agents/skills/html-to-pdf/scripts/render_slides_cdp.py "{input.html}" \
  -o "{output.pdf}" --strategy long-raster --width 1280 --height 900 --dpr 2 --format png --tile-height 4096
```

The script measures `scrollWidth/scrollHeight` in screen layout, screenshots in tiles and stitches them into
one PDF page. Use `--format jpeg --quality 92` if the file is too large.

## Strategy 2: CDP screen-media vector PDF

For "text must be selectable but keep it close to the screen". Sets `Emulation.setEmulatedMedia(screen)`,
measures the page in screen layout, then calls `Page.printToPDF`.

```bash
python .agents/skills/html-to-pdf/scripts/render_slides_cdp.py "{input.html}" \
  -o "{output.pdf}" --strategy screen-vector --width 1280 --height 900
```

This is a vector *attempt*, not screenshot fidelity: filters, 3D transforms and some canvas/WebGL may differ,
and horizontal transform-based decks are less stable than `slides-raster`.

## Strategy 3: print vector one-page PDF

For reports, articles, formal documents: text layer, smaller file, one stable long page. Uses an oversized
page render followed by measured cropping, inside print media.

### 3.1 check the HTML for common print differences

1. **Responsive breakpoints**: `@media (max-width: N)` with N >= 741 — print media triggers around 741 px and can collapse desktop layouts.
2. **Glass effects**: `backdrop-filter` may be dropped silently; provide an opaque fallback.
3. **vh/vw**: `100vh` / `100vw` resolve against the oversized page and can explode heights.
4. **Scroll-triggered animations**: `.fade*` / `.reveal*` / `.animate*` / AOS may stay invisible.

### 3.2 write fix CSS

Put the fixes in a temp file (e.g. `%TEMP%\onepage-fixes.css` / `/tmp/onepage-fixes.css`). See `references/css-fixes.md`.

### 3.3 convert

```bash
python .agents/skills/html-to-pdf/scripts/onepage_pdf.py "{input.html}" \
  -o "{output.pdf}" --width 1280 --extra-css "{fixes.css}"
```

| option | default | meaning |
|---|---|---|
| `--width` | 1280 | design width px, aligned to 8 px |
| `--bedrock` | 18000 | initial oversized page height; doubles on overflow |
| `--padding` | 32 | bottom padding px |
| `--crop` | vector | content detection: vector or pixel |
| `--virtual-time` | 10000 | virtual time budget (ms) for JS-driven pages |
| `--replace` | — | text replacement JSON `[["old","new"],...]` |
| `--forbid` | — | leak words; abort if still present in the PDF |

## Verify every result

Never stop at "command succeeded".

```python
import pymupdf
doc = pymupdf.open("{output.pdf}")
print("pages:", doc.page_count)
for i in range(min(3, doc.page_count)):
    r = doc[i].rect
    print(f"page {i+1}: {r.width:.0f}x{r.height:.0f}pt")
    doc[i].get_pixmap(dpi=72).save(f"pdf-check-{i+1}.png")
doc.close()
```

Check: page count as expected; first pages match the browser; no bottom cut-off, blank pages, misplaced text or
missing images. Non-selectable text is expected under strategy 1. If a vector strategy differs visibly, ask the
user whether to switch to the screenshot route.

## Troubleshooting

| symptom | strategy | cause | fix |
|---|---|---|---|
| looks different from the browser | screen-vector / onepage | PDF pipeline != screen rendering | use `slides-raster` or `long-raster` |
| soft text edges | raster | low DPR or JPEG | `--dpr 2/3 --format png` |
| file too large | raster | PNG at high DPR | `--format jpeg --quality 92` for photo pages |
| slides not all detected | slides-raster | auto selector guessed wrong | `--selector ".slide"` or `[data-slide]` |
| async charts / fonts missing | raster / vector | captured too early | `--ready-expr` or a longer `--delay` |
| horizontal deck captures wrong page | slides-raster | selector hit a container | explicit `--selector`; one `.slide` per page |
| grid collapses to one column | onepage | print media query ~741 px | lock desktop layout in extra CSS |
| glass effect lost | onepage / screen-vector | Chrome PDF limitation | screenshot strategy, or opaque print fallback |
| bottom cut off | onepage | bedrock too small / crop misjudged | raise `--bedrock` or `--crop pixel` |

Mechanics: `references/mechanics.md`. Worked examples: `references/examples.md`. (Both reference files are
in Chinese; they are optional background reading.)

## Files

```text
.agents/skills/html-to-pdf/
├── SKILL.md
├── README.md                 (upstream, Chinese)
├── LICENSE                   (MIT, CSlawyer1985/html-to-pdf-skill)
├── scripts/
│   ├── onepage_pdf.py        # strategy 3: print vector one-page
│   └── render_slides_cdp.py  # strategies 1/2: CDP screenshot / screen vector
└── references/
    ├── css-fixes.md
    ├── mechanics.md
    └── examples.md
```
