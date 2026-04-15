const API_BASE = window.API_BASE || 'http://localhost:8000';

const UI = {
    btn:        document.getElementById('generate-btn'),
    btnText:    document.querySelector('.btn-text'),
    spinner:    document.getElementById('loading-spinner'),
    text:       document.getElementById('pitch-text'),
    style:      document.getElementById('style-select'),
    container:  document.getElementById('storyboard-container'),
    error:      document.getElementById('error-message'),
    section:    document.getElementById('storyboard-section'),
    downloadBtn: document.getElementById('download-btn'),
};

UI.btn.addEventListener('click', async () => {
    const pitchText = UI.text.value.trim();
    if (!pitchText) { showError('Please enter a pitch.'); return; }

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
        renderPanels(data.panels);
        setupDownload(data.html_download_url);

    } catch (err) {
        console.error(err);
        showError('Generation failed: ' + err.message);
    } finally {
        setLoading(false);
    }
});

function renderPanels(panels) {
    UI.section.classList.remove('hidden');
    UI.container.innerHTML = '';

    panels.forEach(panel => {
        const card = document.createElement('div');
        card.className = 'panel-card';
        card.innerHTML = `
            <div class="panel-image-container">
                <div class="panel-number">Scene ${panel.scene_number}</div>
                <img src="${panel.image_url}" alt="${panel.frame.title}" class="panel-image" loading="lazy"/>
            </div>
            <div class="panel-content">
                <h3 class="panel-title">${panel.frame.title}</h3>
                <p class="panel-caption">${panel.caption}</p>
                <div class="panel-meta">
                    <span class="tag tag-emotion">😶 ${panel.frame.emotion}</span>
                    <span class="tag tag-tone">🎭 ${panel.frame.tone}</span>
                </div>
                <details class="prompt-details">
                    <summary>🎨 Visual Prompt</summary>
                    <p class="prompt-text">${panel.enriched_prompt}</p>
                </details>
            </div>
        `;
        UI.container.appendChild(card);
    });
}

function setupDownload(html_download_url) {
    UI.downloadBtn.href = `${API_BASE}${html_download_url}`;
    UI.downloadBtn.classList.remove('hidden');
}

function setLoading(isLoading) {
    UI.btn.disabled = isLoading;
    UI.btnText.textContent = isLoading ? 'Generating...' : 'Generate Storyboard';
    UI.spinner.classList.toggle('hidden', !isLoading);
}

function showError(msg) {
    UI.error.textContent = msg;
    UI.error.classList.remove('hidden');
}

function clearResults() {
    UI.error.classList.add('hidden');
    UI.container.innerHTML = '';
    UI.section.classList.add('hidden');
    UI.downloadBtn.classList.add('hidden');
}
