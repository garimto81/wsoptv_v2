'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import { useRouter, useParams } from 'next/navigation';
import { VideoPlayer } from '@/components/player/video-player';
import { useAuth } from '@/hooks/use-auth';

// Mock data - will be replaced with API call
const mockContents: Record<string, {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  duration: number;
  category: string;
  tags: string[];
  created_at: string;
  view_count: number;
  video_url: string;
}> = {
  '1': {
    id: '1',
    title: 'WSOP 2024 Main Event',
    subtitle: 'Day 1 - Feature Table',
    description: '2024 WSOP Main Event Day 1 Highlights. The world\'s best poker players compete in the main event. Dramatic all-ins and big bluffs unfold.',
    duration: 7200,
    category: 'WSOP',
    tags: ['WSOP', '2024', 'Main Event', 'Final Table'],
    created_at: '2024-01-15T10:00:00Z',
    view_count: 1250,
    video_url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
  },
  '2': {
    id: '2',
    title: 'Hustler Casino Live',
    subtitle: 'High Stakes Cash Game - Episode 15',
    description: 'High Stakes Cash Game Episode 15. Intense cash game action at $100/$200 blinds.',
    duration: 5400,
    category: 'HCL',
    tags: ['Cash Game', 'High Stakes', 'HCL'],
    created_at: '2024-01-10T10:00:00Z',
    view_count: 890,
    video_url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
  },
  '3': {
    id: '3',
    title: 'Poker Strategy Masterclass',
    subtitle: '3-Betting Range Analysis',
    description: 'Preflop 3-Bet Range Analysis. Learn optimal 3-bet ranges by position and how to adjust based on situations.',
    duration: 3600,
    category: 'Tutorial',
    tags: ['Strategy', 'Tutorial', '3-Bet'],
    created_at: '2024-01-08T10:00:00Z',
    view_count: 2100,
    video_url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
  },
};

export default function WatchPage() {
  const router = useRouter();
  const params = useParams();
  const contentId = params.id as string;
  const { token, isAuthenticated, isLoading: authLoading } = useAuth();
  const progressSaveTimeout = useRef<NodeJS.Timeout>();
  const lastSavedProgress = useRef<number>(0);

  const [isLoading, setIsLoading] = useState(true);
  const [content, setContent] = useState<typeof mockContents['1'] | null>(null);
  const [initialProgress, setInitialProgress] = useState(0);

  // Load content and saved progress
  useEffect(() => {
    if (authLoading) return;

    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    const loadContent = async () => {
      // Load content
      await new Promise((resolve) => setTimeout(resolve, 300));
      const data = mockContents[contentId];
      if (!data) {
        router.push('/browse');
        return;
      }
      setContent(data);

      // Load saved progress from API
      if (token) {
        try {
          const response = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/api/v1/progress/${contentId}?token=${token}`
          );
          if (response.ok) {
            const progress = await response.json();
            if (progress && progress.progress_percent < 95) {
              setInitialProgress(progress.progress_percent / 100);
            }
          }
        } catch (error) {
          console.error('Failed to load progress:', error);
        }
      }

      setIsLoading(false);
    };
    loadContent();
  }, [contentId, router, token, isAuthenticated, authLoading]);

  // Save progress to API
  const saveProgress = useCallback(async (playedSeconds: number, duration: number) => {
    if (!token || !contentId) return;

    // Debounce: only save if changed by more than 5 seconds
    if (Math.abs(playedSeconds - lastSavedProgress.current) < 5) return;
    lastSavedProgress.current = playedSeconds;

    try {
      await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/api/v1/progress?token=${token}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            content_id: contentId,
            position_seconds: Math.floor(playedSeconds),
            duration_seconds: Math.floor(duration),
          }),
        }
      );
    } catch (error) {
      console.error('Failed to save progress:', error);
    }
  }, [token, contentId]);

  // Handle progress updates
  const handleProgress = useCallback((state: { played: number; playedSeconds: number; duration: number }) => {
    // Clear previous timeout
    if (progressSaveTimeout.current) {
      clearTimeout(progressSaveTimeout.current);
    }

    // Debounce save
    progressSaveTimeout.current = setTimeout(() => {
      saveProgress(state.playedSeconds, state.duration);
    }, 2000);
  }, [saveProgress]);

  // Handle video ended
  const handleEnded = useCallback(async () => {
    if (token && contentId) {
      try {
        await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/api/v1/progress/${contentId}/complete?token=${token}`,
          { method: 'POST' }
        );
      } catch (error) {
        console.error('Failed to mark as completed:', error);
      }
    }
  }, [token, contentId]);

  // Handle back navigation
  const handleBack = useCallback(() => {
    router.push('/browse');
  }, [router]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (progressSaveTimeout.current) {
        clearTimeout(progressSaveTimeout.current);
      }
    };
  }, []);

  if (isLoading || authLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-red-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!content) {
    return null;
  }

  return (
    <div className="min-h-screen bg-black">
      {/* Video Player - Full Screen */}
      <div className="fixed inset-0 z-50">
        <VideoPlayer
          url={content.video_url}
          title={content.title}
          subtitle={content.subtitle}
          contentId={content.id}
          initialProgress={initialProgress}
          onProgress={handleProgress}
          onEnded={handleEnded}
          onBack={handleBack}
          className="w-full h-full"
        />
      </div>

      {/* Content Info (hidden when fullscreen) */}
      <div className="hidden">
        <div className="bg-[#141414] px-8 py-8">
          <div className="max-w-4xl">
            <div className="flex flex-wrap gap-2 mb-4">
              {content.tags.map((tag) => (
                <span key={tag} className="bg-[#333] text-white text-xs px-3 py-1 rounded">
                  {tag}
                </span>
              ))}
            </div>
            <p className="text-gray-300">{content.description}</p>
            <div className="flex items-center gap-4 mt-4 text-sm text-gray-400">
              <span>{content.view_count.toLocaleString()} views</span>
              <span>•</span>
              <span>{new Date(content.created_at).toLocaleDateString('en-US')}</span>
            </div>
          </div>

          {/* More Like This */}
          <div className="mt-12">
            <h2 className="text-white text-xl font-bold mb-4">More Like This</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
              {Object.values(mockContents)
                .filter((c) => c.id !== contentId)
                .map((c) => (
                  <Link key={c.id} href={`/watch/${c.id}`} className="group">
                    <div className="rounded overflow-hidden bg-[#181818] transition-transform hover:scale-105">
                      <div className="aspect-video bg-[#2F2F2F] flex items-center justify-center">
                        <svg className="w-12 h-12 text-gray-600 group-hover:text-red-600 transition-colors" fill="currentColor" viewBox="0 0 24 24">
                          <path d="M8 5v14l11-7z" />
                        </svg>
                      </div>
                      <div className="p-3">
                        <h3 className="text-white text-sm font-medium line-clamp-2">{c.title}</h3>
                        <p className="text-gray-400 text-xs mt-1">{c.view_count.toLocaleString()} views</p>
                      </div>
                    </div>
                  </Link>
                ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
