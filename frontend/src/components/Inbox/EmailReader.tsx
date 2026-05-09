import { useEffect, useState } from 'react';
import { useStore } from '../../store/useStore';
import { api, formatFullDate, avatarColor, avatarInitials, escHtml } from '../../api/client';
import type { Email } from '../../api/types';

export function EmailReader() {
  const selectedEmail = useStore((s) => s.selectedEmail);
  const setReplyTargetId = useStore((s) => s.setReplyTargetId);
  const addToast = useStore((s) => s.addToast);
  
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState<Email | null>(null);

  useEffect(() => {
    if (!selectedEmail) {
      setEmail(null);
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
  const ccLabel = email.cc?.length ? email.cc.join(', ') : null;

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
            <div className="text-xs text-text-secondary">To: {escHtml(recipientLabel)}{ccLabel ? `  CC: ${escHtml(ccLabel)}` : ''}</div>
          </div>
          <div className="text-xs text-text-muted">{formatFullDate(email.created_at)}</div>
        </div>

        <div className="text-sm leading-relaxed text-text whitespace-pre-wrap mb-7">{escHtml(email.body || '')}</div>

        <div className="flex gap-2.5">
          <button className="btn btn-primary btn-sm" onClick={() => document.getElementById('reply-modal')?.classList.remove('hidden')}>
            Reply
          </button>
        </div>
      </div>
    </div>
  );
}