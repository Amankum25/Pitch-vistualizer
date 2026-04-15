const API_BASE = window.API_BASE || 'http://localhost:8000';

const UI = {
    btn:         document.getElementById('generate-btn'),
    btnText:     document.querySelector('.btn-text'),
    spinner:     document.getElementById('loading-spinner'),
    text:        document.getElementById('pitch-text'),
    style:       document.getElementById('style-select'),
    container:   document.getElementById('storyboard-container'),
    error:       document.getElementById('error-message'),
    section:     document.getElementById('storyboard-section'),
    downloadBtn: document.getElementById('download-btn'),
    viewBtn:     document.getElementById('view-btn'),
    slideshow:   document.getElementById('slideshow-view'),
    slideImg:    document.getElementById('slide-img'),
    slideTitle:  document.getElementById('slide-title'),
    slideCaption:document.getElementById('slide-caption'),
    slideScene:  document.getElementById('slide-scene'),
    slideCounter:document.getElementById('slide-counter'),
    viewToggle:  document.getElementById('view-toggle-btn'),
};

let panels = [];
let currentIdx = 0;
let isSlideshow = false;

// ── Generate ──────────────────────────────────────────────────────────────
UI.btn.addEventListener('click', async () => {
    const pitchText = UI.text.value.trim();
    if (!pitchText) { showError('Please enter your pitch.'); return; }

    setLoading(true);
    clearResults();

    try {
        const res = await fetch(`${API_BASE}/api/v1/generate-storyboard`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: pitchText, style: UI.style.value }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Server error: ${res.status}`);
        }
        const data = await res.json();
        panels = data.panels;

        renderGrid(panels);
        setupActionBtns(data.html_download_url);
        UI.section.classList.remove('hidden');
    } catch (err) {
        console.error(err);
        showError('Generation failed: ' + err.message);
    } finally {
        setLoading(false);
    }
});

// ── Grid rendering ────────────────────────────────────────────────────────
function renderGrid(panels) {
    UI.container.innerHTML = '';
    panels.forEach((panel, i) => {
        const card = document.createElement('div');
        card.className = 'panel-card';
        card.onclick = () => openSlide(i);
        card.innerHTML = `
            <div class="panel-image-wrap">
                <div class="panel-number">Scene ${panel.scene_number}</div>
                <img src="${panel.image_url}" alt="${panel.frame.title}" class="panel-image" loading="lazy"/>
                <div class="panel-overlay">Click to view</div>
            </div>
            <div class="panel-content">
                <h3 class="panel-title">${panel.frame.title}</h3>
                <p class="panel-caption">${panel.caption}</p>
            </div>`;
        UI.container.appendChild(card);
    });
}

// ── Slideshow ─────────────────────────────────────────────────────────────
function renderSlide(idx) {
    const p = panels[idx];
    UI.slideImg.src            = p.image_url;
    UI.slideImg.alt            = p.frame.title;
    UI.slideTitle.textContent  = p.frame.title;
    UI.slideCaption.textContent= p.caption;
    UI.slideScene.textContent  = p.scene_text;
    UI.slideCounter.textContent= `${idx + 1} / ${panels.length}`;
}

function openSlide(idx) {
    currentIdx = idx;
    renderSlide(currentIdx);
    if (!isSlideshow) toggleView();
}

window.nextSlide = function() {
    currentIdx = (currentIdx + 1) % panels.length;
    renderSlide(currentIdx);
};

window.prevSlide = function() {
    currentIdx = (currentIdx - 1 + panels.length) % panels.length;
    renderSlide(currentIdx);
};

window.toggleView = function() {
    isSlideshow = !isSlideshow;
    UI.container.classList.toggle('hidden', isSlideshow);
    UI.slideshow.classList.toggle('hidden', !isSlideshow);
    UI.viewToggle.textContent = isSlideshow ? '⊞ Grid' : '▶ Slideshow';
    if (isSlideshow) renderSlide(currentIdx);
};

// ── Theme ────────────────────────────────────────────────────────────────
window.toggleTheme = function() {
    const root = document.documentElement;
    root.setAttribute('data-theme',
        root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark');
};

// ── Keyboard nav ─────────────────────────────────────────────────────────
document.addEventListener('keydown', (e) => {
    if (!isSlideshow || !panels.length) return;
    if (e.key === 'ArrowRight') nextSlide();
    if (e.key === 'ArrowLeft')  prevSlide();
    if (e.key === 'Escape')     toggleView();
});

// ── Helpers ───────────────────────────────────────────────────────────────
function setupActionBtns(html_download_url) {
    const id = html_download_url.split('/').pop();
    UI.downloadBtn.href = `${API_BASE}/api/v1/download/${id}`;
    UI.viewBtn.href     = `${API_BASE}/api/v1/storyboard/${id}`;
    UI.downloadBtn.classList.remove('hidden');
    UI.viewBtn.classList.remove('hidden');
}

function setLoading(on) {
    UI.btn.disabled          = on;
    UI.btnText.textContent   = on ? 'Generating...' : 'Generate Storyboard';
    UI.spinner.classList.toggle('hidden', !on);
}

function showError(msg) {
    UI.error.textContent = msg;
    UI.error.classList.remove('hidden');
}

function clearResults() {
    UI.error.classList.add('hidden');
    UI.container.innerHTML = '';
    UI.section.classList.add('hidden');
    UI.slideshow.classList.add('hidden');
    UI.downloadBtn.classList.add('hidden');
    UI.viewBtn.classList.add('hidden');
    isSlideshow = false;
    UI.viewToggle.textContent = '▶ Slideshow';
    UI.container.classList.remove('hidden');
}
