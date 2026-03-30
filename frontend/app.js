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
    if (['graph', 'insights', 'simulate', 'voice', 'crew', 'reasoning'].includes(id)) populateSelects();
    if (id === 'alerts') loadAlertsPage();
    if (id === 'voice') loadRecentCalls();
}

// ── Contact lookup map (keyed by senior phone) ──
const _contactMap = {};

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
        if (!seniors.length) { tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No seniors. Click "+ Add Senior".</td></tr>'; return; }
        tbody.innerHTML = seniors.map(s => {
            const l = latestMap[s.phone];
            const mood = l?.mood || 'unknown';
            let sc = mood === 'concerning' ? 'danger' : mood === 'sad' ? 'warning' : l ? 'good' : 'neutral';
            let st = mood === 'concerning' ? 'Concerning' : mood === 'sad' ? 'Needs attention' : l ? 'OK' : 'Pending';
            const score = l?.wellness_score || '—';
            const fc = (s.emergency_contacts && s.emergency_contacts[0]) ? s.emergency_contacts[0] : null;
            if (fc) _contactMap[s.phone] = { ...fc, seniorName: s.name };
            const safeKey = s.phone.replace(/'/g, "\\'");
            const contactHtml = (fc && fc.phone)
                ? `<button class="btn-contact-link" onclick="showContactDetails('${safeKey}')">${(fc.name || 'Family contact').replace(/</g, '&lt;')}</button>`
                : '<span style="color:var(--gray-400);font-size:0.85rem;">—</span>';
            return `<tr>
                <td><div class="name-cell"><div class="avatar ${getColor(s.name)}">${getInitials(s.name)}</div><div class="name-info"><div class="name">${s.name}</div><div class="phone">${s.phone}</div></div></div></td>
                <td><span class="status-badge ${sc}"><span class="dot"></span> ${st}</span></td>
                <td>${score === '—' ? '—' : score+'/10'}</td>
                <td>${contactHtml}</td>
                <td style="max-width:200px;font-size:0.85rem;">${s.medications.join(', ') || '—'}</td>
                <td><button class="btn btn-small" onclick="goToPage('graph', '${safeKey}')">Graph</button>
                    <button class="btn btn-small" onclick="goToPage('insights', '${safeKey}')">Insights</button>
                    <button class="btn btn-small" onclick="goToPage('voice', '${safeKey}')">Call</button></td>
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
    } catch(e) { console.error(e); document.getElementById('seniors-tbody').innerHTML = '<tr><td colspan="6" class="empty-state">Failed to load. Is the server running?</td></tr>'; }
}

// ── Contact Details Modal ──
function showContactDetails(seniorPhone) {
    const fc = _contactMap[seniorPhone] || {};
    const seniorNameEl = document.getElementById('contact-modal-senior-name');
    if (seniorNameEl) seniorNameEl.textContent = fc.seniorName || 'this senior';
    document.getElementById('contact-modal-name').textContent = fc.name || 'Family Contact';
    document.getElementById('contact-modal-phone').textContent = fc.phone || '—';
    document.getElementById('contact-modal-relation').textContent = fc.relation || fc.relationship || '—';
    const callBtn = document.getElementById('contact-modal-call');
    callBtn.href = fc.phone ? `tel:${String(fc.phone).replace(/\s/g, '')}` : '#';
    callBtn.style.display = fc.phone ? 'inline-flex' : 'none';
    document.getElementById('contact-modal').style.display = 'flex';
}
function closeContactModal() { document.getElementById('contact-modal').style.display = 'none'; }

// ── Navigate to page and pre-select a senior ──
async function goToPage(page, phone) {
    showPage(page);
    const selectMap = {
        graph: 'graph-senior-select',
        insights: 'insight-senior-select',
        voice: 'voice-senior-select',
    };
    const selId = selectMap[page];
    if (!selId) return;
    try {
        const seniors = await fetchJSON('/api/seniors');
        const sel = document.getElementById(selId);
        if (!sel) return;
        sel.innerHTML = '<option value="">Select a senior...</option>' +
            seniors.map(s => `<option value="${s.phone}">${s.name}</option>`).join('');
        sel.value = phone;
    } catch(e) {}
    if (page === 'graph') loadGraph();
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
    Doctor: { background: '#0891b2', border: '#0e7490', font: { color: '#fff' } },
    Clinic: { background: '#be185d', border: '#9d174d', font: { color: '#fff' } },
};
const NODE_SHAPES = {
    Senior: 'circle', Medication: 'box', Symptom: 'diamond',
    Condition: 'triangle', FamilyMember: 'star', Service: 'hexagon',
    CheckIn: 'dot', Alert: 'square', Doctor: 'box', Clinic: 'hexagon',
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

async function loadDoctorsGraph() {
    const phone = document.getElementById('graph-senior-select').value;
    if (!phone) return;
    const container = document.getElementById('graph-container');
    container.innerHTML = '<p class="empty-state">Loading doctors network...</p>';
    try {
        const data = await fetchJSON(`/api/graph/doctors-network/${encodeURIComponent(phone)}`);
        if (!data.nodes.length) { container.innerHTML = '<p class="empty-state">No doctors linked to this senior\'s conditions yet.</p>'; return; }

        const nodes = new vis.DataSet(data.nodes.map(n => ({
            id: n.id,
            label: n.label,
            shape: NODE_SHAPES[n.type] || 'dot',
            color: NODE_COLORS[n.type] || { background: '#6b7280', border: '#4b5563' },
            font: { color: '#fff', size: n.type === 'Senior' ? 16 : n.type === 'Doctor' ? 12 : 13, bold: n.type === 'Senior' },
            size: n.type === 'Senior' ? 45 : n.type === 'Doctor' ? 28 : n.type === 'Clinic' ? 25 : 30,
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
                forceAtlas2Based: { gravitationalConstant: -80, springLength: 200, springConstant: 0.02, damping: 0.4 },
                stabilization: { iterations: 200 },
            },
            interaction: { hover: true, tooltipDelay: 100, zoomView: true, dragView: true },
            layout: { improvedLayout: true },
            nodes: { font: { size: 12, face: '-apple-system, sans-serif' }, borderWidth: 2 },
            edges: { smooth: { type: 'continuous' }, length: 200 },
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
            ${data.alert_details && data.alert_details.length ? `
                <div class="notify-section">
                    <h4>Alerts & Family Notifications</h4>
                    ${data.alert_details.map(a => `
                        <div class="notify-card ${a.severity}">
                            <span class="severity ${a.severity}">${a.severity}</span>
                            <span>${a.message}</span>
                            ${a.notify && a.notify.length ? `<div class="notify-target">📱 Notifying: ${a.notify.map(c => `${c.name} (${c.relation}) — ${c.phone}`).join(', ')}</div>` : '<div class="notify-target">📋 Dashboard only</div>'}
                        </div>
                    `).join('')}
                </div>` : ''}
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
        ['graph-senior-select', 'insight-senior-select', 'sim-senior-select', 'voice-senior-select', 'crew-senior-select', 'reasoning-senior-select'].forEach(id => {
            const sel = document.getElementById(id);
            if (!sel) return;
            const current = sel.value;
            sel.innerHTML = '<option value="">Select a senior...</option>' + seniors.map(s => `<option value="${s.phone}">${s.name}</option>`).join('');
            if (current) sel.value = current;
        });
    } catch(e) {}
}

// ── Graph Reasoning Walkthrough ──
let reasoningNetwork = null;

async function startReasoning() {
    const phone = document.getElementById('reasoning-senior-select').value;
    if (!phone) return alert('Select a senior first');

    const stepsEl = document.getElementById('reasoning-steps');
    const graphEl = document.getElementById('reasoning-graph');
    graphEl.innerHTML = '';

    // Define steps
    const steps = [
        { title: 'Look up Senior in Neo4j', icon: '👴', query: 'MATCH (s:Senior {phone: $phone}) RETURN s' },
        { title: 'Find Reported Symptoms', icon: '🔴', query: 'MATCH (s:Senior)-[:REPORTED]->(sy:Symptom) RETURN sy' },
        { title: 'Match Medication Side Effects', icon: '💊', query: 'MATCH (s)-[:TAKES]->(m)-[:SIDE_EFFECT]->(sy)<-[:REPORTED]-(s) RETURN m, sy' },
        { title: 'Detect Drug Interactions', icon: '⚠️', query: 'MATCH (m1)-[:INTERACTS_WITH]->(m2) WHERE (s)-[:TAKES]->(m1) RETURN m1, m2' },
        { title: 'Suggest Conditions from Symptoms', icon: '🏥', query: 'MATCH (sy:Symptom)-[:SUGGESTS]->(c:Condition) RETURN sy, c' },
        { title: 'Recommend Matching Doctors', icon: '👨‍⚕️', query: 'MATCH (c:Condition)<-[:CAN_TREAT]-(d:Doctor) RETURN d' },
    ];

    // Render step cards (all dimmed)
    stepsEl.innerHTML = steps.map((s, i) => `
        <div class="reasoning-step" id="rstep-${i}">
            <div class="step-number">${i + 1}</div>
            <div class="step-content">
                <h3>${s.icon} ${s.title}</h3>
                <code class="step-query">${s.query}</code>
                <p id="rstep-result-${i}"></p>
            </div>
        </div>
    `).join('');

    // Fetch all data
    let senior, sideEffects, interactions, doctors, careNetwork;
    try {
        [senior, sideEffects, interactions, doctors, careNetwork] = await Promise.all([
            fetchJSON(`/api/seniors/${encodeURIComponent(phone)}`),
            fetchJSON(`/api/graph/side-effects/${encodeURIComponent(phone)}`),
            fetchJSON(`/api/graph/drug-interactions/${encodeURIComponent(phone)}`),
            fetchJSON(`/api/graph/doctors/for-senior/${encodeURIComponent(phone)}`),
            fetchJSON(`/api/graph/care-network/${encodeURIComponent(phone)}`),
        ]);
    } catch(e) {
        stepsEl.innerHTML = `<p class="empty-state">Error loading data: ${e.message}</p>`;
        return;
    }

    const symptoms = careNetwork.nodes.filter(n => n.type === 'Symptom').map(n => n.label);
    const conditions = careNetwork.nodes.filter(n => n.type === 'Condition').map(n => n.label);

    // Animate steps
    const results = [
        `<span class="step-result">Found: ${senior.name} — takes ${senior.medications.join(', ')}</span>`,
        `<span class="step-result">Symptoms: ${symptoms.length ? symptoms.join(', ') : 'none reported'}</span>`,
        `<span class="step-result">${sideEffects.side_effects.length ? sideEffects.side_effects.map(s => `${s.medication} → ${s.symptom}`).join(', ') : 'No side effect matches'}</span>`,
        `<span class="step-result">${interactions.interactions.length ? interactions.interactions.map(i => `${i.drug1} ↔ ${i.drug2}`).join(', ') : 'No interactions'}</span>`,
        `<span class="step-result">${conditions.length ? conditions.join(', ') : 'No conditions suggested'}</span>`,
        `<span class="step-result">${doctors.recommended_doctors.length ? doctors.recommended_doctors.slice(0, 3).map(d => `${d.name} (${d.specialty})`).join(', ') : 'No doctors matched'}</span>`,
    ];

    for (let i = 0; i < steps.length; i++) {
        const el = document.getElementById(`rstep-${i}`);
        el.classList.add('active');
        el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        await new Promise(r => setTimeout(r, 800));
        document.getElementById(`rstep-result-${i}`).innerHTML = results[i];
        el.classList.remove('active');
        el.classList.add('done');
        await new Promise(r => setTimeout(r, 700));
    }

    // Build reasoning chain graph
    const nodes = [];
    const edges = [];
    const seen = new Set();

    function addNode(id, label, type) {
        if (!seen.has(id)) { seen.add(id); nodes.push({ id, label, shape: NODE_SHAPES[type] || 'dot', color: NODE_COLORS[type] || {background:'#6b7280',border:'#4b5563'}, font: {color:'#fff', size: 12}, size: type === 'Senior' ? 40 : 28, title: `${type}: ${label}` }); }
    }

    addNode('senior', senior.name, 'Senior');
    senior.medications.forEach(m => { addNode(`med_${m}`, m, 'Medication'); edges.push({from:'senior',to:`med_${m}`,label:'TAKES',arrows:'to',color:{color:'#9ca3af'},font:{size:9,color:'#6b7280',strokeWidth:2,strokeColor:'#fff'}}); });
    symptoms.forEach(s => { addNode(`sym_${s}`, s, 'Symptom'); edges.push({from:'senior',to:`sym_${s}`,label:'REPORTED',arrows:'to',color:{color:'#9ca3af'},font:{size:9,color:'#6b7280',strokeWidth:2,strokeColor:'#fff'}}); });
    sideEffects.side_effects.forEach(se => { if(seen.has(`med_${se.medication}`)&&seen.has(`sym_${se.symptom}`)) edges.push({from:`med_${se.medication}`,to:`sym_${se.symptom}`,label:'SIDE_EFFECT',arrows:'to',color:{color:'#ef4444'},font:{size:9,color:'#ef4444',strokeWidth:2,strokeColor:'#fff'},width:3}); });
    conditions.forEach(c => { addNode(`cond_${c}`, c, 'Condition'); });
    careNetwork.edges.filter(e => e.label === 'SUGGESTS').forEach(e => { const symNode = careNetwork.nodes.find(n=>n.id===e.from); const condNode = careNetwork.nodes.find(n=>n.id===e.to); if(symNode&&condNode&&seen.has(`sym_${symNode.label}`)&&seen.has(`cond_${condNode.label}`)) edges.push({from:`sym_${symNode.label}`,to:`cond_${condNode.label}`,label:'SUGGESTS',arrows:'to',color:{color:'#7c3aed'},font:{size:9,color:'#7c3aed',strokeWidth:2,strokeColor:'#fff'},width:2}); });
    doctors.recommended_doctors.slice(0, 5).forEach(d => { addNode(`doc_${d.name}`, d.name, 'Doctor'); (d.conditions||[]).forEach(c => { if(seen.has(`cond_${c}`)) edges.push({from:`doc_${d.name}`,to:`cond_${c}`,label:'CAN_TREAT',arrows:'to',color:{color:'#0891b2'},font:{size:9,color:'#0891b2',strokeWidth:2,strokeColor:'#fff'},width:2}); }); });

    const options = { physics: { solver:'forceAtlas2Based', forceAtlas2Based:{gravitationalConstant:-80,springLength:180}, stabilization:{iterations:150} }, interaction:{hover:true}, nodes:{borderWidth:2}, edges:{smooth:{type:'continuous'}} };
    reasoningNetwork = new vis.Network(graphEl, { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) }, options);
    reasoningNetwork.once('stabilizationIterationsDone', () => { reasoningNetwork.fit({animation:{duration:500}}); });
}

function resetReasoning() {
    document.getElementById('reasoning-steps').innerHTML = '<p class="empty-state">Select a senior and click "Start Walkthrough" to see how Neo4j reasons through the care graph.</p>';
    document.getElementById('reasoning-graph').innerHTML = '';
}

// ── Demo Mode ──
let demoRunning = false;

async function runDemoMode() {
    if (demoRunning) return;
    demoRunning = true;
    const overlay = document.getElementById('demo-overlay');
    const title = document.getElementById('demo-step-title');
    const desc = document.getElementById('demo-step-desc');
    const bar = document.getElementById('demo-bar');
    overlay.style.display = 'flex';

    const steps = [
        { page: 'seniors', title: 'Dashboard Overview', desc: 'Showing all registered seniors, wellness scores, and active alerts.', pct: 15 },
        { page: 'graph', title: 'Care Network Graph', desc: 'Loading Dorothy Williams care network — medications, symptoms, family.', pct: 30, action: async () => { document.getElementById('graph-senior-select').value = '+14155551003'; await loadGraph(); } },
        { page: 'graph', title: 'Doctors Network', desc: 'Switching to doctors view — symptoms → conditions → 110+ doctors → clinics.', pct: 45, action: async () => { await loadDoctorsGraph(); } },
        { page: 'insights', title: 'AI Drug Interactions', desc: 'Querying Neo4j for Margaret\'s drug interactions + Qwen3-235B explanations.', pct: 55, action: async () => { document.getElementById('insight-senior-select').value = '+14155551001'; await loadDrugInteractions(); } },
        { page: 'insights', title: 'AI Care Plan', desc: 'Generating personalized care plan with GMI Cloud (Qwen3-235B).', pct: 70, action: async () => { document.getElementById('insight-senior-select').value = '+14155551003'; await loadCareRec(); } },
        { page: 'simulate', title: 'Emergency Simulation', desc: 'Simulating: "I fell and feel dizzy. I forgot my medications. I need a doctor."', pct: 85, action: async () => { document.getElementById('sim-senior-select').value = '+14155551001'; document.getElementById('sim-transcript').value = 'I fell and feel dizzy. I forgot my medications. I need to see a doctor.'; await simulateCall(); } },
        { page: 'alerts', title: 'Alerts Dashboard', desc: 'Showing all triggered alerts — critical, high, and medium severity.', pct: 95 },
        { page: 'crew', title: 'CrewAI Agents', desc: 'Five AI agents ready: Check-in → Analysis → Graph → Recommendation → Alert.', pct: 100 },
    ];

    for (const step of steps) {
        if (!demoRunning) break;
        title.textContent = step.title;
        desc.textContent = step.desc;
        bar.style.width = step.pct + '%';
        showPage(step.page);
        await populateSelects();
        if (step.action) await step.action();
        await new Promise(r => setTimeout(r, 4000));
    }

    bar.style.width = '100%';
    demoRunning = false;
    overlay.style.display = 'none';
}

function stopDemo() {
    demoRunning = false;
    document.getElementById('demo-overlay').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => { loadSeniors(); setInterval(loadSeniors, 15000); });
