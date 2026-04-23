'use strict';

/* ─── State ─── */
const state = {
  currentUser: null,
  users: [],
  role: 'user',
  currentView: 'compose',
  currentDraft: null,
  currentThreadId: null,
  draftPollTimer: null,
  ws: null,
  inboxEmails: [],
  sentEmails: [],
  replyTargetEmailId: null,
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
  getUsers:       ()             => api.req('GET', '/api/auth/users'),
  getInbox:       (uid)          => api.req('GET', `/api/emails/inbox?user_id=${uid}`),
  getSent:        (uid)          => api.req('GET', `/api/emails/sent?user_id=${uid}`),
  getEmail:       (eid)          => api.req('GET', `/api/emails/${eid}`),
  markRead:       (eid)          => api.req('PUT', '/api/emails/mark_read', { email_id: eid }),
  sendEmail:      (sid, to, sub, body) => api.req('POST', '/api/emails/send', { sender_id: sid, recipient_email: to, subject: sub, body }),
  replyEmail:     (sid, pid, body)     => api.req('POST', '/api/emails/reply', { sender_id: sid, parent_email_id: pid, body }),
  createDraft:    (uid, to, sub, ctx)  => api.req('POST', '/api/agent/draft', { user_id: uid, recipient: to, subject: sub, context: ctx }),
  getDraft:       (did)          => api.req('GET', `/api/agent/draft/${did}`),
  getDrafts:      (uid)          => api.req('GET', `/api/agent/drafts?user_id=${uid}`),
  sendDraft:      (did, body)    => api.req('POST', `/api/agent/draft/${did}/send`, body !== undefined ? { body } : {}),
  cancelDraft:    (did)          => api.req('DELETE', `/api/agent/draft/${did}`),
  getThread:      (tid)          => api.req('GET', `/api/agent/thread/${tid}`),
  confirmMeeting: (tid)          => api.req('POST', `/api/agent/thread/${tid}/confirm`, {}),
  declineMeeting: (tid)          => api.req('POST', `/api/agent/thread/${tid}/decline`, {}),
  agentHealth:    ()             => api.req('GET', '/health'),
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
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/* ─── Toast ─── */
function toast(msg, type) {
  type = type || 'info';
  const icons = { success: '✓', error: '✕', info: 'i' };
  const el = document.createElement('div');
  el.className = 'toast toast-' + type;
  el.innerHTML = '<span class="toast-icon">' + (icons[type] || icons.info) + '</span><span>' + escHtml(msg) + '</span>';
  document.getElementById('toast-container').appendChild(el);
  requestAnimationFrame(function() { el.classList.add('show'); });
  setTimeout(function() {
    el.classList.remove('show');
    setTimeout(function() { el.remove(); }, 300);
  }, 3500);
}

/* ─── WebSocket ─── */
function connectWS(userId) {
  if (state.ws) { state.ws.close(); state.ws = null; }
  var proto = location.protocol === 'https:' ? 'wss' : 'ws';
  var url = proto + '://' + location.host + '/api/agent/ws/' + userId;
  try {
    state.ws = new WebSocket(url);
    state.ws.onopen  = function() { setAgentStatus(true); };
    state.ws.onclose = function() {
      setAgentStatus(false);
      setTimeout(function() { if (state.currentUser) connectWS(state.currentUser.id); }, 5000);
    };
    state.ws.onerror = function() { setAgentStatus(false); };
    state.ws.onmessage = function(ev) {
      try { handleWsEvent(JSON.parse(ev.data)); } catch(e) {}
    };
  } catch(e) {
    setAgentStatus(false);
  }
}

function handleWsEvent(data) {
  var event = data && data.event;
  switch (event) {
    case 'new_email':
      toast('New email received!', 'info');
      updateInboxBadge(1);
      if (state.currentView === 'inbox') loadInbox();
      break;
    case 'reply_received':
      toast('Reply received!', 'info');
      if (state.currentView === 'inbox') loadInbox();
      break;
    case 'workflow_complete':
      toast('Email workflow completed!', 'success');
      break;
    case 'followup_sent':
      toast('Follow-up email sent automatically.', 'info');
      break;
    case 'status_update':
      toast((data.payload && data.payload.message) || 'Status updated.', 'info');
      break;
  }
}

function setAgentStatus(online) {
  document.getElementById('agent-dot').className = 'status-dot ' + (online ? 'online' : 'offline');
  document.getElementById('agent-text').textContent = online ? 'Agent online' : 'Agent offline';
}

/* ─── Init ─── */
async function init() {
  setupEventListeners();
  showView('compose');
  await loadUsers();
  checkAgentHealth();
}

async function loadUsers() {
  try {
    var users = await api.getUsers();
    state.users = users;
    var sel = document.getElementById('user-select');
    sel.innerHTML = users.map(function(u) {
      return '<option value="' + u.id + '">' + escHtml(u.username) + ' (' + escHtml(u.email) + ')</option>';
    }).join('');
    if (users.length > 0) selectUser(users[0].id);
  } catch(e) {
    toast('Could not load users — is the backend running?', 'error');
  }
}

function selectUser(userId) {
  var user = state.users.find(function(u) { return u.id == userId; });
  if (!user) return;
  state.currentUser = user;
  connectWS(user.id);
  refreshCurrentView();
}

async function checkAgentHealth() {
  try {
    await api.agentHealth();
    setAgentStatus(true);
  } catch(e) {
    setAgentStatus(false);
  }
}

/* ─── View Management ─── */
function showView(viewName) {
  state.currentView = viewName;
  document.querySelectorAll('.view').forEach(function(v) { v.classList.add('hidden'); });
  var view = document.getElementById('view-' + viewName);
  if (view) view.classList.remove('hidden');

  document.querySelectorAll('[data-view]').forEach(function(btn) {
    btn.classList.toggle('active', btn.dataset.view === viewName);
  });

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

/* ─── Inbox ─── */
async function loadInbox() {
  document.getElementById('inbox-list').innerHTML = loadingHTML();
  try {
    var emails = await api.getInbox(state.currentUser.id);
    state.inboxEmails = emails;
    var unread = emails.filter(function(e) { return !e.is_read; }).length;
    document.getElementById('inbox-subtitle').textContent =
      emails.length + ' message' + (emails.length !== 1 ? 's' : '') + (unread ? ', ' + unread + ' unread' : '');
    renderEmailList(emails, 'inbox-list', 'inbox-reader', false);
    var badge = document.getElementById('inbox-badge');
    if (unread > 0) { badge.textContent = unread; badge.classList.remove('hidden'); }
    else badge.classList.add('hidden');
  } catch(e) {
    setListError('inbox-list', 'Failed to load inbox.');
  }
}

function updateInboxBadge(delta) {
  delta = delta || 0;
  var badge = document.getElementById('inbox-badge');
  var current = parseInt(badge.textContent, 10) || 0;
  var next = Math.max(0, current + delta);
  if (next > 0) { badge.textContent = next; badge.classList.remove('hidden'); }
  else badge.classList.add('hidden');
}

/* ─── Sent ─── */
async function loadSent() {
  document.getElementById('sent-list').innerHTML = loadingHTML();
  try {
    var emails = await api.getSent(state.currentUser.id);
    state.sentEmails = emails;
    document.getElementById('sent-subtitle').textContent =
      emails.length + ' sent message' + (emails.length !== 1 ? 's' : '');
    renderEmailList(emails, 'sent-list', 'sent-reader', true);
  } catch(e) {
    setListError('sent-list', 'Failed to load sent mail.');
  }
}

/* ─── Drafts ─── */
async function loadDrafts() {
  document.getElementById('drafts-grid').innerHTML = loadingHTML();
  try {
    var drafts = await api.getDrafts(state.currentUser.id);
    renderDraftGrid(drafts);
  } catch(e) {
    document.getElementById('drafts-grid').innerHTML =
      '<div class="email-empty"><span class="empty-icon">⚠️</span><p>Failed to load drafts.</p></div>';
  }
}

/* ─── Admin: Course Emails ─── */
var COURSE_KEYWORDS = [
  'course', 'class', 'enrollment', 'enroll', 'training', 'lesson',
  'tutorial', 'program', 'curriculum', 'workshop', 'lecture',
  'python', 'data science', 'machine learning', 'ai', 'study',
  'certificate', 'bootcamp', 'module', 'syllabus',
];

async function loadCourseEmails() {
  document.getElementById('review-list').innerHTML = loadingHTML();
  try {
    var allEmails = await fetchAllUserEmails();
    var filtered = allEmails.filter(function(e) {
      var text = ((e.subject || '') + ' ' + (e.body || '')).toLowerCase();
      return COURSE_KEYWORDS.some(function(kw) { return text.includes(kw); });
    });
    renderReviewStats(filtered, allEmails);
    renderEmailList(filtered, 'review-list', 'review-reader', false);
    var badge = document.getElementById('course-badge');
    if (filtered.length) { badge.textContent = filtered.length; badge.classList.remove('hidden'); }
    else badge.classList.add('hidden');
  } catch(e) {
    setListError('review-list', 'Failed to load emails.');
  }
}

async function loadAllEmails() {
  document.getElementById('all-list').innerHTML = loadingHTML();
  try {
    var emails = await fetchAllUserEmails();
    renderEmailList(emails, 'all-list', 'all-reader', false);
  } catch(e) {
    setListError('all-list', 'Failed to load emails.');
  }
}

async function fetchAllUserEmails() {
  var results = [];
  await Promise.all(state.users.map(async function(user) {
    try {
      var inbox = await api.getInbox(user.id);
      inbox.forEach(function(e) { results.push(Object.assign({}, e, { _ownerName: user.username })); });
    } catch(e) {}
  }));
  return results;
}

/* ─── Rendering ─── */
function renderEmailList(emails, listId, readerId, isSent) {
  var list = document.getElementById(listId);
  if (!emails || !emails.length) {
    list.innerHTML = '<div class="email-empty"><span class="empty-icon">💭</span><p>No emails here</p></div>';
    return;
  }
  var sorted = emails.slice().sort(function(a, b) { return new Date(b.created_at) - new Date(a.created_at); });
  list.innerHTML = sorted.map(function(email) {
    var isUnread = !email.is_read && !isSent;
    var fromLabel = isSent
      ? (email.recipient_email || String(email.recipient_id || 'Unknown'))
      : (email.sender_email || String(email.sender_id || 'Unknown'));
    return '<div class="email-item' + (isUnread ? ' unread' : '') + '" onclick="openEmail(' + email.id + ',\'' + readerId + '\',' + isSent + ')">'
      + '<div class="email-item-top">'
      + '<div style="display:flex;align-items:center;gap:6px;overflow:hidden;flex:1">'
      + (isUnread ? '<div class="unread-dot"></div>' : '')
      + '<span class="email-from">' + escHtml(trunc(fromLabel, 28)) + '</span>'
      + '</div>'
      + '<span class="email-date">' + formatDate(email.created_at) + '</span>'
      + '</div>'
      + '<div class="email-subject">' + escHtml(trunc(email.subject || '(no subject)', 45)) + '</div>'
      + '<div class="email-preview">' + escHtml(trunc(email.body || '', 75)) + '</div>'
      + '</div>';
  }).join('');
}

async function openEmail(emailId, readerId, isSent) {
  document.querySelectorAll('.email-item').forEach(function(el) { el.classList.remove('active'); });
  var clicked = document.querySelector('.email-item[onclick*="openEmail(' + emailId + '"]');
  if (clicked) clicked.classList.add('active');

  var reader = document.getElementById(readerId);
  reader.innerHTML = '<div class="reader-empty"><div class="spinner"></div></div>';

  try {
    await api.markRead(emailId);
    updateInboxBadge(-1);
    var email = await api.getEmail(emailId);
    state.replyTargetEmailId = email.id;
    reader.innerHTML = renderEmailFull(email, isSent);
  } catch(e) {
    reader.innerHTML = '<div class="reader-empty"><span class="empty-icon">⚠️</span><p>Could not load email.</p></div>';
  }
}

function renderEmailFull(email, isSent) {
  var isAdmin = state.role === 'admin';
  var actions = isAdmin
    ? '<button class="btn btn-secondary btn-sm" onclick="api.markRead(' + email.id + ').then(function(){toast(\'Marked reviewed\',\'success\')})">&#x2713; Mark Reviewed</button>'
    : '<button class="btn btn-primary btn-sm" onclick="openReplyModal()">↩ Reply</button>';

  return '<div class="email-full">'
    + '<div class="email-full-card">'
    + '<div class="email-full-header">'
    + '<div class="email-full-subject">' + escHtml(email.subject || '(no subject)') + '</div>'
    + '<div class="email-full-meta">'
    + '<div class="meta-row"><span class="meta-key">From:</span>' + escHtml(email.sender_email || String(email.sender_id || '')) + '</div>'
    + '<div class="meta-row"><span class="meta-key">To:</span>' + escHtml(email.recipient_email || String(email.recipient_id || '')) + '</div>'
    + '<div class="meta-row"><span class="meta-key">Date:</span>' + (email.created_at ? new Date(email.created_at).toLocaleString() : '—') + '</div>'
    + '</div>'
    + '</div>'
    + '<div class="email-full-body">' + escHtml(email.body || '') + '</div>'
    + '<div class="email-full-actions">' + actions + '</div>'
    + '</div>'
    + '</div>';
}

function renderDraftGrid(drafts) {
  var grid = document.getElementById('drafts-grid');
  if (!drafts || !drafts.length) {
    grid.innerHTML = '<div class="email-empty" style="grid-column:1/-1"><span class="empty-icon">📝</span><p>No AI drafts yet</p></div>';
    return;
  }
  var sorted = drafts.slice().sort(function(a, b) { return new Date(b.created_at) - new Date(a.created_at); });
  grid.innerHTML = sorted.map(function(d) {
    var sendBtn = d.status === 'ready'
      ? '<button class="btn btn-success btn-sm" onclick="sendExistingDraft(\'' + d.draft_id + '\')">📤 Send</button>' : '';
    var discardBtn = d.status !== 'sent'
      ? '<button class="btn btn-ghost btn-sm" onclick="cancelExistingDraft(\'' + d.draft_id + '\')">Discard</button>' : '';
    return '<div class="draft-grid-card">'
      + '<div class="draft-grid-header">'
      + '<span class="draft-grid-status ' + d.status + '">' + escHtml(d.status) + '</span>'
      + '<span class="draft-grid-date">' + formatDate(d.created_at) + '</span>'
      + '</div>'
      + '<div class="draft-grid-to">To: ' + escHtml((d.draft && d.draft.recipient) || '—') + '</div>'
      + '<div class="draft-grid-subject">' + escHtml((d.draft && d.draft.subject) || '(no subject)') + '</div>'
      + '<div class="draft-grid-body">' + escHtml(trunc((d.draft && d.draft.body) || '', 120)) + '</div>'
      + '<div class="draft-grid-actions">' + sendBtn + discardBtn + '</div>'
      + '</div>';
  }).join('');
}

function renderReviewStats(courseEmails, allEmails) {
  var unread = courseEmails.filter(function(e) { return !e.is_read; }).length;
  var stats = [
    { val: courseEmails.length, label: 'Course Emails' },
    { val: unread, label: 'Unread' },
    { val: allEmails.length, label: 'Total Emails' },
    { val: state.users.length, label: 'Users' },
  ];
  document.getElementById('review-stats').innerHTML = stats.map(function(s) {
    return '<div class="stat-card"><div class="stat-value">' + s.val + '</div><div class="stat-label">' + s.label + '</div></div>';
  }).join('');
}

/* ─── Compose / AI Draft Flow ─── */
async function generateDraft() {
  var to      = document.getElementById('compose-to').value.trim();
  var subject = document.getElementById('compose-subject').value.trim();
  var context = document.getElementById('compose-context').value.trim();

  if (!to)      { toast('Please enter a recipient email.', 'error'); return; }
  if (!context) { toast('Please describe what you need.', 'error'); return; }
  if (!state.currentUser) { toast('Please select a user first.', 'error'); return; }

  var btn = document.getElementById('compose-generate');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-sm"></span> Generating…';

  document.getElementById('compose-empty-state').classList.add('hidden');
  showDraftLoading();

  try {
    var result = await api.createDraft(state.currentUser.id, to, subject, context);
    state.currentDraft    = result;
    state.currentThreadId = result.thread_id || null;
    startDraftPolling(result.draft_id);
  } catch(e) {
    toast('Failed to create draft: ' + e.message, 'error');
    resetGenerateBtn();
    hideDraftPanel();
  }
}

function showDraftLoading() {
  document.getElementById('draft-panel').classList.remove('hidden');
  document.getElementById('draft-status-badge').textContent = 'Generating…';
  document.getElementById('draft-status-badge').className = 'draft-badge pending';
  document.getElementById('draft-loading').classList.remove('hidden');
  document.getElementById('draft-content').classList.add('hidden');
  document.getElementById('meeting-card').classList.add('hidden');
}

function hideDraftPanel() {
  document.getElementById('draft-panel').classList.add('hidden');
  document.getElementById('compose-empty-state').classList.remove('hidden');
  state.currentDraft    = null;
  state.currentThreadId = null;
}

function startDraftPolling(draftId) {
  if (state.draftPollTimer) clearInterval(state.draftPollTimer);
  var attempts = 0;
  state.draftPollTimer = setInterval(async function() {
    attempts++;
    if (attempts > 60) {
      clearInterval(state.draftPollTimer);
      toast('Draft generation timed out.', 'error');
      resetGenerateBtn();
      return;
    }
    try {
      var draft = await api.getDraft(draftId);
      if (draft.status === 'ready') {
        clearInterval(state.draftPollTimer);
        showDraftContent(draft);
        if (draft.thread_id) fetchMeetingInfo(draft.thread_id);
      } else if (draft.status === 'sent') {
        clearInterval(state.draftPollTimer);
        toast('Email sent successfully!', 'success');
        resetComposeForm();
      } else if (draft.status === 'cancelled') {
        clearInterval(state.draftPollTimer);
        hideDraftPanel();
        resetGenerateBtn();
      }
    } catch(e) {}
  }, 2000);
}

function showDraftContent(draft) {
  state.currentDraft = draft;
  document.getElementById('draft-status-badge').textContent = 'Ready to send';
  document.getElementById('draft-status-badge').className = 'draft-badge ready';
  document.getElementById('draft-loading').classList.add('hidden');
  document.getElementById('draft-content').classList.remove('hidden');
  document.getElementById('draft-to-display').textContent = (draft.draft && draft.draft.recipient) || '—';
  document.getElementById('draft-subject-display').textContent = (draft.draft && draft.draft.subject) || '—';
  document.getElementById('draft-body-edit').value = (draft.draft && draft.draft.body) || '';
  resetGenerateBtn();
  toast('Draft ready — review before sending.', 'success');
}

async function fetchMeetingInfo(threadId) {
  try {
    var thread = await api.getThread(threadId);
    var meeting = thread && thread.meeting;
    if (!meeting) return;
    var hasMeeting = (meeting.participants && meeting.participants.length) || meeting.date || meeting.time;
    if (!hasMeeting) return;

    document.getElementById('meeting-card').classList.remove('hidden');
    var rows = [
      meeting.participants && meeting.participants.length && { key: 'Participants', val: meeting.participants.join(', ') },
      meeting.date && { key: 'Date', val: meeting.date },
      meeting.time && { key: 'Time', val: meeting.time },
      meeting.missing_fields && meeting.missing_fields.length && { key: 'Missing', val: meeting.missing_fields.join(', ') },
    ].filter(Boolean);

    document.getElementById('meeting-details').innerHTML = rows.map(function(r) {
      return '<div class="meeting-detail-row">'
        + '<span class="meeting-detail-key">' + escHtml(r.key) + '</span>'
        + '<span class="meeting-detail-val">' + escHtml(r.val) + '</span>'
        + '</div>';
    }).join('');

    if (thread.status === 'interrupted') {
      document.getElementById('meeting-actions').classList.remove('hidden');
    }
  } catch(e) {}
}

async function sendCurrentDraft() {
  if (!state.currentDraft) return;
  var editedBody = document.getElementById('draft-body-edit').value;
  var btn = document.getElementById('draft-send-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-sm"></span> Sending…';

  try {
    await api.sendDraft(state.currentDraft.draft_id, editedBody);
    toast('Email sent successfully!', 'success');
    resetComposeForm();
    if (state.currentView === 'sent') loadSent();
  } catch(e) {
    toast('Failed to send: ' + e.message, 'error');
    btn.disabled = false;
    btn.innerHTML = '<span class="btn-icon">📤</span> Send Email';
  }
}

async function cancelCurrentDraft() {
  if (!state.currentDraft) return;
  try {
    await api.cancelDraft(state.currentDraft.draft_id);
    hideDraftPanel();
    resetGenerateBtn();
    toast('Draft discarded.', 'info');
  } catch(e) {
    toast('Could not discard: ' + e.message, 'error');
  }
}

function resetGenerateBtn() {
  var btn = document.getElementById('compose-generate');
  btn.disabled = false;
  btn.innerHTML = '<span class="btn-icon">✨</span> Generate Draft';
}

function resetComposeForm() {
  document.getElementById('compose-to').value = '';
  document.getElementById('compose-subject').value = '';
  document.getElementById('compose-context').value = '';
  hideDraftPanel();
  resetGenerateBtn();
}

async function sendExistingDraft(draftId) {
  try {
    await api.sendDraft(draftId);
    toast('Email sent!', 'success');
    loadDrafts();
  } catch(e) {
    toast('Failed to send: ' + e.message, 'error');
  }
}

async function cancelExistingDraft(draftId) {
  try {
    await api.cancelDraft(draftId);
    toast('Draft discarded.', 'info');
    loadDrafts();
  } catch(e) {
    toast('Failed to discard: ' + e.message, 'error');
  }
}

async function confirmMeeting() {
  if (!state.currentThreadId) return;
  try {
    await api.confirmMeeting(state.currentThreadId);
    toast('Meeting confirmed! Email will be sent.', 'success');
    document.getElementById('meeting-actions').classList.add('hidden');
  } catch(e) {
    toast('Failed to confirm: ' + e.message, 'error');
  }
}

async function declineMeeting() {
  if (!state.currentThreadId) return;
  try {
    await api.declineMeeting(state.currentThreadId);
    toast('Meeting declined.', 'info');
    document.getElementById('meeting-actions').classList.add('hidden');
    hideDraftPanel();
    resetGenerateBtn();
  } catch(e) {
    toast('Failed to decline: ' + e.message, 'error');
  }
}

/* ─── Reply Modal ─── */
function openReplyModal() {
  document.getElementById('reply-body').value = '';
  document.getElementById('reply-modal').classList.remove('hidden');
  setTimeout(function() { document.getElementById('reply-body').focus(); }, 50);
}

function closeReplyModal() {
  document.getElementById('reply-modal').classList.add('hidden');
}

async function sendReply() {
  var body = document.getElementById('reply-body').value.trim();
  if (!body) { toast('Please enter a message.', 'error'); return; }
  if (!state.replyTargetEmailId) { toast('No email selected.', 'error'); return; }

  var btn = document.getElementById('reply-send-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-sm"></span> Sending…';

  try {
    await api.replyEmail(state.currentUser.id, state.replyTargetEmailId, body);
    toast('Reply sent!', 'success');
    closeReplyModal();
    if (state.currentView === 'sent') loadSent();
  } catch(e) {
    toast('Failed to send reply: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Send Reply';
  }
}

/* ─── Role Switching ─── */
function setRole(role) {
  state.role = role;
  document.querySelectorAll('.role-btn').forEach(function(b) {
    b.classList.toggle('active', b.dataset.role === role);
  });
  if (role === 'user') {
    document.getElementById('user-nav').classList.remove('hidden');
    document.getElementById('admin-nav').classList.add('hidden');
    showView('compose');
  } else {
    document.getElementById('user-nav').classList.add('hidden');
    document.getElementById('admin-nav').classList.remove('hidden');
    showView('review');
  }
}

/* ─── Example Chips ─── */
var EXAMPLES = {
  schedule: {
    to: 'bob@example.com',
    subject: 'Meeting Request',
    context: 'Schedule a meeting with them next Monday at 2pm to discuss the Python programming course enrollment. Make it friendly and professional.',
  },
  followup: {
    to: 'charlie@example.com',
    subject: '',
    context: "Write a follow-up email asking about the status of their course registration. We sent the initial email last week and haven't heard back.",
  },
  intro: {
    to: 'alice@example.com',
    subject: '',
    context: "Write a professional introduction email for our new AI & Data Science training program. Highlight that it's beginner-friendly and starts next month.",
  },
};

function fillExample(type) {
  var ex = EXAMPLES[type];
  if (!ex) return;
  document.getElementById('compose-to').value = ex.to;
  document.getElementById('compose-subject').value = ex.subject;
  document.getElementById('compose-context').value = ex.context;
  document.getElementById('compose-to').focus();
}

/* ─── Admin search ─── */
function filterEmailList(listId, query) {
  document.querySelectorAll('#' + listId + ' .email-item').forEach(function(el) {
    el.style.display = el.textContent.toLowerCase().includes(query.toLowerCase()) ? '' : 'none';
  });
}

/* ─── Helpers ─── */
function loadingHTML() {
  return '<div class="email-empty"><div class="spinner"></div></div>';
}

function setListError(listId, msg) {
  document.getElementById(listId).innerHTML =
    '<div class="email-empty"><span class="empty-icon">⚠️</span><p>' + escHtml(msg) + '</p></div>';
}

/* ─── Event Listeners ─── */
function setupEventListeners() {
  document.getElementById('user-select').addEventListener('change', function(e) { selectUser(e.target.value); });

  document.querySelectorAll('.role-btn').forEach(function(btn) {
    btn.addEventListener('click', function() { setRole(btn.dataset.role); });
  });

  document.querySelectorAll('[data-view]').forEach(function(btn) {
    btn.addEventListener('click', function() { showView(btn.dataset.view); });
  });

  document.getElementById('compose-generate').addEventListener('click', generateDraft);
  document.getElementById('draft-send-btn').addEventListener('click', sendCurrentDraft);
  document.getElementById('draft-cancel-btn').addEventListener('click', cancelCurrentDraft);
  document.getElementById('meeting-confirm-btn').addEventListener('click', confirmMeeting);
  document.getElementById('meeting-decline-btn').addEventListener('click', declineMeeting);

  document.querySelectorAll('.example-chip').forEach(function(chip) {
    chip.addEventListener('click', function() { fillExample(chip.dataset.example); });
  });

  document.getElementById('refresh-inbox').addEventListener('click', loadInbox);
  document.getElementById('refresh-sent').addEventListener('click', loadSent);
  document.getElementById('refresh-drafts').addEventListener('click', loadDrafts);
  document.getElementById('refresh-review').addEventListener('click', loadCourseEmails);
  document.getElementById('refresh-all').addEventListener('click', loadAllEmails);

  document.getElementById('course-search').addEventListener('input', function(e) {
    filterEmailList('review-list', e.target.value);
  });

  document.getElementById('reply-modal-close').addEventListener('click', closeReplyModal);
  document.getElementById('reply-cancel-btn').addEventListener('click', closeReplyModal);
  document.getElementById('reply-send-btn').addEventListener('click', sendReply);
  document.getElementById('reply-modal').addEventListener('click', function(e) {
    if (e.target === e.currentTarget) closeReplyModal();
  });

  document.getElementById('compose-context').addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') generateDraft();
  });
}

/* ─── Start ─── */
document.addEventListener('DOMContentLoaded', init);
