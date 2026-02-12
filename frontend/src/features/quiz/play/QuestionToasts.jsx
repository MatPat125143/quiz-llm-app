import { useEffect, useState } from 'react';

const TOAST_THEME = {
  success: { gradient: 'from-green-600 to-emerald-700', border: '#16a34a' },
  levelUp: { gradient: 'from-purple-600 to-pink-700', border: '#a855f7' },
  milestone: { gradient: 'from-orange-600 to-red-700', border: '#ea580c' },
  fire: { gradient: 'from-orange-600 to-orange-800', border: '#ea580c' },
  timeout: { gradient: 'from-amber-500 to-orange-600', border: '#f59e0b' }
};

function ToastCard({ toast, onDone }) {
  const [phase, setPhase] = useState('in');
  const theme = TOAST_THEME[toast.type] || TOAST_THEME.success;

  useEffect(() => {
    const duration = toast.duration ?? 5000;
    const exitMs = 320;
    const t1 = setTimeout(() => setPhase('out'), Math.max(0, duration - exitMs));
    const t2 = setTimeout(onDone, duration);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [toast, onDone]);

  return (
    <div
      className={`
        ${phase === 'out' ? 'toast-out' : 'toast-in'}
        w-[min(380px,calc(100vw-2rem))]
        bg-gradient-to-r ${theme.gradient}
        text-white px-5 sm:px-6 py-4 rounded-2xl
        flex items-center gap-3
        backdrop-blur-sm
      `}
      style={{
        border: `2px solid ${theme.border}`,
        boxShadow: '0 18px 45px rgba(0,0,0,0.35)'
      }}
      onClick={() => {
        setPhase('out');
        setTimeout(onDone, 180);
      }}
      role="status"
      aria-live="polite"
    >
      <span className="text-4xl animate-bounce">{toast.icon}</span>
      <div className="flex-1">
        <p className="font-bold text-lg leading-tight drop-shadow-md">{toast.message}</p>
      </div>
    </div>
  );
}

export function QuestionToaster({ toast, onDone }) {
  if (!toast) return null;

  return (
    <div
      className="fixed left-0 top-0 z-50 px-3 sm:px-6 pointer-events-none"
      style={{ top: 'calc(env(safe-area-inset-top, 0px) + 14px)' }}
    >
      <div className="flex justify-start pointer-events-none">
        <div className="pointer-events-auto">
          <ToastCard key={toast.id} toast={toast} onDone={onDone} />
        </div>
      </div>
    </div>
  );
}
