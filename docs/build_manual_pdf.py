# /// script
# requires-python = ">=3.10"
# dependencies = ["markdown-it-py"]
# ///
"""Build docs/user-manual.pdf from docs/user-manual.md.

Usage (from the repo root):
    uv run docs/build_manual_pdf.py [input.md] [output.pdf]

Renders the Markdown to HTML and prints it to an A4 PDF with headless
Microsoft Edge (or Chrome). Images are resolved relative to the .md file.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from markdown_it import MarkdownIt

HERE = Path(__file__).resolve().parent
src = Path(sys.argv[1] if len(sys.argv) > 1 else HERE / "user-manual.md").resolve()
out = Path(sys.argv[2] if len(sys.argv) > 2 else src.with_suffix(".pdf")).resolve()

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: "Yu Gothic UI", "Yu Gothic", Meiryo, "Segoe UI", sans-serif; font-size: 10.5pt; line-height: 1.5; color: #1a1a1a; }
h1 { font-size: 20pt; margin: 0 0 4pt; }
h2 { font-size: 14pt; margin: 18pt 0 6pt; border-bottom: 1px solid #ccc; padding-bottom: 3pt; break-after: avoid; }
h3 { break-after: avoid; }
code { font-family: Consolas, monospace; font-size: 9.5pt; background: #f2f2f2; padding: 0 2pt; border-radius: 2pt; }
pre { background: #f2f2f2; padding: 6pt 8pt; border-radius: 3pt; white-space: pre-wrap; word-break: break-all; break-inside: avoid; }
pre code { padding: 0; background: none; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0; font-size: 9.5pt; }
th, td { border: 1px solid #ccc; padding: 4pt 6pt; text-align: left; vertical-align: top; }
th { background: #eee; }
td code { word-break: break-all; }
td:first-child { width: 38%; }
tr { break-inside: avoid; }
li { margin: 3pt 0; }
img { max-width: 100%; border: 1px solid #ccc; margin: 4pt 0; break-inside: avoid; }
a { color: #0b5cad; }
"""


def find_browser():
    candidates = []
    for env in ("ProgramFiles(x86)", "ProgramFiles", "LocalAppData"):
        root = os.environ.get(env)
        if root:
            candidates += [Path(root, "Microsoft/Edge/Application/msedge.exe"),
                           Path(root, "Google/Chrome/Application/chrome.exe")]
    for c in candidates:
        if c.exists():
            return str(c)
    for name in ("msedge", "chrome", "google-chrome", "chromium"):
        if found := shutil.which(name):
            return found
    sys.exit("Error: Microsoft Edge or Google Chrome is required to print the PDF.")


text = src.read_text(encoding="utf-8")
title = next((m.group(1).strip() for m in re.finditer(r"^# (.+)$", text, re.M)), src.stem)
body = MarkdownIt("commonmark").enable("table").render(text)
# The HTML is written to a temp folder, so make relative image paths absolute.
base = src.parent.as_uri()
body = re.sub(r'src="(?![a-z]+:)([^"]+)"', lambda m: f'src="{base}/{m.group(1)}"', body)
html = (f"<!doctype html><html lang='ja'><head><meta charset='utf-8'><title>{title}</title>"
        f"<style>{CSS}</style></head><body>{body}</body></html>")

with tempfile.TemporaryDirectory() as tmp:
    page = Path(tmp, "manual.html")
    page.write_text(html, encoding="utf-8")
    before = out.stat().st_mtime if out.exists() else None
    # A separate profile keeps the headless browser from handing the job to an
    # already-running browser window, which would skip writing the PDF.
    subprocess.run([find_browser(), "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    "--allow-file-access-from-files", f"--user-data-dir={Path(tmp, 'profile')}",
                    f"--print-to-pdf={out}", page.as_uri()],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

if not out.exists() or out.stat().st_mtime == before:
    sys.exit(f"Error: the browser did not write {out}")
print(f"Wrote {out}")
