import { create } from 'zustand';
import type { User, Email, Thread, ChatMessage, CalendarEvent } from '../api/types';

interface StoreState {
  currentUser: User | null;
  currentTab: 'inbox' | 'compose' | 'calendar';
  inboxFilter: 'inbox' | 'sent' | 'deleted';
  emails: Email[];
  emailRefreshKey: number;
  selectedEmail: Email | null;
  threads: Thread[];
  replyTargetId: number | null;
  chatOpen: boolean;
  chatThreads: Record<string, ChatMessage[]>;
  allThreadIds: string[];
  activeThreadId: string | null;
  pendingContext: string | null;
  awaitingRecipient: boolean;
  activeDraftId: string | null;
  calYear: number;
  calMonth: number;
  calSelectedDate: Date;
  calendarEvents: CalendarEvent[];
  setCalSelectedDate: (d: Date) => void;
  setCalendarEvents: (events: CalendarEvent[]) => void;
  toasts: { id: number; message: string; type: 'info' | 'success' | 'error' }[];
  toastId: number;

  setCurrentUser: (user: User | null) => void;
  setCurrentTab: (tab: 'inbox' | 'compose' | 'calendar') => void;
  setInboxFilter: (filter: 'inbox' | 'sent') => void;
  refreshEmails: () => void;
  setEmails: (emails: Email[]) => void;
  setSelectedEmail: (email: Email | null) => void;
  setThreads: (threads: Thread[]) => void;
  setReplyTargetId: (id: number | null) => void;
  setChatOpen: (open: boolean) => void;
  createThread: (threadId: string) => void;
  setActiveThreadId: (threadId: string | null) => void;
  addMessageToThread: (threadId: string, msg: ChatMessage) => void;
  removeMessageFromThread: (threadId: string, msgId: string) => void;
  updateMessageInThread: (threadId: string, msgId: string, updates: Partial<ChatMessage>) => void;
  setPendingContext: (ctx: string | null) => void;
  setAwaitingRecipient: (awaiting: boolean) => void;
  setActiveDraftId: (id: string | null) => void;
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
  emailRefreshKey: 0,
  selectedEmail: null,
  threads: [],
  replyTargetId: null,
  chatOpen: false,
  chatThreads: {},
  allThreadIds: [],
  activeThreadId: null,
  pendingContext: null,
  awaitingRecipient: false,
  activeDraftId: null,
  calYear: new Date().getFullYear(),
  calMonth: new Date().getMonth(),
  calSelectedDate: new Date(),
  calendarEvents: [],
  toasts: [],
  toastId: 0,

  setCurrentUser: (user) => set({ currentUser: user }),
  setCurrentTab: (tab) => set({ currentTab: tab }),
  setInboxFilter: (filter) => set({ inboxFilter: filter }),
  refreshEmails: () => set((state) => ({ emailRefreshKey: state.emailRefreshKey + 1 })),
  setEmails: (emails) => set({ emails }),
  setSelectedEmail: (email) => set({ selectedEmail: email }),
  setThreads: (threads) => set({ threads }),
  setReplyTargetId: (id) => set({ replyTargetId: id }),
  setChatOpen: (open) => set({ chatOpen: open }),
  createThread: (threadId) => set((state) => {
    if (state.allThreadIds.includes(threadId)) return {};
    return {
      chatThreads: { ...state.chatThreads, [threadId]: [] },
      allThreadIds: [...state.allThreadIds, threadId],
      activeThreadId: threadId,
    };
  }),
  setActiveThreadId: (threadId) => set({ activeThreadId: threadId }),
  addMessageToThread: (threadId, msg) => set((state) => {
    const threadMessages = state.chatThreads[threadId] || [];
    return {
      chatThreads: { ...state.chatThreads, [threadId]: [...threadMessages, msg] },
    };
  }),
  removeMessageFromThread: (threadId, msgId) => set((state) => {
    const threadMessages = state.chatThreads[threadId] || [];
    return {
      chatThreads: { ...state.chatThreads, [threadId]: threadMessages.filter(m => m.id !== msgId) },
    };
  }),
  updateMessageInThread: (threadId, msgId, updates) => set((state) => {
    const threadMessages = state.chatThreads[threadId] || [];
    return {
      chatThreads: {
        ...state.chatThreads,
        [threadId]: threadMessages.map(m => m.id === msgId ? { ...m, ...updates } : m),
      },
    };
  }),
  setPendingContext: (ctx) => set({ pendingContext: ctx }),
  setAwaitingRecipient: (awaiting) => set({ awaitingRecipient: awaiting }),
  setActiveDraftId: (id) => set({ activeDraftId: id }),
  setCalSelectedDate: (d) => set({ calSelectedDate: d }),
  setCalendarEvents: (events) => set({ calendarEvents: events }),
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
    chatOpen: false,
    chatThreads: {},
    allThreadIds: [],
    activeThreadId: null,
    pendingContext: null,
    awaitingRecipient: false,
    activeDraftId: null,
    calendarEvents: [],
  }),
}));
