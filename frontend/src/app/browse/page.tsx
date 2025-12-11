'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/header';
import { HeroBillboard } from '@/components/content/hero-billboard';
import { ContentRow } from '@/components/content/content-row';

interface User {
  id: string;
  username: string;
  role: 'admin' | 'user';
  status: string;
}

function getAuthUser(): User | null {
  if (typeof window === 'undefined') return null;
  const userData = localStorage.getItem('auth_user');
  return userData ? JSON.parse(userData) : null;
}

export default function BrowsePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const authUser = getAuthUser();
    if (!authUser) {
      router.push('/login');
      return;
    }
    setUser(authUser);
    setIsLoading(false);
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('auth_user');
    router.push('/login');
  };

  if (isLoading) {
    return (
      <main className="min-h-screen bg-[#141414] flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-[#E50914] border-t-transparent rounded-full animate-spin" />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#141414]">
      {/* Header */}
      <Header
        user={user ? { username: user.username, role: user.role } : undefined}
        onLogout={handleLogout}
      />

      {/* Hero Billboard */}
      <HeroBillboard />

      {/* Content Rows */}
      <div className="relative z-10 -mt-20 pb-12 space-y-4">
        {/* Continue Watching */}
        <ContentRow
          title="Continue Watching"
          items={[]}
          variant="continue-watching"
        />

        {/* Today's Top 10 */}
        <ContentRow
          title="Today in WSOPTV"
          items={[]}
          variant="top10"
        />

        {/* WSOP Series */}
        <ContentRow
          title="WSOP Series"
          items={[]}
          variant="default"
        />

        {/* HCL (Hustler Casino Live) */}
        <ContentRow
          title="Hustler Casino Live"
          items={[]}
          variant="default"
        />

        {/* GGMillions */}
        <ContentRow
          title="GGMillions"
          items={[]}
          variant="default"
        />

        {/* Phil Ivey Collection */}
        <ContentRow
          title="Phil Ivey Moments"
          items={[]}
          variant="default"
        />

        {/* High Stakes Cash Games */}
        <ContentRow
          title="High Stakes Cash Games"
          items={[]}
          variant="default"
        />

        {/* New Releases */}
        <ContentRow
          title="New Releases"
          items={[]}
          variant="default"
        />
      </div>

      {/* Footer */}
      <footer className="px-4 md:px-12 py-8 text-gray-500 text-sm">
        <div className="max-w-6xl">
          <p className="mb-4">Questions? Contact us.</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <a href="#" className="hover:underline">FAQ</a>
            <a href="#" className="hover:underline">Help Center</a>
            <a href="#" className="hover:underline">Terms of Use</a>
            <a href="#" className="hover:underline">Privacy</a>
          </div>
          <p className="text-xs text-gray-600">WSOPTV - Private Poker VOD Platform</p>
        </div>
      </footer>
    </main>
  );
}
