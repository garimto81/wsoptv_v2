'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Header } from '@/components/layout/header';
import { ContentCard } from '@/components/content/content-card';
import { Search, X, Filter } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import type { Content } from '@/types/api';

interface User {
  id: string;
  username: string;
  role: 'admin' | 'user';
}

// Category filter options
const CATEGORIES = [
  { id: 'all', name: 'All' },
  { id: 'wsop', name: 'WSOP' },
  { id: 'hcl', name: 'HCL' },
  { id: 'ggmillions', name: 'GGMillions' },
  { id: 'gog', name: 'GOG' },
  { id: 'mpp', name: 'MPP' },
  { id: 'pad', name: 'PAD' },
];

// Mock search results
function generateMockResults(query: string, category: string): Content[] {
  const categories = ['WSOP', 'HCL', 'GGMillions', 'GOG', 'MPP', 'PAD'];
  const players = ['Phil Ivey', 'Daniel Negreanu', 'Tom Dwan', 'Doug Polk', 'Phil Hellmuth'];

  if (!query) return [];

  return Array.from({ length: 12 }, (_, i) => ({
    id: `search-${i + 1}`,
    title: `${query} - ${players[i % players.length]} ${['Bluff', 'All-in', 'Final Table', 'Cash Game'][i % 4]} ${i + 1}`,
    description: `Search result for "${query}" - Episode ${i + 1}`,
    duration_seconds: (Math.floor(Math.random() * 180) + 30) * 60,
    file_size_bytes: Math.floor(Math.random() * 5000000000),
    category: category !== 'all' ? category.toUpperCase() : categories[i % categories.length],
    year: 2024 - (i % 3),
    quality: 'HD',
    tags: [players[i % players.length], 'Poker', categories[i % categories.length]],
    created_at: new Date().toISOString(),
  })).filter(item =>
    category === 'all' || item.category?.toLowerCase() === category
  );
}

function SearchContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [results, setResults] = useState<Content[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const userData = localStorage.getItem('auth_user');
    if (userData) {
      setUser(JSON.parse(userData));
    }
  }, []);

  useEffect(() => {
    const q = searchParams.get('q');
    if (q) {
      setQuery(q);
      performSearch(q, selectedCategory);
    }
  }, [searchParams, selectedCategory]);

  const performSearch = async (searchQuery: string, category: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setIsLoading(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 300));
    const mockResults = generateMockResults(searchQuery, category);
    setResults(mockResults);
    setIsLoading(false);
  };

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
                {results.map((content) => (
                  <ContentCard
                    key={content.id}
                    content={content}
                    variant="compact"
                  />
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
            {['Phil Ivey', 'WSOP 2024', 'Final Table', 'HCL', 'Tom Dwan', 'High Stakes'].map((term) => (
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
