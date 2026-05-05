import { useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { api, escHtml } from '../../api/client';
import type { DraftResponse, Meeting, ChatMessage } from '../../api/types';

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
        <div className="fixed bottom-6 right-6 w-[360px] h-[500px] bg-white rounded-2xl shadow-xl flex flex-col overflow-hidden chat-in z-[1000]">
          <div className="bg-primary text-white p-3.5 flex items-center justify-between flex-shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-[11px] font-bold flex-shrink-0">AI</div>
              <div>
                <div className="font-semibold text-sm">Email Assistant</div>
                <div className="text-[11px] opacity-80 mt-0.25">Ready to help</div>
              </div>
            </div>
            <button className="bg-none border-none text-white/75 text-base cursor-pointer p-1 rounded transition-colors hover:text-white" onClick={() => setChatOpen(false)}>✕</button>
          </div>

          <ChatMessages />
          
          <ChatInput />
        </div>
      )}
    </>
  );
}

function ChatMessages() {
  const messages = useStore((s) => s.chatMessages);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatOpen = useStore((s) => s.chatOpen);

  useEffect(() => {
    if (messages.length === 0) {
      useStore.getState().addChatMessage({
        id: 'init',
        role: 'ai',
        content: "Hi! Describe what you need and I'll handle it — drafting emails, scheduling meetings, and more.",
        isThinking: false,
      });
    }
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatOpen, messages.length]);

  return (
    <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
      {messages.map((msg) => (
        <ChatMessage key={msg.id} msg={msg} />
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}

function ChatMessage({ msg }: { msg: ChatMessage }) {
  const currentUser = useStore((s) => s.currentUser);
  const name = currentUser?.username || currentUser?.email || '?';
  
  if (msg.role === 'system') {
    return (
      <div className="flex justify-center">
        <div className="bg-success-light text-success text-xs font-medium rounded-full px-3.5 py-1.25 max-w-full text-center">
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
        <div className="w-7 h-7 rounded-full bg-primary text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0">AI</div>
        <div className="bg-bg rounded-[14px] px-4 py-3 flex gap-1.25 items-center">
          <span className="w-1.75 h-1.75 rounded-full bg-text-muted animate-blink" />
          <span className="w-1.75 h-1.75 rounded-full bg-text-muted animate-blink" />
          <span className="w-1.75 h-1.75 rounded-full bg-text-muted animate-blink" />
        </div>
      </div>
    );
  }

  return (
    <div className={`flex gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-primary text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0">AI</div>
      )}
      {isUser && (
        <div className="w-7 h-7 rounded-full text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0" style={{ backgroundColor: '#e84b5a' }}>
          {msg.role === 'user' ? (name[0] + (name.split('@')[0][1] || name[1])).toUpperCase() : 'AI'}
        </div>
      )}
      <div className={`max-w-[78%] px-3.5 py-2.25 rounded-[14px] text-sm leading-relaxed ${isUser ? 'bg-primary text-white rounded-br-sm' : 'bg-bg text-text rounded-bl-sm'}`}>
        {msg.question ? (
          <div className="text-text">
            <div className="font-medium mb-1">Please provide more information:</div>
            <div>{escHtml(msg.question)}</div>
          </div>
        ) : msg.draft ? (
          <DraftCard draft={msg.draft} />
        ) : msg.meeting ? (
          <MeetingCard meeting={msg.meeting} />
        ) : (
          <>
            {(msg.content || '').includes('Schedule a meeting') || (msg.content || '').includes('Follow-up email') ? (
              <div>
                {msg.content}
                <div className="flex flex-wrap gap-1.5 mt-2.5">
                  <button className="px-2.75 py-1.25 bg-white border border-border rounded-full text-[11px] text-text-secondary cursor-pointer transition-colors hover:bg-primary-light hover:text-primary hover:border-primary" onClick={(e) => {
                    const input = document.getElementById('chat-input') as HTMLTextAreaElement;
                    input.value = e.currentTarget.textContent || '';
                    input.focus();
                  }}>
                    Schedule a meeting
                  </button>
                  <button className="px-2.75 py-1.25 bg-white border border-border rounded-full text-[11px] text-text-secondary cursor-pointer transition-colors hover:bg-primary-light hover:text-primary hover:border-primary" onClick={(e) => {
                    const input = document.getElementById('chat-input') as HTMLTextAreaElement;
                    input.value = e.currentTarget.textContent || '';
                    input.focus();
                  }}>
                    Follow-up email
                  </button>
                </div>
              </div>
            ) : (
              escHtml(msg.content || '')
            )}
          </>
        )}
      </div>
    </div>
  );
}

function DraftCard({ draft }: { draft: { draft_id: string; recipient: string; subject: string; body: string } }) {
  const [body, setBody] = useState(draft.body);
  const addToast = useStore((s) => s.addToast);
  const currentTab = useStore((s) => s.currentTab);

  const handleSend = async () => {
    try {
      await api.sendDraft(draft.draft_id, body);
      addToast('Email sent successfully!', 'success');
      if (currentTab === 'inbox' && useStore.getState().inboxFilter === 'sent') {
        useStore.getState().setInboxFilter('sent');
      }
    } catch (err) {
      addToast(`Failed: ${err instanceof Error ? err.message : 'Unknown'}`, 'error');
    }
  };

  const handleDiscard = async () => {
    try {
      await api.cancelDraft(draft.draft_id);
      addToast('Draft discarded.', 'info');
    } catch (err) {
      addToast(`Could not discard: ${err instanceof Error ? err.message : 'Unknown'}`, 'error');
    }
  };

  const handleOpenInCompose = () => {
    useStore.getState().setCurrentTab('compose');
    setTimeout(() => {
      const toInput = document.getElementById('compose-to') as HTMLInputElement;
      const subInput = document.getElementById('compose-subject') as HTMLInputElement;
      const bodyInput = document.getElementById('compose-body') as HTMLTextAreaElement;
      if (toInput) toInput.value = draft.recipient;
      if (subInput) subInput.value = draft.subject;
      if (bodyInput) bodyInput.value = body;
    }, 100);
  };

  return (
    <div className="mt-2.5 bg-white border border-border rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 bg-bg border-b border-border">
        <span className="text-[11px] font-semibold text-text-secondary uppercase tracking-wider">Email Draft</span>
        <span className="text-[10px] font-semibold bg-success-light text-success px-1.75 py-0.5 rounded-full">Ready</span>
      </div>
      <div className="px-3 py-2 border-b border-border">
        <div className="flex gap-2 text-xs mb-0.5">
          <span className="text-text-muted">To</span>
          <span className="text-text font-medium">{escHtml(draft.recipient || '—')}</span>
        </div>
        <div className="flex gap-2 text-xs">
          <span className="text-text-muted">Subject</span>
          <span className="text-text font-medium">{escHtml(draft.subject || '—')}</span>
        </div>
      </div>
      <div className="px-3 py-2">
        <textarea
          className="w-full text-xs leading-relaxed text-text resize-y border-none p-0 bg-white min-h-[90px]"
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
      </div>
      <div className="flex gap-1.5 px-3 py-2 bg-bg border-t border-border">
        <button className="btn btn-primary btn-sm" onClick={handleSend}>Send Email</button>
        <button className="btn btn-secondary btn-sm" onClick={handleOpenInCompose}>Open in Compose</button>
        <button className="btn btn-ghost btn-sm" onClick={handleDiscard}>Discard</button>
      </div>
    </div>
  );
}

function MeetingCard({ meeting }: { meeting: Meeting }) {
  const addToast = useStore((s) => s.addToast);
  const activeThreadId = useStore((s) => s.activeThreadId);

  const handleConfirm = async () => {
    if (!activeThreadId) return;
    try {
      await api.confirmMeeting(activeThreadId);
      addToast('Meeting confirmed! The email will be sent.', 'success');
    } catch (err) {
      addToast(`Failed: ${err instanceof Error ? err.message : 'Unknown'}`, 'error');
    }
  };

  const handleDecline = async () => {
    if (!activeThreadId) return;
    try {
      await api.declineMeeting(activeThreadId);
      addToast('Meeting declined.', 'info');
    } catch (err) {
      addToast(`Failed: ${err instanceof Error ? err.message : 'Unknown'}`, 'error');
    }
  };

  const hasMeeting = meeting.participants?.length || meeting.date || meeting.time;

  if (!hasMeeting) return null;

  return (
    <div className="mt-2.5 bg-primary-light border border-primary/20 rounded-lg p-3">
      <div className="text-[11px] font-bold text-primary uppercase tracking-wider mb-2">Meeting Details</div>
      {meeting.participants?.length && (
        <div className="flex gap-2 text-xs mb-1">
          <span className="text-text-secondary">Participants</span>
          <span className="text-text font-medium">{escHtml(meeting.participants.join(', '))}</span>
        </div>
      )}
      {meeting.date && (
        <div className="flex gap-2 text-xs mb-1">
          <span className="text-text-secondary">Date</span>
          <span className="text-text font-medium">{escHtml(meeting.date)}</span>
        </div>
      )}
      {meeting.time && (
        <div className="flex gap-2 text-xs mb-2">
          <span className="text-text-secondary">Time</span>
          <span className="text-text font-medium">{escHtml(meeting.time)}</span>
        </div>
      )}
      <div className="flex gap-2 mt-2.5">
        <button className="btn btn-success btn-sm" onClick={handleConfirm}>Confirm Meeting</button>
        <button className="btn btn-ghost btn-sm" onClick={handleDecline}>Decline</button>
      </div>
    </div>
  );
}

function ChatInput() {
  const [text, setText] = useState('');
  const currentUser = useStore((s) => s.currentUser);
  const addChatMessage = useStore((s) => s.addChatMessage);
  const setActiveDraftId = useStore((s) => s.setActiveDraftId);
  const setActiveThreadId = useStore((s) => s.setActiveThreadId);

  const handleSend = async () => {
    if (!text.trim() || !currentUser) return;

    const userMsg = text.trim();
    setText('');
    
    addChatMessage({
      id: 'user-' + Date.now(),
      role: 'user',
      content: userMsg
    });

    const userId = currentUser.user_id ?? currentUser.id;

    // Show thinking indicator
    addChatMessage({
      id: 'thinking-' + Date.now(),
      role: 'ai',
      content: '',
      isThinking: true
    });

    try {
      // Send full message to agent - let agent handle email extraction
      const result: DraftResponse = await api.createDraft(userId, '', '', userMsg);
      
      // Remove thinking indicator
      const thinkingId = useStore.getState().chatMessages
        .find(m => m.isThinking)?.id;
      if (thinkingId) {
        useStore.getState().removeChatMessage(thinkingId);
      }

      // Handle agent response
      if (result.error) {
        addChatMessage({
          id: 'ai-' + Date.now(),
          role: 'ai',
          content: result.error
        });
        return;
      }

      // Check if agent needs more information
      if (result.status === 'interrupted' && result.question) {
        setActiveDraftId(result.draft_id);
        setActiveThreadId(result.thread_id || null);
        
        addChatMessage({
          id: 'ai-' + Date.now(),
          role: 'ai',
          question: result.question
        });
        return;
      }

      // Agent generated a draft
      if (result.draft) {
        setActiveDraftId(result.draft_id);
        setActiveThreadId(result.thread_id || null);

        addChatMessage({
          id: 'ai-' + Date.now(),
          role: 'ai',
          draft: result.draft
        });

        // Check for meeting details if thread exists
        if (result.thread_id) {
          try {
            const thread = await api.getThread(result.thread_id);
            if (thread.meeting) {
              addChatMessage({
                id: 'meeting-' + Date.now(),
                role: 'ai',
                meeting: thread.meeting
              });
            }
          } catch {}
        }
      }
    } catch (err) {
      // Remove thinking indicator
      const thinkingId = useStore.getState().chatMessages
        .find(m => m.isThinking)?.id;
      if (thinkingId) {
        useStore.getState().removeChatMessage(thinkingId);
      }
      
      addChatMessage({
        id: 'error-' + Date.now(),
        role: 'ai',
        content: `Sorry, I couldn't process that: ${err instanceof Error ? err.message : 'Unknown error'}`
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
    <div className="p-3 border-t border-border flex-shrink-0 bg-white">
      <div className="flex gap-2 items-end">
        <textarea
          id="chat-input"
          className="flex-1 border border-border-input rounded-full px-3.5 py-2 text-xs resize-none max-h-[100px] leading-relaxed text-text bg-bg transition-colors"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="e.g. Draft an email to bob@example.com…"
          rows={1}
        />
        <button
          className="w-8.5 h-8.5 rounded-full bg-primary text-white border-none text-[11px] font-bold cursor-pointer flex-shrink-0 transition-colors hover:bg-primary-hover hover:scale-105"
          onClick={handleSend}
        >
          Send
        </button>
      </div>
    </div>
  );
}