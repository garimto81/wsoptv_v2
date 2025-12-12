'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api/auth';

export default function LoginPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await authApi.login({
        email: formData.email,
        password: formData.password,
      });

      // 토큰 저장
      localStorage.setItem('token', response.token);
      localStorage.setItem('user_id', response.user_id);

      // 사용자 정보 조회 시도
      try {
        const user = await authApi.me();
        localStorage.setItem('user', JSON.stringify(user));

        if (user.role === 'admin') {
          router.push('/admin');
        } else {
          router.push('/catalog');
        }
      } catch {
        // me API가 없으면 기본 페이지로
        router.push('/catalog');
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';

      if (message.includes('not active')) {
        setError('Your account is pending approval. Please wait for admin approval.');
        router.push('/pending');
      } else if (message.includes('Invalid credentials')) {
        setError('Invalid email or password.');
      } else {
        setError(message);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-black relative">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/80 to-black" />

      {/* Header */}
      <header className="relative z-10 px-8 py-6">
        <Link href="/" className="text-[#E50914] font-bold text-3xl tracking-tight">
          WSOPTV
        </Link>
      </header>

      {/* Login Form */}
      <div className="relative z-10 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md bg-black/75 rounded-md p-16">
          <h1 className="text-white text-3xl font-bold mb-8">Sign In</h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-[#E87C03] text-white text-sm p-3 rounded">
                {error}
              </div>
            )}

            <div>
              <input
                type="email"
                placeholder="Email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                disabled={isLoading}
                required
                className="w-full bg-[#333] text-white rounded px-4 py-4 text-base placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-white/20 border border-transparent focus:border-[#E50914]"
              />
            </div>

            <div>
              <input
                type="password"
                placeholder="Password"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                disabled={isLoading}
                required
                className="w-full bg-[#333] text-white rounded px-4 py-4 text-base placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-white/20 border border-transparent focus:border-[#E50914]"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-[#E50914] hover:bg-[#F40612] text-white py-3 rounded font-semibold text-base transition-colors disabled:opacity-50"
            >
              {isLoading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-8 text-gray-400 text-sm">
            <p>
              New to WSOPTV?{' '}
              <Link href="/register" className="text-white hover:underline">
                Sign up now
              </Link>
            </p>
          </div>

          <div className="mt-4 text-gray-500 text-xs">
            <p>Admin: admin@wsoptv.local / admin</p>
            <p>User: test@wsoptv.local / password</p>
          </div>
        </div>
      </div>
    </main>
  );
}
