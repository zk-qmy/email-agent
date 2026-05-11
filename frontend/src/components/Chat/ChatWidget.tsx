import { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { api, escHtml } from '../../api/client';
import type { Draft, Meeting, ChatMessage, PdfValidateResponse } from '../../api/types';

export function ChatWidget() {
  const currentUser = useStore((s) => s.currentUser);
  const chatOpen = useStore((s) => s.chatOpen);
  const setChatOpen = useStore((s) => s.setChatOpen);
  const allThreadIds = useStore((s) => s.allThreadIds);
  const createThread = useStore((s) => s.createThread);
  const setActiveThreadId = useStore((s) => s.setActiveThreadId);

  if (!currentUser) return null;

  const handleOpenChat = async () => {
    if (!currentUser) return;
    const userId = currentUser.user_id ?? currentUser.id;

    if (allThreadIds.length === 0) {
      try {
        const result = await api.createThread(userId);
        createThread(result.thread_id);
        setActiveThreadId(result.thread_id);
      } catch (err) {
        console.error('Failed to create thread:', err);
      }
    }

    setChatOpen(true);
  };

  return (
    <>
      {!chatOpen && (
        <button
          className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-primary text-white border-none cursor-pointer text-xs font-bold shadow-lg hover:shadow-xl hover:scale-105 transition-all z-[1000] flex items-center justify-center"
          onClick={handleOpenChat}
        >
          AI
        </button>
      )}

      {chatOpen && (
        <div className="fixed bottom-6 right-6 w-[min(90vw,400px)] h-[min(85vh,500px)] bg-white rounded-2xl shadow-xl flex overflow-hidden chat-in z-[1000]">
          <div className="w-20 bg-bg border-r border-border flex flex-col">
            <ThreadSidebar />
          </div>
          <div className="flex-1 flex flex-col">
            <div className="bg-primary text-white p-3 flex items-center justify-between flex-shrink-0">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center text-[9px] font-bold">AI</div>
                <span className="font-semibold text-sm">Assistant</span>
              </div>
              <button className="bg-none border-none text-white/75 text-sm cursor-pointer p-1" onClick={() => setChatOpen(false)}>✕</button>
            </div>
            <ChatMessages />
            <ChatInput />
          </div>
        </div>
      )}
    </>
  );
}

function ThreadSidebar() {
  const allThreadIds = useStore((s) => s.allThreadIds);
  const activeThreadId = useStore((s) => s.activeThreadId);
  const setActiveThreadId = useStore((s) => s.setActiveThreadId);
  const createThread = useStore((s) => s.createThread);
  const currentUser = useStore((s) => s.currentUser);

  const handleNewThread = async () => {
    if (!currentUser) return;
    const userId = currentUser.user_id ?? currentUser.id;
    try {
      const result = await api.createThread(userId);
      createThread(result.thread_id);
      setActiveThreadId(result.thread_id);
    } catch (err) {
      console.error('Failed to create thread:', err);
    }
  };

  return (
    <div className="flex-1 flex flex-col p-2 gap-1.5 overflow-y-auto">
      {allThreadIds.map((threadId, idx) => (
        <button
          key={threadId}
          className={`p-2 rounded text-[10px] font-medium text-left transition-colors ${
            activeThreadId === threadId
              ? 'bg-primary text-white'
              : 'text-text-secondary hover:bg-border'
          }`}
          onClick={() => setActiveThreadId(threadId)}
        >
          Thread {idx + 1}
        </button>
      ))}
      <button
        className="p-2 rounded text-[10px] font-medium text-text-secondary hover:bg-border hover:text-text transition-colors border border-dashed border-border"
        onClick={handleNewThread}
      >
        + New
      </button>
    </div>
  );
}

function ChatMessages() {
  const chatThreads = useStore((s) => s.chatThreads);
  const activeThreadId = useStore((s) => s.activeThreadId);
  const allThreadIds = useStore((s) => s.allThreadIds);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatOpen = useStore((s) => s.chatOpen);

  const messages = activeThreadId ? (chatThreads[activeThreadId] || []) : [];

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatOpen, messages.length, activeThreadId]);

  if (allThreadIds.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center p-4 text-center text-text-muted text-xs">
        Create a new thread to start
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
      {messages.map((msg) => (
        <ThreadedChatMessage key={msg.id} msg={msg} />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}

function ThreadedChatMessage({ msg }: { msg: ChatMessage }) {
  const currentUser = useStore((s) => s.currentUser);
  const name = currentUser?.username || currentUser?.email || '?';
  const activeThreadId = useStore((s) => s.activeThreadId);

  if (msg.role === 'system') {
    return (
      <div className="flex justify-center">
        <div className="bg-success-light text-success text-xs font-medium rounded-full px-3 py-1 max-w-full text-center">
          {escHtml(msg.content || '')}
        </div>
      </div>
    );
  }

  const isUser = msg.role === 'user';
  const isThinking = msg.isThinking;

  if (isThinking) {
    return (
      <div className="flex gap-2">
        <div className="w-6 h-6 rounded-full bg-primary text-white text-[9px] font-bold flex items-center justify-center flex-shrink-0">AI</div>
        <div className="bg-bg rounded-[10px] px-3 py-2 flex gap-1 items-center">
          <span className="w-1.5 h-1.5 rounded-full bg-text-muted animate-blink" />
          <span className="w-1.5 h-1.5 rounded-full bg-text-muted animate-blink" />
          <span className="w-1.5 h-1.5 rounded-full bg-text-muted animate-blink" />
        </div>
      </div>
    );
  }

  return (
    <div className={`flex gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
      {!isUser && (
        <div className="w-6 h-6 rounded-full bg-primary text-white text-[9px] font-bold flex items-center justify-center flex-shrink-0">AI</div>
      )}
      {isUser && (
        <div className="w-6 h-6 rounded-full text-white text-[9px] font-bold flex items-center justify-center flex-shrink-0 bg-primary">
          {name[0].toUpperCase()}
        </div>
      )}
      <div className={`max-w-[80%] px-3 py-1.5 rounded-[10px] text-xs leading-relaxed ${isUser ? 'bg-primary text-white rounded-br-sm' : 'bg-bg text-text rounded-bl-sm'}`}>
        {msg.question ? (
          <div className="text-text">
            <div className="font-medium mb-1 text-[10px]">Please provide:</div>
            <div>{escHtml(msg.question)}</div>
          </div>
        ) : msg.draft ? (
          <ThreadDraftCard draft={msg.draft} threadId={activeThreadId || ''} />
        ) : msg.meeting ? (
          <ThreadMeetingCard meeting={msg.meeting} threadId={activeThreadId || ''} />
        ) : msg.pdfResult ? (
          <PdfResultCard result={msg.pdfResult} />
        ) : (
          escHtml(msg.content || '')
        )}
      </div>
    </div>
  );
}

function ThreadDraftCard({ draft, threadId }: { draft: Draft; threadId: string }) {
  const addToast = useStore((s) => s.addToast);
  const currentTab = useStore((s) => s.currentTab);

  const handleSend = async () => {
    const currentUser = useStore.getState().currentUser;
    const userId = currentUser?.user_id ?? currentUser?.id;
    if (!userId) return;
    try {
      await api.sendDraft(threadId, userId, "y");
      addToast('Email sent!', 'success');
      if (currentTab === 'inbox' && useStore.getState().inboxFilter === 'sent') {
        useStore.getState().setInboxFilter('sent');
      }
    } catch (err) {
      addToast(`Failed: ${err instanceof Error ? err.message : 'Unknown'}`, 'error');
    }
  };

  const handleDiscard = async () => {
    try {
      await api.cancelDraft(threadId);
      addToast('Draft discarded.', 'info');
    } catch (err) {
      addToast(`Error: ${err instanceof Error ? err.message : 'Unknown'}`, 'error');
    }
  };

  return (
    <div className="mt-1.5 bg-white border border-border rounded overflow-hidden">
      <div className="flex items-center justify-between px-2 py-1 bg-bg border-b border-border">
        <span className="text-[9px] font-semibold text-text-secondary uppercase">Draft</span>
      </div>
      <div className="px-2 py-1.5 border-b border-border">
        <div className="text-[10px] mb-0.5">
          <span className="text-text-muted">To: </span>
          <span className="font-medium">{escHtml(draft.recipient_username || '—')}</span>
        </div>
        <div className="text-[10px]">
          <span className="text-text-muted">Subj: </span>
          <span className="font-medium">{escHtml(draft.subject || '—')}</span>
        </div>
      </div>
      <div className="px-2 py-1.5">
        <div className="text-[10px] whitespace-pre-wrap">{draft.body}</div>
      </div>
      <div className="flex gap-1 px-2 py-1.5 bg-bg border-t border-border">
        <button className="btn btn-primary btn-xs" onClick={handleSend}>Send</button>
        <button className="btn btn-ghost btn-xs" onClick={handleDiscard}>Discard</button>
      </div>
    </div>
  );
}

function ThreadMeetingCard({ meeting, threadId }: { meeting: Meeting; threadId: string }) {
  const addToast = useStore((s) => s.addToast);

  const handleConfirm = async () => {
    try {
      await api.confirmMeeting(threadId);
      addToast('Meeting confirmed!', 'success');
    } catch (err) {
      addToast(`Error: ${err instanceof Error ? err.message : 'Unknown'}`, 'error');
    }
  };

  const handleDecline = async () => {
    try {
      await api.declineMeeting(threadId);
      addToast('Meeting declined.', 'info');
    } catch (err) {
      addToast(`Error: ${err instanceof Error ? err.message : 'Unknown'}`, 'error');
    }
  };

  const hasMeeting = meeting.participants?.length || meeting.date || meeting.time;
  if (!hasMeeting) return null;

  return (
    <div className="mt-1.5 bg-primary-light border border-primary/20 rounded p-2">
      <div className="text-[9px] font-bold text-primary uppercase mb-1">Meeting</div>
      {meeting.date && (
        <div className="text-[10px]"><span className="text-text-secondary">Date: </span><span className="font-medium">{escHtml(meeting.date)}</span></div>
      )}
      {meeting.time && (
        <div className="text-[10px]"><span className="text-text-secondary">Time: </span><span className="font-medium">{escHtml(meeting.time)}</span></div>
      )}
      <div className="flex gap-1 mt-2">
        <button className="btn btn-success btn-xs" onClick={handleConfirm}>Confirm</button>
        <button className="btn btn-ghost btn-xs" onClick={handleDecline}>Decline</button>
      </div>
    </div>
  );
}

function PdfResultCard({ result }: { result: PdfValidateResponse }) {
  return (
    <div className="mt-1.5 bg-white border border-border rounded overflow-hidden">
      <div className="px-2 py-1 bg-bg border-b border-border">
        <span className="text-[9px] font-semibold text-text-secondary uppercase">PDF Validation</span>
      </div>
      {result.missing_fields.length > 0 && (
        <div className="px-2 py-1.5 border-b border-border bg-warning-bg">
          <div className="text-[9px] font-semibold text-warning uppercase mb-0.5">
            Missing ({result.missing_fields.length})
          </div>
          <ul className="text-[10px] text-text list-none m-0 p-0">
            {result.missing_fields.map((f, i) => (
              <li key={i} className="before:content-['•'] before:mr-1 before:text-warning"> {escHtml(f)}</li>
            ))}
          </ul>
        </div>
      )}
      <div className="px-2 py-1.5 border-b border-border">
        <div className="text-[9px] font-semibold text-text-secondary uppercase mb-0.5">Required</div>
        <div className="text-[10px] text-text flex flex-wrap gap-x-2">
          {result.required_fields.map((f, i) => (
            <span key={i}>{escHtml(f)}{i < result.required_fields.length - 1 ? ',' : ''}</span>
          ))}
        </div>
      </div>
      {result.optional_fields.length > 0 && (
        <div className="px-2 py-1.5 border-b border-border">
          <div className="text-[9px] font-semibold text-text-secondary uppercase mb-0.5">Optional</div>
          <div className="text-[10px] text-text-muted flex flex-wrap gap-x-2">
            {result.optional_fields.map((f, i) => (
              <span key={i}>{escHtml(f)}{i < result.optional_fields.length - 1 ? ',' : ''}</span>
            ))}
          </div>
        </div>
      )}
      <div className="px-2 py-1.5">
        <div className="text-[10px] text-text leading-relaxed">{escHtml(result.message_to_user)}</div>
      </div>
    </div>
  );
}

function ChatInput() {
  const [text, setText] = useState('');
  const [attachments, setAttachments] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const currentUser = useStore((s) => s.currentUser);
  const activeThreadId = useStore((s) => s.activeThreadId);
  const allThreadIds = useStore((s) => s.allThreadIds);
  const addMessageToThread = useStore((s) => s.addMessageToThread);

  const hasThread = activeThreadId && allThreadIds.length > 0;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    setAttachments(prev => [...prev, ...files]);
    e.target.value = '';
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const handleSend = async () => {
    if ((!text.trim() && attachments.length === 0) || !currentUser || !hasThread) return;

    const userMsg = text.trim();
    const sendThreadId = activeThreadId;
    const userId = currentUser.user_id ?? currentUser.id;
    const role = currentUser.role || 'student';
    setText('');

    if (userMsg) {
      addMessageToThread(sendThreadId, {
        id: 'user-' + Date.now(),
        role: 'user',
        threadId: sendThreadId,
        content: userMsg,
      });
    }

    if (attachments.length > 0) {
      setUploading(true);
      Promise.all(attachments.map(file => uploadPdf(file, sendThreadId, role)))
        .finally(() => { setAttachments([]); setUploading(false); });
    }

    if (!userMsg) return;

    let prompt = userMsg;
    const selectedEmail = useStore.getState().selectedEmail;

    if (userMsg.toLowerCase().includes('summarize') && selectedEmail?.thread_id) {
      prompt = `[Context: User ID: ${userId}, Viewing email thread ID: ${selectedEmail.thread_id}]\n${userMsg}`;
    }

    try {
      const result = await api.createDraft(userId, prompt, sendThreadId);
      if (result.error) {
        addMessageToThread(sendThreadId, {
          id: 'error-' + Date.now(),
          role: 'ai',
          threadId: sendThreadId,
          content: result.error,
        });
      }
      if (result.status === 'interrupted' && result.question) {
        addMessageToThread(sendThreadId, {
          id: 'question-' + Date.now(),
          role: 'ai',
          threadId: sendThreadId,
          question: result.question,
        });
      }
      if (result.draft) {
        addMessageToThread(sendThreadId, {
          id: 'draft-' + Date.now(),
          role: 'ai',
          threadId: sendThreadId,
          draft: result.draft,
        });
      }
    } catch (err) {
      addMessageToThread(sendThreadId, {
        id: 'error-' + Date.now(),
        role: 'ai',
        threadId: sendThreadId,
        content: `Error: ${err instanceof Error ? err.message : 'Unknown'}`,
      });
    }
  };

  async function uploadPdf(file: File, threadId: string, role: string) {
    const msgId = 'pdf-' + Date.now() + '-' + Math.random().toString(36).slice(2, 6);
    if (file.type !== 'application/pdf') {
      addMessageToThread(threadId, {
        id: msgId, role: 'ai', threadId,
        content: `Unsupported file type: ${file.type || file.name}. Only PDF files are supported.`,
      });
      return;
    }
    try {
      const result = await api.validatePdfUpload(file, role);
      addMessageToThread(threadId, {
        id: msgId, role: 'ai', threadId,
        pdfResult: result,
      });
    } catch (err) {
      addMessageToThread(threadId, {
        id: msgId, role: 'ai', threadId,
        content: `PDF Error: ${err instanceof Error ? err.message : 'Unknown'}`,
      });
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-2 border-t border-border flex-shrink-0 bg-white">
      {attachments.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2">
          {attachments.map((file, i) => (
            <div key={i} className={`flex items-center gap-1 bg-bg border border-border rounded-full px-2 py-0.5 text-[10px] text-text ${uploading ? 'opacity-70' : ''}`}>
              <span className={`truncate max-w-[100px] ${uploading ? 'text-text-muted' : ''}`}>{file.name}</span>
              {uploading ? (
                <span className="text-text-muted text-[9px] ml-0.5">⋯</span>
              ) : (
                <button
                  type="button"
                  className="text-text-muted hover:text-primary leading-none ml-0.5"
                  onClick={() => removeAttachment(i)}
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>
      )}
      <div className="flex gap-1.5 items-end">
        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFileChange}
        />
        <button
          type="button"
          className={`flex-shrink-0 w-5 h-5 flex items-center justify-center ${hasThread ? 'cursor-pointer text-text-secondary hover:text-primary' : 'opacity-50 cursor-not-allowed text-text-muted'}`}
          onClick={() => fileInputRef.current?.click()}
          disabled={!hasThread}
          title="Attach files"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
          </svg>
        </button>
        <textarea
          id="chat-input"
          className={`flex-1 border border-border-input rounded-full px-2.5 py-1.5 text-xs resize-none max-h-[80px] text-text bg-bg ${!hasThread ? 'opacity-50 cursor-not-allowed' : ''}`}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={hasThread ? "Describe what you need..." : "Create a new thread to start"}
          disabled={!hasThread}
          rows={1}
        />
        <button
          className={`w-7 h-7 rounded-full text-white border-none text-[9px] font-bold cursor-pointer flex-shrink-0 ${hasThread ? 'bg-primary' : 'bg-text-muted cursor-not-allowed'}`}
          onClick={handleSend}
          disabled={!hasThread}
        >
          Send
        </button>
      </div>
    </div>
  );
}
