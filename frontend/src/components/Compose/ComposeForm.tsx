import { useState } from 'react';
import { useStore } from '../../store/useStore';
import { api } from '../../api/client';

export function ComposeForm() {
  const currentUser = useStore((s) => s.currentUser);
  const setChatOpen = useStore((s) => s.setChatOpen);
  const addToast = useStore((s) => s.addToast);
  const [to, setTo] = useState('');
  const [cc, setCc] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [sending, setSending] = useState(false);

  const handleSend = async () => {
    if (!to || !body) {
      addToast('Please fill in To and Message fields.', 'error');
      return;
    }

    const userId = currentUser?.user_id ?? currentUser?.id;
    if (!userId) return;

    setSending(true);
    try {
      await api.sendEmail(userId, to, subject || '(no subject)', body);
      addToast('Email sent!', 'success');
      setTo('');
      setCc('');
      setSubject('');
      setBody('');
    } catch (err) {
      addToast(`Failed: ${err instanceof Error ? err.message : 'Unknown error'}`, 'error');
    } finally {
      setSending(false);
    }
  };

  const handleClear = () => {
    setTo('');
    setCc('');
    setSubject('');
    setBody('');
  };

  const handleAIDraft = () => {
    const text = [to && `to ${to}`, subject && `about "${subject}"`].filter(Boolean).join(' ');
    if (text) {
      const threadId = 'thread-' + Date.now();
      useStore.getState().createThread(threadId);
      useStore.getState().addMessageToThread(threadId, {
        id: 'temp-' + Date.now(),
        role: 'user',
        threadId,
        content: text
      });
    }
    setChatOpen(true);
  };

  return (
    <div className="flex-1 overflow-y-auto p-8 flex justify-center">
      <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-[680px]">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-bold">New Message</h2>
          <button className="btn btn-ghost btn-sm" onClick={handleClear}>Clear</button>
        </div>

        <div className="mb-4.5">
          <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">To</label>
          <input
            type="email"
            className="input"
            value={to}
            onChange={(e) => setTo(e.target.value)}
            placeholder="recipient@example.com"
          />
        </div>

        <div className="mb-4.5">
          <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">CC</label>
          <input
            type="email"
            className="input"
            value={cc}
            onChange={(e) => setCc(e.target.value)}
            placeholder="cc@example.com"
          />
        </div>

        <div className="mb-4.5">
          <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">Subject</label>
          <input
            type="text"
            className="input"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Email subject"
          />
        </div>

        <div className="mb-6">
          <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">Message</label>
          <textarea
            className="textarea h-[280px]"
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Write your message here…"
          />
        </div>

        <div className="flex gap-2.5 items-center mt-6 pt-5 border-t border-border">
          <button className="btn btn-primary" onClick={handleSend} disabled={sending}>
            {sending ? 'Sending…' : 'Send Email'}
          </button>
          <button className="btn btn-secondary btn-sm" onClick={handleAIDraft}>Draft with AI</button>
        </div>
      </div>
    </div>
  );
}
