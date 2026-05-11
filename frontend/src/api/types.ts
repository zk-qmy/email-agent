export interface User {
  id: number;
  user_id?: number;
  username: string;
  email: string;
}

export interface Email {
  id: number;
  sender_id: number;
  sender_email: string;
  recipient_id: number;
  recipient_email: string;
  subject: string;
  body: string;
  is_read: boolean;
  cc?: string[];
  bcc?: string[];
  created_at: string;
  thread_id?: string;
}

export interface Draft {
  draft_id?: string;
  thread_id?: string;
  recipient_username?: string;
  recipient_email?: string;
  subject: string;
  body: string;
}

export interface Thread {
  id: string;
  thread_id?: string;
  recipient_username?: string;
  recipient_email?: string;
  status: string;
  created_at: string;
  meeting?: Meeting;
}

export interface Meeting {
  date?: string;
  time?: string;
  participants?: string[];
}

export interface DraftResponse {
  draft_id: string;
  thread_id?: string;
  draft?: Draft;
  status?: 'pending' | 'interrupted';
  question?: string;
  messages?: { role: string; content: string }[];
  error?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'ai' | 'system';
  threadId: string;
  content?: string;
  draft?: Draft;
  meeting?: Meeting;
  question?: string;
  isThinking?: boolean;
}

export interface ThreadStatus {
  status: string;
  reply_intent?: string;
}

export interface ThreadHistory {
  messages: { role: string; content: string }[];
}
