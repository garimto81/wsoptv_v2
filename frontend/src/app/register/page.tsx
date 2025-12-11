'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface User {
  id: string;
  username: string;
  password: string;
  role: 'admin' | 'user';
  status: 'pending' | 'active' | 'rejected' | 'suspended';
  created_at: string;
}

function getUsers(): User[] {
  if (typeof window === 'undefined') return [];
  const users = localStorage.getItem('wsoptv_users');
  return users ? JSON.parse(users) : [];
}

function saveUsers(users: User[]): void {
  localStorage.setItem('wsoptv_users', JSON.stringify(users));
}

export default function RegisterPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
  });

  const validateUsername = (username: string): string | null => {
    if (username.length < 4) {
      return 'Username must be at least 4 characters.';
    }
    if (username.length > 20) {
      return 'Username must be 20 characters or less.';
    }
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      return 'Username can only contain letters, numbers, and underscores.';
    }
    return null;
  };

  const validatePassword = (password: string): string | null => {
    if (password.length < 4) {
      return 'Password must be at least 4 characters.';
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // Validate username
      const usernameError = validateUsername(formData.username);
      if (usernameError) {
        setError(usernameError);
        return;
      }

      // Validate password
      const passwordError = validatePassword(formData.password);
      if (passwordError) {
        setError(passwordError);
        return;
      }

      // Check password confirmation
      if (formData.password !== formData.confirmPassword) {
        setError('Passwords do not match.');
        return;
      }

      // Check if username already exists
      const users = getUsers();
      if (users.find((u) => u.username.toLowerCase() === formData.username.toLowerCase())) {
        setError('Username already exists.');
        return;
      }

      // Create new user with pending status
      const newUser: User = {
        id: `user-${Date.now()}`,
        username: formData.username,
        password: formData.password,
        role: 'user',
        status: 'pending',
        created_at: new Date().toISOString(),
      };

      users.push(newUser);
      saveUsers(users);

      // Store pending user info for the pending page
      localStorage.setItem('pending_user', JSON.stringify({
        username: newUser.username,
        created_at: newUser.created_at,
      }));

      // Redirect to pending page
      router.push('/pending');
    } catch {
      setError('Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const passwordsMatch = formData.confirmPassword.length > 0 && formData.password === formData.confirmPassword;
  const passwordsMismatch = formData.confirmPassword.length > 0 && formData.password !== formData.confirmPassword;

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

      {/* Registration Form */}
      <div className="relative z-10 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md bg-black/75 rounded-md p-16">
          <h1 className="text-white text-3xl font-bold mb-8">Sign Up</h1>

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-[#E87C03] text-white text-sm p-3 rounded">
                {error}
              </div>
            )}

            <div>
              <label className="block text-gray-400 text-sm mb-2">Username</label>
              <input
                type="text"
                placeholder="4-20 characters, letters/numbers only"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                disabled={isLoading}
                required
                className="w-full bg-[#333] text-white rounded px-4 py-4 text-base placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-white/20 border border-transparent focus:border-[#E50914]"
              />
            </div>

            <div>
              <label className="block text-gray-400 text-sm mb-2">Password</label>
              <input
                type="password"
                placeholder="At least 4 characters"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                disabled={isLoading}
                required
                className="w-full bg-[#333] text-white rounded px-4 py-4 text-base placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-white/20 border border-transparent focus:border-[#E50914]"
              />
            </div>

            <div>
              <label className="block text-gray-400 text-sm mb-2">Confirm Password</label>
              <input
                type="password"
                placeholder="Re-enter your password"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                disabled={isLoading}
                required
                className={`w-full bg-[#333] text-white rounded px-4 py-4 text-base placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-white/20 border ${
                  passwordsMismatch ? 'border-red-500' : passwordsMatch ? 'border-green-500' : 'border-transparent'
                } focus:border-[#E50914]`}
              />
              {passwordsMismatch && (
                <p className="text-red-500 text-xs mt-1">Passwords do not match</p>
              )}
              {passwordsMatch && (
                <p className="text-green-500 text-xs mt-1">Passwords match</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading || passwordsMismatch}
              className="w-full bg-[#E50914] hover:bg-[#F40612] text-white py-3 rounded font-semibold text-base transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-6"
            >
              {isLoading ? 'Signing Up...' : 'Sign Up'}
            </button>
          </form>

          <div className="mt-8 text-gray-400 text-sm">
            <p>
              Already have an account?{' '}
              <Link href="/login" className="text-white hover:underline">
                Sign in
              </Link>
            </p>
          </div>

          <div className="mt-6 p-4 bg-[#333]/50 rounded text-gray-400 text-xs">
            <p className="font-semibold text-gray-300 mb-2">Note:</p>
            <p>After registration, your account will be in pending status.</p>
            <p>An administrator must approve your account before you can access the platform.</p>
          </div>
        </div>
      </div>
    </main>
  );
}
