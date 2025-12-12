'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import { useRouter, useParams } from 'next/navigation';
import { VideoPlayer } from '@/components/player/video-player';
import { useAuth } from '@/hooks/use-auth';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

interface ContentData {
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
}

export default function WatchPage() {
  const router = useRouter();
  const params = useParams();
  const contentId = params.id as string;
  const { token, isAuthenticated, isLoading: authLoading } = useAuth();
  const progressSaveTimeout = useRef<NodeJS.Timeout>();
  const lastSavedProgress = useRef<number>(0);

  const [isLoading, setIsLoading] = useState(true);
  const [content, setContent] = useState<ContentData | null>(null);
  const [initialProgress, setInitialProgress] = useState(0);

  // Load content and saved progress
  useEffect(() => {
    if (authLoading) return;

    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    const loadContent = async () => {
      try {
        // Catalog API에서 아이템 조회
        const response = await fetch(`${API_URL}/api/v1/catalog/${contentId}`);
        if (!response.ok) {
          console.error('Failed to load catalog item');
          router.push('/browse');
          return;
        }

        const catalogItem = await response.json();

        // 스트림 URL 구성
        const streamUrl = `${API_URL}/stream/${contentId}/video`;

        setContent({
          id: catalogItem.id,
          title: catalogItem.display_title,
          subtitle: catalogItem.short_title || '',
          description: `${catalogItem.project_code} - ${catalogItem.file_name}`,
          duration: catalogItem.duration_seconds || 0,
          category: catalogItem.project_code,
          tags: catalogItem.category_tags || [],
          created_at: catalogItem.created_at,
          view_count: 0,
          video_url: streamUrl,
        });

        // Load saved progress from API
        if (token) {
          try {
            const progressRes = await fetch(
              `${API_URL}/api/v1/progress/${contentId}?token=${token}`
            );
            if (progressRes.ok) {
              const progress = await progressRes.json();
              if (progress && progress.progress_percent < 95) {
                setInitialProgress(progress.progress_percent / 100);
              }
            }
          } catch (error) {
            console.error('Failed to load progress:', error);
          }
        }
      } catch (error) {
        console.error('Failed to load content:', error);
        router.push('/browse');
        return;
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
        `${API_URL}/api/v1/progress?token=${token}`,
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
          `${API_URL}/api/v1/progress/${contentId}/complete?token=${token}`,
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

          {/* More Like This - TODO: API 연동 */}
        </div>
      </div>
    </div>
  );
}
