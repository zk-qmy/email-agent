import { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { api, escHtml } from '../../api/client';
import type { Draft, Meeting, ChatMessage } from '../../api/types';

export function ChatWidget() {
  const currentUser = useStore((s) => s.currentUser);
  const chatOpen = useStore((s) => s.chatOpen);
  const setChatOpen = useStore((s) => s.setChatOpen);

  if (!currentUser) return null;

  return (
    <>
      {!chatOpen && (
        <button
          className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-primary text-white border-none cursor-pointer text-xs font-bold shadow-lg hover:shadow-xl hover:scale-105 transition-all z-[1000] flex items-center justify-center"
          onClick={() => setChatOpen(true)}
        >
          AI
        </button>
      )}

      {chatOpen && (
        <div className="fixed bottom-6 right-6 w-[400px] h-[500px] bg-white rounded-2xl shadow-xl flex overflow-hidden chat-in z-[1000]">
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
        <div className="w-6 h-6 rounded-full text-white text-[9px] font-bold flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#e84b5a' }}>
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

function ChatInput() {
  const [text, setText] = useState('');
  const currentUser = useStore((s) => s.currentUser);
  const activeThreadId = useStore((s) => s.activeThreadId);
  const allThreadIds = useStore((s) => s.allThreadIds);
  const addMessageToThread = useStore((s) => s.addMessageToThread);

  const hasThread = activeThreadId && allThreadIds.length > 0;

  const handleSend = async () => {
    if (!text.trim() || !currentUser || !hasThread) return;

    const userMsg = text.trim();
    setText('');

    const userId = currentUser.user_id ?? currentUser.id;

    addMessageToThread(activeThreadId, {
      id: 'user-' + Date.now(),
      role: 'user',
      threadId: activeThreadId,
      content: userMsg,
    });

    try {
      const result = await api.createDraft(userId, userMsg, activeThreadId);
      if (result.error) {
        addMessageToThread(activeThreadId, {
          id: 'error-' + Date.now(),
          role: 'ai',
          threadId: activeThreadId,
          content: result.error,
        });
      }
      if (result.status === 'interrupted' && result.question) {
        addMessageToThread(activeThreadId, {
          id: 'question-' + Date.now(),
          role: 'ai',
          threadId: activeThreadId,
          question: result.question,
        });
      }
      if (result.draft) {
        addMessageToThread(activeThreadId, {
          id: 'draft-' + Date.now(),
          role: 'ai',
          threadId: activeThreadId,
          draft: result.draft,
        });
      }
    } catch (err) {
      addMessageToThread(activeThreadId, {
        id: 'error-' + Date.now(),
        role: 'ai',
        threadId: activeThreadId,
        content: `Error: ${err instanceof Error ? err.message : 'Unknown'}`,
      });
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="p-2 border-t border-border flex-shrink-0 bg-white">
      <div className="flex gap-1.5 items-end">
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