'use client';

import { useState, useEffect, Suspense, useCallback } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Header } from '@/components/layout/header';
import { ContentCard } from '@/components/content/content-card';
import { Search, X, Filter } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { catalogApi } from '@/lib/api/catalog';
import type { CatalogItem, ProjectCode } from '@/types/api';

interface User {
  id: string;
  username: string;
  role: 'admin' | 'user';
}

// Category filter options (Block F ProjectCode 기반)
const CATEGORIES: Array<{ id: ProjectCode | 'all'; name: string }> = [
  { id: 'all', name: 'All' },
  { id: 'WSOP', name: 'WSOP' },
  { id: 'HCL', name: 'HCL' },
  { id: 'GGMILLIONS', name: 'GGMillions' },
  { id: 'GOG', name: 'GOG' },
  { id: 'MPP', name: 'MPP' },
  { id: 'PAD', name: 'PAD' },
  { id: 'OTHER', name: 'Other' },
];

// 신뢰도 배지 색상
function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.9) return 'text-green-400';
  if (confidence >= 0.7) return 'text-yellow-400';
  if (confidence >= 0.5) return 'text-orange-400';
  return 'text-red-400';
}

// CatalogItem을 ContentCard용으로 변환
function catalogItemToContent(item: CatalogItem) {
  return {
    id: item.id,
    title: item.display_title,
    description: item.file_path,
    duration_seconds: item.duration_seconds || 0,
    file_size_bytes: item.file_size_bytes,
    category: item.project_code,
    year: item.year || undefined,
    quality: item.quality || undefined,
    tags: item.category_tags,
    created_at: item.created_at,
    thumbnail_url: item.thumbnail_url || undefined,
    // Block F 전용 필드
    confidence: item.confidence,
    file_size_formatted: item.file_size_formatted,
    file_extension: item.file_extension,
  };
}

function SearchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [selectedCategory, setSelectedCategory] = useState<ProjectCode | 'all'>('all');
  const [results, setResults] = useState<CatalogItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const userData = localStorage.getItem('auth_user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  // Block F API 검색 함수
  const performSearch = useCallback(async (searchQuery: string, category: ProjectCode | 'all') => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Block F searchCatalog API 사용
      const searchResults = await catalogApi.searchCatalog(searchQuery.trim(), 50);

      // 카테고리 필터 적용 (클라이언트 사이드)
      const filteredResults =
        category === 'all'
          ? searchResults
          : searchResults.filter((item) => item.project_code === category);

      setResults(filteredResults);
    } catch (err) {
      console.error('Search failed:', err);
      setError('Search failed. Please try again.');
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const q = searchParams.get('q');
    if (q) {
      setQuery(q);
      performSearch(q, selectedCategory);
    }
  }, [searchParams, selectedCategory, performSearch]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query)}`);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('auth_user');
    router.push('/login');
  };

  const clearSearch = () => {
    setQuery('');
    setResults([]);
    router.push('/search');
  };

  return (
    <main className="min-h-screen bg-[#141414]">
      <Header
        user={user ? { username: user.username, role: user.role } : undefined}
        onLogout={handleLogout}
      />

      {/* Search Section */}
      <div className="pt-24 px-4 md:px-12">
        {/* Search Input */}
        <form onSubmit={handleSearch} className="max-w-2xl mx-auto mb-8">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
            <Input
              type="search"
              placeholder="Search titles, players, categories..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full pl-12 pr-12 py-6 text-lg bg-[#2a2a2a] border-gray-700 text-white placeholder-gray-500 focus:border-white rounded-md"
            />
            {query && (
              <button
                type="button"
                onClick={clearSearch}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
              >
                <X className="h-5 w-5" />
              </button>
            )}
          </div>
        </form>

        {/* Category Filters */}
        <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-2">
          <Filter className="h-4 w-4 text-gray-400 flex-shrink-0" />
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className={cn(
                'px-4 py-2 rounded-full text-sm font-medium transition-colors whitespace-nowrap',
                selectedCategory === cat.id
                  ? 'bg-white text-black'
                  : 'bg-[#2a2a2a] text-gray-300 hover:bg-[#3a3a3a]'
              )}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-500 rounded text-red-200 max-w-2xl mx-auto">
            {error}
          </div>
        )}

        {/* Results Section */}
        {query ? (
          <>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl text-white">
                {isLoading ? (
                  'Searching...'
                ) : results.length > 0 ? (
                  <>Results for "<span className="text-[#E50914]">{query}</span>"</>
                ) : (
                  <>No results for "<span className="text-[#E50914]">{query}</span>"</>
                )}
              </h2>
              {results.length > 0 && (
                <span className="text-gray-400 text-sm">{results.length} results</span>
              )}
            </div>

            {isLoading ? (
              <div className="flex items-center justify-center py-20">
                <div className="w-12 h-12 border-4 border-[#E50914] border-t-transparent rounded-full animate-spin" />
              </div>
            ) : results.length > 0 ? (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                {results.map((item) => (
                  <div key={item.id} className="group cursor-pointer" onClick={() => router.push(`/watch/${item.id}`)}>
                    <div className="relative rounded overflow-hidden bg-[#181818]">
                      {/* Thumbnail */}
                      <div className="aspect-video bg-[#2F2F2F] relative overflow-hidden">
                        {item.thumbnail_url ? (
                          <img src={item.thumbnail_url} alt={item.short_title} className="w-full h-full object-cover" />
                        ) : (
                          <div className="absolute inset-0 flex items-center justify-center">
                            <svg className="w-12 h-12 text-gray-600 group-hover:text-[#E50914] transition-colors" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M8 5v14l11-7z" />
                            </svg>
                          </div>
                        )}
                        {/* File extension badge */}
                        <div className="absolute top-2 left-2 bg-[#E50914] text-white text-xs px-1.5 py-0.5 rounded uppercase">
                          {item.file_extension.replace('.', '')}
                        </div>
                        {/* Confidence badge */}
                        <div className={`absolute top-2 right-2 ${getConfidenceColor(item.confidence)} text-xs font-semibold`}>
                          {Math.round(item.confidence * 100)}%
                        </div>
                        {/* File size */}
                        <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-1.5 py-0.5 rounded">
                          {item.file_size_formatted}
                        </div>
                      </div>
                      {/* Content info */}
                      <div className="p-2">
                        <h3 className="text-white text-sm font-medium line-clamp-2 group-hover:text-[#E50914] transition-colors">
                          {item.display_title}
                        </h3>
                        <div className="flex items-center gap-2 mt-1 text-xs text-gray-400">
                          <span className="text-[#46D369]">{item.project_code}</span>
                          {item.year && <span>• {item.year}</span>}
                        </div>
                        {/* Tags */}
                        {item.category_tags.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-1">
                            {item.category_tags.slice(0, 2).map((tag, i) => (
                              <span key={i} className="text-xs bg-[#333] text-gray-400 px-1 py-0.5 rounded">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-20">
                <p className="text-gray-400 mb-4">
                  No matches found. Try different keywords or browse categories.
                </p>
                <Button
                  onClick={() => router.push('/browse')}
                  className="bg-[#E50914] hover:bg-[#F40612] text-white"
                >
                  Browse All
                </Button>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-20">
            <Search className="h-16 w-16 text-gray-600 mx-auto mb-4" />
            <h2 className="text-xl text-white mb-2">Search WSOPTV</h2>
            <p className="text-gray-400">
              Find your favorite poker moments, players, and tournaments
            </p>
          </div>
        )}
      </div>

      {/* Popular Searches */}
      {!query && (
        <div className="px-4 md:px-12 py-12">
          <h3 className="text-lg text-white mb-4">Popular Searches</h3>
          <div className="flex flex-wrap gap-2">
            {['Phil Ivey', 'WSOP 2024', 'Main Event', 'HCL', 'Tom Dwan', 'Final Table', 'High Stakes', 'GGMillions'].map((term) => (
              <button
                key={term}
                onClick={() => {
                  setQuery(term);
                  router.push(`/search?q=${encodeURIComponent(term)}`);
                }}
                className="px-4 py-2 bg-[#2a2a2a] text-gray-300 rounded-full text-sm hover:bg-[#3a3a3a] transition-colors"
              >
                {term}
              </button>
            ))}
          </div>
        </div>
      )}
    </main>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen bg-[#141414] flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-[#E50914] border-t-transparent rounded-full animate-spin" />
      </main>
    }>
      <SearchContent />
    </Suspense>
  );
}
