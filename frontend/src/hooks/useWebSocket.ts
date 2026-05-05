import { useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';
import type { Draft } from '../api/types';

interface WsEvent {
  event?: string;
  thread_id?: string;
  draft?: { recipient?: string; recipient_username?: string; recipient_email?: string; subject: string; body: string };
  interrupt?: { type?: string; question?: string };
  message?: string;
  reply_body?: string;
  sender?: string;
  intent?: string;
}

export function useWebSocket(userId: number | undefined) {
  const wsRef = useRef<WebSocket | null>(null);
  const addToast = useStore((s) => s.addToast);
  const setEmails = useStore((s) => s.setEmails);
  const setCurrentTab = useStore((s) => s.setCurrentTab);
  const createThread = useStore((s) => s.createThread);
  const addMessageToThread = useStore((s) => s.addMessageToThread);
  const removeMessageFromThread = useStore((s) => s.removeMessageFromThread);
  const updateMessageInThread = useStore((s) => s.updateMessageInThread);
  const setActiveThreadId = useStore((s) => s.setActiveThreadId);

  useEffect(() => {
    if (!userId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsUrl = `${protocol}://${window.location.hostname}:5001/ws/push/${userId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('[ws] Connected to backend');
    };

    ws.onclose = () => {
      console.log('[ws] Disconnected, reconnecting...');
      setTimeout(() => {
        if (wsRef.current?.readyState !== WebSocket.OPEN) {
          const newWs = new WebSocket(wsUrl);
          wsRef.current = newWs;
        }
      }, 5000);
    };

    ws.onmessage = (ev) => {
      try {
        const data: WsEvent = JSON.parse(ev.data);
        const event = data.event;
        const threadId = data.thread_id;

        console.log('[ws] Received:', event, threadId);

        if (event === 'new_email') {
          addToast('New email received!', 'info');
          if (useStore.getState().currentTab === 'inbox') {
            useStore.getState().setCurrentTab('inbox');
          }
          return;
        }

        if (event === 'followup_sent') {
          addToast('Follow-up email sent automatically.', 'success');
          return;
        }

        if (event === 'reply_received') {
          addToast('Reply received!', 'info');
          if (useStore.getState().currentTab === 'inbox') {
            useStore.getState().setCurrentTab('inbox');
          }
          return;
        }

        if (!threadId) return;

        const now = Date.now();

        if (event === 'create_processing') {
          createThread(threadId);
          addMessageToThread(threadId, {
            id: `thinking-${threadId}-${now}`,
            role: 'ai',
            threadId,
            isThinking: true,
            content: '',
          });
          setActiveThreadId(threadId);
          return;
        }

        if (event === 'create_complete') {
          const thinkingMsg = useStore.getState().chatThreads[threadId]?.find(m => m.isThinking);
          if (thinkingMsg) {
            removeMessageFromThread(threadId, thinkingMsg.id);
          }

          const draft: Draft = {
            thread_id: threadId,
            recipient_username: data.draft?.recipient_username || '',
            recipient_email: data.draft?.recipient_email || '',
            subject: data.draft?.subject || '',
            body: data.draft?.body || '',
          };

          addMessageToThread(threadId, {
            id: `draft-${threadId}-${now}`,
            role: 'ai',
            threadId,
            draft,
          });

          if (data.interrupt?.type === 'question' && data.interrupt.question) {
            addMessageToThread(threadId, {
              id: `question-${threadId}-${now}`,
              role: 'ai',
              threadId,
              question: data.interrupt.question,
            });
          }
          return;
        }

        if (event === 'create_error') {
          const thinkingMsg = useStore.getState().chatThreads[threadId]?.find(m => m.isThinking);
          if (thinkingMsg) {
            removeMessageFromThread(threadId, thinkingMsg.id);
          }

          addMessageToThread(threadId, {
            id: `error-${threadId}-${now}`,
            role: 'ai',
            threadId,
            content: data.message || 'Failed to create draft',
          });
          addToast(data.message || 'Failed to create draft', 'error');
          return;
        }

        if (event === 'reply_processing') {
          addMessageToThread(threadId, {
            id: `sending-${Date.now()}`,
            role: 'ai',
            threadId,
            isThinking: true,
            content: 'Sending email...',
          });
          return;
        }

        if (event === 'reply_complete') {
          const sendingMsg = useStore.getState().chatThreads[threadId]?.find(m => m.content === 'Sending email...');
          if (sendingMsg) {
            removeMessageFromThread(threadId, sendingMsg.id);
          }
          addToast('Email sent successfully!', 'success');
          return;
        }

        if (event === 'reply_error') {
          const sendingMsg = useStore.getState().chatThreads[threadId]?.find(m => m.content === 'Sending email...');
          if (sendingMsg) {
            removeMessageFromThread(threadId, sendingMsg.id);
          }
          addMessageToThread(threadId, {
            id: `reply-error-${Date.now()}`,
            role: 'ai',
            threadId,
            content: data.message || 'Failed to send reply',
          });
          addToast(data.message || 'Failed to send reply', 'error');
          return;
        }

        if (event === 'meeting_confirmed') {
          addToast('Meeting confirmed! Email sent.', 'success');
          return;
        }

        if (event === 'meeting_declined') {
          addToast('Meeting declined.', 'info');
          return;
        }

        if (event === 'draft_sent') {
          addToast('Draft sent!', 'success');
          return;
        }

        if (event === 'waiting_reply') {
          addToast('Waiting for reply...', 'info');
          return;
        }

      } catch {}
    };

    return () => {
      ws.close();
    };
  }, [userId, addToast, setEmails, setCurrentTab, createThread, addMessageToThread, removeMessageFromThread, updateMessageInThread, setActiveThreadId]);

  return wsRef;
}