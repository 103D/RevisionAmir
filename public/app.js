// ============================================================
// RevisionAmir Schedule Dashboard — Read-Only Frontend
// ============================================================

const state = {
  page: 1,
  pageSize: 25,
  total: 0,
  search: '',
  sortField: 'event_date',
  sortOrder: 'asc',

  auditPage: 1,
  auditSize: 50,
  auditTotal: 0,
  auditFilter: '',

  sheetsConfigured: false,
};

const $ = (s, p = document) => p.querySelector(s);
const $$ = (s, p = document) => [...p.querySelectorAll(s)];

const itemsBody = $('#itemsBody');
const pageInfo = $('#pageInfo');
const pagePrev = $('#pagePrev');
const pageNext = $('#pageNext');
const pageSizeSelect = $('#pageSizeSelect');
const searchInput = $('#searchInput');
const searchClear = $('#searchClear');

const statusText = $('#statusText');
const statusDot = $('#statusDot');
const toastContainer = $('#toastContainer');
const themeSwitch = $('#themeSwitch');
const sidebar = $('#sidebar');
const overlay = $('#overlay');
const syncStatus = $('#syncStatus');

// Dashboard
const statsGrid = $('#statsGrid');
const statusChart = $('#statusChart');
const projectsChart = $('#projectsChart');

// Audit
const auditBody = $('#auditBody');
const auditPageInfo = $('#auditPageInfo');
const auditPagePrev = $('#auditPagePrev');
const auditPageNext = $('#auditPageNext');
const auditFilter = $('#auditFilter');
const refreshAuditBtn = $('#refreshAuditBtn');

// Export search card
const searchExportCard = $('#searchExportCard');

const numFmt = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 });
const fmtMoney = v => (v == null || v === '') ? '' : numFmt.format(Number(v));

// SVG icons for toasts
const icons = {
  success: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
  error: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
  warning: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
};

async function api(url, opts = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  if (res.status === 204) return null;
  const data = await res.json();
  if (!res.ok) throw new Error(data?.error?.message || data?.error || `HTTP ${res.status}`);
  return data;
}

function toast(msg, type = 'success') {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span class="toast-icon">${icons[type] || icons.success}</span> ${msg}`;
  toastContainer.appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(-10px)';
    setTimeout(() => el.remove(), 300);
  }, 3000);
}

function setStatus(online, text) {
  statusDot.className = `status-dot ${online ? 'online' : 'offline'}`;
  statusText.textContent = text;
}

function setSyncStatus(msg, isGood = true) {
  syncStatus.textContent = msg;
  syncStatus.style.color = isGood ? 'var(--success)' : 'var(--danger)';
  setTimeout(() => {
    syncStatus.textContent = 'Ожидание действий';
    syncStatus.style.color = 'var(--text-secondary)';
  }, 6000);
}

/* ── Navigation ── */
$$('.nav-item').forEach(btn => {
  btn.addEventListener('click', () => {
    $$('.nav-item').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    $$('.view').forEach(v => v.classList.remove('active'));
    const viewName = btn.dataset.view;
    const target = $(`#view${viewName.charAt(0).toUpperCase() + viewName.slice(1)}`);
    if (target) target.classList.add('active');

    sidebar.classList.remove('open');
    overlay.classList.remove('active');

    if (viewName === 'dashboard') loadDashboard();
    if (viewName === 'audit') loadAudit();
  });
});

$('.sidebar-header').addEventListener('click', () => {
  if (window.innerWidth <= 768) {
    sidebar.classList.toggle('open');
    overlay.classList.toggle('active');
  }
});
overlay.addEventListener('click', () => {
  sidebar.classList.remove('open');
  overlay.classList.remove('active');
});

/* ═══════════════════ DASHBOARD ═══════════════════ */
async function loadDashboard() {
  statsGrid.querySelectorAll('.stat-card').forEach(c => c.classList.add('skeleton'));
  try {
    const data = await api('/api/dashboard');
    const breakdown = data.statusBreakdown || {};
    const conducted = breakdown['Проведено'] || 0;
    const planned = breakdown['Запланировано'] || 0;

    const m = {
      total: data.totalItems ?? '—',
      planned,
      conducted,
      projects: data.projectsCount ?? '—',
      upcoming: data.upcoming ?? '—',
      overdue: data.overdue ?? '—',
      plannedSum: fmtMoney(data.totalPlanned),
      actualSum: fmtMoney(data.totalActual),
    };

    statsGrid.querySelectorAll('.stat-card').forEach(c => {
      c.classList.remove('skeleton');
      const val = c.querySelector('.stat-value');
      const key = c.dataset.stat;
      if (key === 'overdue') {
        val.textContent = m[key];
        if (data.overdue > 0) val.style.color = 'var(--danger)';
      } else if (key === 'upcoming') {
        val.textContent = m[key];
        if (data.upcoming > 0) val.style.color = 'var(--success)';
      } else {
        val.textContent = m[key];
      }
    });

    renderChart(statusChart, Object.entries(breakdown).sort((a, b) => b[1] - a[1]));
    renderChart(projectsChart, (data.uniqueProjects || []).slice(0, 10).map(p => [p.project, p.count]));
  } catch (err) {
    toast('Ошибка загрузки дашборда: ' + err.message, 'error');
    statsGrid.querySelectorAll('.stat-card').forEach(c => c.classList.remove('skeleton'));
  }
}

function renderChart(container, entries) {
  const colors = ['green', 'orange', 'red', 'blue', 'purple', 'teal', 'gray'];
  const max = Math.max(...entries.map(e => e[1]), 1);
  container.innerHTML = entries.length
    ? entries.map(([label, count], i) => `
      <div class="chart-bar-row">
        <span class="chart-bar-label" title="${esc(label)}">${esc(label)}</span>
        <div class="chart-bar-track">
          <div class="chart-bar-fill ${colors[i % colors.length]}" style="width:${(count / max) * 100}%"></div>
        </div>
        <span class="chart-bar-count">${count}</span>
      </div>
    `).join('')
    : '<div style="color:var(--text-secondary);padding:20px;text-align:center;">Нет данных</div>';
}

/* ═══════════════════ TABLE ═══════════════════ */
async function loadItems(page = state.page) {
  itemsBody.innerHTML = `<tr class="loading-row"><td colspan="10"><div class="loading-spinner"></div></td></tr>`;
  try {
    const url = state.search
      ? `/api/items/search?search=${encodeURIComponent(state.search)}&sort_field=${state.sortField}&sort_order=${state.sortOrder}&page=${page}&size=${state.pageSize}`
      : `/api/items?page=${page}&size=${state.pageSize}`;

    const data = await api(url);
    state.page = data.page;
    state.total = data.total;

    itemsBody.innerHTML = '';
    if (!data.items?.length) {
      itemsBody.innerHTML = `<tr class="empty-row"><td colspan="10">Нет записей. Загрузите данные из Google Sheets.</td></tr>`;
    } else {
      data.items.forEach(item => itemsBody.appendChild(renderRow(item)));
    }

    // Show/hide search export card
    searchExportCard.hidden = !state.search;

    updatePagination();
  } catch (err) {
    itemsBody.innerHTML = `<tr class="empty-row"><td colspan="10">Ошибка: ${esc(err.message)}</td></tr>`;
    toast(err.message, 'error');
  }
}

function renderRow(item) {
  const tr = document.createElement('tr');
  tr.innerHTML = `
    <td>${esc(item.year)}</td>
    <td>${esc(item.month)}</td>
    <td><strong>${esc(item.project)}</strong></td>
    <td>${esc(item.revision_info)}</td>
    <td>${esc(item.event_date)}</td>
    <td>${esc(item.weekday)}</td>
    <td>${esc(item.inspection_type)}</td>
    <td><span class="status-badge ${statusClass(item.status)}">${esc(item.status)}</span></td>
    <td>${esc(fmtMoney(item.amount_planned))}</td>
    <td>${esc(fmtMoney(item.amount_actual))}</td>
  `;
  return tr;
}

function statusClass(status) {
  const s = (status || '').toLowerCase();
  if (s.startsWith('провед')) return 'conducted';
  if (s.startsWith('запланир')) return 'planned';
  if (s.startsWith('не прове')) return 'not-conducted';
  if (s.startsWith('отмен')) return 'cancelled';
  if (s.startsWith('перенес')) return 'postponed';
  return '';
}

function updatePagination() {
  const totalPages = Math.ceil(state.total / state.pageSize) || 1;
  pageInfo.textContent = `Страница ${state.page} из ${totalPages} · ${state.total} записей`;
  pagePrev.disabled = state.page <= 1;
  pageNext.disabled = state.page >= totalPages;
}

pagePrev.addEventListener('click', () => loadItems(state.page - 1));
pageNext.addEventListener('click', () => loadItems(state.page + 1));
pageSizeSelect.addEventListener('change', () => {
  state.pageSize = parseInt(pageSizeSelect.value);
  state.page = 1;
  loadItems();
});

/* ── Search ── */
let searchTimer;
searchInput.addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.search = searchInput.value.trim();
    searchClear.hidden = !state.search;
    state.page = 1;
    loadItems();
  }, 350);
});
searchClear.addEventListener('click', () => {
  searchInput.value = '';
  state.search = '';
  searchClear.hidden = true;
  state.page = 1;
  loadItems();
  searchInput.focus();
});

/* ── Sort ── */
$$('thead th[data-sort]').forEach(th => {
  th.addEventListener('click', () => {
    const field = th.dataset.sort;
    if (state.sortField === field) {
      state.sortOrder = state.sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
      state.sortField = field;
      state.sortOrder = 'asc';
    }
    $$('thead th[data-sort]').forEach(t => t.classList.remove('asc', 'desc'));
    th.classList.add(state.sortOrder);
    loadItems();
  });
});

/* ── Toolbar ── */
$('#refreshBtn').addEventListener('click', () => loadItems(1));

// Export all
document.getElementById('exportBtn').addEventListener('click', () => {
  window.open('/api/export/excel', '_blank');
  toast('Скачивается Excel-файл со всеми записями');
});

// Export search results
document.getElementById('exportSearchBtn').addEventListener('click', () => {
  if (!state.search) return;
  window.open(`/api/export/excel?search=${encodeURIComponent(state.search)}`, '_blank');
  toast('Скачивается Excel-файл с результатами поиска');
});

// Sync push
document.getElementById('syncPushBtn').addEventListener('click', async () => {
  const btn = document.getElementById('syncPushBtn');
  btn.disabled = true;
  try {
    const result = await api('/api/sync/push', { method: 'POST' });
    toast(`Отправлено в Google Sheets: ${result.rows_written} строк`);
    setStatus(true, 'Данные отправлены');
    setSyncStatus(`✓ Отправлено ${result.rows_written} строк`);
  } catch (err) {
    toast('Ошибка отправки: ' + err.message, 'error');
    setStatus(false, 'Ошибка синхронизации');
    setSyncStatus('✗ Ошибка: ' + err.message, false);
  } finally {
    btn.disabled = false;
  }
});

// Sync pull
document.getElementById('syncPullBtn').addEventListener('click', async () => {
  const btn = document.getElementById('syncPullBtn');
  btn.disabled = true;
  try {
    const result = await api('/api/sync/pull', { method: 'POST' });
    toast(`Загружено из Google Sheets: ${result.rows_imported} строк`);
    setStatus(true, 'Данные загружены');
    setSyncStatus(`✓ Загружено ${result.rows_imported} строк`);
    loadItems(1);
  } catch (err) {
    toast('Ошибка загрузки: ' + err.message, 'error');
    setStatus(false, 'Ошибка синхронизации');
    setSyncStatus('✗ Ошибка: ' + err.message, false);
  } finally {
    btn.disabled = false;
  }
});

/* ═══════════════════ AUDIT ═══════════════════ */
async function loadAudit(page = state.auditPage) {
  auditBody.innerHTML = `<tr class="loading-row"><td colspan="4"><div class="loading-spinner"></div></td></tr>`;
  try {
    let url = `/api/audit?page=${page}&size=${state.auditSize}`;
    if (state.auditFilter) url += `&action=${state.auditFilter}`;

    const data = await api(url);
    state.auditPage = data.page;
    state.auditTotal = data.total;

    auditBody.innerHTML = '';
    if (!data.logs?.length) {
      auditBody.innerHTML = `<tr class="empty-row"><td colspan="4">Нет записей аудита</td></tr>`;
    } else {
      data.logs.forEach(log => {
        const tr = document.createElement('tr');
        const actionLower = (log.action || '').toLowerCase();
        const time = log.timestamp ? new Date(log.timestamp + 'Z').toLocaleString('ru-RU') : '—';

        let details = '—';
        if (log.details) {
          details = esc(log.details);
        } else if (log.new_data) {
          try {
            const nd = JSON.parse(log.new_data);
            if (log.action === 'REPLACE') {
              details = `Импортировано ${nd.rows_imported || '?'} строк`;
            } else if (log.old_data) {
              const od = JSON.parse(log.old_data);
              const changed = Object.keys(nd).filter(k => JSON.stringify(od[k]) !== JSON.stringify(nd[k]));
              details = changed.length ? changed.map(k => `${k}: ${JSON.stringify(od[k])} → ${JSON.stringify(nd[k])}`).join('; ') : 'обновлена';
            } else {
              details = 'создана';
            }
          } catch { details = '—'; }
        }

        tr.innerHTML = `
          <td style="white-space:nowrap">${time}</td>
          <td><span class="audit-action ${actionLower}">${esc(log.action)}</span></td>
          <td>${log.item_id ?? '—'}</td>
          <td><span class="audit-details" title="${esc(details)}">${esc(details)}</span></td>
        `;
        auditBody.appendChild(tr);
      });
    }

    const totalPages = Math.ceil(state.auditTotal / state.auditSize) || 1;
    auditPageInfo.textContent = `Страница ${state.auditPage} из ${totalPages} · ${state.auditTotal} записей`;
    auditPagePrev.disabled = state.auditPage <= 1;
    auditPageNext.disabled = state.auditPage >= totalPages;
  } catch (err) {
    auditBody.innerHTML = `<tr class="empty-row"><td colspan="4">Ошибка: ${esc(err.message)}</td></tr>`;
  }
}

auditPagePrev.addEventListener('click', () => loadAudit(state.auditPage - 1));
auditPageNext.addEventListener('click', () => loadAudit(state.auditPage + 1));
auditFilter.addEventListener('change', () => {
  state.auditFilter = auditFilter.value;
  state.auditPage = 1;
  loadAudit();
});
refreshAuditBtn.addEventListener('click', () => loadAudit(1));

/* ═══════════════════ THEME ═══════════════════ */
function applyTheme(dark) {
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
  themeSwitch.checked = dark;
  localStorage.setItem('theme', dark ? 'dark' : 'light');
}
themeSwitch.addEventListener('change', () => applyTheme(themeSwitch.checked));
if (localStorage.getItem('theme') === 'dark') applyTheme(true);

/* ═══════════════════ INIT ═══════════════════ */
async function init() {
  try {
    const cfg = await api('/api/config');
    state.sheetsConfigured = cfg.sheetsConfigured;
    setStatus(cfg.sheetsConfigured, cfg.sheetsConfigured ? 'Google Sheets подключён' : 'Локальный режим');
    if (!cfg.sheetsConfigured) {
      setSyncStatus('Google Sheets не настроен', false);
    }
  } catch {
    setStatus(false, 'Не удалось загрузить конфигурацию');
  }
  loadDashboard();
  loadItems();
}

function esc(str) {
  if (str == null) return '';
  const d = document.createElement('div');
  d.textContent = String(str);
  return d.innerHTML;
}

init();