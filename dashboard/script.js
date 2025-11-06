const API_BASE = window.location.origin; // assumes dashboard served from same server as API
const REFRESH_INTERVAL = 5000; // 5s
let timer = null;

function el(id){ return document.getElementById(id); }

async function fetchLogs(){
  try{
    el('status').textContent = 'Fetching...';
    const resp = await fetch(API_BASE + '/logs');
    if(!resp.ok) throw new Error('HTTP ' + resp.status);
    const data = await resp.json();
    renderTable(data);
    el('status').textContent = 'Last: ' + new Date().toLocaleTimeString();
  }catch(err){
    el('status').textContent = 'Error: ' + err.message;
  }
}

function renderTable(rows){
  const tbody = document.querySelector('#logsTable tbody');
  tbody.innerHTML = '';
  rows.forEach(r => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${escapeHtml(r.id)}</td>
      <td>${escapeHtml(r.timestamp)}</td>
      <td>${escapeHtml(r.event_type)}</td>
      <td>${escapeHtml(r.path)}</td>
      <td><code>${escapeHtml(r.old_hash || '')}</code></td>
      <td><code>${escapeHtml(r.new_hash || '')}</code></td>
    `;
    tbody.appendChild(tr);
  });
}

function escapeHtml(s){
  if(s === null || s === undefined) return '';
  return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[c]);
}

function exportCSV(){
  const rows = Array.from(document.querySelectorAll('#logsTable tr')).map(tr =>
    Array.from(tr.querySelectorAll('th,td')).map(td => '"' + td.textContent.replace(/"/g, '""') + '"')
  );
  const csv = rows.map(r => r.join(',')).join('\n');
  const blob = new Blob([csv], {type: 'text/csv'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'integrity_logs.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

el('refreshBtn').addEventListener('click', fetchLogs);
el('exportBtn').addEventListener('click', exportCSV);

// auto-refresh
fetchLogs();
if(timer) clearInterval(timer);
timer = setInterval(fetchLogs, REFRESH_INTERVAL);
