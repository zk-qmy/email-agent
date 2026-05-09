import type { User, Email, DraftResponse, Thread } from './types';

const AGENT_BASE_URL = '';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const opts: RequestInit = { method, headers: { 'Content-Type': 'application/json' } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  
  const res = await fetch(`${AGENT_BASE_URL}${path}`, opts);
  const data = await res.json().catch(() => ({}));

  if (!res.ok) throw new ApiError(res.status, data.detail || `HTTP ${res.status}`);
  return data;
}

export const api = {
  login: (email: string, password: string) =>
    req<User>('POST', '/api/auth/login', { email, password }),

  getInbox: (userId: number) =>
    req<{ emails: { email: Email }[] }>('GET', `/api/emails/inbox?user_id=${userId}`)
      .then(r => r.emails?.map(e => e.email) || []),

  getSent: (userId: number) =>
    req<{ emails: { email: Email }[] }>('GET', `/api/emails/sent?user_id=${userId}`)
      .then(r => r.emails?.map(e => e.email) || []),

  getEmail: (emailId: number) =>
    req<{ email: Email }>('GET', `/api/emails/${emailId}`)
      .then(r => r.email || r),

  sendEmail: (senderId: number, recipientEmail: string, subject: string, body: string) =>
    req('POST', '/api/emails/send', { sender_id: senderId, recipient_email: recipientEmail, subject, body }),

  markRead: (emailId: number) =>
    req('PUT', '/api/emails/mark_read', { email_id: emailId }),

  replyEmail: (senderId: number, parentEmailId: number, body: string) =>
    req('POST', '/api/emails/reply', { sender_id: senderId, parent_email_id: parentEmailId, body }),

  createThread: (userId: number) =>
    req<{ thread_id: string }>('POST', '/api/agent/thread', { user_id: userId }),

  createDraft: (userId: number, prompt: string, threadId?: string) =>
    req<DraftResponse>('POST', '/api/agent/draft', { user_id: userId, prompt, thread_id: threadId || null }),

  sendDraft: (threadId: string, userId: number, body: string) =>
    req('POST', `/api/agent/thread/${threadId}/reply`, { user_id: userId, response: body }),

  cancelDraft: (threadId: string) =>
    req('DELETE', `/api/agent/thread/${threadId}`),

  getThread: (threadId: string) =>
    req<Thread>('GET', `/api/agent/thread/${threadId}`),

  getThreads: (userId: number, status?: string) =>
    req<{ threads: Thread[] }>('GET', `/api/agent/threads?user_id=${userId}${status ? `&status=${status}` : ''}`)
      .then(r => r.threads || []),

  confirmMeeting: (threadId: string) =>
    req('POST', `/api/agent/thread/${threadId}/confirm`, {}),

  declineMeeting: (threadId: string) =>
    req('POST', `/api/agent/thread/${threadId}/decline`, {}),

  getThreadStatus: (threadId: string) =>
    req<{ status: string; reply_intent?: string }>('GET', `/api/agent/status/${threadId}`),

  getThreadHistory: (threadId: string) =>
    req<{ messages: { role: string; content: string }[] }>('GET', `/api/agent/history/${threadId}`),
};

export function extractEmail(text: string): string | null {
  const match = text.match(/[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}/);
  return match ? match[0] : null;
}

export function formatDate(str: string | undefined): string {
  if (!str) return '';
  const d = new Date(str);
  if (Number.isNaN(d.getTime())) return str;
  const now = new Date();
  if (d.toDateString() === now.toDateString()) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
}

export function formatFullDate(str: string | undefined): string {
  if (!str) return '—';
  const d = new Date(str);
  if (Number.isNaN(d.getTime())) return str;
  return d.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });
}

export function trunc(s: string | undefined, n: number = 70): string {
  if (!s) return '';
  return s.length > n ? s.slice(0, n) + '…' : s;
}

export function escHtml(s: string): string {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

const AVATAR_COLORS = ['#e84b5a', '#6366f1', '#10b981', '#f59e0b', '#8b5cf6', '#0ea5e9', '#ec4899', '#14b8a6'];

export function avatarColor(name: string): string {
  let n = 0;
  for (let i = 0; i < (name || '').length; i++) n += name.charCodeAt(i);
  return AVATAR_COLORS[n % AVATAR_COLORS.length];
}

export function avatarInitials(label: string): string {
  const parts = String(label || '?').split(/[@.\s]+/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return (parts[0] || '?')[0].toUpperCase();
}
