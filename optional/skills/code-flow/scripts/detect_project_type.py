#!/usr/bin/env python3
"""Detect project type by scanning imports, file structure, and code patterns.

Usage: python3 detect_project_type.py <project-root>

Outputs JSON with detected type, confidence, signals, entry points,
and suggested pipelines for the dataflow diagram skill.
"""

import ast
import json
import os
import re
import sys
from pathlib import Path
from collections import defaultdict

TYPES = {
    "ml_dl": {
        "label": "ML / 딥러닝",
        "imports": {
            "torch": 5, "tensorflow": 5, "keras": 5, "jax": 5,
            "sklearn": 3, "xgboost": 3, "lightgbm": 3,
            "torchvision": 3, "transformers": 4, "datasets": 2,
            "wandb": 2, "mlflow": 2, "tensorboard": 2,
            "pytorch_lightning": 4, "lightning": 4,
        },
        "files": {
            "train.py": 4, "predict.py": 3, "evaluate.py": 3,
            "model.py": 2, "dataset.py": 2, "inference.py": 3,
            "finetune.py": 3, "pretrain.py": 3,
        },
        "dirs": {
            "models": 2, "checkpoints": 2, "weights": 2,
        },
        "patterns": [
            (r"nn\.Module", 4), (r"model\.fit\(", 3), (r"optimizer", 2),
            (r"\.backward\(\)", 4), (r"epoch", 2), (r"loss", 2),
            (r"DataLoader", 3), (r"\.train\(\)", 2), (r"\.eval\(\)", 2),
            (r"gradient", 2), (r"batch_size", 2),
        ],
        "pipelines": ["학습 (training)", "추론 (inference)", "평가 (evaluation)"],
        "data_types": {
            "file":   {"label": "파일",       "preset": "gray"},
            "image":  {"label": "이미지",     "preset": "amber"},
            "array":  {"label": "배열",       "preset": "green"},
            "tensor": {"label": "텐서",       "preset": "blue"},
            "output": {"label": "출력/logits","preset": "purple"},
            "loss":   {"label": "손실",       "preset": "red"},
        },
    },
    "web_server": {
        "label": "웹 서버 / API",
        "imports": {
            "flask": 5, "django": 5, "fastapi": 5, "starlette": 3,
            "aiohttp": 4, "tornado": 4, "bottle": 4, "sanic": 4,
            "uvicorn": 2, "gunicorn": 2, "celery": 2,
            "sqlalchemy": 2, "pymongo": 2, "redis": 2,
            "express": 5, "koa": 5, "hapi": 4, "nestjs": 5,
        },
        "files": {
            "app.py": 3, "server.py": 3, "wsgi.py": 3, "asgi.py": 3,
            "manage.py": 4, "urls.py": 3, "views.py": 3,
            "routes.py": 3, "middleware.py": 2,
            "server.ts": 3, "server.js": 3, "app.ts": 3, "app.js": 3,
        },
        "dirs": {
            "routes": 3, "views": 3, "controllers": 3,
            "templates": 2, "static": 1, "migrations": 2,
            "middleware": 2, "handlers": 2,
        },
        "patterns": [
            (r"@app\.route", 4), (r"@router\.(get|post|put|delete)", 4),
            (r"@api_view", 3), (r"class.*View", 2),
            (r"Request|Response", 2), (r"middleware", 2),
            (r"app\.listen", 3), (r"router\.", 2),
        ],
        "pipelines": ["요청 처리 (request)", "인증 (auth)", "데이터 접근 (data access)"],
        "data_types": {
            "client":  {"label": "클라이언트", "preset": "gray"},
            "request": {"label": "Request",    "preset": "blue"},
            "data":    {"label": "데이터",     "preset": "green"},
            "response":{"label": "Response",   "preset": "purple"},
            "db":      {"label": "DB/저장소",  "preset": "amber"},
            "error":   {"label": "에러",       "preset": "red"},
        },
    },
    "cli_tool": {
        "label": "CLI 도구",
        "imports": {
            "argparse": 3, "click": 4, "typer": 4, "fire": 3,
            "rich": 2, "prompt_toolkit": 2, "questionary": 2,
            "colorama": 1, "tqdm": 1,
        },
        "files": {
            "cli.py": 4, "__main__.py": 3, "main.py": 2,
            "commands.py": 3, "console.py": 2,
        },
        "dirs": {
            "commands": 3, "plugins": 2,
        },
        "patterns": [
            (r"add_argument", 3), (r"@click\.command", 4),
            (r"@click\.group", 4), (r"typer\.Typer", 4),
            (r"if __name__.*__main__", 1), (r"sys\.argv", 2),
            (r"sys\.exit", 1), (r"sys\.stdin|sys\.stdout", 2),
        ],
        "pipelines": ["명령 실행 (command)", "입출력 처리 (I/O)"],
        "data_types": {
            "input":  {"label": "입력",      "preset": "gray"},
            "parsed": {"label": "파싱 결과", "preset": "blue"},
            "data":   {"label": "처리 데이터","preset": "green"},
            "output": {"label": "출력",      "preset": "purple"},
            "file":   {"label": "파일",      "preset": "amber"},
        },
    },
    "data_pipeline": {
        "label": "데이터 파이프라인 / ETL",
        "imports": {
            "pandas": 3, "pyspark": 5, "airflow": 5, "luigi": 5,
            "prefect": 5, "dagster": 5,
            "polars": 3, "dask": 3, "beam": 4,
            "sqlalchemy": 2, "psycopg2": 2, "pymysql": 2,
        },
        "files": {
            "pipeline.py": 4, "dag.py": 4, "etl.py": 4,
            "transform.py": 3, "extract.py": 3, "load.py": 3,
            "ingest.py": 3, "migrate.py": 3,
        },
        "dirs": {
            "dags": 4, "pipelines": 3, "transforms": 3,
            "extractors": 3, "loaders": 3,
        },
        "patterns": [
            (r"DataFrame", 2), (r"read_csv|read_parquet|read_json", 3),
            (r"to_sql|to_csv|to_parquet", 2), (r"DAG\(", 4),
            (r"@task", 2), (r"pipeline", 1),
            (r"\.merge\(|\.join\(|\.groupby\(", 2),
        ],
        "pipelines": ["추출 (extract)", "변환 (transform)", "적재 (load)"],
        "data_types": {
            "source": {"label": "소스",        "preset": "gray"},
            "raw":    {"label": "원시 데이터",  "preset": "amber"},
            "clean":  {"label": "정제 데이터",  "preset": "green"},
            "agg":    {"label": "집계 데이터",  "preset": "blue"},
            "target": {"label": "대상 저장소",  "preset": "purple"},
        },
    },
    "library": {
        "label": "라이브러리 / 패키지",
        "files": {
            "setup.py": 3, "pyproject.toml": 2, "setup.cfg": 2,
        },
        "dirs": {
            "src": 2, "tests": 2, "docs": 2, "examples": 2,
        },
        "patterns": [
            (r"__all__\s*=", 3), (r"__version__", 2),
        ],
        "pipelines": ["공개 API 호출", "내부 처리"],
        "data_types": {
            "input":    {"label": "입력",     "preset": "blue"},
            "internal": {"label": "내부 상태","preset": "green"},
            "output":   {"label": "반환값",   "preset": "purple"},
        },
    },
    "frontend": {
        "label": "프론트엔드",
        "files": {
            "package.json": 2, "tsconfig.json": 2,
            "next.config.js": 4, "next.config.ts": 4,
            "next.config.mjs": 4,
            "vite.config.ts": 4, "vite.config.js": 4,
            "webpack.config.js": 3,
            "nuxt.config.ts": 4, "nuxt.config.js": 4,
            "angular.json": 5,
        },
        "dirs": {
            "components": 3, "pages": 3, "public": 1,
            "styles": 2, "src/views": 3, "src/components": 4,
            "src/hooks": 3, "src/store": 3,
        },
        "patterns": [
            (r"import.*React", 4), (r"import.*Vue", 4),
            (r"@Component", 4), (r"useState|useEffect", 3),
            (r"createApp|defineComponent", 3),
        ],
        "pipelines": ["사용자 인터랙션", "상태 관리", "데이터 페칭"],
        "data_types": {
            "event":  {"label": "이벤트",  "preset": "gray"},
            "state":  {"label": "상태",    "preset": "blue"},
            "props":  {"label": "Props",   "preset": "green"},
            "api":    {"label": "API 응답","preset": "amber"},
            "render": {"label": "렌더링",  "preset": "purple"},
        },
    },
}


def _collect_py_imports(py_files):
    imports = set()
    code_chunks = []
    for pf in py_files:
        try:
            src = pf.read_text(encoding="utf-8", errors="ignore")
            code_chunks.append(src)
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])
        except Exception:
            pass
    return imports, "\n".join(code_chunks)


def _collect_js_imports(root, js_files):
    imports = set()
    code_chunks = []
    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8", errors="ignore"))
            for section in ("dependencies", "devDependencies", "peerDependencies"):
                imports.update(data.get(section, {}).keys())
        except Exception:
            pass
    for jf in js_files:
        try:
            src = jf.read_text(encoding="utf-8", errors="ignore")
            code_chunks.append(src)
            for m in re.finditer(r"""(?:import|require)\s*\(?['"]([@\w/.-]+)['"]""", src):
                imports.add(m.group(1).split("/")[0])
        except Exception:
            pass
    return imports, "\n".join(code_chunks)


def _collect_go_imports(root, go_files):
    imports = set()
    code_chunks = []
    gomod = root / "go.mod"
    if gomod.exists():
        try:
            src = gomod.read_text(encoding="utf-8", errors="ignore")
            for m in re.finditer(r"^\s+([\w./-]+)", src, re.MULTILINE):
                imports.add(m.group(1).split("/")[-1])
        except Exception:
            pass
    for gf in go_files:
        try:
            src = gf.read_text(encoding="utf-8", errors="ignore")
            code_chunks.append(src)
        except Exception:
            pass
    return imports, "\n".join(code_chunks)


SKIP_DIRS = {".git", "__pycache__", "node_modules", "venv", "env", ".venv",
             ".env", ".tox", ".mypy_cache", ".pytest_cache", "dist", "build",
             ".next", ".nuxt"}


def scan_project(root_path):
    root = Path(root_path).resolve()
    scores = defaultdict(lambda: {"score": 0, "signals": []})

    py_files, js_files, go_files = [], [], []
    all_files, all_dirs = [], set()

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir != ".":
            all_dirs.add(rel_dir)
        for fn in filenames:
            if fn.startswith("."):
                continue
            fp = Path(dirpath) / fn
            rel = str(fp.relative_to(root))
            all_files.append(rel)
            if fn.endswith(".py"):
                py_files.append(fp)
            elif fn.endswith((".js", ".ts", ".jsx", ".tsx", ".mjs")):
                js_files.append(fp)
            elif fn.endswith(".go"):
                go_files.append(fp)

    all_imports = set()
    all_code = ""

    if py_files:
        imp, code = _collect_py_imports(py_files)
        all_imports |= imp
        all_code += code
    if js_files:
        imp, code = _collect_js_imports(root, js_files)
        all_imports |= imp
        all_code += code
    if go_files:
        imp, code = _collect_go_imports(root, go_files)
        all_imports |= imp
        all_code += code

    for type_key, spec in TYPES.items():
        score = 0
        signals = []

        for imp, weight in spec.get("imports", {}).items():
            if imp in all_imports:
                score += weight
                signals.append(f"import: {imp}")

        for fname, weight in spec.get("files", {}).items():
            for af in all_files:
                if af == fname or af.endswith("/" + fname):
                    score += weight
                    signals.append(f"file: {fname}")
                    break

        for dname, weight in spec.get("dirs", {}).items():
            for ad in all_dirs:
                if ad == dname or ad.endswith("/" + dname):
                    score += weight
                    signals.append(f"dir: {dname}/")
                    break

        for pattern, weight in spec.get("patterns", []):
            if re.search(pattern, all_code):
                score += weight
                signals.append(f"pattern: {pattern}")

        scores[type_key]["score"] = score
        scores[type_key]["signals"] = signals

    entry_points = []
    for pf in py_files:
        try:
            src = pf.read_text(encoding="utf-8", errors="ignore")
            if "if __name__" in src and "__main__" in src:
                entry_points.append(str(pf.relative_to(root)))
        except Exception:
            pass
    for jf in js_files:
        name = jf.name
        if name in ("index.js", "index.ts", "main.js", "main.ts",
                     "server.js", "server.ts", "app.js", "app.ts"):
            entry_points.append(str(jf.relative_to(root)))

    ranked = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
    top_key, top_val = ranked[0]
    max_score = top_val["score"]

    if max_score == 0:
        confidence = 0.0
    else:
        second = ranked[1][1]["score"] if len(ranked) > 1 else 0
        confidence = min(1.0, max_score / 20) * (1 - second / (max_score + 1) * 0.3)
        confidence = round(confidence, 2)

    spec = TYPES[top_key]
    return {
        "detected_type": top_key,
        "type_label": spec["label"],
        "confidence": confidence,
        "score": max_score,
        "signals": top_val["signals"],
        "entry_points": sorted(set(entry_points)),
        "suggested_pipelines": spec.get("pipelines", ["메인 처리 흐름"]),
        "suggested_data_types": spec.get("data_types", {}),
        "all_scores": {
            k: {"score": v["score"], "label": TYPES[k]["label"]}
            for k, v in ranked if v["score"] > 0
        },
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <project-root>", file=sys.stderr)
        sys.exit(1)
    result = scan_project(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))
