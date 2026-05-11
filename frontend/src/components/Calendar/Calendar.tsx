import { useEffect } from 'react';
import { useStore } from '../../store/useStore';
import { api, escHtml } from '../../api/client';
import type { CalendarEvent } from '../../api/types';

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];

export function Calendar() {
  const currentUser = useStore((s) => s.currentUser);
  const calYear = useStore((s) => s.calYear);
  const calMonth = useStore((s) => s.calMonth);
  const calendarEvents = useStore((s) => s.calendarEvents);
  const selectedDate = useStore((s) => s.selectedDate);
  const setCalendarEvents = useStore((s) => s.setCalendarEvents);
  const setSelectedDate = useStore((s) => s.setSelectedDate);
  const navigateCalendar = useStore((s) => s.navigateCalendar);

  useEffect(() => {
    const userId = currentUser?.user_id ?? currentUser?.id;
    if (!userId) return;

    // Fetch events for the current month
    const startOfMonth = new Date(calYear, calMonth, 1);
    const endOfMonth = new Date(calYear, calMonth + 1, 0);
    const startDate = startOfMonth.toISOString().split('T')[0];
    const endDate = endOfMonth.toISOString().split('T')[0];

    api.getCalendarEvents(userId, startDate, endDate)
      .then(setCalendarEvents)
      .catch(console.error);
  }, [currentUser, calYear, calMonth, setCalendarEvents]);

  const today = new Date();
  const firstDay = new Date(calYear, calMonth, 1).getDay();
  const daysCount = new Date(calYear, calMonth + 1, 0).getDate();
  const isNow = today.getFullYear() === calYear && today.getMonth() === calMonth;

  const days: (number | null)[] = [];
  for (let i = 0; i < firstDay; i++) days.push(null);
  for (let d = 1; d <= daysCount; d++) days.push(d);

  // Helper function to check if a date has events
  const hasEventsOnDate = (day: number): boolean => {
    const date = new Date(calYear, calMonth, day);
    return calendarEvents.some(event => {
      const eventDate = new Date(event.start_time);
      return eventDate.toDateString() === date.toDateString();
    });
  };

  // Helper function to get events for a specific date
  const getEventsForDate = (day: number): CalendarEvent[] => {
    const date = new Date(calYear, calMonth, day);
    return calendarEvents.filter(event => {
      const eventDate = new Date(event.start_time);
      return eventDate.toDateString() === date.toDateString();
    });
  };

  // Handle date click
  const handleDateClick = (day: number) => {
    const date = new Date(calYear, calMonth, day);
    setSelectedDate(selectedDate?.toDateString() === date.toDateString() ? null : date);
  };

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
          {days.map((day, i) => {
            if (day === null) {
              return <div key={i} className="aspect-square" />;
            }

            const isToday = isNow && day === today.getDate();
            const isSelected = selectedDate && selectedDate.getDate() === day && selectedDate.getMonth() === calMonth && selectedDate.getFullYear() === calYear;
            const hasEvents = hasEventsOnDate(day);

            return (
              <div
                key={i}
                className={`aspect-square flex items-center justify-center rounded-full text-sm cursor-pointer transition-colors relative ${
                  isSelected
                    ? 'bg-blue-500 text-white font-bold'
                    : isToday
                    ? 'bg-primary text-white font-bold'
                    : hasEvents
                    ? 'bg-green-100 text-green-800 hover:bg-green-200'
                    : 'text-text hover:bg-gray-100'
                }`}
                onClick={() => handleDateClick(day)}
              >
                {day}
                {hasEvents && !isSelected && !isToday && (
                  <div className="absolute bottom-0.5 left-1/2 transform -translate-x-1/2 w-1 h-1 bg-green-500 rounded-full"></div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="flex-1 p-7 overflow-y-auto">
        <h3 className="font-bold text-sm mb-4">
          {selectedDate
            ? `Events for ${selectedDate.toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric' })}`
            : 'Scheduled Events'
          }
        </h3>
        
        {!selectedDate ? (
          <div className="text-center text-text-muted text-xs p-12">
            Click on a date to view events for that day.
          </div>
        ) : (() => {
          const dayEvents = getEventsForDate(selectedDate.getDate());
          return !dayEvents.length ? (
            <div className="text-center text-text-muted text-xs p-12">
              No events scheduled for this date.
            </div>
          ) : (
            <div>
              {dayEvents.map((event) => (
                <div key={event.id} className="bg-white rounded-lg p-3.5 mb-2.5 border-l-[3px] border-primary shadow-sm">
                  <div className="font-semibold text-xs text-text mb-0.75">{escHtml(event.title)}</div>
                  <div className="text-xs text-text-secondary mb-1.5">
                    {new Date(event.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - {new Date(event.end_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                  {event.location && (
                    <div className="text-xs text-text-secondary mb-1.5">📍 {escHtml(event.location)}</div>
                  )}
                  {event.description && (
                    <div className="text-xs text-text-secondary">{escHtml(event.description)}</div>
                  )}
                </div>
              ))}
            </div>
          );
        })()}
      </div>
    </div>
  );
}