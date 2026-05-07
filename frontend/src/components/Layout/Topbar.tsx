import { useStore } from '../../store/useStore';
import { avatarColor, avatarInitials } from '../../api/client';

export function Topbar() {
  const currentUser = useStore((s) => s.currentUser);
  const currentTab = useStore((s) => s.currentTab);
  const setCurrentTab = useStore((s) => s.setCurrentTab);
  const logout = useStore((s) => s.logout);

  if (!currentUser) return null;

  const initials = avatarInitials(currentUser.username || currentUser.email);
  const color = avatarColor(currentUser.username || currentUser.email);

  return (
    <header className="fixed top-0 left-0 right-0 h-14 bg-white border-b border-border flex items-center px-5 gap-4 z-[200] shadow-sm">
      <div className="flex items-center gap-2.5 flex-shrink-0">
        <div className="w-8 h-8 rounded-lg bg-primary text-white text-[11px] font-extrabold flex items-center justify-center tracking-wide">
          EA
        </div>
        <span className="font-bold text-[15px] text-text">Email Agent</span>
      </div>

      <nav className="flex-1 flex justify-center gap-2">
        <button
          className={`px-4.5 py-1.75 rounded-lg border-none bg-transparent text-sm font-medium cursor-pointer transition-colors whitespace-nowrap ${currentTab === 'inbox' ? 'bg-primary-light text-primary font-semibold' : 'text-text-secondary hover:bg-gray-100'}`}
          onClick={() => setCurrentTab('inbox')}
        >
          Inbox
        </button>
        <button
          className={`px-4.5 py-1.75 rounded-lg border-none bg-transparent text-sm font-medium cursor-pointer transition-colors whitespace-nowrap ${currentTab === 'compose' ? 'bg-primary-light text-primary font-semibold' : 'text-text-secondary hover:bg-gray-100'}`}
          onClick={() => setCurrentTab('compose')}
        >
          Compose
        </button>
        <button
          className={`px-4.5 py-1.75 rounded-lg border-none bg-transparent text-sm font-medium cursor-pointer transition-colors whitespace-nowrap ${currentTab === 'calendar' ? 'bg-primary-light text-primary font-semibold' : 'text-text-secondary hover:bg-gray-100'}`}
          onClick={() => setCurrentTab('calendar')}
        >
          Calendar
        </button>
      </nav>

      <div className="flex items-center gap-2.5 flex-shrink-0">
        <div className="flex items-center gap-2 px-3 py-1 bg-bg border border-border rounded-full">
          <div className="w-6 h-6 rounded-full text-white text-[10px] font-bold flex items-center justify-center flex-shrink-0" style={{ backgroundColor: color }}>
            {initials}
          </div>
          <span className="text-xs font-medium text-text max-w-[120px] truncate">
            {currentUser.username || currentUser.email}
          </span>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={logout}>
          Sign out
        </button>
      </div>
    </header>
  );
}