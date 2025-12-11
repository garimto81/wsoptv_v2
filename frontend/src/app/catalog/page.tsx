'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { catalogApi } from '@/lib/api/catalog';
import type { NASFile } from '@/types/api';

// Video content type for display
interface VideoContent {
  id: string;
  title: string;
  description: string;
  thumbnail_url: string | null;
  size_bytes: number;
  category: string;
  path: string;
  extension: string;
}

const categories = [
  { value: 'all', label: 'All' },
  { value: 'WSOP', label: 'WSOP' },
  { value: 'HCL', label: 'HCL' },
  { value: 'GGMillions', label: 'GGMillions' },
  { value: 'GOG', label: 'GOG' },
  { value: 'MPP', label: 'MPP' },
  { value: 'PAD', label: 'PAD' },
];

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function extractProjectFromPath(path: string): string {
  const parts = path.split('/');
  if (parts.length > 1) {
    const project = parts[1];
    if (['WSOP', 'HCL', 'GGMillions', 'GOG', 'MPP', 'PAD'].includes(project)) {
      return project;
    }
    if (project.startsWith('GOG')) return 'GOG';
  }
  return 'OTHER';
}

function ContentCard({ content }: { content: VideoContent }) {
  return (
    <Link href={`/watch/${content.id}`} className="group">
      <div className="relative netflix-card rounded overflow-hidden bg-[#181818]">
        {/* Thumbnail */}
        <div className="aspect-video bg-[#2F2F2F] relative overflow-hidden">
          <div className="absolute inset-0 flex items-center justify-center">
            <svg className="w-16 h-16 text-gray-600 group-hover:text-[#E50914] transition-colors" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
          {/* Size badge */}
          <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-1 rounded">
            {formatSize(content.size_bytes)}
          </div>
          {/* Extension badge */}
          <div className="absolute top-2 left-2 bg-[#E50914] text-white text-xs px-2 py-1 rounded uppercase">
            {content.extension.replace('.', '')}
          </div>
          {/* Hover overlay */}
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />
        </div>

        {/* Content info */}
        <div className="p-3">
          <h3 className="text-white font-medium text-sm line-clamp-2 group-hover:text-[#E50914] transition-colors">
            {content.title}
          </h3>
          <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
            <span className="text-[#46D369]">{content.category}</span>
          </div>
        </div>
      </div>
    </Link>
  );
}

function ContentSkeleton() {
  return (
    <div className="rounded overflow-hidden bg-[#181818]">
      <div className="aspect-video bg-[#2F2F2F] animate-pulse" />
      <div className="p-3 space-y-2">
        <div className="h-4 bg-[#2F2F2F] rounded animate-pulse" />
        <div className="h-3 bg-[#2F2F2F] rounded w-2/3 animate-pulse" />
      </div>
    </div>
  );
}

export default function CatalogPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [contents, setContents] = useState<VideoContent[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [user, setUser] = useState<{ username: string; role: string } | null>(null);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<{ total: number; totalSize: string } | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    if (!token) {
      router.push('/login');
      return;
    }
    if (userData) {
      setUser(JSON.parse(userData));
    }

    const loadContents = async () => {
      try {
        // Fetch video files from Catalog API
        const videoFiles = await catalogApi.getNASVideoFiles();

        // Transform NAS files to VideoContent
        const transformedContents: VideoContent[] = videoFiles.map((file: NASFile) => ({
          id: file.id,
          title: file.file_name,
          description: file.file_path,
          thumbnail_url: null,
          size_bytes: file.file_size_bytes,
          category: extractProjectFromPath(file.file_path),
          path: file.file_path,
          extension: file.file_extension || '.mp4',
        }));

        setContents(transformedContents);

        // Get stats
        const fileStats = await catalogApi.getNASFileStats();
        setStats({
          total: fileStats.total_files,
          totalSize: formatSize(fileStats.total_size_bytes),
        });

        setIsLoading(false);
      } catch (err) {
        console.error('Failed to load contents:', err);
        setError('Failed to load video catalog. Please try again.');
        setIsLoading(false);
      }
    };
    loadContents();
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.push('/login');
  };

  const filteredContents = contents.filter((content) => {
    const matchesSearch =
      searchQuery === '' ||
      content.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      content.path.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory =
      selectedCategory === 'all' || content.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-screen bg-[#141414]">
      {/* Netflix-style Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-b from-black/80 to-transparent">
        <div className="flex items-center justify-between px-8 py-4">
          <div className="flex items-center gap-8">
            <Link href="/catalog" className="text-[#E50914] font-bold text-2xl tracking-tight">
              WSOPTV
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              {categories.map((cat) => (
                <button
                  key={cat.value}
                  onClick={() => setSelectedCategory(cat.value)}
                  className={`text-sm transition-colors ${
                    selectedCategory === cat.value
                      ? 'text-white font-semibold'
                      : 'text-gray-300 hover:text-gray-100'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
              <Link
                href="/hand-analysis"
                className="text-gray-300 hover:text-white text-sm transition-colors border-l border-gray-600 pl-6"
              >
                Hand Analysis
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            {/* Search */}
            <div className="relative">
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-black/50 border border-gray-600 text-white text-sm rounded px-4 py-2 w-48 focus:w-64 focus:outline-none focus:border-white transition-all placeholder-gray-400"
              />
              <svg className="w-4 h-4 text-gray-400 absolute right-3 top-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>

            {/* Admin link */}
            {user?.role === 'admin' && (
              <Link
                href="/admin"
                className="text-gray-300 hover:text-white text-sm transition-colors"
              >
                Admin
              </Link>
            )}

            {/* User menu */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 group"
              >
                <div className="w-8 h-8 bg-[#E50914] rounded flex items-center justify-center text-white font-semibold text-sm">
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </div>
                <svg className={`w-4 h-4 text-white transition-transform ${showUserMenu ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {showUserMenu && (
                <div className="absolute right-0 top-12 w-48 bg-[#141414] border border-[#333] rounded shadow-lg py-2">
                  <div className="px-4 py-2 border-b border-[#333]">
                    <p className="text-white text-sm font-medium">{user?.username}</p>
                    <p className="text-gray-400 text-xs">{user?.role === 'admin' ? 'Admin' : 'User'}</p>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-gray-300 hover:bg-[#333] text-sm transition-colors"
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-24 px-8 pb-16">
        {/* Category title */}
        <div className="mb-6">
          <h1 className="text-white text-2xl font-bold">
            {categories.find((c) => c.value === selectedCategory)?.label || 'All'} Videos
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            {isLoading ? '...' : `${filteredContents.length} of ${stats?.total || 0} videos`}
            {stats && ` (${stats.totalSize} total)`}
          </p>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-500 rounded text-red-200">
            {error}
          </div>
        )}

        {/* Content Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
          {isLoading
            ? Array.from({ length: 12 }).map((_, i) => <ContentSkeleton key={i} />)
            : filteredContents.map((content) => (
                <ContentCard key={content.id} content={content} />
              ))}
        </div>

        {/* No results */}
        {!isLoading && filteredContents.length === 0 && (
          <div className="text-center py-16">
            <p className="text-gray-400 text-lg">No results found</p>
            <p className="text-gray-500 text-sm mt-2">Try a different search term or category</p>
          </div>
        )}
      </main>
    </div>
  );
}
