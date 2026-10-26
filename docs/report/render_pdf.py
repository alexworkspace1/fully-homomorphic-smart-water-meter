# Renders report.html to PDF with Playwright Chromium.
# Usage: python render_pdf.py report.html "Senior Design Project.pdf"
import sys, pathlib
from playwright.sync_api import sync_playwright
src, out = pathlib.Path(sys.argv[1]).resolve(), sys.argv[2]
foot = '<div style="width:100%;font-size:8px;color:#59636e;font-family:Segoe UI,Arial;text-align:center"><span class="pageNumber"></span></div>'
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    errs = []; pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(src.as_uri(), wait_until="networkidle")
    pg.wait_for_selector("body[data-ready='1']", timeout=60000)
    pg.pdf(path=out, format="Letter", print_background=True, display_header_footer=True,
           header_template="<div></div>", footer_template=foot, prefer_css_page_size=True)
    b.close()
print("errors:", errs)
