/* ─────────────────────────────────────────────────────────────────────
   PITCH VISUALIZER — app.js
   Multi-page SPA: Landing → Loading → Storyboard (Grid / Slideshow)
   No backend changes – purely presentation layer.
───────────────────────────────────────────────────────────────────── */

const API_BASE = window.location.origin;

// ── Page helpers ──────────────────────────────────────────────────────────
function navigateTo(pageId) {
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('page-active');
        p.style.display = 'none';
    });
    const target = document.getElementById(pageId);
    target.style.display = pageId === 'storyboard-page' ? 'flex' : 'flex';
    // force reflow so animation replays
    void target.offsetWidth;
    target.classList.add('page-active');
}

// ── DOM refs ──────────────────────────────────────────────────────────────
const UI = {
    generateBtn:  document.getElementById('generate-btn'),
    btnText:      document.querySelector('.btn-text'),
    spinner:      document.getElementById('loading-spinner'),
    pitchText:    document.getElementById('pitch-text'),
    styleSelect:  document.getElementById('style-select'),
    errorMsg:     document.getElementById('error-message'),

    // grid
    gridContainer: document.getElementById('storyboard-container'),
    downloadBtn:   document.getElementById('download-btn'),
    viewBtn:       document.getElementById('view-btn'),

    // slideshow
    slideImg:     document.getElementById('slide-img'),
    slideTitle:   document.getElementById('slide-title'),
    slideCaption: document.getElementById('slide-caption'),
    slideScene:   document.getElementById('slide-scene'),
    slideBadge:   document.getElementById('slide-counter-badge'),
    thumbStrip:   document.getElementById('thumb-strip'),

    // loading page
    progressBar:     document.getElementById('progress-bar'),
    progressPct:     document.getElementById('progress-pct'),
    progressStepTxt: document.getElementById('progress-step-text'),
};

// ── State ─────────────────────────────────────────────────────────────────
let panels      = [];
let currentIdx  = 0;
let inSlideshow = false;
let progressInterval = null;

// ── Generate ──────────────────────────────────────────────────────────────
UI.generateBtn.addEventListener('click', async () => {
    const text = UI.pitchText.value.trim();
    if (!text) { showError('Please enter your story narrative!'); return; }

    UI.errorMsg.classList.add('hidden');
    startLoading();
    navigateTo('loading-page');

    try {
        const res = await fetch(`${API_BASE}/api/v1/generate-storyboard`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, style: UI.styleSelect.value }),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Server error ${res.status}`);
        }
        const data = await res.json();
        panels = data.panels;

        finishLoading();

        // Give the progress bar a beat to hit 100% visually
        await sleep(600);

        renderGrid(panels);
        buildThumbStrip(panels);
        setupActionBtns(data.html_download_url);
        navigateTo('storyboard-page');
        switchTab('grid');

    } catch (err) {
        console.error(err);
        stopLoading();
        navigateTo('landing-page');
        showError('Generation failed: ' + err.message);
    }
});

// ── Loading animation ─────────────────────────────────────────────────────
const STEPS = [
    { id: 'step-1', label: 'Parsing narrative…',     pct: 15  },
    { id: 'step-2', label: 'Generating scene frames…', pct: 40 },
    { id: 'step-3', label: 'Rendering visuals…',      pct: 70  },
    { id: 'step-4', label: 'Assembling storyboard…',  pct: 90  },
];

function startLoading() {
    UI.generateBtn.disabled = true;
    UI.btnText.textContent  = 'Generating…';
    UI.spinner.classList.remove('hidden');

    // reset steps
    STEPS.forEach(s => {
        const el = document.getElementById(s.id);
        if (el) { el.classList.remove('active', 'done'); }
    });
    setProgress(0, 'Initializing pipeline…');

    let stepIdx = 0;
    progressInterval = setInterval(() => {
        if (stepIdx < STEPS.length) {
            const s = STEPS[stepIdx];
            // mark previous done
            if (stepIdx > 0) markStepDone(STEPS[stepIdx - 1].id);
            markStepActive(s.id);
            setProgress(s.pct, s.label);
            stepIdx++;
        }
    }, 2400);
}

function finishLoading() {
    clearInterval(progressInterval);
    STEPS.forEach(s => markStepDone(s.id));
    setProgress(100, 'Complete!');
    stopLoading();
}

function stopLoading() {
    clearInterval(progressInterval);
    UI.generateBtn.disabled = false;
    UI.btnText.textContent  = 'Generate Storyboard';
    UI.spinner.classList.add('hidden');
}

function setProgress(pct, label) {
    if (UI.progressBar) UI.progressBar.style.width  = pct + '%';
    if (UI.progressPct) UI.progressPct.textContent   = pct + '%';
    if (UI.progressStepTxt) UI.progressStepTxt.textContent = label;
}

function markStepActive(id) {
    const el = document.getElementById(id);
    if (el) { el.classList.remove('done'); el.classList.add('active'); }
}
function markStepDone(id) {
    const el = document.getElementById(id);
    if (el) { el.classList.remove('active'); el.classList.add('done'); }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Tab switching (Grid / Slideshow) ──────────────────────────────────────
window.switchTab = function(tab) {
    const isGrid = tab === 'grid';
    document.getElementById('grid-view').classList.toggle('hidden', !isGrid);
    document.getElementById('slideshow-view').classList.toggle('hidden', isGrid);
    document.getElementById('tab-grid').classList.toggle('toolbar-tab-active', isGrid);
    document.getElementById('tab-slideshow').classList.toggle('toolbar-tab-active', !isGrid);
    inSlideshow = !isGrid;
    if (!isGrid && panels.length) renderSlide(currentIdx);
};

// ── Grid Rendering ────────────────────────────────────────────────────────
function renderGrid(panels) {
    UI.gridContainer.innerHTML = '';
    panels.forEach((panel, i) => {
        const card = document.createElement('div');
        card.className = 'panel-card';
        card.style.animationDelay = `${i * 0.07}s`;
        card.onclick = () => { currentIdx = i; switchTab('slideshow'); };

        card.innerHTML = `
            <div class="image-wrapper">
                <span class="scene-badge">Scene ${panel.scene_number}</span>
                <img src="${escapeHTML(panel.image_url)}"
                     alt="${escapeHTML(panel.frame.title)}"
                     loading="lazy"
                     onerror="this.style.opacity='0.4'"/>
            </div>
            <div class="card-content">
                <h3 class="card-title">${escapeHTML(panel.frame.title)}</h3>
                <p class="card-caption">${escapeHTML(panel.caption)}</p>
            </div>`;

        UI.gridContainer.appendChild(card);
    });
}

// ── Thumbnail strip ───────────────────────────────────────────────────────
function buildThumbStrip(panels) {
    if (!UI.thumbStrip) return;
    UI.thumbStrip.innerHTML = '';
    panels.forEach((panel, i) => {
        const thumb = document.createElement('div');
        thumb.className = 'thumb-item';
        thumb.id = `thumb-${i}`;
        thumb.onclick = () => goToSlide(i);
        thumb.innerHTML = `<img src="${escapeHTML(panel.image_url)}" alt="Scene ${panel.scene_number}" loading="lazy"/>`;
        UI.thumbStrip.appendChild(thumb);
    });
}

function goToSlide(idx) {
    currentIdx = idx;
    renderSlide(idx);
}

// ── Slideshow ─────────────────────────────────────────────────────────────
function renderSlide(idx) {
    const p = panels[idx];
    if (!p) return;

    // fade out → update → fade in
    if (UI.slideImg) {
        UI.slideImg.style.opacity = '0';
        setTimeout(() => {
            UI.slideImg.src         = p.image_url;
            UI.slideImg.alt         = p.frame.title;
            UI.slideImg.style.opacity = '1';
        }, 200);
    }

    if (UI.slideTitle)   UI.slideTitle.textContent   = p.frame.title;
    if (UI.slideCaption) UI.slideCaption.textContent = p.caption;
    if (UI.slideScene)   UI.slideScene.textContent   = p.scene_text || '';
    if (UI.slideBadge)   UI.slideBadge.textContent   = `${idx + 1} / ${panels.length}`;

    // update thumbnails
    document.querySelectorAll('.thumb-item').forEach((el, i) => {
        el.classList.toggle('active', i === idx);
    });

    // scroll active thumb into view
    const activeThumb = document.getElementById(`thumb-${idx}`);
    if (activeThumb && UI.thumbStrip) {
        activeThumb.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
}

window.nextSlide = function() {
    currentIdx = (currentIdx + 1) % panels.length;
    renderSlide(currentIdx);
};
window.prevSlide = function() {
    currentIdx = (currentIdx - 1 + panels.length) % panels.length;
    renderSlide(currentIdx);
};

// ── Keyboard navigation ───────────────────────────────────────────────────
document.addEventListener('keydown', e => {
    if (!inSlideshow || !panels.length) return;
    if (e.key === 'ArrowRight') nextSlide();
    if (e.key === 'ArrowLeft')  prevSlide();
    if (e.key === 'Escape')     switchTab('grid');
});

// ── Theme toggle ──────────────────────────────────────────────────────────
window.toggleTheme = function() {
    const root  = document.documentElement;
    const isDark = root.getAttribute('data-theme') === 'dark';
    root.setAttribute('data-theme', isDark ? 'light' : 'dark');

    // update sidebar theme icons
    document.querySelectorAll('.sb-moon').forEach(el => el.classList.toggle('hidden', !isDark));
    document.querySelectorAll('.sb-sun').forEach(el  => el.classList.toggle('hidden',  isDark));
};

// ── Action buttons ────────────────────────────────────────────────────────
function setupActionBtns(html_download_url) {
    if (!html_download_url) return;
    const id = html_download_url.split('/').pop();
    UI.downloadBtn.href = `${API_BASE}/api/v1/download/${id}`;
    UI.viewBtn.href     = `${API_BASE}/api/v1/storyboard/${id}`;
    UI.downloadBtn.classList.remove('hidden');
    UI.viewBtn.classList.remove('hidden');
}

// ── Error display ─────────────────────────────────────────────────────────
function showError(msg) {
    UI.errorMsg.textContent = msg;
    UI.errorMsg.classList.remove('hidden');
}

// ── XSS-safe helper ───────────────────────────────────────────────────────
function escapeHTML(str) {
    if (typeof str !== 'string') return '';
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// ── Init ──────────────────────────────────────────────────────────────────
navigateTo('landing-page');
