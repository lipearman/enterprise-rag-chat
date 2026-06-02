const els = {
  messages: document.getElementById('messages'),
  form: document.getElementById('chatForm'),
  input: document.getElementById('messageInput'),
  sendBtn: document.getElementById('sendBtn'),
  stopBtn: document.getElementById('stopBtn'),
  statusText: document.getElementById('statusText'),
  providerMode: document.getElementById('providerMode'),
  providerUrl: document.getElementById('providerUrl'),
  providerModel: document.getElementById('providerModel'),
  reloadProvider: document.getElementById('reloadProvider'),
  clearChat: document.getElementById('clearChat'),
  copyLast: document.getElementById('copyLast'),
  enterToSend: document.getElementById('enterToSend'),
  saveHistory: document.getElementById('saveHistory'),
  kbList: document.getElementById('kbList'),
  mobileKbList: document.getElementById('mobileKbList'),
};

let controller = null;
let lastAssistantText = '';
let selectedKb = '';
const STORAGE_KEY = 'enterprise-rag-chat-history-v3';

function nowText() {
  return new Date().toLocaleTimeString('th-TH', { hour: '2-digit', minute: '2-digit' });
}

function linkify(text) {
  const escaped = text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
  return escaped.replace(/(https?:\/\/[^\s)]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
}

function buildSourcesHtml(sources) {
  if (!sources || sources.length === 0) return '';
  const links = sources.map(s => {
    const pct = Math.round(s.similarity * 100);
    const title = s.title.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
    return `<a class="source-link" href="${s.url}" target="_blank" rel="noopener noreferrer">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
      <span class="source-title">${title}</span>
      <span class="source-sim">${pct}%</span>
    </a>`;
  }).join('');
  return `<div class="sources"><span class="sources-label">แหล่งอ้างอิง</span><div class="sources-list">${links}</div></div>`;
}

function addMessage(role, text, save = true, sources = []) {
  const item = document.createElement('div');
  item.className = `message ${role}`;
  const sourcesHtml = role === 'assistant' ? buildSourcesHtml(sources) : '';
  item.innerHTML = `
    <div class="meta">${role === 'user' ? 'คุณ' : 'AI'} • ${nowText()}</div>
    <div class="bubble">${linkify(text)}</div>
    ${sourcesHtml}
  `;
  // store sources so saveHistory() can persist them
  if (role === 'assistant' && sources.length) {
    item.dataset.sources = JSON.stringify(sources);
  }
  els.messages.appendChild(item);
  els.messages.scrollTop = els.messages.scrollHeight;

  if (role === 'assistant') lastAssistantText = text;
  if (save && els.saveHistory.checked) saveHistory();
  return item;
}

function addTyping() {
  const item = document.createElement('div');
  item.className = 'message assistant';
  item.innerHTML = `
    <div class="meta">AI • กำลังตอบ</div>
    <div class="bubble"><span class="typing"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span></div>
  `;
  els.messages.appendChild(item);
  els.messages.scrollTop = els.messages.scrollHeight;
  return item;
}

function saveHistory() {
  const data = [...els.messages.querySelectorAll('.message')].map(m => ({
    role: m.classList.contains('user') ? 'user' : 'assistant',
    text: m.querySelector('.bubble')?.innerText || '',
    sources: m.dataset.sources ? JSON.parse(m.dataset.sources) : [],
  })).filter(x => x.text.trim() && !x.text.includes('กำลังตอบ'));
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data.slice(-60)));
}

function loadHistory() {
  const raw = localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    addMessage('assistant', 'สวัสดีครับ ผมพร้อมช่วยตอบคำถามจาก Enterprise RAG และทดสอบ Ollama Local/Cloud แล้วครับ', false);
    return;
  }
  try {
    JSON.parse(raw).forEach(m => addMessage(m.role, m.text, false, m.sources || []));
  } catch {
    localStorage.removeItem(STORAGE_KEY);
  }
}

async function loadProvider() {
  try {
    els.statusText.textContent = 'กำลังโหลด provider...';
    const res = await fetch('/provider');
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    els.providerMode.textContent = data.provider || '-';
    els.providerUrl.textContent = data.base_url || '-';
    els.providerModel.textContent = data.chat_model || '-';
    els.statusText.textContent = `พร้อมใช้งานผ่าน ${data.provider || 'provider'}`;
  } catch (err) {
    els.statusText.textContent = 'โหลด provider ไม่สำเร็จ';
    els.providerMode.textContent = 'error';
    els.providerUrl.textContent = err.message;
  }
}

function selectKb(code, label) {
  selectedKb = code;
  // sync sidebar
  els.kbList.querySelectorAll('.kb-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.code === code)
  );
  // sync mobile pills
  els.mobileKbList.querySelectorAll('.mobile-kb-pill').forEach(b =>
    b.classList.toggle('active', b.dataset.code === code)
  );
  updateKbBadge(label);
}

async function loadKb() {
  try {
    const res = await fetch('/kb');
    const data = await res.json();
    selectedKb = data.default || '';
    els.kbList.innerHTML = '';
    els.mobileKbList.innerHTML = '';

    data.items.forEach(kb => {
      const isActive = kb.code === selectedKb;

      // Sidebar button
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'kb-btn' + (isActive ? ' active' : '');
      btn.dataset.code = kb.code;
      btn.innerHTML = `
        <span>${kb.label}</span>
        <span class="kb-meta">${kb.docs.toLocaleString()} docs · ${kb.faqs.toLocaleString()} FAQs</span>
      `;
      btn.addEventListener('click', () => selectKb(kb.code, kb.label));
      els.kbList.appendChild(btn);

      // Mobile pill
      const pill = document.createElement('button');
      pill.type = 'button';
      pill.className = 'mobile-kb-pill' + (isActive ? ' active' : '');
      pill.dataset.code = kb.code;
      pill.textContent = kb.label;
      pill.addEventListener('click', () => selectKb(kb.code, kb.label));
      els.mobileKbList.appendChild(pill);
    });

    const active = data.items.find(k => k.code === selectedKb);
    if (active) updateKbBadge(active.label);
  } catch {
    els.kbList.innerHTML = '<div class="kb-loading">โหลด KB ไม่สำเร็จ</div>';
    els.mobileKbList.innerHTML = '';
  }
}

function updateKbBadge(label) {
  let badge = document.getElementById('kbBadge');
  if (!badge) {
    badge = document.createElement('span');
    badge.id = 'kbBadge';
    badge.className = 'kb-badge';
    document.querySelector('.topbar h2').after(badge);
  }
  badge.textContent = label;
}

async function sendMessage(message) {
  controller = new AbortController();
  els.sendBtn.disabled = true;
  els.stopBtn.disabled = false;
  els.statusText.textContent = 'กำลังส่งคำถาม...';
  addMessage('user', message);
  const typing = addTyping();

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, company_code: selectedKb }),
      signal: controller.signal,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || JSON.stringify(data) || res.statusText);
    typing.remove();
    addMessage('assistant', data.answer || '(ไม่มีคำตอบ)', true, data.sources || []);
    els.statusText.textContent = 'ตอบเสร็จแล้ว';
  } catch (err) {
    typing.remove();
    addMessage('assistant', err.name === 'AbortError' ? 'หยุดการตอบแล้ว' : `เกิดข้อผิดพลาด: ${err.message}`);
    els.statusText.textContent = 'เกิดข้อผิดพลาด';
  } finally {
    els.sendBtn.disabled = false;
    els.stopBtn.disabled = true;
    controller = null;
    els.input.focus();
  }
}

els.form.addEventListener('submit', (e) => {
  e.preventDefault();
  const message = els.input.value.trim();
  if (!message) return;
  els.input.value = '';
  sendMessage(message);
});

els.input.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey && els.enterToSend.checked) {
    e.preventDefault();
    els.form.requestSubmit();
  }
});

els.input.addEventListener('input', () => {
  els.input.style.height = 'auto';
  els.input.style.height = Math.min(els.input.scrollHeight, 200) + 'px';
});

els.stopBtn.addEventListener('click', () => controller?.abort());
els.reloadProvider.addEventListener('click', loadProvider);
els.clearChat.addEventListener('click', () => {
  els.messages.innerHTML = '';
  localStorage.removeItem(STORAGE_KEY);
  addMessage('assistant', 'ล้างประวัติแล้วครับ เริ่มถามใหม่ได้เลย', false);
});
els.copyLast.addEventListener('click', async () => {
  if (!lastAssistantText) return;
  await navigator.clipboard.writeText(lastAssistantText);
  els.statusText.textContent = 'Copy คำตอบล่าสุดแล้ว';
});

document.querySelectorAll('.prompt-chip').forEach(btn => {
  btn.addEventListener('click', () => {
    els.input.value = btn.textContent.trim();
    els.input.focus();
  });
});

loadHistory();
loadProvider();
loadKb();
