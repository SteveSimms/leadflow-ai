let allLeads = [];
let currentFilter = 'all';
let config = {};

// ── Boot ──────────────────────────────────────────────────────────────────────
async function boot() {
  config = await fetch('/api/config').then(r => r.json());
  if (!config.city_x || !config.city_y) {
    document.getElementById('setup-modal').classList.remove('hidden');
  } else {
    updateCorridorBadge();
    await refreshAll();
  }
}

function updateCorridorBadge() {
  const el = document.getElementById('nav-corridor');
  if (config.city_x && config.city_y) {
    el.textContent = `📍 ${config.city_x} → ${config.city_y}`;
  }
}

async function refreshAll() {
  await Promise.all([loadStats(), loadLeads()]);
}

// ── Config ────────────────────────────────────────────────────────────────────
async function saveConfig() {
  const cfg = {
    agent_name: document.getElementById('cfg-agent-name').value,
    city_x: document.getElementById('cfg-city-x').value,
    city_y: document.getElementById('cfg-city-y').value,
    radius_miles: parseInt(document.getElementById('cfg-radius').value) || 15,
    claude_api_key: document.getElementById('cfg-api-key').value,
  };
  if (!cfg.city_x || !cfg.city_y) { alert('Please enter both cities.'); return; }
  await fetch('/api/config', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(cfg) });
  config = cfg;
  document.getElementById('setup-modal').classList.add('hidden');
  updateCorridorBadge();
  await refreshAll();
}

function openSettings() {
  document.getElementById('cfg-agent-name').value = config.agent_name || '';
  document.getElementById('cfg-city-x').value = config.city_x || '';
  document.getElementById('cfg-city-y').value = config.city_y || '';
  document.getElementById('cfg-radius').value = config.radius_miles || 15;
  document.getElementById('cfg-api-key').value = config.claude_api_key || '';
  document.getElementById('setup-modal').classList.remove('hidden');
}

// ── Stats ─────────────────────────────────────────────────────────────────────
async function loadStats() {
  const s = await fetch('/api/stats').then(r => r.json());
  document.getElementById('stat-hot').textContent = s.hot;
  document.getElementById('stat-warm').textContent = s.warm;
  document.getElementById('stat-total').textContent = s.total;
  document.getElementById('stat-contacted').textContent = s.contacted;
}

// ── Leads ─────────────────────────────────────────────────────────────────────
async function loadLeads() {
  allLeads = await fetch('/api/leads').then(r => r.json());
  renderLeads();
}

function filterLeads(filter, el) {
  currentFilter = filter;
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  el.classList.add('active');
  renderLeads();
}

function renderLeads() {
  const grid = document.getElementById('leads-grid');
  let leads = allLeads;
  if (currentFilter === 'hot') leads = leads.filter(l => l.score >= 7);
  else if (currentFilter === 'warm') leads = leads.filter(l => l.score >= 4 && l.score < 7);
  else if (currentFilter === 'contacted') leads = leads.filter(l => l.status === 'contacted');

  if (!leads.length) {
    grid.innerHTML = `<div class="empty-state"><div class="empty-icon">🔍</div><h3>No leads yet</h3><p>Click <strong>Scan for Leads</strong> to find motivated sellers in your corridor.</p></div>`;
    return;
  }
  grid.innerHTML = leads.map(lead => leadCard(lead)).join('');
}

function tier(score) {
  if (score >= 7) return 'hot';
  if (score >= 4) return 'warm';
  return 'cold';
}

function tierLabel(score) {
  if (score >= 7) return '🔥 Hot';
  if (score >= 4) return '🌤 Warm';
  return '❄️ Cold';
}

function leadCard(l) {
  const t = tier(l.score);
  const points = JSON.parse(l.talking_points || '[]');
  const tags = [l.source, l.timeline, l.approach, ...points.slice(0,1)].filter(Boolean);
  return `
  <div class="lead-card" onclick="openLead(${l.id})">
    <div class="score-bar ${t}"></div>
    <div class="lead-card-header">
      <div>
        <div class="lead-name">${l.name || 'Unknown'}</div>
        <div class="lead-city">${l.city || ''}</div>
      </div>
      <span class="score-badge ${t}">${tierLabel(l.score)} · ${l.score}/10</span>
    </div>
    <div class="lead-address">📍 ${l.address || 'Address not available'}</div>
    <div class="lead-tags">
      ${tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
    </div>
    <div class="lead-card-actions" onclick="event.stopPropagation()">
      <button class="btn-copy" onclick="copyEmail(${l.id})">📋 Copy Email</button>
      <button class="btn-copy" onclick="copySMS(${l.id})">💬 Copy SMS</button>
      ${l.status !== 'contacted' ? `<button class="btn-mark" onclick="markContacted(${l.id})">✅ Mark Contacted</button>` : '<span style="font-size:.8rem;color:var(--green);padding:7px">✅ Contacted</span>'}
    </div>
  </div>`;
}

// ── Lead Detail Modal ─────────────────────────────────────────────────────────
function openLead(id) {
  const l = allLeads.find(x => x.id === id);
  if (!l) return;
  const t = tier(l.score);
  const points = JSON.parse(l.talking_points || '[]');
  document.getElementById('lead-detail-content').innerHTML = `
    <h2 style="padding-right:30px">${l.name} <span class="score-badge ${t}" style="font-size:.85rem">${tierLabel(l.score)} · ${l.score}/10</span></h2>
    <p style="color:var(--text-muted);margin:6px 0 20px">📍 ${l.address}, ${l.city}</p>
    <div class="detail-section">
      <h4>Key Signals</h4>
      <div style="display:flex;gap:8px;flex-wrap:wrap">${points.map(p=>`<span class="tag">${p}</span>`).join('')||'<span class="tag">No signals detected</span>'}</div>
    </div>
    ${l.email_outreach ? `
    <div class="detail-section">
      <h4>✉️ Email Outreach (AI Generated)</h4>
      <div class="outreach-box" id="email-box-${l.id}">${l.email_outreach}</div>
      <div class="copy-btn-row"><button onclick="copyText('email-box-${l.id}','Email')">📋 Copy Email</button></div>
    </div>` : ''}
    ${l.sms_outreach ? `
    <div class="detail-section">
      <h4>💬 SMS (AI Generated)</h4>
      <div class="outreach-box" id="sms-box-${l.id}">${l.sms_outreach}</div>
      <div class="copy-btn-row"><button onclick="copyText('sms-box-${l.id}','SMS')">📋 Copy SMS</button></div>
    </div>` : ''}
    ${l.voicemail_outreach ? `
    <div class="detail-section">
      <h4>📞 Voicemail Script</h4>
      <div class="outreach-box" id="vm-box-${l.id}">${l.voicemail_outreach}</div>
      <div class="copy-btn-row"><button onclick="copyText('vm-box-${l.id}','Voicemail')">📋 Copy Script</button></div>
    </div>` : '<p style="color:var(--text-muted);font-size:.85rem;margin-top:12px">⚡ AI outreach is generated only for Hot leads (score ≥ 7). This lead scored ${l.score}/10.</p>'}
    <div style="display:flex;gap:10px;margin-top:20px">
      ${l.status !== 'contacted' ? `<button class="btn-mark" onclick="markContacted(${l.id});closeLeadModal()" style="flex:1;padding:12px">✅ Mark as Contacted</button>` : ''}
    </div>`;
  document.getElementById('lead-modal').classList.remove('hidden');
}

function closeLeadModal() {
  document.getElementById('lead-modal').classList.add('hidden');
}

// ── Actions ───────────────────────────────────────────────────────────────────
function copyText(elId, label) {
  const text = document.getElementById(elId).textContent;
  navigator.clipboard.writeText(text).then(() => showToast(`${label} copied!`));
}

function copyEmail(id) {
  const l = allLeads.find(x => x.id === id);
  if (!l?.email_outreach) { showToast('No email generated (lead score too low)'); return; }
  navigator.clipboard.writeText(l.email_outreach).then(() => showToast('Email copied!'));
}

function copySMS(id) {
  const l = allLeads.find(x => x.id === id);
  if (!l?.sms_outreach) { showToast('No SMS generated (lead score too low)'); return; }
  navigator.clipboard.writeText(l.sms_outreach).then(() => showToast('SMS copied!'));
}

async function markContacted(id) {
  await fetch(`/api/leads/${id}`, { method: 'PATCH', headers: {'Content-Type':'application/json'}, body: JSON.stringify({status:'contacted'}) });
  await refreshAll();
  showToast('Lead marked as contacted ✅');
}

async function startScan() {
  const btn = document.getElementById('scan-btn');
  const banner = document.getElementById('scan-banner');
  btn.textContent = '⏳ Scanning...';
  btn.classList.add('scanning');
  btn.disabled = true;
  banner.classList.remove('hidden');
  await fetch('/api/scan', { method: 'POST' });
  setTimeout(async () => {
    await refreshAll();
    btn.textContent = '🔍 Scan for Leads';
    btn.classList.remove('scanning');
    btn.disabled = false;
    banner.classList.add('hidden');
    showToast('Scan complete! New leads added.');
  }, 35000);
}

function showToast(msg) {
  const t = document.createElement('div');
  t.textContent = msg;
  Object.assign(t.style, {
    position:'fixed', bottom:'24px', right:'24px', background:'#22c55e',
    color:'#fff', padding:'12px 20px', borderRadius:'8px', fontWeight:'600',
    fontSize:'.9rem', zIndex:'9999', animation:'fadeIn .3s'
  });
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

document.getElementById('lead-modal').addEventListener('click', function(e) {
  if (e.target === this) closeLeadModal();
});

boot();
