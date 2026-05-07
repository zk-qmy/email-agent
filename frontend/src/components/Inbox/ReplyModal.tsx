import { useState } from 'react';
import { useStore } from '../../store/useStore';
import { api } from '../../api/client';

export function ReplyModal() {
  const currentUser = useStore((s) => s.currentUser);
  const replyTargetId = useStore((s) => s.replyTargetId);
  const addToast = useStore((s) => s.addToast);
  const [body, setBody] = useState('');
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    if (!body || !replyTargetId) return;
    
    const userId = currentUser?.user_id ?? currentUser?.id;
    if (!userId) return;

    setSending(true);
    try {
      await api.replyEmail(userId, replyTargetId, body);
      addToast('Reply sent!', 'success');
      setBody('');
      document.getElementById('reply-modal')?.classList.add('hidden');
    } catch (err) {
      addToast(`Failed: ${err instanceof Error ? err.message : 'Unknown error'}`, 'error');
    } finally {
      setSending(false);
    }
  };

  const handleClose = () => {
    document.getElementById('reply-modal')?.classList.add('hidden');
    setBody('');
  };

  return (
    <div id="reply-modal" className="fixed inset-0 bg-black/40 flex items-center justify-center z-[500] hidden" onClick={(e) => e.target === e.currentTarget && handleClose()}>
      <div className="bg-white rounded-xl shadow-md w-[480px] max-w-[95vw] overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h3 className="text-sm font-bold">Reply</h3>
          <button className="bg-none border-none text-text-muted text-base cursor-pointer p-1 rounded hover:bg-bg" onClick={handleClose}>
            ✕
          </button>
        </div>
        <div className="p-5">
          <div className="mb-4">
            <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">Message</label>
            <textarea
              className="textarea h-32"
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="Type your reply…"
              autoFocus
            />
          </div>
        </div>
        <div className="flex justify-end gap-2.5 px-5 py-4 border-t border-border bg-bg">
          <button className="btn btn-ghost" onClick={handleClose}>Cancel</button>
          <button className="btn btn-primary" onClick={handleSend} disabled={sending || !body}>
            {sending ? 'Sending…' : 'Send Reply'}
          </button>
        </div>
      </div>
    </div>
  );
}