'use strict';

/* ─── State ─── */
const state = {
  currentUser:       null,
  ws:                null,
  currentTab:        'inbox',
  inboxFilter:       'inbox',
  replyTargetId:     null,
  // Chat
  chatOpen:          false,
  pendingContext:     null,
  awaitingRecipient: false,
  activeDraftId:     null,
  activeThreadId:    null,
  // Calendar
  calYear:           new Date().getFullYear(),
  calMonth:          new Date().getMonth(),
};

/* ─── API ─── */
const api = {
  async req(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) opts.body = JSON.stringify(body);
    const res  = await fetch(path, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  },
  login:          (email, pw)          => api.req('POST', '/api/auth/login', { email, password: pw }),
  getInbox:       (uid)                => api.req('GET', `/api/emails/inbox?user_id=${uid}`).then(r => (r.emails || []).map(e => e.email || e)),
  getSent:        (uid)                => api.req('GET', `/api/emails/sent?user_id=${uid}`).then(r => (r.emails || []).map(e => e.email || e)),
  getEmail:       (eid)                => api.req('GET', `/api/emails/${eid}`).then(r => r.email || r),
  sendEmail:      (sid, to, sub, body) => api.req('POST', '/api/emails/send', { sender_id: sid, recipient_email: to, subject: sub, body }),
  markRead:       (eid)                => api.req('PUT', '/api/emails/mark_read', { email_id: eid }),
  replyEmail:     (sid, pid, body)     => api.req('POST', '/api/emails/reply', { sender_id: sid, parent_email_id: pid, body }),
  createDraft:    (uid, to, sub, ctx)  => api.req('POST', '/api/agent/draft', { user_id: uid, recipient: to, subject: sub, context: ctx }),
  sendDraft:      (did, body)          => api.req('POST', `/api/agent/draft/${did}/send`, body !== undefined ? { body } : {}),
  cancelDraft:    (did)                => api.req('DELETE', `/api/agent/draft/${did}`),
  getThread:      (tid)                => api.req('GET', `/api/agent/thread/${tid}`),
  getThreads:     (uid)                => api.req('GET', `/api/agent/threads?user_id=${uid}`).then(r => r.threads || []),
  confirmMeeting: (tid)                => api.req('POST', `/api/agent/thread/${tid}/confirm`, {}),
  declineMeeting: (tid)                => api.req('POST', `/api/agent/thread/${tid}/decline`, {}),
};

/* ─── Utilities ─── */
function formatDate(str) {
  if (!str) return '';
  const d = new Date(str);
  if (isNaN(d)) return str;
  const now = new Date();
  if (d.toDateString() === now.toDateString())
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

function trunc(s, n = 70) { return !s ? '' : s.length > n ? s.slice(0, n) + '…' : s; }

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function extractEmail(text) {
  const m = text.match(/[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}/);
  return m ? m[0] : null;
}

const AVATAR_COLORS = ['#e84b5a','#6366f1','#10b981','#f59e0b','#8b5cf6','#0ea5e9','#ec4899','#14b8a6'];

function avatarColor(name) {
  let n = 0;
  for (let i = 0; i < (name||'').length; i++) n += name.charCodeAt(i);
  return AVATAR_COLORS[n % AVATAR_COLORS.length];
}

function avatarInitials(label) {
  const parts = String(label||'?').split(/[@.\s]+/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return (parts[0]||'?')[0].toUpperCase();
}

/* ─── Toast ─── */
function toast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  el.innerHTML = `<span>${escHtml(msg)}</span>`;
  document.getElementById('toast-container').appendChild(el);
  requestAnimationFrame(() => el.classList.add('show'));
  setTimeout(() => { el.classList.remove('show'); setTimeout(() => el.remove(), 300); }, 3500);
}

/* ─── Login / Logout ─── */
async function submitLogin() {
  const email = document.getElementById('login-email').value.trim();
  const pw    = document.getElementById('login-password').value;
  const errEl = document.getElementById('login-error');

  errEl.classList.add('hidden');
  if (!email || !pw) { errEl.textContent = 'Please enter your email and password.'; errEl.classList.remove('hidden'); return; }

  const btn = document.getElementById('login-submit');
  btn.disabled    = true;
  btn.textContent = 'Signing in…';

  try {
    const user = await api.login(email, pw);
    showMainApp(user);
  } catch (e) {
    errEl.textContent = e.message.includes('401') || e.message.toLowerCase().includes('invalid')
      ? 'Incorrect email or password.'
      : (e.message || 'Sign in failed. Please try again.');
    errEl.classList.remove('hidden');
  } finally {
    btn.disabled    = false;
    btn.textContent = 'Sign in';
  }
}

function submitForgot() {
  const email = document.getElementById('forgot-email').value.trim();
  const errEl = document.getElementById('forgot-error');

  errEl.classList.add('hidden');
  if (!email) { errEl.textContent = 'Please enter your email address.'; errEl.classList.remove('hidden'); return; }

  toast('If that email is registered, reset instructions are on their way.', 'success');
  document.getElementById('forgot-email').value = '';
  document.getElementById('forgot-form').classList.add('hidden');
  document.getElementById('signin-form').classList.remove('hidden');
}

function showMainApp(user) {
  state.currentUser = user;

  // Update user pill in topbar
  const initials = avatarInitials(user.username || user.email);
  const color    = avatarColor(user.username || user.email);
  document.getElementById('user-pill-avatar').textContent          = initials;
  document.getElementById('user-pill-avatar').style.background     = color;
  document.getElementById('user-pill-name').textContent            = user.username || user.email;

  // Swap screens
  document.getElementById('login-screen').classList.add('hidden');
  document.getElementById('main-app').classList.remove('hidden');
  document.getElementById('chat-fab').classList.remove('hidden');

  // Connect WS and load initial tab
  connectWS(user.user_id || user.id);
  showTab('inbox');
}

function logout() {
  if (state.ws) { state.ws.close(); state.ws = null; }
  state.currentUser = null;

  // Reset chat
  document.getElementById('chat-messages').innerHTML = `
    <div class="msg msg-ai">
      <div class="msg-avatar-wrap"><div class="msg-avatar ai-avatar">AI</div></div>
      <div class="msg-bubble">
        Hi! Describe what you need and I'll handle it — drafting emails, scheduling meetings, and more.
        <div class="msg-suggestions">
          <button class="suggestion-chip" data-text="Schedule a meeting with bob@example.com next Monday at 2pm to discuss the Python course">Schedule a meeting</button>
          <button class="suggestion-chip" data-text="Write a follow-up email to charlie@example.com about their course enrollment">Follow-up email</button>
        </div>
      </div>
    </div>`;
  bindSuggestionChips();
  document.getElementById('chat-widget').classList.add('hidden');
  state.chatOpen = false;

  // Swap screens
  document.getElementById('main-app').classList.add('hidden');
  document.getElementById('chat-fab').classList.add('hidden');
  document.getElementById('login-screen').classList.remove('hidden');
  document.getElementById('login-email').value    = '';
  document.getElementById('login-password').value = '';
  document.getElementById('login-error').classList.add('hidden');
}

/* ─── WebSocket ─── */
function connectWS(userId) {
  if (state.ws) { state.ws.close(); state.ws = null; }
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  try {
    state.ws = new WebSocket(`${proto}://${location.hostname}:8000/api/agent/ws/${userId}`);
    state.ws.onclose   = () => setTimeout(() => { if (state.currentUser) connectWS(userId); }, 5000);
    state.ws.onmessage = (ev) => { try { handleWsEvent(JSON.parse(ev.data)); } catch {} };
  } catch {}
}

function handleWsEvent(data) {
  const ev = data && data.event;
  if (ev === 'new_email')        { toast('New email received!', 'info'); updateInboxBadge(1); if (state.currentTab === 'inbox') refreshTab('inbox'); }
  if (ev === 'followup_sent')    addSystemMsg('Follow-up email sent automatically.');
  if (ev === 'reply_received')   { addSystemMsg('Reply received!'); if (state.currentTab === 'inbox') refreshTab('inbox'); }
}

/* ─── Init ─── */
function init() {
  setupEventListeners();
}

/* ─── Tab Management ─── */
function showTab(name) {
  state.currentTab = name;
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
  document.getElementById(`tab-${name}`)?.classList.remove('hidden');
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
  refreshTab(name);
}

function refreshTab(name) {
  if (!state.currentUser) return;
  switch (name) {
    case 'inbox':    state.inboxFilter === 'sent' ? loadSent() : loadInbox(); break;
    case 'calendar': loadCalendar(); break;
  }
}

/* ─── Inbox / Sent ─── */
async function loadInbox() {
  document.getElementById('inbox-list').innerHTML = '<div class="email-empty"><p>Loading…</p></div>';
  const uid = state.currentUser.user_id || state.currentUser.id;
  try {
    const emails = await api.getInbox(uid);
    const unread = emails.filter(e => !e.is_read).length;
    document.getElementById('inbox-subtitle').textContent =
      `${emails.length} message${emails.length !== 1 ? 's' : ''}${unread ? `, ${unread} unread` : ''}`;
    renderEmailList(emails, 'inbox-list', 'inbox-reader', false);
    updateInboxBadge(0, unread);
  } catch { setListError('inbox-list', 'Failed to load inbox.'); }
}

async function loadSent() {
  document.getElementById('inbox-list').innerHTML = '<div class="email-empty"><p>Loading…</p></div>';
  const uid = state.currentUser.user_id || state.currentUser.id;
  try {
    const emails = await api.getSent(uid);
    document.getElementById('inbox-subtitle').textContent =
      `${emails.length} sent message${emails.length !== 1 ? 's' : ''}`;
    renderEmailList(emails, 'inbox-list', 'inbox-reader', true);
    updateInboxBadge(0, 0);
  } catch { setListError('inbox-list', 'Failed to load sent mail.'); }
}

function updateInboxBadge(delta = 0, forceCount = null) {
  const badge = document.getElementById('inbox-badge');
  const next  = forceCount !== null ? forceCount : Math.max(0, (parseInt(badge.textContent, 10) || 0) + delta);
  if (next > 0) { badge.textContent = next; badge.classList.remove('hidden'); }
  else badge.classList.add('hidden');
}

/* ─── Compose ─── */
async function sendCompose() {
  const to      = document.getElementById('compose-to').value.trim();
  const subject = document.getElementById('compose-subject').value.trim();
  const body    = document.getElementById('compose-body').value.trim();

  if (!to || !body) { toast('Please fill in To and Message fields.', 'error'); return; }

  const btn = document.getElementById('compose-send');
  btn.disabled = true; btn.textContent = 'Sending…';

  try {
    const uid = state.currentUser.user_id || state.currentUser.id;
    await api.sendEmail(uid, to, subject || '(no subject)', body);
    toast('Email sent!', 'success');
    document.getElementById('compose-to').value      = '';
    document.getElementById('compose-subject').value = '';
    document.getElementById('compose-body').value    = '';
  } catch (e) { toast(`Failed: ${e.message}`, 'error'); }
  finally { btn.disabled = false; btn.textContent = 'Send Email'; }
}

function populateCompose(to, subject, body) {
  document.getElementById('compose-to').value      = to || '';
  document.getElementById('compose-subject').value = subject || '';
  document.getElementById('compose-body').value    = body || '';
  showTab('compose');
}

/* ─── Calendar ─── */
function loadCalendar() {
  renderCalendarGrid();
  loadMeetings();
}

function renderCalendarGrid() {
  const { calYear: year, calMonth: month } = state;
  const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  document.getElementById('cal-month-title').textContent = `${MONTHS[month]} ${year}`;

  const today     = new Date();
  const firstDay  = new Date(year, month, 1).getDay();
  const daysCount = new Date(year, month + 1, 0).getDate();
  const isNow     = today.getFullYear() === year && today.getMonth() === month;

  let html = '';
  for (let i = 0; i < firstDay; i++) html += '<div class="cal-day empty"></div>';
  for (let d = 1; d <= daysCount; d++) {
    const isToday = isNow && d === today.getDate();
    html += `<div class="cal-day${isToday ? ' today' : ''}">${d}</div>`;
  }
  document.getElementById('cal-grid').innerHTML = html;
}

async function loadMeetings() {
  if (!state.currentUser) return;
  const el  = document.getElementById('meetings-list');
  const uid = state.currentUser.user_id || state.currentUser.id;
  try {
    const threads = await api.getThreads(uid);
    if (!threads.length) {
      el.innerHTML = '<div class="email-empty"><p>No scheduled meetings yet.<br>Use the AI assistant to schedule one.</p></div>';
      return;
    }
    el.innerHTML = threads.map(t => `
      <div class="meeting-card">
        <div class="meeting-card-recipient">${escHtml(t.recipient || '—')}</div>
        <div class="meeting-card-detail">Sent ${formatDate(t.created_at)}</div>
        <span class="meeting-status-badge ${t.status || ''}">${escHtml((t.status || '').replace(/_/g,' '))}</span>
      </div>`).join('');
  } catch {
    el.innerHTML = '<div class="email-empty"><p>Could not load meetings.</p></div>';
  }
}

/* ─── Chat Widget ─── */
function toggleChat() {
  const w = document.getElementById('chat-widget');
  state.chatOpen = !state.chatOpen;
  w.classList.toggle('hidden', !state.chatOpen);
  if (state.chatOpen) setTimeout(() => document.getElementById('chat-input')?.focus(), 80);
}

function openChat() {
  document.getElementById('chat-widget').classList.remove('hidden');
  state.chatOpen = true;
  setTimeout(() => document.getElementById('chat-input')?.focus(), 80);
}

/* ─── Chat Messages ─── */
function addUserMsg(text) {
  const msgs     = document.getElementById('chat-messages');
  const div      = document.createElement('div');
  div.className  = 'msg msg-user';
  const name     = state.currentUser?.username || state.currentUser?.email || '?';
  div.innerHTML  = `
    <div class="msg-avatar-wrap">
      <div class="msg-avatar user-avatar" style="background:${avatarColor(name)}">${avatarInitials(name)}</div>
    </div>
    <div class="msg-bubble">${escHtml(text)}</div>`;
  msgs.appendChild(div);
  scrollChat();
}

function addAiMsg(html) {
  const msgs    = document.getElementById('chat-messages');
  const div     = document.createElement('div');
  div.className = 'msg msg-ai';
  div.innerHTML = `
    <div class="msg-avatar-wrap"><div class="msg-avatar ai-avatar">AI</div></div>
    <div class="msg-bubble">${html}</div>`;
  msgs.appendChild(div);
  scrollChat();
  return div;
}

function addThinkingMsg() {
  const msgs    = document.getElementById('chat-messages');
  const div     = document.createElement('div');
  div.className = 'msg msg-ai';
  div.id        = 'msg-thinking';
  div.innerHTML = `
    <div class="msg-avatar-wrap"><div class="msg-avatar ai-avatar">AI</div></div>
    <div class="msg-bubble msg-thinking"><span></span><span></span><span></span></div>`;
  msgs.appendChild(div);
  scrollChat();
}

function removeThinkingMsg() { document.getElementById('msg-thinking')?.remove(); }

function addSystemMsg(text, isError = false) {
  const msgs    = document.getElementById('chat-messages');
  const div     = document.createElement('div');
  div.className = `msg msg-system${isError ? ' error' : ''}`;
  div.innerHTML = `<div class="msg-bubble">${escHtml(text)}</div>`;
  msgs.appendChild(div);
  scrollChat();
}

function scrollChat() {
  const msgs = document.getElementById('chat-messages');
  if (msgs) msgs.scrollTop = msgs.scrollHeight;
}

/* ─── Chat Logic ─── */
async function sendChatMessage() {
  const input = document.getElementById('chat-input');
  const text  = input.value.trim();
  if (!text || !state.currentUser) return;

  input.value = '';
  autoResizeInput(input);
  addUserMsg(text);

  if (state.awaitingRecipient) {
    const email = extractEmail(text);
    if (email) {
      state.awaitingRecipient = false;
      const ctx = state.pendingContext;
      state.pendingContext    = null;
      addThinkingMsg();
      await processDraft(email, ctx);
    } else {
      addAiMsg('I need a valid email address — please include it, e.g. <code>bob@example.com</code>.');
    }
    return;
  }

  const recipient = extractEmail(text);
  if (recipient) {
    addThinkingMsg();
    await processDraft(recipient, text);
  } else {
    state.pendingContext    = text;
    state.awaitingRecipient = true;
    addAiMsg("Got it! Who should I send this to? Please provide the recipient's email address.");
  }
}

async function processDraft(recipient, context) {
  try {
    const uid    = state.currentUser.user_id || state.currentUser.id;
    const result = await api.createDraft(uid, recipient, '', context);
    state.activeDraftId  = result.draft_id;
    state.activeThreadId = result.thread_id || null;
    removeThinkingMsg();
    showDraftInChat(result);
    if (result.thread_id) showMeetingInChat(result.thread_id);
  } catch (e) {
    removeThinkingMsg();
    addAiMsg(`Sorry, I couldn't process that: ${escHtml(e.message)}`);
  }
}

function showDraftInChat(draft) {
  const draftId = draft.draft_id;
  const to      = escHtml(draft.draft?.recipient || '—');
  const subject = escHtml(draft.draft?.subject   || '—');
  const rawBody = draft.draft?.body || '';

  const msgEl = addAiMsg(`
    Here's the draft I've prepared:
    <div class="msg-draft-card">
      <div class="msg-draft-header">
        <span class="msg-draft-label">Email Draft</span>
        <span class="msg-draft-badge">Ready</span>
      </div>
      <div class="msg-draft-meta">
        <div class="msg-draft-meta-row"><span class="msg-draft-key">To</span><span class="msg-draft-val">${to}</span></div>
        <div class="msg-draft-meta-row"><span class="msg-draft-key">Subject</span><span class="msg-draft-val">${subject}</span></div>
      </div>
      <div class="msg-draft-body">
        <textarea id="draft-body-${draftId}" rows="5"></textarea>
      </div>
      <div class="msg-draft-actions">
        <button class="btn btn-primary btn-sm" onclick="sendDraftFromChat('${draftId}')">Send Email</button>
        <button class="btn btn-secondary btn-sm" onclick="editDraftInCompose('${draftId}')">Open in Compose</button>
        <button class="btn btn-ghost btn-sm" onclick="discardDraftFromChat('${draftId}')">Discard</button>
      </div>
    </div>`);

  const ta = msgEl.querySelector(`#draft-body-${draftId}`);
  if (ta) ta.value = rawBody;
}

function editDraftInCompose(draftId) {
  const ta      = document.getElementById(`draft-body-${draftId}`);
  const card    = ta?.closest('.msg-draft-card');
  const vals    = card?.querySelectorAll('.msg-draft-val') || [];
  populateCompose(vals[0]?.textContent || '', vals[1]?.textContent || '', ta?.value || '');
  if (state.chatOpen) toggleChat();
}

async function showMeetingInChat(threadId) {
  try {
    const thread  = await api.getThread(threadId);
    const meeting = thread?.meeting;
    if (!meeting) return;
    const hasMeeting = meeting.participants?.length || meeting.date || meeting.time;
    if (!hasMeeting) return;

    const rows = [
      meeting.participants?.length && `<div class="msg-meeting-row"><span class="msg-meeting-key">Participants</span><span class="msg-meeting-val">${escHtml(meeting.participants.join(', '))}</span></div>`,
      meeting.date && `<div class="msg-meeting-row"><span class="msg-meeting-key">Date</span><span class="msg-meeting-val">${escHtml(meeting.date)}</span></div>`,
      meeting.time && `<div class="msg-meeting-row"><span class="msg-meeting-key">Time</span><span class="msg-meeting-val">${escHtml(meeting.time)}</span></div>`,
    ].filter(Boolean).join('');

    const confirmBtns = thread.status === 'interrupted'
      ? `<div style="margin-top:10px;display:flex;gap:8px;">
           <button class="btn btn-success btn-sm" onclick="confirmMeetingFromChat('${threadId}')">Confirm Meeting</button>
           <button class="btn btn-ghost btn-sm"   onclick="declineMeetingFromChat('${threadId}')">Decline</button>
         </div>` : '';

    addAiMsg(`
      <div class="msg-meeting-card">
        <div class="msg-meeting-title">Meeting Details</div>
        ${rows}
      </div>${confirmBtns}`);
  } catch {}
}

async function sendDraftFromChat(draftId) {
  const ta  = document.getElementById(`draft-body-${draftId}`);
  const body = ta?.value;
  const btn  = ta?.closest('.msg-draft-card')?.querySelector('.btn-primary');
  if (btn) { btn.disabled = true; btn.textContent = 'Sending…'; }
  try {
    await api.sendDraft(draftId, body);
    addSystemMsg('Email sent successfully!');
    const card = ta?.closest('.msg-draft-card');
    if (card) card.innerHTML = '<div style="padding:10px 14px;font-size:12px;color:var(--success)">Sent successfully</div>';
    if (state.inboxFilter === 'sent' && state.currentTab === 'inbox') loadSent();
  } catch (e) {
    toast(`Failed to send: ${e.message}`, 'error');
    if (btn) { btn.disabled = false; btn.textContent = 'Send Email'; }
  }
}

async function discardDraftFromChat(draftId) {
  try {
    await api.cancelDraft(draftId);
    addSystemMsg('Draft discarded.');
    document.getElementById(`draft-body-${draftId}`)?.closest('.msg-draft-card')?.remove();
  } catch (e) { toast(`Could not discard: ${e.message}`, 'error'); }
}

async function confirmMeetingFromChat(threadId) {
  try { await api.confirmMeeting(threadId); addSystemMsg('Meeting confirmed! The email will be sent.'); }
  catch (e) { toast(`Failed: ${e.message}`, 'error'); }
}

async function declineMeetingFromChat(threadId) {
  try { await api.declineMeeting(threadId); addSystemMsg('Meeting declined.'); }
  catch (e) { toast(`Failed: ${e.message}`, 'error'); }
}

/* ─── Email List Rendering ─── */
function renderEmailList(emails, listId, readerId, isSent) {
  const list = document.getElementById(listId);
  if (!emails || !emails.length) {
    list.innerHTML = '<div class="email-empty"><p>No emails here yet</p></div>';
    return;
  }
  const sorted = [...emails].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  list.innerHTML = sorted.map(email => {
    const isUnread  = !email.is_read && !isSent;
    const fromLabel = isSent
      ? (email.recipient_email || String(email.recipient_id || 'Unknown'))
      : (email.sender_email    || String(email.sender_id    || 'Unknown'));
    return `
      <div class="email-item${isUnread ? ' unread' : ''}" onclick="openEmail(${email.id},'${readerId}',${isSent})">
        <div class="email-avatar" style="background:${avatarColor(fromLabel)}">${avatarInitials(fromLabel)}</div>
        <div class="email-item-body">
          <div class="email-item-top">
            <span class="email-from">${escHtml(trunc(fromLabel, 22))}</span>
            <span class="email-date">${formatDate(email.created_at)}</span>
          </div>
          <div class="email-subject">${escHtml(trunc(email.subject || '(no subject)', 40))}</div>
          <div class="email-preview">${escHtml(trunc(email.body || '', 60))}</div>
        </div>
        ${isUnread ? '<div class="unread-dot"></div>' : ''}
      </div>`;
  }).join('');
}

async function openEmail(emailId, readerId, isSent) {
  document.querySelectorAll('.email-item').forEach(el => el.classList.remove('active'));
  document.querySelector(`.email-item[onclick*="openEmail(${emailId}"]`)?.classList.add('active');

  const reader = document.getElementById(readerId);
  reader.innerHTML = '<div class="reader-empty"><div class="spinner"></div></div>';

  try {
    await api.markRead(emailId);
    updateInboxBadge(-1);
    const email = await api.getEmail(emailId);
    state.replyTargetId = email.id;
    reader.innerHTML = renderEmailFull(email, isSent);
  } catch {
    reader.innerHTML = '<div class="reader-empty"><p>Could not load email.</p></div>';
  }
}

function renderEmailFull(email, isSent) {
  const senderLabel    = email.sender_email    || String(email.sender_id    || 'Unknown');
  const recipientLabel = email.recipient_email || String(email.recipient_id || 'Unknown');
  const dateStr        = email.created_at ? new Date(email.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : '—';

  return `
    <div class="email-full">
      <div class="email-full-subject">${escHtml(email.subject || '(no subject)')}</div>
      <div class="email-sender-row">
        <div class="email-sender-avatar" style="background:${avatarColor(senderLabel)}">${avatarInitials(senderLabel)}</div>
        <div class="email-sender-info">
          <div class="email-sender-name">${escHtml(senderLabel)}</div>
          <div class="email-sender-addr">To: ${escHtml(recipientLabel)}</div>
        </div>
        <div class="email-sent-time">${dateStr}</div>
      </div>
      <div class="email-full-body">${escHtml(email.body || '')}</div>
      <div class="email-full-actions">
        <button class="btn btn-primary btn-sm" onclick="openReplyModal()">Reply</button>
      </div>
    </div>`;
}

/* ─── Reply Modal ─── */
function openReplyModal() {
  document.getElementById('reply-body').value = '';
  document.getElementById('reply-modal').classList.remove('hidden');
  setTimeout(() => document.getElementById('reply-body').focus(), 50);
}

function closeReplyModal() { document.getElementById('reply-modal').classList.add('hidden'); }

async function sendReply() {
  const body = document.getElementById('reply-body').value.trim();
  if (!body || !state.replyTargetId) return;
  const btn = document.getElementById('reply-send-btn');
  btn.disabled = true;
  try {
    const uid = state.currentUser.user_id || state.currentUser.id;
    await api.replyEmail(uid, state.replyTargetId, body);
    toast('Reply sent!', 'success');
    closeReplyModal();
  } catch (e) { toast(`Failed: ${e.message}`, 'error'); }
  finally { btn.disabled = false; }
}

/* ─── Helpers ─── */
function setListError(listId, msg) {
  document.getElementById(listId).innerHTML = `<div class="email-empty"><p>${escHtml(msg)}</p></div>`;
}

function autoResizeInput(el) {
  el.style.height = 'auto';
  el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
}

function bindSuggestionChips() {
  document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const input = document.getElementById('chat-input');
      input.value = chip.dataset.text;
      autoResizeInput(input);
      input.focus();
    });
  });
}

/* ─── Event Listeners ─── */
function setupEventListeners() {
  // Login form
  document.getElementById('login-submit').addEventListener('click', submitLogin);
  document.getElementById('login-password').addEventListener('keydown', e => { if (e.key === 'Enter') submitLogin(); });
  document.getElementById('login-email').addEventListener('keydown', e => { if (e.key === 'Enter') document.getElementById('login-password').focus(); });

  // Forgot password
  document.getElementById('show-forgot').addEventListener('click', () => {
    document.getElementById('signin-form').classList.add('hidden');
    document.getElementById('forgot-form').classList.remove('hidden');
    document.getElementById('forgot-email').focus();
  });
  document.getElementById('show-signin').addEventListener('click', () => {
    document.getElementById('forgot-form').classList.add('hidden');
    document.getElementById('signin-form').classList.remove('hidden');
    document.getElementById('login-error').classList.add('hidden');
  });
  document.getElementById('forgot-submit').addEventListener('click', submitForgot);
  document.getElementById('forgot-email').addEventListener('keydown', e => { if (e.key === 'Enter') submitForgot(); });

  // Logout
  document.getElementById('logout-btn').addEventListener('click', logout);

  // Tabs
  document.querySelectorAll('.tab-btn').forEach(b => b.addEventListener('click', () => showTab(b.dataset.tab)));

  // Inbox filter
  document.querySelectorAll('.filter-btn').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.filter-btn').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    state.inboxFilter = b.dataset.filter;
    state.inboxFilter === 'sent' ? loadSent() : loadInbox();
  }));

  document.getElementById('refresh-inbox').addEventListener('click', () => state.inboxFilter === 'sent' ? loadSent() : loadInbox());

  // Compose
  document.getElementById('compose-send').addEventListener('click', sendCompose);
  document.getElementById('compose-clear').addEventListener('click', () => {
    ['compose-to','compose-subject','compose-body'].forEach(id => document.getElementById(id).value = '');
  });
  document.getElementById('compose-ai-btn').addEventListener('click', () => {
    const to  = document.getElementById('compose-to').value.trim();
    const sub = document.getElementById('compose-subject').value.trim();
    if (to || sub) {
      document.getElementById('chat-input').value = [to && `to ${to}`, sub && `about "${sub}"`].filter(Boolean).join(' ');
    }
    openChat();
  });

  // Calendar nav
  document.getElementById('cal-prev').addEventListener('click', () => {
    if (--state.calMonth < 0) { state.calMonth = 11; state.calYear--; }
    renderCalendarGrid();
  });
  document.getElementById('cal-next').addEventListener('click', () => {
    if (++state.calMonth > 11) { state.calMonth = 0; state.calYear++; }
    renderCalendarGrid();
  });

  // Chat
  document.getElementById('chat-toggle').addEventListener('click', toggleChat);
  document.getElementById('chat-close').addEventListener('click', toggleChat);
  document.getElementById('chat-send').addEventListener('click', sendChatMessage);
  const chatInput = document.getElementById('chat-input');
  chatInput.addEventListener('keydown', e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(); } });
  chatInput.addEventListener('input', () => autoResizeInput(chatInput));

  bindSuggestionChips();

  // Reply modal
  document.getElementById('reply-modal-close').addEventListener('click', closeReplyModal);
  document.getElementById('reply-cancel-btn').addEventListener('click', closeReplyModal);
  document.getElementById('reply-send-btn').addEventListener('click', sendReply);
  document.getElementById('reply-modal').addEventListener('click', e => { if (e.target === e.currentTarget) closeReplyModal(); });
}

/* ─── Start ─── */
document.addEventListener('DOMContentLoaded', init);
