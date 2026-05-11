import { useEffect } from 'react';
import { useStore } from '../../store/useStore';

export function ToastContainer() {
  const toasts = useStore((s) => s.toasts);
  const removeToast = useStore((s) => s.removeToast);

  return (
    <div className="fixed bottom-[90px] right-6 z-[2000] flex flex-col gap-2">
      {toasts.map((toast) => (
        <Toast key={toast.id} {...toast} onClose={() => removeToast(toast.id)} />
      ))}
    </div>
  );
}

function Toast({ message, type, onClose }: { message: string; type: string; onClose: () => void }) {
  useEffect(() => {
    const timer = setTimeout(onClose, 3500);
    return () => clearTimeout(timer);
  }, [onClose]);

  const typeClasses = {
    info: 'bg-blue-50 border-blue-200 text-blue-600',
    success: 'bg-success-light border-green-200 text-success',
    error: 'bg-danger-light border-green-200 text-danger',
  };

  return (
    <div className={`px-4 py-2.5 rounded-xl text-sm font-medium max-w-[300px] shadow-md border transition-all translate-y-2 opacity-0 animate-[chatIn_0.2s_ease-out_forwards] ${typeClasses[type as keyof typeof typeClasses] || typeClasses.info}`}>
      {message}
    </div>
  );
}