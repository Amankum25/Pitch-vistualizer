"""
html_exporter.py – Comic-style storyboard HTML with:
  - Grid view
  - Slideshow mode (prev/next)
  - Light/Dark mode toggle
  - Download button
  - Shareable standalone file (no external deps)
"""

import pathlib

OUTPUTS_DIR = pathlib.Path("outputs")


def export_html_storyboard(panels: list, storyboard_id: str) -> str:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

    panels_js = []
    panels_html_grid = ""

    for panel in panels:
        n = panel.get("scene_number", "?")
        title = panel.get("frame", {}).get("title", f"Frame {n}")
        caption = panel.get("caption", "")
        scene = panel.get("scene_text", "")
        img = panel.get("image_url", "")

        panels_js.append({"title": title, "image": img, "caption": caption, "scene": scene})

        panels_html_grid += f"""
        <div class="panel" onclick="openSlide({n - 1})">
          <div class="panel-num">Scene {n}</div>
          <img src="{img}" alt="{title}" loading="lazy" class="panel-img"/>
          <div class="panel-body">
            <h2>{title}</h2>
            <p class="caption">{caption}</p>
          </div>
        </div>"""

    panels_json = __import__("json").dumps(panels_js, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Storyboard · {storyboard_id}</title>
<style>
/* ── Tokens ── */
:root[data-theme="dark"]  {{ --bg:#0a0f1a; --surface:#151b2b; --surface2:#1f273b; --acc:#00b4a6; --acc2:#00e0cf; --text:#f0f4f8; --muted:#a0aec0; --border:rgba(0,180,166,.2); }}
:root[data-theme="light"] {{ --bg:#f0f4f8; --surface:#ffffff; --surface2:#e2e8f0; --acc:#007c73; --acc2:#00b4a6; --text:#1a202c; --muted:#4a5568; --border:rgba(0,124,115,.25); }}
/* ── Reset ── */
*{{ box-sizing:border-box; margin:0; padding:0; }}
body{{ font-family:system-ui,sans-serif; background:var(--bg); color:var(--text); transition:background .3s,color .3s; }}
/* ── Header ── */
header{{ text-align:center; padding:2rem 1rem 1rem; border-bottom:1px solid var(--border); }}
header h1{{ font-size:2rem; background:linear-gradient(135deg,var(--text),var(--acc)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; }}
header p{{ color:var(--muted); font-size:.9rem; margin-top:.25rem; }}
.toolbar{{ display:flex; justify-content:center; gap:.75rem; margin-top:1rem; flex-wrap:wrap; }}
.btn{{ padding:.5rem 1.2rem; border-radius:8px; border:none; cursor:pointer; font-size:.9rem; font-weight:600; transition:all .2s; }}
.btn-teal{{ background:var(--acc); color:#fff; }}
.btn-teal:hover{{ background:var(--acc2); transform:translateY(-1px); }}
.btn-outline{{ background:transparent; border:1px solid var(--acc); color:var(--acc); }}
.btn-outline:hover{{ background:var(--acc); color:#fff; }}
.btn-ghost{{ background:var(--surface2); color:var(--text); border:1px solid var(--border); }}
.btn-ghost:hover{{ border-color:var(--acc); }}
/* ── Grid view ── */
#grid-view{{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:1.5rem; max-width:1200px; margin:2rem auto; padding:0 1.5rem; }}
.panel{{ background:var(--surface); border-radius:12px; overflow:hidden; border:1px solid var(--border); cursor:pointer; transition:all .25s; }}
.panel:hover{{ border-color:var(--acc); transform:translateY(-4px); box-shadow:0 8px 24px rgba(0,180,166,.15); }}
.panel-num{{ display:inline-flex; align-items:center; background:var(--acc); color:#fff; font-size:.75rem; font-weight:700; padding:.3rem .9rem; border-radius:0 0 8px 0; }}
.panel-img{{ width:100%; aspect-ratio:16/9; object-fit:cover; display:block; transition:transform .4s; }}
.panel:hover .panel-img{{ transform:scale(1.04); }}
.panel-body{{ padding:1rem 1.25rem; }}
.panel-body h2{{ font-size:.95rem; color:var(--acc); margin-bottom:.4rem; }}
.caption{{ font-size:.85rem; color:var(--muted); line-height:1.5; }}
/* ── Slideshow ── */
#slideshow-view{{ display:none; max-width:860px; margin:2rem auto; padding:0 1.5rem; text-align:center; }}
#slide-img{{ width:100%; aspect-ratio:16/9; object-fit:cover; border-radius:12px; border:1px solid var(--border); margin-bottom:1.5rem; box-shadow:0 12px 40px rgba(0,0,0,.4); }}
#slide-title{{ font-size:1.6rem; font-weight:700; color:var(--acc); margin-bottom:.5rem; }}
#slide-caption{{ font-size:1.1rem; color:var(--muted); margin-bottom:1rem; line-height:1.6; }}
#slide-scene{{ font-size:.85rem; color:var(--muted); background:var(--surface); border:1px solid var(--border); padding:.75rem 1rem; border-radius:8px; margin-bottom:1.5rem; text-align:left; }}
.slide-nav{{ display:flex; justify-content:center; align-items:center; gap:1.5rem; }}
#slide-counter{{ color:var(--muted); font-size:.9rem; }}
/* ── Footer ── */
footer{{ text-align:center; padding:2rem; color:var(--muted); font-size:.8rem; border-top:1px solid var(--border); margin-top:2rem; }}
</style>
</head>
<body>

<header>
  <h1>🎬 Storyboard</h1>
  <p>ID: {storyboard_id}</p>
  <div class="toolbar">
    <button class="btn btn-ghost" onclick="toggleTheme()">🌗 Toggle Theme</button>
    <button class="btn btn-outline" id="view-toggle-btn" onclick="toggleView()">▶ Slideshow</button>
    <a href="/api/v1/download/{storyboard_id}" class="btn btn-teal" download>⬇ Download HTML</a>
  </div>
</header>

<!-- GRID VIEW -->
<div id="grid-view">
{panels_html_grid}
</div>

<!-- SLIDESHOW VIEW -->
<div id="slideshow-view">
  <img id="slide-img" src="" alt=""/>
  <h2 id="slide-title"></h2>
  <p id="slide-caption"></p>
  <div id="slide-scene"></div>
  <div class="slide-nav">
    <button class="btn btn-outline" onclick="prevSlide()">← Prev</button>
    <span id="slide-counter"></span>
    <button class="btn btn-outline" onclick="nextSlide()">Next →</button>
  </div>
</div>

<footer>Generated by Pitch Visualizer · Storyboard {storyboard_id}</footer>

<script>
const panels = {panels_json};
let currentIdx = 0;
let isSlideshow = false;

function renderSlide(idx) {{
  const p = panels[idx];
  document.getElementById('slide-img').src     = p.image;
  document.getElementById('slide-img').alt     = p.title;
  document.getElementById('slide-title').textContent   = p.title;
  document.getElementById('slide-caption').textContent = p.caption;
  document.getElementById('slide-scene').textContent   = p.scene;
  document.getElementById('slide-counter').textContent = `${{idx + 1}} / ${{panels.length}}`;
}}

function openSlide(idx) {{
  currentIdx = idx;
  renderSlide(currentIdx);
  if (!isSlideshow) toggleView();
}}

function nextSlide() {{
  currentIdx = (currentIdx + 1) % panels.length;
  renderSlide(currentIdx);
}}

function prevSlide() {{
  currentIdx = (currentIdx - 1 + panels.length) % panels.length;
  renderSlide(currentIdx);
}}

function toggleView() {{
  isSlideshow = !isSlideshow;
  document.getElementById('grid-view').style.display      = isSlideshow ? 'none'  : 'grid';
  document.getElementById('slideshow-view').style.display = isSlideshow ? 'block' : 'none';
  document.getElementById('view-toggle-btn').textContent  = isSlideshow ? '⊞ Grid' : '▶ Slideshow';
  if (isSlideshow) renderSlide(currentIdx);
}}

function toggleTheme() {{
  const root = document.documentElement;
  root.setAttribute('data-theme', root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
}}

// Keyboard nav
document.addEventListener('keydown', (e) => {{
  if (!isSlideshow) return;
  if (e.key === 'ArrowRight') nextSlide();
  if (e.key === 'ArrowLeft')  prevSlide();
  if (e.key === 'Escape')     toggleView();
}});
</script>
</body>
</html>"""

    out_path = OUTPUTS_DIR / f"storyboard_{storyboard_id}.html"
    out_path.write_text(html, encoding="utf-8")
    return str(out_path)
