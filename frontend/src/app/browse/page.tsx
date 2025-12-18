'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Header } from '@/components/layout/header';
import { HeroBillboard } from '@/components/content/hero-billboard';
import { ContentRow } from '@/components/content/content-row';
import { catalogApi } from '@/lib/api/catalog';
import type { CatalogItem, ProjectCode } from '@/types/api';

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

// CatalogItem을 ContentRow의 ContentItem으로 변환
function catalogToContentItem(item: CatalogItem) {
  return {
    id: item.id,
    title: item.display_title,
    shortTitle: item.short_title,
    thumbnail: item.thumbnail_url || undefined,
    category: item.project_code,
    year: item.year || undefined,
    duration: item.duration_seconds
      ? `${Math.floor(item.duration_seconds / 3600)}h ${Math.floor((item.duration_seconds % 3600) / 60)}m`
      : undefined,
    confidence: item.confidence,
    tags: item.category_tags,
  };
}

// CatalogItem을 HeroBillboard의 FeaturedContent로 변환
function catalogToFeaturedContent(item: CatalogItem) {
  return {
    id: item.id,
    title: item.display_title,
    description: `${item.project_code} ${item.year || ''} - ${item.category_tags.slice(0, 3).join(', ')}`,
    category: item.project_code,
    thumbnail: item.thumbnail_url || undefined,
    year: item.year || undefined,
    duration: item.duration_seconds
      ? `${Math.floor(item.duration_seconds / 3600)}h ${Math.floor((item.duration_seconds % 3600) / 60)}m`
      : undefined,
    tags: item.category_tags,
  };
}

export default function BrowsePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Block F 데이터
  const [wsopItems, setWsopItems] = useState<CatalogItem[]>([]);
  const [hclItems, setHclItems] = useState<CatalogItem[]>([]);
  const [ggmillionsItems, setGgmillionsItems] = useState<CatalogItem[]>([]);
  const [gogItems, setGogItems] = useState<CatalogItem[]>([]);
  const [recentItems, setRecentItems] = useState<CatalogItem[]>([]);
  const [topItems, setTopItems] = useState<CatalogItem[]>([]);

  useEffect(() => {
    const authUser = getAuthUser();
    if (!authUser) {
      router.push('/login');
      return;
    }
    setUser(authUser);

    // Block F API로 데이터 로드
    const loadCatalogData = async () => {
      try {
        const [wsop, hcl, ggmillions, gog, recent] = await Promise.all([
          catalogApi.getCatalogItems({ project_code: 'WSOP' as ProjectCode, limit: 15 }),
          catalogApi.getCatalogItems({ project_code: 'HCL' as ProjectCode, limit: 15 }),
          catalogApi.getCatalogItems({ project_code: 'GGMILLIONS' as ProjectCode, limit: 15 }),
          catalogApi.getCatalogItems({ project_code: 'GOG' as ProjectCode, limit: 15 }),
          catalogApi.getCatalogItems({ limit: 10 }), // 최신 항목
        ]);

        setWsopItems(wsop.items);
        setHclItems(hcl.items);
        setGgmillionsItems(ggmillions.items);
        setGogItems(gog.items);
        setRecentItems(recent.items);

        // Top 10: 신뢰도 높은 순으로 정렬
        const allItems = [...wsop.items, ...hcl.items, ...ggmillions.items, ...gog.items];
        const sorted = allItems.sort((a, b) => b.confidence - a.confidence).slice(0, 10);
        setTopItems(sorted);
      } catch (err) {
        console.error('Failed to load catalog data:', err);
      } finally {
        setIsLoading(false);
      }
    };

    loadCatalogData();
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
      <HeroBillboard content={topItems[0] ? catalogToFeaturedContent(topItems[0]) : undefined} />

      {/* Content Rows */}
      <div className="relative z-10 -mt-20 pb-12 space-y-4">
        {/* Continue Watching - 추후 Watch History 연동 */}
        <ContentRow
          title="Continue Watching"
          items={[]}
          variant="continue-watching"
        />

        {/* Today's Top 10 */}
        <ContentRow
          title="Today in WSOPTV"
          items={topItems.map((item, i) => ({
            ...catalogToContentItem(item),
            rank: i + 1,
          }))}
          variant="top10"
        />

        {/* WSOP Series */}
        {wsopItems.length > 0 && (
          <ContentRow
            title="WSOP Series"
            items={wsopItems.map(catalogToContentItem)}
            variant="default"
          />
        )}

        {/* HCL (Hustler Casino Live) */}
        {hclItems.length > 0 && (
          <ContentRow
            title="Hustler Casino Live"
            items={hclItems.map(catalogToContentItem)}
            variant="default"
          />
        )}

        {/* GGMillions */}
        {ggmillionsItems.length > 0 && (
          <ContentRow
            title="GGMillions"
            items={ggmillionsItems.map(catalogToContentItem)}
            variant="default"
          />
        )}

        {/* GOG */}
        {gogItems.length > 0 && (
          <ContentRow
            title="Game of Gold"
            items={gogItems.map(catalogToContentItem)}
            variant="default"
          />
        )}

        {/* New Releases */}
        {recentItems.length > 0 && (
          <ContentRow
            title="Recently Added"
            items={recentItems.map(catalogToContentItem)}
            variant="default"
          />
        )}
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
