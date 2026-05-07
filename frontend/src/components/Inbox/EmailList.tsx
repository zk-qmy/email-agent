import { useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { api, formatDate, avatarColor, avatarInitials, trunc, escHtml } from '../../api/client';
import type { Email } from '../../api/types';

export function EmailList() {
  const currentUser = useStore((s) => s.currentUser);
  const inboxFilter = useStore((s) => s.inboxFilter);
  const emailRefreshKey = useStore((s) => s.emailRefreshKey);
  const emails = useStore((s) => s.emails);
  const selectedEmail = useStore((s) => s.selectedEmail);
  const setEmails = useStore((s) => s.setEmails);
  const setSelectedEmail = useStore((s) => s.setSelectedEmail);
  const refreshEmails = useStore((s) => s.refreshEmails);

  const userId = currentUser?.user_id ?? currentUser?.id;

  useEffect(() => {
    if (!userId) return;

    const loadEmails = async () => {
      if (inboxFilter === 'deleted') {
        setEmails([]);
        return;
      }
      try {
        const data = inboxFilter === 'sent'
          ? await api.getSent(userId)
          : await api.getInbox(userId);
        setEmails(data);
      } catch (err) {
        console.error('Failed to load emails:', err);
      }
    };

    loadEmails();
  }, [userId, inboxFilter, emailRefreshKey, setEmails]);

  const sortedEmails = [...emails].sort((a, b) =>
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const unreadCount = emails.filter(e => !e.is_read).length;
  const subtitle = inboxFilter === 'sent'
    ? `${emails.length} sent message${emails.length !== 1 ? 's' : ''}`
    : inboxFilter === 'deleted'
    ? 'Deleted items'
    : `${emails.length} message${emails.length !== 1 ? 's' : ''}${unreadCount ? `, ${unreadCount} unread` : ''}`;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 px-5 py-2.5 bg-white border-b border-border flex-shrink-0">
        <div className="flex gap-0.5 bg-bg border border-border rounded-lg p-0.5">
          <button
            className={`px-3.5 py-1 rounded-md border-none bg-transparent text-xs font-medium cursor-pointer transition-colors ${inboxFilter === 'inbox' ? 'bg-primary text-white' : 'text-text-secondary'}`}
            onClick={() => useStore.getState().setInboxFilter('inbox')}
          >
            Inbox
          </button>
          <button
            className={`px-3.5 py-1 rounded-md border-none bg-transparent text-xs font-medium cursor-pointer transition-colors ${inboxFilter === 'sent' ? 'bg-primary text-white' : 'text-text-secondary'}`}
            onClick={() => useStore.getState().setInboxFilter('sent')}
          >
            Sent
          </button>
          <button
            className={`px-3.5 py-1 rounded-md border-none bg-transparent text-xs font-medium cursor-pointer transition-colors ${inboxFilter === 'deleted' ? 'bg-primary text-white' : 'text-text-secondary'}`}
            onClick={() => useStore.getState().setInboxFilter('deleted')}
          >
            Deleted
          </button>
        </div>
        <span className="flex-1 text-xs text-text-secondary">{subtitle}</span>
        <button className="btn btn-ghost btn-sm" onClick={refreshEmails}>
          Refresh
        </button>
      </div>

      <div className="flex-1 overflow-y-auto bg-white">
        {!emails.length ? (
          <div className="p-12 text-center text-text-muted text-xs">No emails here yet</div>
        ) : (
          sortedEmails.map((email) => (
            <EmailItem
              key={email.id}
              email={email}
              isSelected={selectedEmail?.id === email.id}
              isSent={inboxFilter === 'sent'}
              onClick={() => setSelectedEmail(email)}
            />
          ))
        )}
      </div>
    </div>
  );
}

function EmailItem({ email, isSelected, isSent, onClick }: {
  email: Email;
  isSelected: boolean;
  isSent: boolean;
  onClick: () => void;
}) {
  const isUnread = !email.is_read && !isSent;
  const fromLabel = isSent
    ? (email.recipient_email || String(email.recipient_id || 'Unknown'))
    : (email.sender_email || String(email.sender_id || 'Unknown'));

  return (
    <div
      className={`flex items-start gap-2.75 px-4 py-3 border-b border-border cursor-pointer transition-colors hover:bg-gray-50 ${isSelected ? 'bg-primary-light' : ''} ${isUnread ? 'bg-[#fdfcff]' : ''}`}
      onClick={onClick}
    >
      <div className="w-9 h-9 rounded-full text-white text-[12px] font-semibold flex items-center justify-center flex-shrink-0 mt-0.25" style={{ backgroundColor: avatarColor(fromLabel) }}>
        {avatarInitials(fromLabel)}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-baseline mb-0.5">
          <span className="text-xs font-semibold text-text truncate max-w-[140px]">{escHtml(trunc(fromLabel, 22))}</span>
          <span className="text-[11px] text-text-muted flex-shrink-0">{formatDate(email.created_at)}</span>
        </div>
        <div className="text-xs text-text whitespace-nowrap overflow-hidden text-ellipsis mb-0.5">{escHtml(trunc(email.subject || '(no subject)', 40))}</div>
        <div className="text-[12px] text-text-muted whitespace-nowrap overflow-hidden text-ellipsis">{escHtml(trunc(email.body || '', 60))}</div>
      </div>
      {isUnread && <div className="w-1.75 h-1.75 rounded-full bg-primary flex-shrink-0 mt-1.5" />}
    </div>
  );
}
