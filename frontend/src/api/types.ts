export interface User {
  id: number;
  user_id?: number;
  username: string;
  email: string;
  role?: string;
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

export interface PdfFormField {
  name: string;
  type: string;
  required: boolean;
  value: string | null;
}

export interface PdfValidateResponse {
  required_fields: string[];
  optional_fields: string[];
  not_user_fields: string[];
  missing_fields: string[];
  message_to_user: string;
}

export interface RagSuggestDepartmentResponse {
  department: string | null;
  contact: string | null;
  reply_time: string | null;
  reason: string | null;
  notes: string | null;
}

export interface RagAskGuideResponse {
  answer: string | null;
  source_section: string | null;
  found_in_guide: boolean;
}

export interface RagSearchResultItem {
  text: string;
  section: string;
  score: number;
}

export interface RagSearchResponse {
  results: RagSearchResultItem[];
}

export interface RagStatusResponse {
  index_loaded: boolean;
  index_exists: boolean;
  chunk_count: number;
  cache_path: string;
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
  pdfResult?: PdfValidateResponse;
  ragDepartmentResult?: RagSuggestDepartmentResponse;
  ragGuideResult?: RagAskGuideResponse;
  ragSearchResult?: RagSearchResponse;
}

export interface ThreadStatus {
  status: string;
  reply_intent?: string;
}

export interface ThreadHistory {
  messages: { role: string; content: string }[];
}

export interface CalendarEvent {
  id: number;
  organizer_id: number;
  organizer_email?: string;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  attendee_ids: number[];
  location?: string;
  created_at: string;
  updated_at?: string;
}
