import { useEffect } from 'react';
import { useStore } from './store/useStore';
import { useWebSocket } from './hooks/useWebSocket';
import { Login } from './components/Auth/Login';
import { Topbar } from './components/Layout/Topbar';
import { ToastContainer } from './components/Layout/Toast';
import { EmailList } from './components/Inbox/EmailList';
import { EmailReader } from './components/Inbox/EmailReader';
import { ReplyModal } from './components/Inbox/ReplyModal';
import { ComposeForm } from './components/Compose/ComposeForm';
import { Calendar } from './components/Calendar/Calendar';
import { ChatWidget } from './components/Chat/ChatWidget';

function App() {
  const currentUser = useStore((s) => s.currentUser);
  const currentTab = useStore((s) => s.currentTab);
  const setCurrentTab = useStore((s) => s.setCurrentTab);

  const userId = currentUser?.user_id ?? currentUser?.id;
  useWebSocket(userId);

  useEffect(() => {
    if (!currentUser) {
      setCurrentTab('inbox');
    }
  }, [currentUser, setCurrentTab]);

  if (!currentUser) {
    return (
      <>
        <Login />
        <ToastContainer />
      </>
    );
  }

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Topbar />
      <main className="mt-14 h-[calc(100vh-56px)] overflow-hidden">
        {currentTab === 'inbox' && (
          <div className="flex h-full">
            <div className="w-[300px] flex-shrink-0 border-r border-border">
              <EmailList />
            </div>
            <EmailReader />
          </div>
        )}
        {currentTab === 'compose' && <ComposeForm />}
        {currentTab === 'calendar' && <Calendar />}
      </main>
      <ChatWidget />
      <ReplyModal />
      <ToastContainer />
    </div>
  );
}

export default App;