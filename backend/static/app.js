'use strict';

/* ─── State ─── */
const state = {
  currentUser: null,
  users: [],
  role: 'user',
  currentView: 'chat',
  ws: null,
  inboxEmails: [],
  sentEmails: [],
  replyTargetEmailId: null,
  // Chat-specific
  pendingContext: null,
  awaitingRecipient: false,
  activeDraftId: null,
  activeThreadId: null,
  draftPollTimer: null,
};

/* ─── API ─── */
const api = {
  async req(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body !== undefined) opts.body = JSON.stringify(body);
    const res = await fetch(path, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  },
  getUsers:       ()                   => api.req('GET', '/api/auth/users').then(r => r.users || r),
  getInbox:       (uid)                => api.req('GET', `/api/emails/inbox?user_id=${uid}`),
  getSent:        (uid)                => api.req('GET', `/api/emails/sent?user_id=${uid}`),
  getEmail:       (eid)                => api.req('GET', `/api/emails/${eid}`),
  markRead:       (eid)                => api.req('PUT', '/api/emails/mark_read', { email_id: eid }),
  replyEmail:     (sid, pid, body)     => api.req('POST', '/api/emails/reply', { sender_id: sid, parent_email_id: pid, body }),
  createDraft:    (uid, to, sub, ctx)  => api.req('POST', '/api/agent/draft', { user_id: uid, recipient: to, subject: sub, context: ctx }),
  getDraft:       (did)                => api.req('GET', `/api/agent/draft/${did}`),
  getDrafts:      (uid)                => api.req('GET', `/api/agent/drafts?user_id=${uid}`),
  sendDraft:      (did, body)          => api.req('POST', `/api/agent/draft/${did}/send`, body !== undefined ? { body } : {}),
  cancelDraft:    (did)                => api.req('DELETE', `/api/agent/draft/${did}`),
  getThread:      (tid)                => api.req('GET', `/api/agent/thread/${tid}`),
  confirmMeeting: (tid)                => api.req('POST', `/api/agent/thread/${tid}/confirm`, {}),
  declineMeeting: (tid)                => api.req('POST', `/api/agent/thread/${tid}/decline`, {}),
  agentHealth:    ()                   => api.req('GET', '/health'),
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

function trunc(s, n = 70) {
  if (!s) return '';
  return s.length > n ? s.slice(0, n) + '…' : s;
}

function escHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function extractEmail(text) {
  const m = text.match(/[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}/);
  return m ? m[0] : null;
}

/* ─── Avatar ─── */
const AVATAR_COLORS = ['#e84b5a','#6366f1','#10b981','#f59e0b','#8b5cf6','#0ea5e9','#ec4899','#14b8a6'];

function avatarColor(name) {
  let n = 0;
  for (let i = 0; i < (name || '').length; i++) n += name.charCodeAt(i);
  return AVATAR_COLORS[n % AVATAR_COLORS.length];
}

function avatarInitials(label) {
  const parts = String(label || '?').split(/[@.\s]+/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return (parts[0] || '?')[0].toUpperCase();
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

/* ─── WebSocket ─── */
function connectWS(userId) {
  if (state.ws) { state.ws.close(); state.ws = null; }
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const url = `${proto}://${location.hostname}:8000/api/agent/ws/${userId}`;
  try {
    state.ws = new WebSocket(url);
    state.ws.onopen  = () => setAgentStatus(true);
    state.ws.onclose = () => { setAgentStatus(false); setTimeout(() => { if (state.currentUser) connectWS(state.currentUser.id); }, 5000); };
    state.ws.onerror = () => setAgentStatus(false);
    state.ws.onmessage = (ev) => { try { handleWsEvent(JSON.parse(ev.data)); } catch {} };
  } catch { setAgentStatus(false); }
}

function handleWsEvent(data) {
  const ev = data && data.event;
  if (ev === 'new_email')       { toast('New email received!', 'info'); updateInboxBadge(1); if (state.currentView === 'inbox') loadInbox(); }
  if (ev === 'workflow_complete') toast('Workflow completed!', 'success');
  if (ev === 'followup_sent')   addSystemMsg('Follow-up email sent automatically.');
  if (ev === 'reply_received')  { addSystemMsg('Reply received!'); if (state.currentView === 'inbox') loadInbox(); }
}

function setAgentStatus(online) {
  document.getElementById('agent-dot').className = `status-dot ${online ? 'online' : 'offline'}`;
  document.getElementById('agent-text').textContent = online ? 'Agent online' : 'Agent offline';
  document.getElementById('chat-status').textContent = online ? 'Ready to help' : 'Agent offline';
  document.getElementById('chat-status').style.color = online ? 'var(--success)' : 'var(--danger)';
}

/* ─── Init ─── */
async function init() {
  setupEventListeners();
  showView('chat');
  await loadUsers();
  checkAgentHealth();
}

async function loadUsers() {
  try {
    const users = await api.getUsers();
    state.users = users;
    const sel = document.getElementById('user-select');
    sel.innerHTML = users.map(u =>
      `<option value="${u.id}">${escHtml(u.username)} (${escHtml(u.email)})</option>`
    ).join('');
    if (users.length > 0) selectUser(users[0].id);
  } catch { toast('Could not load users — is the backend running?', 'error'); }
}

function selectUser(userId) {
  const user = state.users.find(u => u.id == userId);
  if (!user) return;
  state.currentUser = user;
  connectWS(user.id);
  refreshCurrentView();
}

async function checkAgentHealth() {
  try { await api.agentHealth(); setAgentStatus(true); }
  catch { setAgentStatus(false); }
}

/* ─── View Management ─── */
function showView(viewName) {
  state.currentView = viewName;
  document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
  const view = document.getElementById(`view-${viewName}`);
  if (view) view.classList.remove('hidden');
  document.querySelectorAll('[data-view]').forEach(btn =>
    btn.classList.toggle('active', btn.dataset.view === viewName)
  );
  refreshCurrentView();
}

function refreshCurrentView() {
  if (!state.currentUser) return;
  switch (state.currentView) {
    case 'inbox':      loadInbox(); break;
    case 'sent':       loadSent(); break;
    case 'drafts':     loadDrafts(); break;
    case 'review':     loadCourseEmails(); break;
    case 'all-emails': loadAllEmails(); break;
  }
}

/* ─── Chat Logic ─── */
function getUserInitials() {
  if (!state.currentUser) return '?';
  return avatarInitials(state.currentUser.username);
}

function addUserMsg(text) {
  const msgs = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'msg msg-user';
  div.innerHTML = `
    <div class="msg-avatar-wrap">
      <div class="msg-avatar user-avatar" style="background:${avatarColor(state.currentUser?.username || '')}">${getUserInitials()}</div>
    </div>
    <div class="msg-bubble">${escHtml(text)}</div>`;
  msgs.appendChild(div);
  scrollChat();
}

function addAiMsg(html) {
  const msgs = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'msg msg-ai';
  div.innerHTML = `
    <div class="msg-avatar-wrap">
      <div class="msg-avatar ai-avatar">AI</div>
    </div>
    <div class="msg-bubble">${html}</div>`;
  msgs.appendChild(div);
  scrollChat();
  return div;
}

function addThinkingMsg() {
  const msgs = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'msg msg-ai';
  div.id = 'msg-thinking';
  div.innerHTML = `
    <div class="msg-avatar-wrap">
      <div class="msg-avatar ai-avatar">AI</div>
    </div>
    <div class="msg-bubble msg-thinking">
      <span></span><span></span><span></span>
    </div>`;
  msgs.appendChild(div);
  scrollChat();
}

function removeThinkingMsg() {
  const el = document.getElementById('msg-thinking');
  if (el) el.remove();
}

function addSystemMsg(text, isError = false) {
  const msgs = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `msg msg-system${isError ? ' error' : ''}`;
  div.innerHTML = `<div class="msg-bubble">${escHtml(text)}</div>`;
  msgs.appendChild(div);
  scrollChat();
}

function scrollChat() {
  const msgs = document.getElementById('chat-messages');
  msgs.scrollTop = msgs.scrollHeight;
}

async function sendChatMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text || !state.currentUser) return;

  input.value = '';
  autoResizeInput(input);
  addUserMsg(text);

  // If we're waiting for the user to supply a recipient
  if (state.awaitingRecipient) {
    const email = extractEmail(text);
    if (email) {
      state.awaitingRecipient = false;
      const ctx = state.pendingContext;
      state.pendingContext = null;
      addThinkingMsg();
      await processDraft(email, ctx);
    } else {
      addAiMsg('I need a valid email address. Please include it in your message (e.g. <code>bob@example.com</code>).');
    }
    return;
  }

  const recipient = extractEmail(text);
  if (recipient) {
    addThinkingMsg();
    await processDraft(recipient, text);
  } else {
    // No email found — ask for it
    state.pendingContext = text;
    state.awaitingRecipient = true;
    addAiMsg(`Got it! Who should I send this to? Please reply with the recipient's email address.`);
  }
}

async function processDraft(recipient, context) {
  try {
    const result = await api.createDraft(state.currentUser.id, recipient, '', context);
    state.activeDraftId   = result.draft_id;
    state.activeThreadId  = result.thread_id || null;
    pollDraft(result.draft_id);
  } catch (e) {
    removeThinkingMsg();
    addAiMsg(`Sorry, I couldn't process that request: ${escHtml(e.message)}`);
  }
}

function pollDraft(draftId) {
  if (state.draftPollTimer) clearInterval(state.draftPollTimer);
  let attempts = 0;
  state.draftPollTimer = setInterval(async () => {
    attempts++;
    if (attempts > 60) {
      clearInterval(state.draftPollTimer);
      removeThinkingMsg();
      addAiMsg('Draft generation timed out. Please try again.');
      return;
    }
    try {
      const draft = await api.getDraft(draftId);
      if (draft.status === 'ready') {
        clearInterval(state.draftPollTimer);
        removeThinkingMsg();
        showDraftInChat(draft);
        if (draft.thread_id) showMeetingInChat(draft.thread_id);
      } else if (draft.status === 'sent') {
        clearInterval(state.draftPollTimer);
        removeThinkingMsg();
        addSystemMsg('Email sent successfully!');
      } else if (draft.status === 'cancelled') {
        clearInterval(state.draftPollTimer);
        removeThinkingMsg();
      }
    } catch {}
  }, 2000);
}

function showDraftInChat(draft) {
  const draftId = draft.draft_id;
  const to      = escHtml(draft.draft?.recipient || '—');
  const subject = escHtml(draft.draft?.subject   || '—');
  const body    = escHtml(draft.draft?.body      || '');
  const rawBody = draft.draft?.body || '';

  const msgEl = addAiMsg(`
    Here's the draft I've prepared for you:
    <div class="msg-draft-card">
      <div class="msg-draft-header">
        <span class="msg-draft-label">Email Draft</span>
        <span class="msg-draft-badge">Ready</span>
      </div>
      <div class="msg-draft-meta">
        <div class="msg-draft-meta-row">
          <span class="msg-draft-key">To</span>
          <span class="msg-draft-val">${to}</span>
        </div>
        <div class="msg-draft-meta-row">
          <span class="msg-draft-key">Subject</span>
          <span class="msg-draft-val">${subject}</span>
        </div>
      </div>
      <div class="msg-draft-body">
        <textarea id="draft-body-${draftId}" rows="6">${body}</textarea>
      </div>
      <div class="msg-draft-actions">
        <button class="btn btn-primary btn-sm" onclick="sendDraftFromChat('${draftId}')">Send Email</button>
        <button class="btn btn-ghost btn-sm" onclick="discardDraftFromChat('${draftId}')">Discard</button>
      </div>
    </div>`);

  // Set raw (unescaped) body value to the textarea
  const ta = msgEl.querySelector(`#draft-body-${draftId}`);
  if (ta) ta.value = rawBody;
}

async function showMeetingInChat(threadId) {
  try {
    const thread = await api.getThread(threadId);
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
           <button class="btn btn-ghost btn-sm" onclick="declineMeetingFromChat('${threadId}')">Decline</button>
         </div>` : '';

    addAiMsg(`
      <div class="msg-meeting-card">
        <div class="msg-meeting-title">Meeting Details Extracted</div>
        ${rows}
      </div>
      ${confirmBtns}`);
  } catch {}
}

async function sendDraftFromChat(draftId) {
  const ta = document.getElementById(`draft-body-${draftId}`);
  const body = ta ? ta.value : undefined;
  const btn = ta?.closest('.msg-draft-card')?.querySelector('.btn-primary');
  if (btn) { btn.disabled = true; btn.innerHTML = '<span class="spinner-sm"></span> Sending…'; }
  try {
    await api.sendDraft(draftId, body);
    addSystemMsg('Email sent successfully!');
    if (btn) btn.closest('.msg-draft-card').innerHTML = '<div style="padding:10px 14px;font-size:13px;color:var(--success)">Sent!</div>';
    if (state.currentView === 'sent') loadSent();
  } catch (e) {
    toast(`Failed to send: ${e.message}`, 'error');
    if (btn) { btn.disabled = false; btn.textContent = 'Send Email'; }
  }
}

async function discardDraftFromChat(draftId) {
  try {
    await api.cancelDraft(draftId);
    addSystemMsg('Draft discarded.');
    const card = document.getElementById(`draft-body-${draftId}`)?.closest('.msg-draft-card');
    if (card) card.remove();
  } catch (e) {
    toast(`Could not discard: ${e.message}`, 'error');
  }
}

async function confirmMeetingFromChat(threadId) {
  try {
    await api.confirmMeeting(threadId);
    addSystemMsg('Meeting confirmed! The email will be sent.');
  } catch (e) { toast(`Failed: ${e.message}`, 'error'); }
}

async function declineMeetingFromChat(threadId) {
  try {
    await api.declineMeeting(threadId);
    addSystemMsg('Meeting declined.');
  } catch (e) { toast(`Failed: ${e.message}`, 'error'); }
}

function clearChat() {
  const msgs = document.getElementById('chat-messages');
  msgs.innerHTML = `
    <div class="msg msg-ai">
      <div class="msg-avatar-wrap"><div class="msg-avatar ai-avatar">AI</div></div>
      <div class="msg-bubble">
        Chat cleared. What would you like to do?
        <div class="msg-suggestions">
          <button class="suggestion-chip" data-text="Schedule a meeting with bob@example.com next Monday at 2pm to discuss the Python course">Schedule a meeting</button>
          <button class="suggestion-chip" data-text="Write a follow-up email to charlie@example.com about their course enrollment, we haven't heard back in a week">Follow-up email</button>
          <button class="suggestion-chip" data-text="Send an introduction email to alice@example.com about our new AI and Data Science program starting next month">Introduction email</button>
        </div>
      </div>
    </div>`;
  bindSuggestionChips();
  state.pendingContext    = null;
  state.awaitingRecipient = false;
  if (state.draftPollTimer) { clearInterval(state.draftPollTimer); state.draftPollTimer = null; }
}

/* ─── Inbox ─── */
async function loadInbox() {
  document.getElementById('inbox-list').innerHTML = '<div class="email-empty"><p>Loading…</p></div>';
  try {
    const emails = await api.getInbox(state.currentUser.id);
    state.inboxEmails = emails;
    const unread = emails.filter(e => !e.is_read).length;
    document.getElementById('inbox-subtitle').textContent =
      `${emails.length} message${emails.length !== 1 ? 's' : ''}${unread ? `, ${unread} unread` : ''}`;
    renderEmailList(emails, 'inbox-list', 'inbox-reader', false);
    const badge = document.getElementById('inbox-badge');
    if (unread > 0) { badge.textContent = unread; badge.classList.remove('hidden'); }
    else badge.classList.add('hidden');
  } catch { setListError('inbox-list', 'Failed to load inbox.'); }
}

function updateInboxBadge(delta = 0) {
  const badge = document.getElementById('inbox-badge');
  const next = Math.max(0, (parseInt(badge.textContent, 10) || 0) + delta);
  if (next > 0) { badge.textContent = next; badge.classList.remove('hidden'); }
  else badge.classList.add('hidden');
}

/* ─── Sent ─── */
async function loadSent() {
  document.getElementById('sent-list').innerHTML = '<div class="email-empty"><p>Loading…</p></div>';
  try {
    const emails = await api.getSent(state.currentUser.id);
    document.getElementById('sent-subtitle').textContent = `${emails.length} sent message${emails.length !== 1 ? 's' : ''}`;
    renderEmailList(emails, 'sent-list', 'sent-reader', true);
  } catch { setListError('sent-list', 'Failed to load sent mail.'); }
}

/* ─── Drafts ─── */
async function loadDrafts() {
  document.getElementById('drafts-grid').innerHTML = '<div class="email-empty"><p>Loading…</p></div>';
  try {
    const drafts = await api.getDrafts(state.currentUser.id);
    renderDraftGrid(drafts);
  } catch { document.getElementById('drafts-grid').innerHTML = '<div class="email-empty"><p>Failed to load drafts.</p></div>'; }
}

/* ─── Admin Emails ─── */
const COURSE_KEYWORDS = ['course','class','enrollment','enroll','training','lesson','tutorial','program','curriculum','workshop','lecture','python','data science','machine learning','ai','study','certificate','bootcamp','module','syllabus'];

async function loadCourseEmails() {
  document.getElementById('review-list').innerHTML = '<div class="email-empty"><p>Loading…</p></div>';
  try {
    const allEmails = await fetchAllUserEmails();
    const filtered = allEmails.filter(e => {
      const text = `${e.subject || ''} ${e.body || ''}`.toLowerCase();
      return COURSE_KEYWORDS.some(kw => text.includes(kw));
    });
    renderReviewStats(filtered, allEmails);
    renderEmailList(filtered, 'review-list', 'review-reader', false);
    const badge = document.getElementById('course-badge');
    if (filtered.length) { badge.textContent = filtered.length; badge.classList.remove('hidden'); }
    else badge.classList.add('hidden');
  } catch { setListError('review-list', 'Failed to load emails.'); }
}

async function loadAllEmails() {
  document.getElementById('all-list').innerHTML = '<div class="email-empty"><p>Loading…</p></div>';
  try {
    const emails = await fetchAllUserEmails();
    renderEmailList(emails, 'all-list', 'all-reader', false);
  } catch { setListError('all-list', 'Failed to load emails.'); }
}

async function fetchAllUserEmails() {
  const results = [];
  await Promise.all(state.users.map(async user => {
    try {
      const inbox = await api.getInbox(user.id);
      inbox.forEach(e => results.push({ ...e, _ownerName: user.username }));
    } catch {}
  }));
  return results;
}

/* ─── Email List Rendering ─── */
function renderEmailList(emails, listId, readerId, isSent) {
  const list = document.getElementById(listId);
  if (!emails || !emails.length) {
    list.innerHTML = '<div class="email-empty"><p>No emails here</p></div>';
    return;
  }
  const sorted = [...emails].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  list.innerHTML = sorted.map(email => {
    const isUnread  = !email.is_read && !isSent;
    const fromLabel = isSent
      ? (email.recipient_email || String(email.recipient_id || 'Unknown'))
      : (email.sender_email    || String(email.sender_id    || 'Unknown'));
    const initials = avatarInitials(fromLabel);
    const color    = avatarColor(fromLabel);
    return `
      <div class="email-item${isUnread ? ' unread' : ''}" onclick="openEmail(${email.id},'${readerId}',${isSent})">
        <div class="email-avatar" style="background:${color}">${initials}</div>
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
  const clicked = document.querySelector(`.email-item[onclick*="openEmail(${emailId}"]`);
  if (clicked) clicked.classList.add('active');

  const reader = document.getElementById(readerId);
  reader.innerHTML = '<div class="reader-empty"><div class="spinner"></div></div>';

  try {
    await api.markRead(emailId);
    updateInboxBadge(-1);
    const email = await api.getEmail(emailId);
    state.replyTargetEmailId = email.id;
    reader.innerHTML = renderEmailFull(email, isSent);
  } catch {
    reader.innerHTML = '<div class="reader-empty"><p>Could not load email.</p></div>';
  }
}

function renderEmailFull(email, isSent) {
  const isAdmin       = state.role === 'admin';
  const senderLabel   = email.sender_email    || String(email.sender_id    || 'Unknown');
  const recipientLabel= email.recipient_email || String(email.recipient_id || 'Unknown');
  const initials      = avatarInitials(senderLabel);
  const color         = avatarColor(senderLabel);
  const dateStr       = email.created_at ? new Date(email.created_at).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : '—';
  const actions       = isAdmin
    ? `<button class="btn btn-secondary btn-sm" onclick="api.markRead(${email.id}).then(()=>toast('Marked reviewed','success'))">Mark Reviewed</button>`
    : `<button class="btn btn-primary btn-sm" onclick="openReplyModal()">Reply</button>`;

  return `
    <div class="email-full">
      <div class="email-full-header">
        <div class="email-full-subject">${escHtml(email.subject || '(no subject)')}</div>
        <div class="email-sender-row">
          <div class="email-sender-avatar" style="background:${color}">${initials}</div>
          <div class="email-sender-info">
            <div class="email-sender-name">${escHtml(senderLabel)}</div>
            <div class="email-sender-addr">To: ${escHtml(recipientLabel)}</div>
          </div>
          <div class="email-sent-time">${dateStr}</div>
        </div>
      </div>
      <div class="email-full-body">${escHtml(email.body || '')}</div>
      <div class="email-full-actions">${actions}</div>
    </div>`;
}

function renderDraftGrid(drafts) {
  const grid = document.getElementById('drafts-grid');
  if (!drafts || !drafts.length) {
    grid.innerHTML = '<div class="email-empty" style="grid-column:1/-1"><p>No AI drafts yet</p></div>';
    return;
  }
  const sorted = [...drafts].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  grid.innerHTML = sorted.map(d => `
    <div class="draft-grid-card">
      <div class="draft-grid-header">
        <span class="draft-grid-status ${d.status}">${d.status}</span>
        <span class="draft-grid-date">${formatDate(d.created_at)}</span>
      </div>
      <div class="draft-grid-to">To: ${escHtml(d.draft?.recipient || '—')}</div>
      <div class="draft-grid-subject">${escHtml(d.draft?.subject || '(no subject)')}</div>
      <div class="draft-grid-body">${escHtml(trunc(d.draft?.body || '', 120))}</div>
      <div class="draft-grid-actions">
        ${d.status === 'ready' ? `<button class="btn btn-success btn-sm" onclick="sendExistingDraft('${d.draft_id}')">Send</button>` : ''}
        ${d.status !== 'sent' ? `<button class="btn btn-ghost btn-sm" onclick="cancelExistingDraft('${d.draft_id}')">Discard</button>` : ''}
      </div>
    </div>`).join('');
}

function renderReviewStats(courseEmails, allEmails) {
  const unread = courseEmails.filter(e => !e.is_read).length;
  document.getElementById('review-stats').innerHTML = [
    { val: courseEmails.length, label: 'Course Emails' },
    { val: unread,              label: 'Unread' },
    { val: allEmails.length,   label: 'Total Emails' },
    { val: state.users.length, label: 'Users' },
  ].map(s => `
    <div class="stat-card">
      <div class="stat-value">${s.val}</div>
      <div class="stat-label">${s.label}</div>
    </div>`).join('');
}

async function sendExistingDraft(draftId) {
  try { await api.sendDraft(draftId); toast('Email sent!', 'success'); loadDrafts(); }
  catch (e) { toast(`Failed: ${e.message}`, 'error'); }
}

async function cancelExistingDraft(draftId) {
  try { await api.cancelDraft(draftId); toast('Draft discarded.', 'info'); loadDrafts(); }
  catch (e) { toast(`Failed: ${e.message}`, 'error'); }
}

/* ─── Reply Modal ─── */
function openReplyModal() {
  document.getElementById('reply-body').value = '';
  document.getElementById('reply-modal').classList.remove('hidden');
  setTimeout(() => document.getElementById('reply-body').focus(), 50);
}

function closeReplyModal() {
  document.getElementById('reply-modal').classList.add('hidden');
}

async function sendReply() {
  const body = document.getElementById('reply-body').value.trim();
  if (!body || !state.replyTargetEmailId) return;
  const btn = document.getElementById('reply-send-btn');
  btn.disabled = true;
  try {
    await api.replyEmail(state.currentUser.id, state.replyTargetEmailId, body);
    toast('Reply sent!', 'success');
    closeReplyModal();
  } catch (e) { toast(`Failed: ${e.message}`, 'error'); }
  finally { btn.disabled = false; }
}

/* ─── Role ─── */
function setRole(role) {
  state.role = role;
  document.querySelectorAll('.role-btn').forEach(b => b.classList.toggle('active', b.dataset.role === role));
  document.getElementById('user-nav').classList.toggle('hidden', role === 'admin');
  document.getElementById('admin-nav').classList.toggle('hidden', role === 'user');
  showView(role === 'user' ? 'chat' : 'review');
}

/* ─── Input auto-resize ─── */
function autoResizeInput(el) {
  el.style.height = 'auto';
  el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
}

/* ─── Suggestion chips ─── */
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
  document.getElementById('user-select').addEventListener('change', e => selectUser(e.target.value));

  document.querySelectorAll('.role-btn').forEach(btn =>
    btn.addEventListener('click', () => setRole(btn.dataset.role))
  );

  document.querySelectorAll('[data-view]').forEach(btn =>
    btn.addEventListener('click', () => showView(btn.dataset.view))
  );

  // Chat
  document.getElementById('chat-send').addEventListener('click', sendChatMessage);
  document.getElementById('chat-clear').addEventListener('click', clearChat);

  const chatInput = document.getElementById('chat-input');
  chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChatMessage(); }
  });
  chatInput.addEventListener('input', () => autoResizeInput(chatInput));

  // Suggestion chips (initial render)
  bindSuggestionChips();

  // Refresh buttons
  document.getElementById('refresh-inbox').addEventListener('click', loadInbox);
  document.getElementById('refresh-sent').addEventListener('click', loadSent);
  document.getElementById('refresh-drafts').addEventListener('click', loadDrafts);
  document.getElementById('refresh-review').addEventListener('click', loadCourseEmails);
  document.getElementById('refresh-all').addEventListener('click', loadAllEmails);

  // Admin search
  document.getElementById('course-search').addEventListener('input', e => {
    document.querySelectorAll('#review-list .email-item').forEach(el => {
      el.style.display = el.textContent.toLowerCase().includes(e.target.value.toLowerCase()) ? '' : 'none';
    });
  });

  // Reply modal
  document.getElementById('reply-modal-close').addEventListener('click', closeReplyModal);
  document.getElementById('reply-cancel-btn').addEventListener('click', closeReplyModal);
  document.getElementById('reply-send-btn').addEventListener('click', sendReply);
  document.getElementById('reply-modal').addEventListener('click', e => { if (e.target === e.currentTarget) closeReplyModal(); });
}

/* ─── Helpers ─── */
function setListError(listId, msg) {
  document.getElementById(listId).innerHTML = `<div class="email-empty"><p>${escHtml(msg)}</p></div>`;
}

/* ─── Start ─── */
document.addEventListener('DOMContentLoaded', init);
