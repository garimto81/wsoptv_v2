'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

// User type definition
interface User {
  id: string;
  username: string;
  password: string;
  role: 'admin' | 'user';
  status: 'pending' | 'active' | 'rejected' | 'suspended';
  created_at: string;
}

// Initialize users in localStorage
function initializeUsers(): User[] {
  if (typeof window === 'undefined') return [];

  const existingUsers = localStorage.getItem('wsoptv_users');
  if (existingUsers) {
    return JSON.parse(existingUsers);
  }

  // Create default admin user
  const defaultUsers: User[] = [
    {
      id: '1',
      username: 'garimto',
      password: '1234',
      role: 'admin',
      status: 'active',
      created_at: new Date().toISOString(),
    },
  ];

  localStorage.setItem('wsoptv_users', JSON.stringify(defaultUsers));
  return defaultUsers;
}

export default function LoginPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });

  useEffect(() => {
    // Initialize users on component mount
    initializeUsers();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      await new Promise((resolve) => setTimeout(resolve, 500));

      const users = initializeUsers();
      const user = users.find(
        (u) => u.username === formData.username && u.password === formData.password
      );

      if (!user) {
        setError('Invalid username or password.');
        return;
      }

      // Check user status
      switch (user.status) {
        case 'pending':
          setError('Your account is pending approval. Please wait for admin approval.');
          router.push('/pending');
          return;
        case 'rejected':
          setError('Your account has been rejected.');
          return;
        case 'suspended':
          setError('Your account has been suspended.');
          return;
        case 'active':
          // Login successful
          localStorage.setItem('token', `token-${user.id}-${Date.now()}`);
          localStorage.setItem('user', JSON.stringify({
            id: user.id,
            username: user.username,
            role: user.role,
            status: user.status,
          }));

          if (user.role === 'admin') {
            router.push('/admin');
          } else {
            router.push('/catalog');
          }
          break;
      }
    } catch {
      setError('Login failed. Please try again.');
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
                type="text"
                placeholder="Username"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
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
            <p>Admin: garimto / 1234</p>
          </div>
        </div>
      </div>
    </main>
  );
}
