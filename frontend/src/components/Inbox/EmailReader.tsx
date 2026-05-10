import { useEffect, useState } from 'react';
import { useStore } from '../../store/useStore';
import { api, formatFullDate, avatarColor, avatarInitials, escHtml } from '../../api/client';
import type { Email } from '../../api/types';

export function EmailReader() {
  const selectedEmail = useStore((s) => s.selectedEmail);
  const setReplyTargetId = useStore((s) => s.setReplyTargetId);
  const addToast = useStore((s) => s.addToast);
  const currentUser = useStore((s) => s.currentUser);

  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState<Email | null>(null);
  const [summary, setSummary] = useState<string | null>(null);
  const [summarizing, setSummarizing] = useState(false);

  const handleSummarize = async () => {
    if (!email || !currentUser) return;
    const userId = currentUser.user_id ?? currentUser.id;
    setSummarizing(true);
    setSummary(null);
    try {
      const result = await api.createDraft(userId, `[User ID: ${userId}] Summarize the email thread with ID: ${email.id}`);
      const text = result.draft?.body || (result.messages?.map(m => m.content).join('\n')) || null;
      setSummary(text || 'No summary returned.');
    } catch (err) {
      addToast(`Summarize failed: ${err instanceof Error ? err.message : 'Unknown error'}`, 'error');
    } finally {
      setSummarizing(false);
    }
  };

  useEffect(() => {
    if (!selectedEmail) {
      setEmail(null);
      setSummary(null);
      return;
    }

    const loadEmail = async () => {
      setLoading(true);
      try {
        await api.markRead(selectedEmail.id);
        const data = await api.getEmail(selectedEmail.id);
        setEmail(data);
        setReplyTargetId(data.id);
      } catch (err) {
        console.error('Failed to load email:', err);
        addToast('Failed to load email', 'error');
      } finally {
        setLoading(false);
      }
    };

    loadEmail();
  }, [selectedEmail, setReplyTargetId, addToast]);

  if (!selectedEmail) {
    return (
      <div className="flex-1 bg-bg flex items-center justify-center text-text-muted text-xs">
        Select an email to read
      </div>
    );
  }

  if (loading || !email) {
    return (
      <div className="flex-1 bg-bg flex items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }

  const senderLabel = email.sender_email || String(email.sender_id || 'Unknown');
  const recipientLabel = email.recipient_email || String(email.recipient_id || 'Unknown');

  return (
    <div className="flex-1 bg-bg overflow-y-auto p-7">
      <div className="max-w-[760px] mx-auto bg-white rounded-xl p-7 shadow-sm">
        <div className="text-xl font-bold text-text mb-4 leading-tight">{escHtml(email.subject || '(no subject)')}</div>
        
        <div className="flex items-center gap-3 mb-6 pb-5 border-b border-border">
          <div className="w-10 h-10 rounded-full text-white text-[13px] font-semibold flex items-center justify-center flex-shrink-0" style={{ backgroundColor: avatarColor(senderLabel) }}>
            {avatarInitials(senderLabel)}
          </div>
          <div className="flex-1">
            <div className="font-semibold text-sm">{escHtml(senderLabel)}</div>
            <div className="text-xs text-text-secondary">To: {escHtml(recipientLabel)}</div>
          </div>
          <div className="text-xs text-text-muted">{formatFullDate(email.created_at)}</div>
        </div>

        <div className="text-sm leading-relaxed text-text whitespace-pre-wrap mb-7">{escHtml(email.body || '')}</div>

        {summary && (
          <div className="mb-6 bg-bg border border-border rounded-lg p-4">
            <div className="text-[11px] font-semibold text-text-secondary uppercase tracking-wider mb-2">Summary</div>
            <div className="text-sm leading-relaxed text-text whitespace-pre-wrap">{summary}</div>
          </div>
        )}

        <div className="flex gap-2.5">
          <button className="btn btn-primary btn-sm" onClick={() => document.getElementById('reply-modal')?.classList.remove('hidden')}>
            Reply
          </button>
          <button className="btn btn-secondary btn-sm" onClick={handleSummarize} disabled={summarizing}>
            {summarizing ? 'Summarizing…' : 'Summarize'}
          </button>
        </div>
      </div>
    </div>
  );
}