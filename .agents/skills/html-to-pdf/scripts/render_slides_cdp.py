#!/usr/bin/env python3
"""CDP screen-rendered HTML -> PDF.

Strategies:
  - slides-raster: one viewport screenshot per slide, then assemble a multi-page PDF.
  - long-raster: tile the rendered browser page and assemble one continuous PDF page.
  - screen-vector: ask Chrome to print the screen-media layout to a vector PDF.

The raster strategies are the highest visual-fidelity route because they capture
what Chrome painted in screen mode. Text is not selectable in those PDFs.
"""

import argparse
import base64
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf

import websocket


CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]

PX_TO_PT = 72.0 / 96.0


def find_chrome(explicit=None):
    if explicit:
        if Path(explicit).exists():
            return explicit
        sys.exit(f"Chrome not found: {explicit}")
    for path in CHROME_PATHS:
        if Path(path).exists():
            return path
    found = (
        shutil.which("chrome")
        or shutil.which("chromium")
        or shutil.which("chromium-browser")
        or shutil.which("google-chrome")
        or shutil.which("msedge")
    )
    if found:
        return found
    sys.exit("Chrome/Edge not found. Install Chrome or pass --chrome PATH")


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class CDP:
    def __init__(self, ws):
        self.ws = ws
        self.msg_id = 0

    def send(self, method, params=None, timeout=30):
        self.msg_id += 1
        mid = self.msg_id
        self.ws.send(json.dumps({"id": mid, "method": method, "params": params or {}}))
        self.ws.settimeout(timeout)
        while True:
            response = json.loads(self.ws.recv())
            if response.get("id") != mid:
                continue
            if "error" in response:
                raise RuntimeError(f"CDP {method}: {response['error']}")
            return response.get("result", {})

    def eval(self, expression, await_promise=False, timeout=30):
        result = self.send(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": await_promise,
                "returnByValue": True,
            },
            timeout=timeout,
        )
        if "exceptionDetails" in result:
            raise RuntimeError(f"Runtime.evaluate failed: {result['exceptionDetails']}")
        return result.get("result", {}).get("value")


def start_chrome(chrome_path, port, width, height, headful=False):
    user_dir = tempfile.mkdtemp(prefix="cdp-html-pdf-profile-")
    cmd = [
        chrome_path,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_dir}",
        "--remote-allow-origins=*",
        "--no-first-run",
        "--no-default-browser-check",
        "--allow-file-access-from-files",
        "--hide-scrollbars",
        "--force-color-profile=srgb",
        "--enable-webgl",
        "--ignore-gpu-blocklist",
        f"--window-size={width},{height}",
    ]
    if not headful:
        cmd.insert(1, "--headless=new")

    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    version_url = f"http://127.0.0.1:{port}/json/version"
    for _ in range(60):
        try:
            urllib.request.urlopen(version_url, timeout=1)
            break
        except Exception:
            time.sleep(0.25)
    else:
        proc.terminate()
        shutil.rmtree(user_dir, ignore_errors=True)
        sys.exit("Chrome did not start")
    return proc, user_dir


def open_page(cdp, input_path, width, height, dpr, delay, ready_expr=None):
    cdp.send("Page.enable")
    cdp.send("Runtime.enable")
    cdp.send("Emulation.setDeviceMetricsOverride", {
        "width": width,
        "height": height,
        "deviceScaleFactor": dpr,
        "mobile": False,
        "screenWidth": width,
        "screenHeight": height,
    })
    cdp.send("Page.navigate", {"url": Path(input_path).resolve().as_uri()})
    time.sleep(delay)
    wait_for_ready(cdp, ready_expr)


def wait_for_ready(cdp, ready_expr=None):
    cdp.eval(
        """(async () => {
          const timeout = (ms) => new Promise(resolve => setTimeout(resolve, ms));
          const until = async (predicate, ms) => {
            const started = Date.now();
            while (Date.now() - started < ms) {
              if (predicate()) return true;
              await timeout(100);
            }
            return false;
          };
          await until(() => document.readyState !== 'loading', 10000);
          if (document.fonts && document.fonts.ready) {
            await Promise.race([document.fonts.ready.catch(() => {}), timeout(10000)]);
          }
          const images = Array.from(document.images || []);
          await Promise.all(images.map((img) => {
            if (img.complete && img.naturalWidth !== 0) return Promise.resolve();
            if (img.decode) return Promise.race([img.decode().catch(() => {}), timeout(8000)]);
            return new Promise((resolve) => {
              img.addEventListener('load', resolve, {once: true});
              img.addEventListener('error', resolve, {once: true});
              setTimeout(resolve, 8000);
            });
          }));
          await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
          return true;
        })()""",
        await_promise=True,
        timeout=35,
    )
    if ready_expr:
        value = cdp.eval(
            f"""(async () => {{
              const started = Date.now();
              while (Date.now() - started < 30000) {{
                if (Boolean(await (async () => ({ready_expr}))())) return true;
                await new Promise(resolve => setTimeout(resolve, 100));
              }}
              return false;
            }})()""",
            await_promise=True,
            timeout=35,
        )
        if not value:
            sys.exit(f"ready expression timed out: {ready_expr}")


def parse_json_eval(cdp, expression, timeout=30):
    value = cdp.eval(expression, timeout=timeout)
    if isinstance(value, str):
        return json.loads(value)
    return value


def detect_slides(cdp, selector=None):
    selector_js = json.dumps(selector or "")
    return parse_json_eval(cdp, f"""(() => {{
      const explicitSelector = {selector_js};
      const base = explicitSelector
        ? Array.from(document.querySelectorAll(explicitSelector))
        : Array.from(document.querySelectorAll(
            '.slide, [class*="slide"], [data-slide], section, .page, .magazine-page'
          ));
      const seen = new Set();
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      const selected = [];

      for (const el of base) {{
        if (!el || seen.has(el)) continue;
        seen.add(el);
        const rect = el.getBoundingClientRect();
        const text = [
          el.tagName || '',
          el.id || '',
          typeof el.className === 'string' ? el.className : '',
          el.getAttribute('role') || '',
          el.dataset && el.dataset.slide ? 'data-slide' : ''
        ].join(' ').toLowerCase();
        const nameLooksLikeSlide = /(\\b|[-_])(slide|page|screen|section)(\\b|[-_])/.test(text)
          || el.hasAttribute('data-slide')
          || el.matches('section');
        const sizeLooksLikeSlide = rect.width >= vw * 0.55 && rect.height >= vh * 0.45;
        const isContainer = /(container|wrapper|track|deck)/.test(text)
          && rect.width > vw * 1.3
          && rect.height <= vh * 1.2;
        if (nameLooksLikeSlide && sizeLooksLikeSlide && !isContainer) selected.push(el);
      }}

      const slides = selected.length >= 2 ? selected : base.filter((el) => {{
        const rect = el.getBoundingClientRect();
        return rect.width >= vw * 0.7 && rect.height >= vh * 0.7;
      }});

      slides.forEach((el, i) => el.setAttribute('data-cdp-pdf-slide', String(i)));
      const first = slides[0] && slides[0].getBoundingClientRect();
      return JSON.stringify({{
        count: slides.length,
        first: first ? {{
          x: Math.round(first.x), y: Math.round(first.y),
          width: Math.round(first.width), height: Math.round(first.height)
        }} : null
      }});
    }})()""")


def activate_slide(cdp, index, width, height, slide_delay):
    info = parse_json_eval(cdp, f"""(() => {{
      const styleId = 'cdp-html-pdf-slide-isolation';
      let style = document.getElementById(styleId);
      if (!style) {{
        style = document.createElement('style');
        style.id = styleId;
        style.textContent = `
          html[data-cdp-pdf-capturing="slides"],
          html[data-cdp-pdf-capturing="slides"] body {{
            width: {width}px !important;
            height: {height}px !important;
            min-width: {width}px !important;
            min-height: {height}px !important;
            overflow: hidden !important;
            margin: 0 !important;
            padding: 0 !important;
            scroll-behavior: auto !important;
          }}
          html[data-cdp-pdf-capturing="slides"] [data-cdp-pdf-slide] {{
            visibility: hidden !important;
          }}
          html[data-cdp-pdf-capturing="slides"] [data-cdp-pdf-slide][data-cdp-pdf-active="true"] {{
            visibility: visible !important;
            position: fixed !important;
            left: 0 !important;
            top: 0 !important;
            right: auto !important;
            bottom: auto !important;
            width: {width}px !important;
            height: {height}px !important;
            min-width: {width}px !important;
            min-height: {height}px !important;
            max-width: {width}px !important;
            max-height: {height}px !important;
            margin: 0 !important;
            transform: none !important;
            opacity: 1 !important;
            overflow: hidden !important;
            z-index: 2147483647 !important;
          }}
        `;
        document.head.appendChild(style);
      }}
      const el = document.querySelector('[data-cdp-pdf-slide="{index}"]');
      if (!el) return JSON.stringify({{ok:false, reason:'missing slide'}});
      document.documentElement.setAttribute('data-cdp-pdf-capturing', 'slides');
      document.documentElement.style.scrollBehavior = 'auto';
      document.body.style.scrollBehavior = 'auto';
      document.querySelectorAll('[data-cdp-pdf-slide]').forEach((slide) => {{
        slide.removeAttribute('data-cdp-pdf-active');
      }});
      el.setAttribute('data-cdp-pdf-active', 'true');
      window.scrollTo(0, 0);
      let rect = el.getBoundingClientRect();
      return JSON.stringify({{
        ok: true,
        x: Math.round(rect.x), y: Math.round(rect.y),
        width: Math.round(rect.width), height: Math.round(rect.height),
        scrollX: Math.round(window.scrollX),
        scrollY: Math.round(window.scrollY),
        pageLeft: Math.round(window.visualViewport ? window.visualViewport.pageLeft : window.scrollX),
        pageTop: Math.round(window.visualViewport ? window.visualViewport.pageTop : window.scrollY)
      }});
    }})()""")
    time.sleep(slide_delay)
    return info


def capture(cdp, out_path, fmt, quality, clip=None):
    params = {
        "format": fmt,
        "fromSurface": True,
        "captureBeyondViewport": True,
    }
    if clip is not None:
        params["clip"] = clip
    if fmt == "jpeg":
        params["quality"] = quality
    result = cdp.send("Page.captureScreenshot", params, timeout=120)
    Path(out_path).write_bytes(base64.b64decode(result["data"]))


def insert_image(page, image_path, x, y, width, height):
    page.insert_image(
        pymupdf.Rect(x * PX_TO_PT, y * PX_TO_PT, (x + width) * PX_TO_PT, (y + height) * PX_TO_PT),
        filename=str(image_path),
    )


def slides_raster(cdp, args, workdir):
    info = detect_slides(cdp, args.selector)
    slide_count = info.get("count", 0)
    if slide_count == 0:
        sys.exit("No slides detected. Pass --selector or use --strategy long-raster.")

    print(f"Strategy: slides-raster | Slides: {slide_count} | viewport: {args.width}x{args.height} @ {args.dpr}x")
    doc = pymupdf.open()
    page_width_pt = args.width * PX_TO_PT
    page_height_pt = args.height * PX_TO_PT

    ext = "jpg" if args.format == "jpeg" else "png"
    for index in range(slide_count):
        nav = activate_slide(cdp, index, args.width, args.height, args.slide_delay)
        wait_for_ready(cdp)
        img_path = workdir / f"slide-{index:03d}.{ext}"
        capture(
            cdp,
            img_path,
            args.format,
            args.quality,
            {"x": 0, "y": 0, "width": args.width, "height": args.height, "scale": 1},
        )
        page = doc.new_page(width=page_width_pt, height=page_height_pt)
        page.insert_image(pymupdf.Rect(0, 0, page_width_pt, page_height_pt), filename=str(img_path))
        sys.stdout.write(
            f"\r  [{index + 1}/{slide_count}] {img_path.stat().st_size // 1024}KB "
            f"slide@({nav.get('x', '?')},{nav.get('y', '?')}) "
            f"scroll=({nav.get('pageLeft', '?')},{nav.get('pageTop', '?')})"
        )
        sys.stdout.flush()
    print()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    doc.save(args.output, deflate=True, garbage=3)
    doc.close()
    print(f"Done: {args.output} ({Path(args.output).stat().st_size / 1024:.0f}KB, {slide_count}p)")


def layout_size(cdp):
    return parse_json_eval(cdp, """(() => {
      const doc = document.documentElement;
      const body = document.body || doc;
      const width = Math.ceil(Math.max(
        doc.scrollWidth, body.scrollWidth, doc.clientWidth, window.innerWidth
      ));
      const height = Math.ceil(Math.max(
        doc.scrollHeight, body.scrollHeight, doc.clientHeight, window.innerHeight
      ));
      return JSON.stringify({width, height});
    })()""")


def long_raster(cdp, args, workdir):
    size = layout_size(cdp)
    content_width = max(args.width, int(size["width"]))
    content_height = max(args.height, int(size["height"]))
    tile_h = max(256, int(args.tile_height))
    ext = "jpg" if args.format == "jpeg" else "png"

    print(
        f"Strategy: long-raster | content: {content_width}x{content_height}px "
        f"@ {args.dpr}x | tile: {tile_h}px"
    )

    cdp.send("Emulation.setDeviceMetricsOverride", {
        "width": max(args.width, min(content_width, args.width)),
        "height": args.height,
        "deviceScaleFactor": args.dpr,
        "mobile": False,
        "screenWidth": args.width,
        "screenHeight": args.height,
    })

    doc = pymupdf.open()
    page = doc.new_page(width=content_width * PX_TO_PT, height=content_height * PX_TO_PT)

    y = 0
    tile_index = 0
    while y < content_height:
        h = min(tile_h, content_height - y)
        img_path = workdir / f"tile-{tile_index:03d}.{ext}"
        capture(
            cdp,
            img_path,
            args.format,
            args.quality,
            {"x": 0, "y": y, "width": content_width, "height": h, "scale": 1},
        )
        insert_image(page, img_path, 0, y, content_width, h)
        y += h
        tile_index += 1
        sys.stdout.write(f"\r  tiles: {tile_index} | {min(y, content_height)}/{content_height}px")
        sys.stdout.flush()
    print()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    doc.save(args.output, deflate=True, garbage=3)
    doc.close()
    print(f"Done: {args.output} ({Path(args.output).stat().st_size / 1024:.0f}KB, 1p)")
    if content_height * PX_TO_PT > 14400:
        print("warning: page height exceeds the 14400pt Acrobat compatibility limit")


def screen_vector(cdp, args):
    cdp.send("Emulation.setEmulatedMedia", {"media": "screen"})
    size = layout_size(cdp)
    width = max(args.width, int(size["width"]))
    height = max(args.height, int(size["height"]))
    print(f"Strategy: screen-vector | measured: {width}x{height}px")
    result = cdp.send(
        "Page.printToPDF",
        {
            "printBackground": True,
            "preferCSSPageSize": False,
            "paperWidth": width / 96.0,
            "paperHeight": height / 96.0,
            "marginTop": 0,
            "marginBottom": 0,
            "marginLeft": 0,
            "marginRight": 0,
            "pageRanges": "1",
            "scale": 1,
        },
        timeout=180,
    )
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_bytes(base64.b64decode(result["data"]))
    print(f"Done: {args.output} ({Path(args.output).stat().st_size / 1024:.0f}KB)")


def choose_auto(cdp, args):
    info = detect_slides(cdp, args.selector)
    if info.get("count", 0) >= 2:
        return "slides-raster"
    return "long-raster"


def build_arg_parser():
    parser = argparse.ArgumentParser(description="HTML -> high-fidelity PDF via Chrome CDP")
    parser.add_argument("input", help="HTML file path")
    parser.add_argument("-o", "--output", required=True, help="Output PDF path")
    parser.add_argument(
        "--strategy",
        choices=["auto", "slides-raster", "long-raster", "screen-vector"],
        default="slides-raster",
        help="default keeps backward compatibility with the old slide renderer",
    )
    parser.add_argument("--width", type=int, default=1280, help="viewport width in CSS px")
    parser.add_argument("--height", type=int, default=720, help="viewport height in CSS px")
    parser.add_argument("--dpr", type=float, default=2.0, help="device scale factor for raster output")
    parser.add_argument("--format", choices=["png", "jpeg"], default="png", help="raster image format")
    parser.add_argument("--quality", type=int, default=92, help="JPEG quality, ignored for PNG")
    parser.add_argument("--tile-height", type=int, default=4096, help="CSS px per long-page tile")
    parser.add_argument("--selector", help="explicit slide selector, e.g. '.slide' or '[data-slide]'")
    parser.add_argument("--ready-expr", help="JS expression that must become truthy before capture")
    parser.add_argument("--chrome", help="Chrome/Edge executable path")
    parser.add_argument("--port", type=int, help="CDP port; default chooses a free port")
    parser.add_argument("--delay", type=float, default=1.0, help="initial load wait seconds")
    parser.add_argument("--slide-delay", type=float, default=0.25, help="wait after slide navigation")
    parser.add_argument("--headful", action="store_true", help="show Chrome while rendering")
    parser.add_argument("--keep-temp", action="store_true")
    return parser


def main():
    args = build_arg_parser().parse_args()
    if not Path(args.input).exists():
        sys.exit(f"File not found: {args.input}")
    if args.dpr <= 0:
        sys.exit("--dpr must be positive")

    chrome_path = find_chrome(args.chrome)
    port = args.port or free_port()
    workdir = Path(tempfile.mkdtemp(prefix="cdp-html-pdf-"))
    chrome_proc = None
    user_dir = None
    try:
        print(f"Launching Chrome (CDP port {port})...")
        chrome_proc, user_dir = start_chrome(chrome_path, port, args.width, args.height, headful=args.headful)
        targets = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=5).read())
        target = next((item for item in targets if item.get("type") == "page"), targets[0])
        ws = websocket.create_connection(target["webSocketDebuggerUrl"])
        try:
            cdp = CDP(ws)
            open_page(cdp, args.input, args.width, args.height, args.dpr, args.delay, args.ready_expr)
            strategy = choose_auto(cdp, args) if args.strategy == "auto" else args.strategy
            if strategy == "slides-raster":
                slides_raster(cdp, args, workdir)
            elif strategy == "long-raster":
                long_raster(cdp, args, workdir)
            elif strategy == "screen-vector":
                screen_vector(cdp, args)
            else:
                sys.exit(f"unknown strategy: {strategy}")
        finally:
            ws.close()
    finally:
        if chrome_proc:
            chrome_proc.terminate()
            try:
                chrome_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                chrome_proc.kill()
        if user_dir:
            shutil.rmtree(user_dir, ignore_errors=True)
        if args.keep_temp:
            print(f"temp kept: {workdir}")
        else:
            shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
