import { create } from 'zustand';
import type { User, Email, Thread, ChatMessage } from '../api/types';

interface StoreState {
  currentUser: User | null;
  currentTab: 'inbox' | 'compose' | 'calendar';
  inboxFilter: 'inbox' | 'sent';
  emails: Email[];
  selectedEmail: Email | null;
  threads: Thread[];
  replyTargetId: number | null;
  chatOpen: boolean;
  chatMessages: ChatMessage[];
  pendingContext: string | null;
  awaitingRecipient: boolean;
  activeDraftId: string | null;
  activeThreadId: string | null;
  calYear: number;
  calMonth: number;
  toasts: { id: number; message: string; type: 'info' | 'success' | 'error' }[];
  toastId: number;

  setCurrentUser: (user: User | null) => void;
  setCurrentTab: (tab: 'inbox' | 'compose' | 'calendar') => void;
  setInboxFilter: (filter: 'inbox' | 'sent') => void;
  setEmails: (emails: Email[]) => void;
  setSelectedEmail: (email: Email | null) => void;
  setThreads: (threads: Thread[]) => void;
  setReplyTargetId: (id: number | null) => void;
  setChatOpen: (open: boolean) => void;
  addChatMessage: (msg: ChatMessage) => void;
  removeChatMessage: (id: string) => void;
  setPendingContext: (ctx: string | null) => void;
  setAwaitingRecipient: (awaiting: boolean) => void;
  setActiveDraftId: (id: string | null) => void;
  setActiveThreadId: (id: string | null) => void;
  navigateCalendar: (prev: boolean) => void;
  addToast: (message: string, type?: 'info' | 'success' | 'error') => void;
  removeToast: (id: number) => void;
  logout: () => void;
}

export const useStore = create<StoreState>((set) => ({
  currentUser: null,
  currentTab: 'inbox',
  inboxFilter: 'inbox',
  emails: [],
  selectedEmail: null,
  threads: [],
  replyTargetId: null,
  chatOpen: false,
  chatMessages: [],
  pendingContext: null,
  awaitingRecipient: false,
  activeDraftId: null,
  activeThreadId: null,
  calYear: new Date().getFullYear(),
  calMonth: new Date().getMonth(),
  toasts: [],
  toastId: 0,

  setCurrentUser: (user) => set({ currentUser: user }),
  setCurrentTab: (tab) => set({ currentTab: tab }),
  setInboxFilter: (filter) => set({ inboxFilter: filter }),
  setEmails: (emails) => set({ emails }),
  setSelectedEmail: (email) => set({ selectedEmail: email }),
  setThreads: (threads) => set({ threads }),
  setReplyTargetId: (id) => set({ replyTargetId: id }),
  setChatOpen: (open) => set({ chatOpen: open }),
  addChatMessage: (msg) => set((state) => ({ 
    chatMessages: [...state.chatMessages, msg] 
  })),
  removeChatMessage: (id) => set((state) => ({
    chatMessages: state.chatMessages.filter(m => m.id !== id)
  })),
  setPendingContext: (ctx) => set({ pendingContext: ctx }),
  setAwaitingRecipient: (awaiting) => set({ awaitingRecipient: awaiting }),
  setActiveDraftId: (id) => set({ activeDraftId: id }),
  setActiveThreadId: (id) => set({ activeThreadId: id }),
  navigateCalendar: (prev) => set((state) => {
    let month = state.calMonth;
    let year = state.calYear;
    if (prev) {
      if (--month < 0) { month = 11; year--; }
    } else {
      if (++month > 11) { month = 0; year++; }
    }
    return { calMonth: month, calYear: year };
  }),
  addToast: (message, type = 'info') => set((state) => ({
    toasts: [...state.toasts, { id: state.toastId, message, type }],
    toastId: state.toastId + 1
  })),
  removeToast: (id) => set((state) => ({
    toasts: state.toasts.filter(t => t.id !== id)
  })),
  logout: () => set({
    currentUser: null,
    emails: [],
    selectedEmail: null,
    threads: [],
    chatMessages: [],
    chatOpen: false,
    pendingContext: null,
    awaitingRecipient: false,
    activeDraftId: null,
    activeThreadId: null,
  }),
}));