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
    if (['graph', 'insights', 'simulate', 'voice', 'crew'].includes(id)) populateSelects();
    if (id === 'alerts') loadAlertsPage();
    if (id === 'voice') loadRecentCalls();
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
                    <button class="btn btn-small" onclick="showPage('insights');document.getElementById('insight-senior-select').value='${s.phone}'">Insights</button>
                    <button class="btn btn-small" onclick="showPage('voice');document.getElementById('voice-senior-select').value='${s.phone}'">Call</button></td>
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

// ── Interactive Graph View (vis.js) ──
const NODE_COLORS = {
    Senior: { background: '#2563eb', border: '#1d4ed8', font: { color: '#fff' } },
    Medication: { background: '#16a34a', border: '#15803d', font: { color: '#fff' } },
    Symptom: { background: '#dc2626', border: '#b91c1c', font: { color: '#fff' } },
    Condition: { background: '#7c3aed', border: '#6d28d9', font: { color: '#fff' } },
    FamilyMember: { background: '#d97706', border: '#b45309', font: { color: '#fff' } },
    Service: { background: '#0d9488', border: '#0f766e', font: { color: '#fff' } },
    CheckIn: { background: '#6366f1', border: '#4f46e5', font: { color: '#fff' } },
    Alert: { background: '#ef4444', border: '#dc2626', font: { color: '#fff' } },
};
const NODE_SHAPES = {
    Senior: 'circle', Medication: 'box', Symptom: 'diamond',
    Condition: 'triangle', FamilyMember: 'star', Service: 'hexagon',
    CheckIn: 'dot', Alert: 'square',
};

async function loadGraph() {
    const phone = document.getElementById('graph-senior-select').value;
    if (!phone) return;
    const container = document.getElementById('graph-container');
    container.innerHTML = '<p class="empty-state">Loading graph...</p>';
    try {
        const data = await fetchJSON(`/api/graph/care-network/${encodeURIComponent(phone)}`);
        if (!data.nodes.length) { container.innerHTML = '<p class="empty-state">No graph data</p>'; return; }

        document.getElementById('stat-nodes').textContent = data.nodes.length;

        const nodes = new vis.DataSet(data.nodes.map(n => ({
            id: n.id,
            label: n.label,
            shape: NODE_SHAPES[n.type] || 'dot',
            color: NODE_COLORS[n.type] || { background: '#6b7280', border: '#4b5563' },
            font: { color: '#fff', size: n.type === 'Senior' ? 16 : 13, bold: n.type === 'Senior' },
            size: n.type === 'Senior' ? 45 : 30,
            title: `${n.type}: ${n.label}`,
            margin: 10,
        })));

        const edges = new vis.DataSet(data.edges.map((e, i) => ({
            id: i,
            from: e.from,
            to: e.to,
            label: e.label,
            arrows: 'to',
            color: { color: '#9ca3af', highlight: '#2563eb' },
            font: { size: 10, color: '#6b7280', strokeWidth: 2, strokeColor: '#fff' },
        })));

        const options = {
            physics: {
                solver: 'forceAtlas2Based',
                forceAtlas2Based: { gravitationalConstant: -120, springLength: 250, springConstant: 0.02, damping: 0.4 },
                stabilization: { iterations: 200 },
            },
            interaction: { hover: true, tooltipDelay: 100, zoomView: true, dragView: true },
            layout: { improvedLayout: true },
            nodes: { font: { size: 14, face: '-apple-system, sans-serif' }, borderWidth: 2 },
            edges: { smooth: { type: 'continuous' }, length: 250 },
        };

        const network = new vis.Network(container, { nodes, edges }, options);
        network.once('stabilizationIterationsDone', () => {
            network.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
        });
    } catch(e) { container.innerHTML = `<p class="empty-state">Error: ${e.message}</p>`; }
}

// ── AI Insights ──
async function loadDrugInteractions() {
    const phone = document.getElementById('insight-senior-select').value;
    if (!phone) return;
    const el = document.getElementById('insights-content');
    el.innerHTML = '<p class="loading-text">Loading drug interactions...</p>';
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
    el.innerHTML = '<p class="loading-text">Checking side effects...</p>';
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
    el.innerHTML = '<p class="loading-text">Finding similar symptoms...</p>';
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
    el.innerHTML = '<p class="loading-text">Generating AI care recommendation...</p>';
    try {
        const data = await fetchJSON(`/api/graph/care-recommendation/${encodeURIComponent(phone)}`);
        el.innerHTML = `<h3>AI Care Plan for ${data.senior}</h3><div style="white-space:pre-wrap;line-height:1.6;">${data.recommendation || 'No recommendation available (set GMI_API_KEY in .env)'}</div>
        <h4 style="margin-top:1.5rem;">Graph Insights</h4><pre style="background:var(--gray-50);padding:1rem;border-radius:var(--radius);font-size:0.8rem;">${JSON.stringify(data.graph_insights, null, 2)}</pre>`;
    } catch(e) { el.innerHTML = `Error: ${e.message}`; }
}

// ── Voice Calls (Bland AI) ──
async function initiateCall() {
    const phone = document.getElementById('voice-senior-select').value;
    const voice = document.getElementById('voice-select').value;
    if (!phone) return alert('Select a senior first');
    const el = document.getElementById('voice-status');
    el.innerHTML = '<div class="status-card calling"><span class="pulse"></span> Initiating call...</div>';
    try {
        const data = await fetchJSON(`/api/voice/call/${encodeURIComponent(phone)}?voice=${voice}`, { method: 'POST' });
        if (data.status === 'error') {
            el.innerHTML = `<div class="status-card error"><strong>Call failed for ${data.senior}</strong><br>${data.message}<br><br><em>Note: Demo phone numbers (+1415555xxxx) are not real. Use a real phone number to test Bland AI calls.</em></div>`;
        } else {
            el.innerHTML = `<div class="status-card success">
                <strong>Call initiated!</strong><br>
                Senior: ${data.senior}<br>
                Call ID: <code>${data.call_id}</code><br>
                Status: ${data.message}
            </div>`;
            setTimeout(loadRecentCalls, 3000);
        }
    } catch(e) { el.innerHTML = `<div class="status-card error">Failed: ${e.message}</div>`; }
}

async function callAllSeniors() {
    if (!confirm('This will call ALL registered seniors. Continue?')) return;
    const voice = document.getElementById('voice-select').value;
    const el = document.getElementById('voice-status');
    el.innerHTML = '<div class="status-card calling"><span class="pulse"></span> Calling all seniors...</div>';
    try {
        const data = await fetchJSON(`/api/voice/call-all?voice=${voice}`, { method: 'POST' });
        el.innerHTML = `<div class="status-card success">
            <strong>${data.calls_initiated} calls initiated!</strong><br>
            ${data.results.map(r => `${r.senior}: ${r.status} (${r.call_id || 'N/A'})`).join('<br>')}
        </div>`;
        setTimeout(loadRecentCalls, 5000);
    } catch(e) { el.innerHTML = `<div class="status-card error">Failed: ${e.message}</div>`; }
}

async function loadRecentCalls() {
    const el = document.getElementById('voice-calls-list');
    const phone = document.getElementById('voice-senior-select').value;
    try {
        const data = await fetchJSON('/api/voice/calls?limit=10');
        const calls = data.calls || data;
        if (!calls || !calls.length) { el.innerHTML = '<p class="empty-state">No calls yet. Initiate a call above.</p>'; return; }
        el.innerHTML = calls.map(c => `<div class="call-card">
            <div class="call-header">
                <strong>${c.to || 'Unknown'}</strong>
                <span class="status-badge ${c.status === 'completed' ? 'good' : c.status === 'failed' ? 'danger' : 'neutral'}"><span class="dot"></span> ${c.status}</span>
            </div>
            <div class="call-meta">
                ${c.call_length ? `Duration: ${c.call_length} min` : ''}
                ${c.created_at ? ` | ${new Date(c.created_at).toLocaleString()}` : ''}
                ${c.call_id ? ` | ID: ${c.call_id}` : ''}
            </div>
            ${c.concatenated_transcript ? `<div class="call-summary"><strong>Transcript:</strong> ${c.concatenated_transcript.substring(0, 300)}${c.concatenated_transcript.length > 300 ? '...' : ''}</div>` : ''}
            ${c.summary ? `<div class="call-summary"><strong>Summary:</strong> ${c.summary}</div>` : ''}
            ${c.status === 'completed' && phone ? `<button class="btn btn-small btn-primary" onclick="processCall('${c.call_id}', '${phone}')" style="margin-top:0.5rem;">Save to Graph</button>` : ''}
        </div>`).join('');
    } catch(e) { el.innerHTML = '<p class="empty-state">Could not load calls. Is BLAND_API_KEY set?</p>'; }
}

async function processCall(callId, phone) {
    const el = document.getElementById('voice-status');
    el.innerHTML = '<div class="status-card calling"><span class="pulse"></span> Processing call into graph...</div>';
    try {
        const data = await fetchJSON(`/api/voice/process/${callId}?phone=${encodeURIComponent(phone)}`, { method: 'POST' });
        el.innerHTML = `<div class="status-card success">
            <strong>Call processed into Neo4j graph!</strong><br>
            Senior: ${data.senior}<br>
            Mood: ${data.analysis.mood} | Wellness: ${data.analysis.wellness_score}/10 | Meds: ${data.analysis.medication_taken === true ? 'Taken' : data.analysis.medication_taken === false ? 'Missed' : 'Unknown'}<br>
            ${data.analysis.concerns.length ? `Concerns: ${data.analysis.concerns.join(', ')}<br>` : ''}
            ${data.analysis.service_requests.length ? `Services: ${data.analysis.service_requests.map(r => r.label).join(', ')}<br>` : ''}
            Alerts generated: ${data.alerts_generated}
        </div>`;
        loadSeniors();
    } catch(e) { el.innerHTML = `<div class="status-card error">Failed: ${e.message}</div>`; }
}

// ── CrewAI Agents ──
function runCrewCheckin() {
    const phone = document.getElementById('crew-senior-select').value;
    if (!phone) return alert('Select a senior first');
    document.getElementById('crew-transcript-area').style.display = 'none';
    runCrew(`/api/crew/checkin/${encodeURIComponent(phone)}`, 'Full Check-in (5 Agents)');
}

function runCrewAnalyze() {
    const phone = document.getElementById('crew-senior-select').value;
    if (!phone) return alert('Select a senior first');
    document.getElementById('crew-transcript-area').style.display = 'block';
    const transcript = document.getElementById('crew-transcript').value || 'I feel a bit dizzy today. Yes I took my medications but my head hurts.';
    runCrew(`/api/crew/analyze/${encodeURIComponent(phone)}?transcript=${encodeURIComponent(transcript)}`, 'Analyze Transcript (4 Agents)');
}

function runCrewInsights() {
    const phone = document.getElementById('crew-senior-select').value;
    if (!phone) return alert('Select a senior first');
    document.getElementById('crew-transcript-area').style.display = 'none';
    runCrew(`/api/crew/insights/${encodeURIComponent(phone)}`, 'Graph Insights (2 Agents)');
}

async function runCrew(url, label) {
    const statusEl = document.getElementById('crew-status');
    const resultEl = document.getElementById('crew-result');
    statusEl.innerHTML = `<div class="status-card calling"><span class="pulse"></span> Running ${label}... This may take a minute.</div>`;
    resultEl.innerHTML = '';
    try {
        const data = await fetchJSON(url, { method: 'POST' });
        statusEl.innerHTML = `<div class="status-card success"><strong>${label} — Complete!</strong><br>Senior: ${data.senior} | Phone: ${data.phone}</div>`;
        resultEl.innerHTML = `<div class="crew-output"><h3>Crew Output</h3><pre>${typeof data.crew_output === 'string' ? data.crew_output : JSON.stringify(data, null, 2)}</pre></div>`;
        loadSeniors();
    } catch(e) {
        statusEl.innerHTML = `<div class="status-card error">Failed: ${e.message}</div>`;
    }
}

// ── Simulate Call ──
async function simulateCall() {
    const phone = document.getElementById('sim-senior-select').value;
    const transcript = document.getElementById('sim-transcript').value;
    if (!phone || !transcript) return alert('Select a senior and enter a transcript');
    const el = document.getElementById('sim-result');
    el.innerHTML = '<p class="loading-text">Processing...</p>';
    try {
        const data = await fetchJSON(`/api/checkins/simulate/${encodeURIComponent(phone)}?transcript=${encodeURIComponent(transcript)}`, { method: 'POST' });
        el.innerHTML = `<div class="sim-result-card">
            <h3>Check-in Result</h3>
            <div class="sim-grid">
                <div class="sim-item"><span class="sim-label">Mood</span><span class="status-badge ${data.analysis.mood === 'happy' ? 'good' : data.analysis.mood === 'concerning' ? 'danger' : data.analysis.mood === 'sad' ? 'warning' : 'neutral'}"><span class="dot"></span> ${data.analysis.mood}</span></div>
                <div class="sim-item"><span class="sim-label">Wellness</span><strong>${data.analysis.wellness_score}/10</strong></div>
                <div class="sim-item"><span class="sim-label">Medications</span><span>${data.analysis.medication_taken === true ? '✅ Taken' : data.analysis.medication_taken === false ? '❌ Missed' : '❓ Unknown'}</span></div>
                <div class="sim-item"><span class="sim-label">Alerts</span><strong>${data.alerts}</strong></div>
            </div>
            ${data.analysis.concerns.length ? `<div style="margin-top:1rem;"><strong>Concerns:</strong> ${data.analysis.concerns.join(', ')}</div>` : ''}
            ${data.analysis.service_requests.length ? `<div style="margin-top:0.5rem;"><strong>Service Needs:</strong> ${data.analysis.service_requests.map(r => r.label).join(', ')}</div>` : ''}
            <div style="margin-top:0.5rem;color:var(--gray-500);font-size:0.85rem;">${data.analysis.summary}</div>
        </div>`;
        loadSeniors();
    } catch(e) { el.innerHTML = `<div class="status-card error">Error: ${e.message}</div>`; }
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
        ['graph-senior-select', 'insight-senior-select', 'sim-senior-select', 'voice-senior-select', 'crew-senior-select'].forEach(id => {
            const sel = document.getElementById(id);
            if (!sel) return;
            const current = sel.value;
            sel.innerHTML = '<option value="">Select a senior...</option>' + seniors.map(s => `<option value="${s.phone}">${s.name}</option>`).join('');
            if (current) sel.value = current;
        });
    } catch(e) {}
}

document.addEventListener('DOMContentLoaded', () => { loadSeniors(); setInterval(loadSeniors, 15000); });
