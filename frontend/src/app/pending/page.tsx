'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface PendingUser {
  username: string;
  created_at: string;
}

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

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function PendingPage() {
  const router = useRouter();
  const [pendingUser, setPendingUser] = useState<PendingUser | null>(null);
  const [currentStatus, setCurrentStatus] = useState<string>('pending');
  const [isChecking, setIsChecking] = useState(false);

  useEffect(() => {
    // Get pending user info
    const pendingData = localStorage.getItem('pending_user');
    if (pendingData) {
      setPendingUser(JSON.parse(pendingData));
    }
  }, []);

  const checkStatus = async () => {
    if (!pendingUser) return;

    setIsChecking(true);

    // Simulate checking delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    const users = getUsers();
    const user = users.find((u) => u.username === pendingUser.username);

    if (user) {
      setCurrentStatus(user.status);

      if (user.status === 'active') {
        // Clear pending user and redirect to login
        localStorage.removeItem('pending_user');
        router.push('/login');
      } else if (user.status === 'rejected') {
        // Show rejected message
        localStorage.removeItem('pending_user');
      }
    }

    setIsChecking(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('pending_user');
    router.push('/login');
  };

  if (currentStatus === 'rejected') {
    return (
      <main className="min-h-screen bg-black relative">
        <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/80 to-black" />

        <header className="relative z-10 px-8 py-6">
          <Link href="/" className="text-[#E50914] font-bold text-3xl tracking-tight">
            WSOPTV
          </Link>
        </header>

        <div className="relative z-10 flex items-center justify-center px-4 py-12">
          <div className="w-full max-w-md bg-black/75 rounded-md p-16 text-center">
            <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
              <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h1 className="text-white text-2xl font-bold mb-4">Registration Rejected</h1>
            <p className="text-gray-400 mb-8">
              Your registration request has been rejected by the administrator.
            </p>
            <button
              onClick={handleLogout}
              className="w-full bg-[#E50914] hover:bg-[#F40612] text-white py-3 rounded font-semibold transition-colors"
            >
              Back to Sign In
            </button>
          </div>
        </div>
      </main>
    );
  }

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

      {/* Pending Content */}
      <div className="relative z-10 flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-md bg-black/75 rounded-md p-16 text-center">
          {/* Pending Icon */}
          <div className="w-20 h-20 bg-yellow-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>

          <h1 className="text-white text-2xl font-bold mb-4">Pending Approval</h1>

          <p className="text-gray-400 mb-2">
            Your account has been created successfully.
          </p>
          <p className="text-yellow-500 text-sm mb-6">
            Please wait for administrator approval.
          </p>

          {pendingUser && (
            <div className="bg-[#333]/50 rounded p-4 mb-6 text-left">
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-400 text-sm">Username:</span>
                <span className="text-white font-medium">{pendingUser.username}</span>
              </div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-400 text-sm">Status:</span>
                <span className="text-yellow-500 font-medium">Pending</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-400 text-sm">Registered:</span>
                <span className="text-gray-300 text-sm">{formatDate(pendingUser.created_at)}</span>
              </div>
            </div>
          )}

          <button
            onClick={checkStatus}
            disabled={isChecking}
            className="w-full bg-[#46D369] hover:bg-[#3fc25d] text-white py-3 rounded font-semibold transition-colors disabled:opacity-50 mb-4"
          >
            {isChecking ? 'Checking...' : 'Check Status'}
          </button>

          <button
            onClick={handleLogout}
            className="w-full bg-[#333] hover:bg-[#444] text-white py-3 rounded font-semibold transition-colors"
          >
            Back to Sign In
          </button>

          <div className="mt-8 text-gray-500 text-xs">
            <p>Once approved, you can sign in with your credentials.</p>
          </div>
        </div>
      </div>
    </main>
  );
}
