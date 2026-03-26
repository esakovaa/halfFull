'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function LoginPage() {
  const router = useRouter();
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    setSubmitting(true);
    setError(null);

    try {
      const response = await fetch('/api/account/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ login, password }),
      });

      const data = await response.json().catch(() => ({ error: 'Could not log in.' }));
      if (!response.ok) {
        throw new Error((data as { error?: string }).error ?? 'Could not log in.');
      }

      // Store login state in localStorage so the app knows the user is logged in
      if (typeof window !== 'undefined') {
        localStorage.setItem('halffull_account', JSON.stringify({ login: (data as { login: string }).login }));
      }

      router.push('/results');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not log in.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="phone-frame flex flex-col">
      <main className="flex-1 px-5 py-6">
        <div className="mx-auto flex max-w-lg flex-col gap-5">
          <div className="flex items-center justify-between text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--color-ink)]">
            <span>HalfFull</span>
            <Link href="/" className="text-[var(--color-ink-soft)]">Back</Link>
          </div>

          <section className="section-card px-5 py-6">
            <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--color-ink-soft)]">
              Welcome back
            </p>
            <h1 className="text-[2rem] font-bold leading-[1.02] tracking-[-0.05em] text-[var(--color-ink)]">
              Log in
            </h1>
            <p className="mt-3 text-sm leading-6 text-[var(--color-ink-soft)]">
              Log in to access your saved results and update your data after doctor visits.
            </p>

            <div className="mt-5 flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-[var(--color-ink)]" htmlFor="login">
                  Login
                </label>
                <input
                  id="login"
                  value={login}
                  onChange={(e) => setLogin(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
                  className="w-full rounded-[1.35rem] border border-[rgba(151,166,210,0.28)] bg-white px-4 py-3 text-base text-[var(--color-ink)] focus:border-[var(--color-accent)] focus:outline-none"
                  placeholder="Your login"
                  autoComplete="username"
                />
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-[var(--color-ink)]" htmlFor="password">
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
                  className="w-full rounded-[1.35rem] border border-[rgba(151,166,210,0.28)] bg-white px-4 py-3 text-base text-[var(--color-ink)] focus:border-[var(--color-accent)] focus:outline-none"
                  placeholder="Your password"
                  autoComplete="current-password"
                />
              </div>

              {error && <p className="text-sm text-[#b34343]">{error}</p>}

              <button
                type="button"
                onClick={handleLogin}
                disabled={submitting || login.trim().length < 3 || password.length < 1}
                className="rounded-full bg-[var(--color-lime)] px-5 py-4 text-base font-bold text-[var(--color-ink)] disabled:cursor-not-allowed disabled:opacity-45"
              >
                {submitting ? 'Logging in...' : 'Log in'}
              </button>

              <p className="text-center text-sm text-[var(--color-ink-soft)]">
                No account yet?{' '}
                <Link href="/consent" className="font-semibold text-[var(--color-ink)] underline">
                  Take the assessment
                </Link>
              </p>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}
