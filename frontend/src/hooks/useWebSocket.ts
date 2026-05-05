import { useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';

interface WsEvent {
  event?: string;
}

export function useWebSocket(userId: number | undefined) {
  const wsRef = useRef<WebSocket | null>(null);
  const addToast = useStore((s) => s.addToast);
  const setEmails = useStore((s) => s.setEmails);
  const setCurrentTab = useStore((s) => s.setCurrentTab);

  useEffect(() => {
    if (!userId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${protocol}://${window.location.hostname}:8000/api/agent/ws/${userId}`);
    wsRef.current = ws;

    ws.onclose = () => {
      setTimeout(() => {
        if (wsRef.current?.readyState !== WebSocket.OPEN) {
          const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
          const newWs = new WebSocket(`${protocol}://${window.location.hostname}:8000/api/agent/ws/${userId}`);
          wsRef.current = newWs;
        }
      }, 5000);
    };

    ws.onmessage = (ev) => {
      try {
        const data: WsEvent = JSON.parse(ev.data);
        const event = data.event;
        
        if (event === 'new_email') {
          addToast('New email received!', 'info');
          if (useStore.getState().currentTab === 'inbox') {
            useStore.getState().setCurrentTab('inbox');
          }
        } else if (event === 'followup_sent') {
          addToast('Follow-up email sent automatically.', 'success');
        } else if (event === 'reply_received') {
          addToast('Reply received!', 'info');
          if (useStore.getState().currentTab === 'inbox') {
            useStore.getState().setCurrentTab('inbox');
          }
        }
      } catch {}
    };

    return () => {
      ws.close();
    };
  }, [userId, addToast, setEmails, setCurrentTab]);

  return wsRef;
}