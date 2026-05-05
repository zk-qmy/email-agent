import { useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { api, formatDate, escHtml } from '../../api/client';

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

export function Calendar() {
  const currentUser = useStore((s) => s.currentUser);
  const calYear = useStore((s) => s.calYear);
  const calMonth = useStore((s) => s.calMonth);
  const threads = useStore((s) => s.threads);
  const setThreads = useStore((s) => s.setThreads);
  const navigateCalendar = useStore((s) => s.navigateCalendar);

  useEffect(() => {
    const userId = currentUser?.user_id ?? currentUser?.id;
    if (!userId) return;

    api.getThreads(userId)
      .then(setThreads)
      .catch(console.error);
  }, [currentUser, setThreads]);

  const today = new Date();
  const firstDay = new Date(calYear, calMonth, 1).getDay();
  const daysCount = new Date(calYear, calMonth + 1, 0).getDate();
  const isNow = today.getFullYear() === calYear && today.getMonth() === calMonth;

  const days: (number | null)[] = [];
  for (let i = 0; i < firstDay; i++) days.push(null);
  for (let d = 1; d <= daysCount; d++) days.push(d);

  return (
    <div className="flex flex-1 overflow-hidden">
      <div className="w-80 flex-shrink-0 bg-white border-r border-border p-7 overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <button className="w-7 h-7 border border-border rounded-md bg-white text-text-secondary text-lg cursor-pointer flex items-center justify-center transition-colors hover:bg-primary-light hover:text-primary hover:border-primary" onClick={() => navigateCalendar(true)}>
            ‹
          </button>
          <span className="font-bold text-sm">{MONTHS[calMonth]} {calYear}</span>
          <button className="w-7 h-7 border border-border rounded-md bg-white text-text-secondary text-lg cursor-pointer flex items-center justify-center transition-colors hover:bg-primary-light hover:text-primary hover:border-primary" onClick={() => navigateCalendar(false)}>
            ›
          </button>
        </div>

        <div className="grid grid-cols-7 mb-1.5">
          {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day) => (
            <span key={day} className="text-[11px] font-semibold text-text-muted text-center py-1 uppercase">{day}</span>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-0.75">
          {days.map((day, i) => (
            <div
              key={i}
              className={`aspect-square flex items-center justify-center rounded-full text-sm cursor-default transition-colors ${day === null ? 'pointer-events-none' : ''} ${isNow && day === today.getDate() ? 'bg-primary text-white font-bold' : 'text-text'}`}
            >
              {day}
            </div>
          ))}
        </div>
      </div>

      <div className="flex-1 p-7 overflow-y-auto">
        <h3 className="font-bold text-sm mb-4">Scheduled Meetings</h3>
        
        {!threads.length ? (
          <div className="text-center text-text-muted text-xs p-12">No scheduled meetings yet<br/>Use the AI assistant to schedule one.</div>
        ) : (
          <div>
            {threads.map((thread) => (
              <div key={thread.id} className="bg-white rounded-lg p-3.5 mb-2.5 border-l-[3px] border-primary shadow-sm">
                <div className="font-semibold text-xs text-text mb-0.75">{escHtml(thread.recipient || '—')}</div>
                <div className="text-xs text-text-secondary mb-1.5">Sent {formatDate(thread.created_at)}</div>
                <span className={`inline-block text-[11px] font-medium px-2 py-0.5 rounded-full ${thread.status === 'waiting_reply' ? 'bg-warning-light text-warning' : thread.status === 'completed' ? 'bg-success-light text-success' : thread.status === 'declined' ? 'bg-danger-light text-danger' : 'bg-blue-50 text-blue-500'}`}>
                  {escHtml((thread.status || '').replace(/_/g, ' '))}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}