'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { catalogApi } from '@/lib/api/catalog';
import type { CatalogItem, CatalogStats, ProjectCode } from '@/types/api';

// 프로젝트 목록 (Block F 지원)
const PROJECT_CODES: Array<{ value: ProjectCode | 'all'; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'WSOP', label: 'WSOP' },
  { value: 'HCL', label: 'HCL' },
  { value: 'GGMILLIONS', label: 'GGMillions' },
  { value: 'GOG', label: 'GOG' },
  { value: 'MPP', label: 'MPP' },
  { value: 'PAD', label: 'PAD' },
  { value: 'OTHER', label: 'Other' },
];

/**
 * 신뢰도에 따른 배지 색상
 */
function getConfidenceBadgeColor(confidence: number): string {
  if (confidence >= 0.9) return 'bg-green-500';
  if (confidence >= 0.7) return 'bg-yellow-500';
  if (confidence >= 0.5) return 'bg-orange-500';
  return 'bg-red-500';
}

/**
 * CatalogItem 기반 콘텐츠 카드
 */
function CatalogCard({ item, onClick }: { item: CatalogItem; onClick: () => void }) {
  return (
    <div
      className="group cursor-pointer"
      onClick={onClick}
    >
      <div className="relative netflix-card rounded overflow-hidden bg-[#181818]">
        {/* Thumbnail */}
        <div className="aspect-video bg-[#2F2F2F] relative overflow-hidden">
          {item.thumbnail_url ? (
            <img
              src={item.thumbnail_url}
              alt={item.short_title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <svg className="w-16 h-16 text-gray-600 group-hover:text-[#E50914] transition-colors" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
          )}

          {/* File size badge */}
          <div className="absolute bottom-2 right-2 bg-black/80 text-white text-xs px-2 py-1 rounded">
            {item.file_size_formatted}
          </div>

          {/* Extension badge */}
          <div className="absolute top-2 left-2 bg-[#E50914] text-white text-xs px-2 py-1 rounded uppercase">
            {item.file_extension.replace('.', '')}
          </div>

          {/* Confidence badge */}
          <div className={`absolute top-2 right-2 ${getConfidenceBadgeColor(item.confidence)} text-white text-xs px-2 py-1 rounded`}>
            {Math.round(item.confidence * 100)}%
          </div>

          {/* Hover overlay */}
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors" />
        </div>

        {/* Content info */}
        <div className="p-3">
          <h3 className="text-white font-medium text-sm line-clamp-2 group-hover:text-[#E50914] transition-colors">
            {item.display_title}
          </h3>
          <div className="flex items-center gap-2 mt-2 text-xs text-gray-400">
            <span className="text-[#46D369]">{item.project_code}</span>
            {item.year && <span>•</span>}
            {item.year && <span>{item.year}</span>}
          </div>
          {/* Category tags */}
          {item.category_tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {item.category_tags.slice(0, 3).map((tag, i) => (
                <span key={i} className="text-xs bg-[#333] text-gray-300 px-1.5 py-0.5 rounded">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
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

/**
 * 콘텐츠 상세 모달
 */
function ContentDetailModal({
  item,
  onClose,
  onPlay,
}: {
  item: CatalogItem;
  onClose: () => void;
  onPlay: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80" onClick={onClose}>
      <div
        className="bg-[#181818] rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header with close button */}
        <div className="relative">
          <div className="aspect-video bg-[#2F2F2F] flex items-center justify-center">
            {item.thumbnail_url ? (
              <img src={item.thumbnail_url} alt={item.display_title} className="w-full h-full object-cover" />
            ) : (
              <svg className="w-24 h-24 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </div>
          <button
            onClick={onClose}
            className="absolute top-4 right-4 w-8 h-8 bg-[#181818] rounded-full flex items-center justify-center text-white hover:bg-[#333] transition-colors"
          >
            ✕
          </button>
        </div>

        <div className="p-6">
          {/* Title and actions */}
          <h2 className="text-2xl font-bold text-white mb-4">{item.display_title}</h2>
          <div className="flex gap-3 mb-6">
            <button
              onClick={onPlay}
              className="flex items-center gap-2 bg-white text-black px-6 py-2 rounded font-semibold hover:bg-gray-200 transition-colors"
            >
              ▶ Play
            </button>
            <button className="flex items-center justify-center w-10 h-10 border border-gray-500 rounded-full text-white hover:border-white transition-colors">
              +
            </button>
          </div>

          {/* Title Generator Metadata */}
          <div className="border-t border-[#333] pt-4 mb-4">
            <h3 className="text-lg font-semibold text-white mb-3">Title Generator Metadata</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-400">Project:</span>
                <span className="text-white ml-2">{item.project_code}</span>
              </div>
              {item.year && (
                <div>
                  <span className="text-gray-400">Year:</span>
                  <span className="text-white ml-2">{item.year}</span>
                </div>
              )}
              <div className="col-span-2">
                <span className="text-gray-400">Confidence:</span>
                <div className="inline-flex items-center ml-2">
                  <div className="w-32 h-2 bg-[#333] rounded overflow-hidden">
                    <div
                      className={`h-full ${getConfidenceBadgeColor(item.confidence)}`}
                      style={{ width: `${item.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-white ml-2">{Math.round(item.confidence * 100)}%</span>
                </div>
              </div>
            </div>
          </div>

          {/* File Info */}
          <div className="border-t border-[#333] pt-4 mb-4">
            <h3 className="text-lg font-semibold text-white mb-3">File Information</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-400">File Name:</span>
                <span className="text-white ml-2 break-all">{item.file_name}</span>
              </div>
              <div>
                <span className="text-gray-400">Size:</span>
                <span className="text-white ml-2">{item.file_size_formatted}</span>
              </div>
              <div>
                <span className="text-gray-400">Format:</span>
                <span className="text-white ml-2 uppercase">{item.file_extension.replace('.', '')}</span>
              </div>
              {item.duration_seconds && (
                <div>
                  <span className="text-gray-400">Duration:</span>
                  <span className="text-white ml-2">
                    {Math.floor(item.duration_seconds / 3600)}h {Math.floor((item.duration_seconds % 3600) / 60)}m
                  </span>
                </div>
              )}
              {item.quality && (
                <div>
                  <span className="text-gray-400">Quality:</span>
                  <span className="text-white ml-2">{item.quality}</span>
                </div>
              )}
            </div>
          </div>

          {/* Category Tags */}
          {item.category_tags.length > 0 && (
            <div className="border-t border-[#333] pt-4">
              <h3 className="text-lg font-semibold text-white mb-3">Category Tags</h3>
              <div className="flex flex-wrap gap-2">
                {item.category_tags.map((tag, i) => (
                  <span key={i} className="bg-[#333] text-white px-3 py-1 rounded text-sm">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CatalogPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [items, setItems] = useState<CatalogItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProject, setSelectedProject] = useState<ProjectCode | 'all'>('all');
  const [selectedYear, setSelectedYear] = useState<number | null>(null);
  const [availableYears, setAvailableYears] = useState<number[]>([]);
  const [user, setUser] = useState<{ username: string; role: string } | null>(null);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<CatalogStats | null>(null);
  const [selectedItem, setSelectedItem] = useState<CatalogItem | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const LIMIT = 100;

  // 데이터 로드 함수
  const loadCatalog = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Block F API 사용
      const params = {
        project_code: selectedProject !== 'all' ? selectedProject : undefined,
        year: selectedYear || undefined,
        visible_only: true,
        skip: page * LIMIT,
        limit: LIMIT,
      };

      const [catalogResponse, statsResponse, yearsResponse] = await Promise.all([
        catalogApi.getCatalogItems(params),
        catalogApi.getCatalogStats(),
        catalogApi.getCatalogYears(selectedProject !== 'all' ? selectedProject : undefined),
      ]);

      setItems(catalogResponse.items);
      setTotal(catalogResponse.total);
      setStats(statsResponse);
      setAvailableYears(yearsResponse);
    } catch (err) {
      console.error('Failed to load catalog:', err);
      setError('Failed to load catalog. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedProject, selectedYear, page]);

  // 검색 함수
  const handleSearch = useCallback(async () => {
    if (!searchQuery.trim()) {
      loadCatalog();
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const results = await catalogApi.searchCatalog(searchQuery.trim());
      setItems(results);
      setTotal(results.length);
    } catch (err) {
      console.error('Search failed:', err);
      setError('Search failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [searchQuery, loadCatalog]);

  // 초기 로드
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

    loadCatalog();
  }, [router, loadCatalog]);

  // 프로젝트/연도 변경 시 재로드
  useEffect(() => {
    if (!searchQuery) {
      loadCatalog();
    }
  }, [selectedProject, selectedYear, page, loadCatalog, searchQuery]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.push('/login');
  };

  const handlePlay = (item: CatalogItem) => {
    router.push(`/watch/${item.id}`);
  };

  // 클라이언트 사이드 필터링 (검색어 입력 시)
  const filteredItems = searchQuery
    ? items.filter(
        (item) =>
          item.display_title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          item.file_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          item.category_tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      )
    : items;

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
              {PROJECT_CODES.map((proj) => (
                <button
                  key={proj.value}
                  onClick={() => {
                    setSelectedProject(proj.value);
                    setSelectedYear(null);
                    setPage(0);
                  }}
                  className={`text-sm transition-colors ${
                    selectedProject === proj.value
                      ? 'text-white font-semibold'
                      : 'text-gray-300 hover:text-gray-100'
                  }`}
                >
                  {proj.label}
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
            {/* Year filter */}
            {availableYears.length > 0 && (
              <select
                value={selectedYear || ''}
                onChange={(e) => {
                  setSelectedYear(e.target.value ? parseInt(e.target.value) : null);
                  setPage(0);
                }}
                className="bg-black/50 border border-gray-600 text-white text-sm rounded px-3 py-2 focus:outline-none focus:border-white"
              >
                <option value="">All Years</option>
                {availableYears.map((year) => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            )}

            {/* Search */}
            <div className="relative">
              <input
                type="text"
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                className="bg-black/50 border border-gray-600 text-white text-sm rounded px-4 py-2 w-48 focus:w-64 focus:outline-none focus:border-white transition-all placeholder-gray-400"
              />
              <button
                onClick={handleSearch}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </button>
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
            {PROJECT_CODES.find((p) => p.value === selectedProject)?.label || 'All'} Videos
            {selectedYear && ` (${selectedYear})`}
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            {isLoading ? '...' : `${filteredItems.length} of ${total} videos`}
            {stats && ` • ${stats.total_items} total in catalog`}
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
            : filteredItems.map((item) => (
                <CatalogCard
                  key={item.id}
                  item={item}
                  onClick={() => setSelectedItem(item)}
                />
              ))}
        </div>

        {/* No results */}
        {!isLoading && filteredItems.length === 0 && (
          <div className="text-center py-16">
            <p className="text-gray-400 text-lg">No results found</p>
            <p className="text-gray-500 text-sm mt-2">Try a different search term or filter</p>
          </div>
        )}

        {/* Pagination */}
        {!searchQuery && total > LIMIT && (
          <div className="flex justify-center gap-4 mt-8">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-4 py-2 bg-[#333] text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#444] transition-colors"
            >
              Previous
            </button>
            <span className="px-4 py-2 text-gray-400">
              Page {page + 1} of {Math.ceil(total / LIMIT)}
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={(page + 1) * LIMIT >= total}
              className="px-4 py-2 bg-[#333] text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#444] transition-colors"
            >
              Next
            </button>
          </div>
        )}
      </main>

      {/* Content Detail Modal */}
      {selectedItem && (
        <ContentDetailModal
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          onPlay={() => handlePlay(selectedItem)}
        />
      )}
    </div>
  );
}
