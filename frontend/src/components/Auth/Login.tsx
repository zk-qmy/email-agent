import { useState } from 'react';
import { api } from '../../api/client';
import { useStore } from '../../store/useStore';

export function Login() {
  const [showForgot, setShowForgot] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [forgotEmail, setForgotEmail] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const setCurrentUser = useStore((s) => s.setCurrentUser);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (!email || !password) {
      setError('Please enter your email and password.');
      return;
    }

    setLoading(true);
    try {
      const user = await api.login(email, password);
      setCurrentUser(user);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Sign in failed';
      setError(message.includes('401') || message.toLowerCase().includes('invalid')
        ? 'Incorrect email or password.'
        : message);
    } finally {
      setLoading(false);
    }
  };

  const handleForgot = (e: React.FormEvent) => {
    e.preventDefault();
    if (!forgotEmail) {
      setError('Please enter your email address.');
      return;
    }
    setError('If that email is registered, reset instructions are on their way.');
    setTimeout(() => {
      setShowForgot(false);
      setForgotEmail('');
      setError('');
    }, 2000);
  };

  const user = useStore((s) => s.currentUser);

  if (user) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-bg flex items-center justify-center z-[9000]">
      <div className="bg-card rounded-2xl shadow-lg p-10 w-full max-w-[400px]">
        <div className="flex items-center gap-2.5 mb-8">
          <div className="w-8 h-8 rounded-lg bg-primary text-white text-xs font-extrabold flex items-center justify-center tracking-wide">
            EA
          </div>
          <span className="font-bold text-[15px] text-text">Email Agent</span>
        </div>

        {!showForgot ? (
          <form onSubmit={handleLogin}>
            <h1 className="text-2xl font-bold text-text mb-1.5">Sign in</h1>
            <p className="text-sm text-text-secondary mb-6">Enter your email and password to continue</p>
            
            <div className="mb-4">
              <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input"
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input"
                placeholder="••••••••"
                autoComplete="current-password"
              />
            </div>

            {error && (
              <p className="text-xs text-danger bg-danger-light rounded px-3 py-2 mb-4">{error}</p>
            )}

            <button type="submit" className="btn btn-primary w-full py-3 text-[15px] mt-2 mb-4" disabled={loading}>
              {loading ? 'Signing in…' : 'Sign in'}
            </button>

            <button type="button" className="block w-full bg-none border-none text-primary text-sm font-medium cursor-pointer py-1 text-center opacity-75 hover:opacity-100" onClick={() => setShowForgot(true)}>
              Forgot password?
            </button>
          </form>
        ) : (
          <form onSubmit={handleForgot}>
            <h1 className="text-2xl font-bold text-text mb-1.5">Reset password</h1>
            <p className="text-sm text-text-secondary mb-6">Enter your email and we'll send you a reset link</p>
            
            <div className="mb-4">
              <label className="block text-xs font-semibold text-text-secondary uppercase tracking-wider mb-1.5">Email</label>
              <input
                type="email"
                value={forgotEmail}
                onChange={(e) => setForgotEmail(e.target.value)}
                className="input"
                placeholder="you@example.com"
                autoComplete="email"
              />
            </div>

            {error && (
              <p className="text-xs text-success bg-success-light rounded px-3 py-2 mb-4">{error}</p>
            )}

            <button type="submit" className="btn btn-primary w-full py-3 text-[15px] mt-2 mb-4">
              Send reset link
            </button>

            <button type="button" className="block w-full bg-none border-none text-primary text-sm font-medium cursor-pointer py-1 text-center opacity-75 hover:opacity-100" onClick={() => { setShowForgot(false); setError(''); }}>
              Back to sign in
            </button>
          </form>
        )}
      </div>
    </div>
  );
}