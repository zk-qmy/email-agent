import { useState, useRef } from 'react';
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
  const [attachments, setAttachments] = useState<File[]>([]);
  const [sending, setSending] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSend = async () => {
    if (!to || !body) {
      addToast('Please fill in To and Message fields.', 'error');
      return;
    }

    const userId = currentUser?.user_id ?? currentUser?.id;
    if (!userId) return;

    setSending(true);
    try {
      const ccList = cc.split(',').map(s => s.trim()).filter(Boolean);
      const bccList = (document.getElementById('bcc-input') as HTMLInputElement)?.value
        ?.split(',').map(s => s.trim()).filter(Boolean) || [];
      await api.sendEmail(userId, to, subject || '(no subject)', body, ccList, bccList);
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
    setAttachments([]);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setAttachments(prev => [...prev, ...files]);
    e.target.value = '';
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
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
    <div className="h-full overflow-y-auto p-8 flex justify-center">
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
            type="text"
            className="input"
            value={cc}
            onChange={(e) => setCc(e.target.value)}
            placeholder="cc@example.com (comma-separated)"
          />
        </div>

        <div className="mb-4.5">
          <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">BCC</label>
          <input
            id="bcc-input"
            type="text"
            className="input"
            placeholder="bcc@example.com (comma-separated)"
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

        <div className="mb-6">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileChange}
          />
          <button
            type="button"
            className="btn btn-ghost btn-sm flex items-center gap-1.5"
            onClick={() => fileInputRef.current?.click()}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
            Attach files
          </button>
          {attachments.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-2">
              {attachments.map((file, i) => (
                <div key={i} className="flex items-center gap-1.5 bg-bg border border-border rounded-full px-3 py-1 text-xs text-text">
                  <span className="truncate max-w-[180px]">{file.name}</span>
                  <span className="text-text-muted">({(file.size / 1024).toFixed(0)}KB)</span>
                  <button
                    type="button"
                    className="text-text-muted hover:text-danger ml-1 leading-none"
                    onClick={() => removeAttachment(i)}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
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
