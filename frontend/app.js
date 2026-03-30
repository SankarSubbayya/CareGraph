const AVATAR_COLORS = ['avatar-blue', 'avatar-green', 'avatar-orange', 'avatar-pink', 'avatar-teal'];

async function fetchJSON(url, opts = {}) {
    const resp = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
    if (!resp.ok) throw new Error(`API error: ${resp.status}`);
    return resp.json();
}
function getInitials(name) { return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2); }
function getColor(name) { let h = 0; for (const c of name) h = ((h << 5) - h) + c.charCodeAt(0); return AVATAR_COLORS[Math.abs(h) % AVATAR_COLORS.length]; }

// ── Page Navigation ──
function showPage(id) {
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.sidebar-item').forEach(i => i.classList.remove('active'));
    const page = document.getElementById('page-' + id);
    if (page) page.classList.add('active');
    document.querySelectorAll('.sidebar-item').forEach(i => { if (i.textContent.trim().toLowerCase().includes(id)) i.classList.add('active'); });
    if (id === 'graph' || id === 'insights' || id === 'simulate') populateSelects();
    if (id === 'alerts') loadAlertsPage();
}

// ── Seniors ──
async function loadSeniors() {
    try {
        const seniors = await fetchJSON('/api/seniors');
        let latest = [];
        try { latest = await fetchJSON('/api/checkins/latest/all'); } catch(e) {}
        const latestMap = {};
        latest.forEach(c => { latestMap[c.senior_phone] = c; });
        const alerts = await fetchJSON('/api/alerts');

        document.getElementById('stat-total').textContent = seniors.length;
        document.getElementById('stat-alerts').textContent = alerts.length;
        const scores = latest.filter(c => c.wellness_score > 0).map(c => c.wellness_score);
        document.getElementById('stat-avg').textContent = scores.length ? (scores.reduce((a,b)=>a+b,0)/scores.length).toFixed(1)+'/10' : '—';

        const tbody = document.getElementById('seniors-tbody');
        if (!seniors.length) { tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No seniors. Click "+ Add Senior".</td></tr>'; return; }
        tbody.innerHTML = seniors.map(s => {
            const l = latestMap[s.phone];
            const mood = l?.mood || 'unknown';
            let sc = mood === 'concerning' ? 'danger' : mood === 'sad' ? 'warning' : l ? 'good' : 'neutral';
            let st = mood === 'concerning' ? 'Concerning' : mood === 'sad' ? 'Needs attention' : l ? 'OK' : 'Pending';
            const score = l?.wellness_score || '—';
            return `<tr>
                <td><div class="name-cell"><div class="avatar ${getColor(s.name)}">${getInitials(s.name)}</div><div class="name-info"><div class="name">${s.name}</div><div class="phone">${s.phone}</div></div></div></td>
                <td><span class="status-badge ${sc}"><span class="dot"></span> ${st}</span></td>
                <td>${score === '—' ? '—' : score+'/10'}</td>
                <td style="max-width:200px;font-size:0.85rem;">${s.medications.join(', ') || '—'}</td>
                <td><button class="btn btn-small" onclick="showPage('graph');document.getElementById('graph-senior-select').value='${s.phone}';loadGraph()">Graph</button>
                    <button class="btn btn-small" onclick="showPage('insights');document.getElementById('insight-senior-select').value='${s.phone}'">Insights</button></td>
            </tr>`;
        }).join('');

        // Alert banner
        const banner = document.getElementById('alerts-banner');
        const badge = document.getElementById('alert-badge');
        if (alerts.length) {
            banner.style.display = 'block'; badge.style.display = 'inline'; badge.textContent = alerts.length;
            document.getElementById('alerts-banner-content').innerHTML = alerts.slice(0,3).map(a =>
                `<div style="display:flex;align-items:center;gap:0.5rem;padding:0.3rem 0;"><span class="severity ${a.severity}">${a.severity}</span><span>${a.message}</span></div>`
            ).join('');
        } else { banner.style.display = 'none'; badge.style.display = 'none'; }
    } catch(e) { console.error(e); document.getElementById('seniors-tbody').innerHTML = '<tr><td colspan="5" class="empty-state">Failed to load. Is the server running?</td></tr>'; }
}

// ── Graph View ──
async function loadGraph() {
    const phone = document.getElementById('graph-senior-select').value;
    if (!phone) return;
    try {
        const data = await fetchJSON(`/api/graph/care-network/${encodeURIComponent(phone)}`);
        const container = document.getElementById('graph-container');
        if (!data.nodes.length) { container.innerHTML = '<p class="empty-state">No graph data</p>'; return; }
        let html = '<div style="margin-bottom:1rem;"><strong>Nodes:</strong></div><div>';
        data.nodes.forEach(n => { html += `<span class="graph-node ${n.type}">${n.type === 'Senior' ? '👴' : n.type === 'Medication' ? '💊' : n.type === 'Symptom' ? '🔴' : n.type === 'FamilyMember' ? '👨‍👩‍👧' : '📋'} ${n.label}</span>`; });
        html += '</div><div style="margin-top:1.5rem;"><strong>Relationships:</strong></div><div style="margin-top:0.5rem;">';
        data.edges.forEach(e => {
            const fromNode = data.nodes.find(n => n.id === e.from);
            const toNode = data.nodes.find(n => n.id === e.to);
            html += `<div style="font-size:0.85rem;padding:0.2rem 0;">${fromNode?.label || e.from} <span class="graph-edge">—[${e.label}]→</span> ${toNode?.label || e.to}</div>`;
        });
        html += '</div>';
        container.innerHTML = html;

        // Update node count
        document.getElementById('stat-nodes').textContent = data.nodes.length;
    } catch(e) { document.getElementById('graph-container').innerHTML = `<p class="empty-state">Error: ${e.message}</p>`; }
}

// ── AI Insights ──
async function loadDrugInteractions() {
    const phone = document.getElementById('insight-senior-select').value;
    if (!phone) return;
    const el = document.getElementById('insights-content');
    el.innerHTML = 'Loading drug interactions...';
    try {
        const data = await fetchJSON(`/api/graph/drug-interactions/${encodeURIComponent(phone)}`);
        if (!data.interactions.length) { el.innerHTML = '<p>No drug interactions detected.</p>'; return; }
        el.innerHTML = '<h3>Drug Interactions</h3>' + data.interactions.map(i =>
            `<div class="alert-card medium"><div style="flex:1"><strong>${i.drug1} ↔ ${i.drug2}</strong>${i.ai_explanation ? `<p style="margin-top:0.5rem;">${i.ai_explanation}</p>` : ''}</div></div>`
        ).join('');
    } catch(e) { el.innerHTML = `Error: ${e.message}`; }
}

async function loadSideEffects() {
    const phone = document.getElementById('insight-senior-select').value;
    if (!phone) return;
    const el = document.getElementById('insights-content');
    el.innerHTML = 'Checking side effects...';
    try {
        const data = await fetchJSON(`/api/graph/side-effects/${encodeURIComponent(phone)}`);
        if (!data.side_effects.length) { el.innerHTML = '<p>No side effect matches found.</p>'; return; }
        el.innerHTML = '<h3>Possible Side Effects</h3>' + data.side_effects.map(s =>
            `<div class="alert-card high"><div style="flex:1"><strong>${s.medication} → ${s.symptom}</strong><p>${s.insight}</p></div></div>`
        ).join('');
    } catch(e) { el.innerHTML = `Error: ${e.message}`; }
}

async function loadSimilarSymptoms() {
    const phone = document.getElementById('insight-senior-select').value;
    if (!phone) return;
    const el = document.getElementById('insights-content');
    el.innerHTML = 'Finding similar symptoms...';
    try {
        const data = await fetchJSON(`/api/graph/similar-symptoms/${encodeURIComponent(phone)}`);
        if (!data.similar.length) { el.innerHTML = '<p>No other seniors reported similar symptoms.</p>'; return; }
        el.innerHTML = '<h3>Seniors with Similar Symptoms</h3><table class="data-table"><thead><tr><th>Symptom</th><th>Other Senior</th></tr></thead><tbody>' +
            data.similar.map(s => `<tr><td>${s.symptom}</td><td>${s.other_senior}</td></tr>`).join('') + '</tbody></table>';
    } catch(e) { el.innerHTML = `Error: ${e.message}`; }
}

async function loadCareRec() {
    const phone = document.getElementById('insight-senior-select').value;
    if (!phone) return;
    const el = document.getElementById('insights-content');
    el.innerHTML = 'Generating AI care recommendation...';
    try {
        const data = await fetchJSON(`/api/graph/care-recommendation/${encodeURIComponent(phone)}`);
        el.innerHTML = `<h3>AI Care Plan for ${data.senior}</h3><div style="white-space:pre-wrap;line-height:1.6;">${data.recommendation || 'No recommendation available (RocketRide API key needed)'}</div>
        <h4 style="margin-top:1.5rem;">Graph Insights</h4><pre style="background:var(--gray-50);padding:1rem;border-radius:var(--radius);font-size:0.8rem;">${JSON.stringify(data.graph_insights, null, 2)}</pre>`;
    } catch(e) { el.innerHTML = `Error: ${e.message}`; }
}

// ── Simulate Call ──
async function simulateCall() {
    const phone = document.getElementById('sim-senior-select').value;
    const transcript = document.getElementById('sim-transcript').value;
    if (!phone || !transcript) return alert('Select a senior and enter a transcript');
    const el = document.getElementById('sim-result');
    el.textContent = 'Processing...';
    try {
        const data = await fetchJSON(`/api/checkins/simulate/${encodeURIComponent(phone)}?transcript=${encodeURIComponent(transcript)}`, { method: 'POST' });
        el.textContent = JSON.stringify(data, null, 2);
        loadSeniors();
    } catch(e) { el.textContent = `Error: ${e.message}`; }
}

// ── Add Senior ──
function showAddModal() { document.getElementById('add-modal').style.display = 'flex'; }
function closeModal() { document.getElementById('add-modal').style.display = 'none'; }
async function addSenior(e) {
    e.preventDefault();
    const senior = {
        name: document.getElementById('s-name').value,
        phone: document.getElementById('s-phone').value,
        medications: document.getElementById('s-meds').value.split(',').map(m => m.trim()).filter(Boolean),
        checkin_schedule: document.getElementById('s-schedule').value,
        notes: document.getElementById('s-notes').value,
        emergency_contacts: [],
    };
    try { await fetchJSON('/api/seniors', { method: 'POST', body: JSON.stringify(senior) }); closeModal(); document.getElementById('add-form').reset(); loadSeniors(); } catch(e) { alert('Error: ' + e.message); }
}

// ── Alerts Page ──
async function loadAlertsPage() {
    try {
        const alerts = await fetchJSON('/api/alerts?acknowledged=true');
        const el = document.getElementById('alerts-full-list');
        if (!alerts.length) { el.innerHTML = '<p class="empty-state">No alerts.</p>'; return; }
        el.innerHTML = alerts.map(a => `<div class="alert-card ${a.severity}"><div style="flex:1;"><span class="severity ${a.severity}">${a.severity}</span> <strong>${a.alert_type.replace(/_/g,' ')}</strong><div style="margin-top:0.25rem;">${a.message}</div><div style="font-size:0.75rem;color:var(--gray-500);margin-top:0.25rem;">${new Date(a.timestamp).toLocaleString()}</div></div>${!a.acknowledged ? `<button class="btn btn-small" onclick="ackAlert('${a.id}')">Acknowledge</button>` : ''}</div>`).join('');
    } catch(e) { console.error(e); }
}
async function ackAlert(id) { await fetchJSON(`/api/alerts/${encodeURIComponent(id)}/acknowledge`, { method: 'PUT' }); loadAlertsPage(); loadSeniors(); }

// ── Helpers ──
async function populateSelects() {
    try {
        const seniors = await fetchJSON('/api/seniors');
        ['graph-senior-select', 'insight-senior-select', 'sim-senior-select'].forEach(id => {
            const sel = document.getElementById(id);
            if (!sel) return;
            const current = sel.value;
            sel.innerHTML = '<option value="">Select a senior...</option>' + seniors.map(s => `<option value="${s.phone}">${s.name}</option>`).join('');
            if (current) sel.value = current;
        });
    } catch(e) {}
}

document.addEventListener('DOMContentLoaded', () => { loadSeniors(); setInterval(loadSeniors, 15000); });
