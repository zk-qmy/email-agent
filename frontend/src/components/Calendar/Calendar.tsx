import { useState, useEffect, useCallback } from 'react';
import { useStore } from '../../store/useStore';
import { api, formatDate, escHtml } from '../../api/client';
import type { CalendarEvent } from '../../api/types';

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

function formatTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function formatDateStr(d: Date): string {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function localToISO(localDate: string, localTime: string): string {
  return new Date(`${localDate}T${localTime}:00`).toISOString();
}

function EventModal({
  mode,
  event,
  selectedDate,
  onSave,
  onClose,
  onEdit,
  onDelete,
}: {
  mode: 'create' | 'edit' | 'view';
  event?: CalendarEvent;
  selectedDate: Date;
  onSave: (data: {
    title: string;
    description: string;
    start_time: string;
    end_time: string;
    location: string;
  }) => void;
  onClose: () => void;
  onEdit?: () => void;
  onDelete?: () => void;
}) {
  const [title, setTitle] = useState(event?.title || '');
  const [description, setDescription] = useState(event?.description || '');
  const [startDate, setStartDate] = useState(
    event ? event.start_time.split('T')[0] : formatDateStr(selectedDate)
  );
  const [startTime, setStartTime] = useState(
    event ? event.start_time.split('T')[1]?.slice(0, 5) : '09:00'
  );
  const [endDate, setEndDate] = useState(
    event ? event.end_time.split('T')[0] : formatDateStr(selectedDate)
  );
  const [endTime, setEndTime] = useState(
    event ? event.end_time.split('T')[1]?.slice(0, 5) : '10:00'
  );
  const [location, setLocation] = useState(event?.location || '');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Title is required');
      return;
    }
    if (new Date(`${endDate}T${endTime}`) <= new Date(`${startDate}T${startTime}`)) {
      setError('End time must be after start time');
      return;
    }
    onSave({
      title: title.trim(),
      description: description.trim(),
      start_time: localToISO(startDate, startTime),
      end_time: localToISO(endDate, endTime),
      location: location.trim(),
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between px-5 py-4 border-b border-border">
          <h2 className="font-bold text-sm">
            {mode === 'create' ? 'New Event' : mode === 'edit' ? 'Edit Event' : 'Event Details'}
          </h2>
          <div className="flex items-center gap-2">
            {mode === 'view' && onEdit && (
              <button
                type="button"
                onClick={onEdit}
                className="px-3 py-1 text-xs bg-primary text-white rounded-md hover:bg-primary-dark"
              >
                Edit
              </button>
            )}
            {mode === 'view' && onDelete && (
              <button
                type="button"
                onClick={onDelete}
                className="px-3 py-1 text-xs bg-danger text-white rounded-md hover:opacity-90"
              >
                Delete
              </button>
            )}
            {mode !== 'view' && (
              <button
                type="button"
                onClick={onClose}
                className="text-text-muted hover:text-text text-lg leading-none"
              >
                ×
              </button>
            )}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1">Title</label>
            {mode === 'view' ? (
              <p className="text-sm font-semibold">{escHtml(event?.title || '')}</p>
            ) : (
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary"
                placeholder="Event title"
              />
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Start</label>
              {mode === 'view' ? (
                <p className="text-sm">
                  {event ? `${formatDate(event.start_time)} ${formatTime(event.start_time)}` : '—'}
                </p>
              ) : (
                <div className="space-y-1">
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full border border-border rounded-md px-2 py-1.5 text-sm focus:outline-none focus:border-primary"
                  />
                  <input
                    type="time"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="w-full border border-border rounded-md px-2 py-1.5 text-sm focus:outline-none focus:border-primary"
                  />
                </div>
              )}
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">End</label>
              {mode === 'view' ? (
                <p className="text-sm">
                  {event ? `${formatDate(event.end_time)} ${formatTime(event.end_time)}` : '—'}
                </p>
              ) : (
                <div className="space-y-1">
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full border border-border rounded-md px-2 py-1.5 text-sm focus:outline-none focus:border-primary"
                  />
                  <input
                    type="time"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="w-full border border-border rounded-md px-2 py-1.5 text-sm focus:outline-none focus:border-primary"
                  />
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1">Location</label>
            {mode === 'view' ? (
              <p className="text-sm">{escHtml(event?.location || '—')}</p>
            ) : (
              <input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full border border-border rounded-md px-3 py-2 text-sm focus:outline-none focus:border-primary"
                placeholder="Location (optional)"
              />
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1">Description</label>
            {mode === 'view' ? (
              <p className="text-sm text-text-secondary">{escHtml(event?.description || '—')}</p>
            ) : (
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="w-full border border-border rounded-md px-3 py-2 text-sm resize-none focus:outline-none focus:border-primary"
                placeholder="Description (optional)"
              />
            )}
          </div>

          {error && <p className="text-xs text-red-500">{error}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm border border-border rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            {mode !== 'view' && (
              <button
                type="submit"
                className="px-4 py-2 text-sm bg-primary text-white rounded-md hover:bg-primary-dark"
              >
                {mode === 'create' ? 'Create Event' : 'Save Changes'}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}

export function Calendar() {
  const currentUser = useStore((s) => s.currentUser);
  const calYear = useStore((s) => s.calYear);
  const calMonth = useStore((s) => s.calMonth);
  const calSelectedDate = useStore((s) => s.calSelectedDate);
  const calendarEvents = useStore((s) => s.calendarEvents);
  const setCalSelectedDate = useStore((s) => s.setCalSelectedDate);
  const setCalendarEvents = useStore((s) => s.setCalendarEvents);
  const navigateCalendar = useStore((s) => s.navigateCalendar);
  const addToast = useStore((s) => s.addToast);

  const [modal, setModal] = useState<{ mode: 'create' | 'edit' | 'view'; event?: CalendarEvent } | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchEvents = useCallback(async () => {
    const userId = currentUser?.user_id ?? currentUser?.id;
    if (!userId) return;

    setLoading(true);
    try {
      const start = new Date(calYear, calMonth, 1).toISOString();
      const end = new Date(calYear, calMonth + 1, 0, 23, 59, 59).toISOString();
      const events = await api.getCalendarEvents(userId, start, end);
      setCalendarEvents(events);
    } catch {
      addToast('Failed to load events', 'error');
    } finally {
      setLoading(false);
    }
  }, [currentUser, calYear, calMonth, setCalendarEvents, addToast]);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  const handleCreateEvent = async (data: {
    title: string;
    description: string;
    start_time: string;
    end_time: string;
    location: string;
  }) => {
    const userId = currentUser?.user_id ?? currentUser?.id;
    if (!userId) return;

    try {
      const event = await api.createCalendarEvent(
        userId,
        data.title,
        data.start_time,
        data.end_time,
        data.description || undefined,
        undefined,
        data.location || undefined
      );
      setCalendarEvents([...calendarEvents, event.event]);
      setModal(null);
      addToast('Event created', 'success');
    } catch {
      addToast('Failed to create event', 'error');
    }
  };

  const handleUpdateEvent = async (data: {
    title: string;
    description: string;
    start_time: string;
    end_time: string;
    location: string;
  }) => {
    if (!modal?.event) return;
    try {
      const updated = await api.updateCalendarEvent(modal.event.id, {
        title: data.title,
        description: data.description || undefined,
        start_time: data.start_time,
        end_time: data.end_time,
        location: data.location || undefined,
      });
      setCalendarEvents(calendarEvents.map((e) => (e.id === updated.event.id ? updated.event : e)));
      setModal(null);
      addToast('Event updated', 'success');
    } catch {
      addToast('Failed to update event', 'error');
    }
  };

  const handleDeleteEvent = async () => {
    if (!modal?.event) return;
    try {
      await api.deleteCalendarEvent(modal.event.id);
      setCalendarEvents(calendarEvents.filter((e) => e.id !== modal.event!.id));
      setModal(null);
      addToast('Event deleted', 'success');
    } catch {
      addToast('Failed to delete event', 'error');
    }
  };

  const today = new Date();
  const firstDay = new Date(calYear, calMonth, 1).getDay();
  const daysCount = new Date(calYear, calMonth + 1, 0).getDate();
  const isCurrentMonth = today.getFullYear() === calYear && today.getMonth() === calMonth;

  const days: (number | null)[] = [];
  for (let i = 0; i < firstDay; i++) days.push(null);
  for (let d = 1; d <= daysCount; d++) days.push(d);

  const isToday = (day: number | null) =>
    isCurrentMonth && day !== null && day === today.getDate();

  const isSelected = (day: number | null) =>
    day !== null &&
    calSelectedDate.getFullYear() === calYear &&
    calSelectedDate.getMonth() === calMonth &&
    calSelectedDate.getDate() === day;

  const hasEvents = (day: number | null) => {
    if (day === null) return false;
    const dateStr = formatDateStr(new Date(calYear, calMonth, day));
    return calendarEvents.some((e) => {
      const start = e.start_time.split('T')[0];
      const end = e.end_time.split('T')[0];
      return dateStr >= start && dateStr <= end;
    });
  };

  const handleDayClick = (day: number | null) => {
    if (day === null) return;
    setCalSelectedDate(new Date(calYear, calMonth, day));
  };

  const selectedDateStr = formatDateStr(calSelectedDate);
  const selectedDateEvents = calendarEvents.filter((e) => {
    const start = e.start_time.split('T')[0];
    const end = e.end_time.split('T')[0];
    return selectedDateStr >= start && selectedDateStr <= end;
  });

  return (
    <div className="flex flex-1 overflow-hidden">
      <div className="w-80 flex-shrink-0 bg-white border-r border-border p-7 overflow-y-auto">
        <div className="flex items-center justify-between mb-5">
          <button
            className="w-7 h-7 border border-border rounded-md bg-white text-text-secondary text-lg cursor-pointer flex items-center justify-center transition-colors hover:bg-primary-light hover:text-primary hover:border-primary"
            onClick={() => navigateCalendar(true)}
          >
            ‹
          </button>
          <span className="font-bold text-sm">{MONTHS[calMonth]} {calYear}</span>
          <button
            className="w-7 h-7 border border-border rounded-md bg-white text-text-secondary text-lg cursor-pointer flex items-center justify-center transition-colors hover:bg-primary-light hover:text-primary hover:border-primary"
            onClick={() => navigateCalendar(false)}
          >
            ›
          </button>
        </div>

        <div className="grid grid-cols-7 mb-1.5">
          {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((d) => (
            <span key={d} className="text-[11px] font-semibold text-text-muted text-center py-1 uppercase">{d}</span>
          ))}
        </div>

        <div className="grid grid-cols-7 gap-0.75">
          {days.map((day, i) => (
            <div
              key={i}
              onClick={() => handleDayClick(day)}
              className={`relative aspect-square flex items-center justify-center rounded-full text-sm cursor-pointer transition-colors select-none ${day === null ? 'pointer-events-none' : ''} ${isSelected(day) ? (isToday(day) ? 'bg-primary text-white font-bold ring-2 ring-primary ring-offset-1' : 'bg-primary-light text-primary font-bold ring-2 ring-primary ring-offset-1') : (isToday(day) ? 'bg-primary text-white font-bold' : 'text-text hover:bg-primary-light hover:text-primary')}`}
            >
              {day}
              {hasEvents(day) && (
                <span className={`absolute bottom-0.5 left-1/2 -translate-x-1/2 w-1 h-1 rounded-full ${isSelected(day) ? 'bg-white' : 'bg-primary'}`} />
              )}
            </div>
          ))}
        </div>

        <button
          onClick={() => setModal({ mode: 'create' })}
          className="mt-5 w-full py-2 text-xs font-semibold text-primary border border-primary rounded-md hover:bg-primary-light transition-colors"
        >
          + New Event
        </button>
      </div>

      <div className="flex-1 p-7 overflow-y-auto">
        <h3 className="font-bold text-sm mb-4">
          Events — {calSelectedDate.toLocaleDateString([], { month: 'long', day: 'numeric', year: 'numeric' })}
        </h3>

        {loading ? (
          <div className="text-center text-text-muted text-xs p-12">Loading events...</div>
        ) : !selectedDateEvents.length ? (
          <div className="text-center text-text-muted text-xs p-12">
            No events for this date
          </div>
        ) : (
          <div>
            {selectedDateEvents.map((event) => (
              <div
                key={event.id}
                className="bg-white rounded-lg p-3.5 mb-2.5 border-l-[3px] border-primary shadow-sm cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => setModal({ mode: 'view', event })}
              >
                <div className="font-semibold text-xs text-text mb-0.5">{escHtml(event.title)}</div>
                <div className="text-xs text-text-secondary">
                  {formatTime(event.start_time)} — {formatTime(event.end_time)}
                  {event.location && (
                    <span className="ml-2">· {escHtml(event.location)}</span>
                  )}
                </div>
                {event.description && (
                  <div className="text-xs text-text-muted mt-1 truncate">{escHtml(event.description)}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {modal && (
        <EventModal
          mode={modal.mode}
          event={modal.event}
          selectedDate={calSelectedDate}
          onSave={modal.mode === 'create' ? handleCreateEvent : handleUpdateEvent}
          onClose={() => setModal(null)}
          onEdit={modal.mode === 'view' && modal.event ? () => setModal({ mode: 'edit', event: modal.event }) : undefined}
          onDelete={modal.mode === 'view' ? handleDeleteEvent : undefined}
        />
      )}
    </div>
  );
}
