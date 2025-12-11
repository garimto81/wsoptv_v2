'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

const CATALOG_API_URL = process.env.NEXT_PUBLIC_CATALOG_API_URL || 'http://localhost:8004';

interface HandClip {
  id: string;
  title?: string;
  timecode?: string;
  timecode_end?: string;
  duration_seconds?: number;
  hand_grade?: string;
  pot_size?: number;
  winner_hand?: string;
  notes?: string;
  episode_id?: string;
  video_file_id?: string;
}

interface Player {
  id: string;
  name: string;
  country?: string;
}

interface Tag {
  id: string;
  name: string;
  category?: string;
}

interface LinkageStats {
  total_clips: number;
  with_video_file: number;
  with_episode: number;
  video_only: number;
  orphan_clips: number;
  linkage_rate: number;
}

function formatDuration(seconds?: number): string {
  if (!seconds) return '-';
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

function formatPot(amount?: number): string {
  if (!amount) return '-';
  return `$${amount.toLocaleString()}`;
}

function GradeLabel({ grade }: { grade?: string }) {
  const colors: Record<string, string> = {
    'S': 'bg-purple-600',
    'A': 'bg-red-600',
    'B': 'bg-orange-500',
    'C': 'bg-yellow-500',
    'D': 'bg-green-500',
  };
  if (!grade) return null;
  return (
    <span className={`${colors[grade] || 'bg-gray-500'} text-white text-xs px-2 py-1 rounded`}>
      {grade}
    </span>
  );
}

function ClipCard({ clip }: { clip: HandClip }) {
  return (
    <div className="bg-[#181818] rounded-lg p-4 hover:bg-[#252525] transition-colors">
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-white font-medium text-sm line-clamp-2 flex-1">
          {clip.title || `Hand @ ${clip.timecode || 'Unknown'}`}
        </h3>
        <GradeLabel grade={clip.hand_grade} />
      </div>

      <div className="space-y-1 text-xs text-gray-400">
        {clip.timecode && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Time:</span>
            <span className="text-[#46D369]">{clip.timecode}</span>
            {clip.timecode_end && (
              <>
                <span className="text-gray-500">→</span>
                <span className="text-[#46D369]">{clip.timecode_end}</span>
              </>
            )}
          </div>
        )}

        {clip.pot_size && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Pot:</span>
            <span className="text-yellow-400">{formatPot(clip.pot_size)}</span>
          </div>
        )}

        {clip.winner_hand && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Winner:</span>
            <span className="text-white">{clip.winner_hand}</span>
          </div>
        )}

        {clip.duration_seconds && (
          <div className="flex items-center gap-2">
            <span className="text-gray-500">Duration:</span>
            <span>{formatDuration(clip.duration_seconds)}</span>
          </div>
        )}
      </div>

      {clip.notes && (
        <p className="mt-2 text-xs text-gray-500 line-clamp-2">
          {clip.notes}
        </p>
      )}
    </div>
  );
}

function StatCard({ label, value, subtext }: { label: string; value: number | string; subtext?: string }) {
  return (
    <div className="bg-[#181818] rounded-lg p-4">
      <p className="text-gray-400 text-sm mb-1">{label}</p>
      <p className="text-white text-2xl font-bold">{value}</p>
      {subtext && <p className="text-gray-500 text-xs mt-1">{subtext}</p>}
    </div>
  );
}

export default function HandAnalysisPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [clips, setClips] = useState<HandClip[]>([]);
  const [players, setPlayers] = useState<Player[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [stats, setStats] = useState<LinkageStats | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedGrade, setSelectedGrade] = useState<string>('all');
  const [user, setUser] = useState<{ username: string; role: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const grades = ['all', 'S', 'A', 'B', 'C', 'D'];

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

    const loadData = async () => {
      try {
        // Load hand clips
        const clipsRes = await fetch(`${CATALOG_API_URL}/api/v1/hand-clips?limit=100`);
        if (clipsRes.ok) {
          const clipsData = await clipsRes.json();
          setClips(clipsData);
        }

        // Load linkage stats
        const statsRes = await fetch(`${CATALOG_API_URL}/api/v1/hand-clips/linkage-stats`);
        if (statsRes.ok) {
          const statsData = await statsRes.json();
          setStats(statsData);
        }

        // Load players
        const playersRes = await fetch(`${CATALOG_API_URL}/api/v1/players?limit=50`);
        if (playersRes.ok) {
          const playersData = await playersRes.json();
          setPlayers(playersData);
        }

        // Load tags
        const tagsRes = await fetch(`${CATALOG_API_URL}/api/v1/tags?limit=50`);
        if (tagsRes.ok) {
          const tagsData = await tagsRes.json();
          setTags(tagsData);
        }

        setIsLoading(false);
      } catch (err) {
        console.error('Failed to load hand analysis data:', err);
        setError('Failed to load data. Backend might not be running.');
        setIsLoading(false);
      }
    };

    loadData();
  }, [router]);

  const filteredClips = clips.filter((clip) => {
    const matchesSearch =
      searchQuery === '' ||
      (clip.title?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false) ||
      (clip.winner_hand?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false);
    const matchesGrade =
      selectedGrade === 'all' || clip.hand_grade === selectedGrade;
    return matchesSearch && matchesGrade;
  });

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    router.push('/login');
  };

  return (
    <div className="min-h-screen bg-[#141414]">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-b from-black/80 to-transparent">
        <div className="flex items-center justify-between px-8 py-4">
          <div className="flex items-center gap-8">
            <Link href="/catalog" className="text-[#E50914] font-bold text-2xl tracking-tight">
              WSOPTV
            </Link>
            <nav className="hidden md:flex items-center gap-6">
              <Link href="/catalog" className="text-gray-300 hover:text-white text-sm transition-colors">
                Catalog
              </Link>
              <span className="text-white font-semibold text-sm">
                Hand Analysis
              </span>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <input
              type="text"
              placeholder="Search hands..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-black/50 border border-gray-600 text-white text-sm rounded px-4 py-2 w-48 focus:w-64 focus:outline-none focus:border-white transition-all placeholder-gray-400"
            />
            <div className="w-8 h-8 bg-[#E50914] rounded flex items-center justify-center text-white font-semibold text-sm">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-24 px-8 pb-16">
        {/* Page Title */}
        <div className="mb-6">
          <h1 className="text-white text-2xl font-bold">Hand Analysis</h1>
          <p className="text-gray-400 text-sm mt-1">
            Browse and analyze poker hands from VODs
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 p-4 bg-red-900/50 border border-red-500 rounded text-red-200">
            {error}
          </div>
        )}

        {/* Stats Grid */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-8">
            <StatCard label="Total Clips" value={stats.total_clips} />
            <StatCard label="With Video" value={stats.with_video_file} subtext={`${stats.linkage_rate}% linked`} />
            <StatCard label="With Episode" value={stats.with_episode} />
            <StatCard label="Video Only" value={stats.video_only} />
            <StatCard label="Orphan Clips" value={stats.orphan_clips} />
            <StatCard label="Linkage Rate" value={`${stats.linkage_rate}%`} />
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 mb-6">
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-sm">Grade:</span>
            {grades.map((grade) => (
              <button
                key={grade}
                onClick={() => setSelectedGrade(grade)}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  selectedGrade === grade
                    ? 'bg-[#E50914] text-white'
                    : 'bg-[#333] text-gray-300 hover:bg-[#444]'
                }`}
              >
                {grade === 'all' ? 'All' : grade}
              </button>
            ))}
          </div>
        </div>

        {/* Clips Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="bg-[#181818] rounded-lg p-4 animate-pulse">
                <div className="h-4 bg-[#2F2F2F] rounded mb-3" />
                <div className="h-3 bg-[#2F2F2F] rounded w-2/3 mb-2" />
                <div className="h-3 bg-[#2F2F2F] rounded w-1/2" />
              </div>
            ))}
          </div>
        ) : filteredClips.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {filteredClips.map((clip) => (
              <ClipCard key={clip.id} clip={clip} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16">
            <p className="text-gray-400 text-lg">No hand clips found</p>
            <p className="text-gray-500 text-sm mt-2">
              {clips.length === 0
                ? 'Import hand clips from Google Sheets to get started'
                : 'Try adjusting your search or filters'}
            </p>
          </div>
        )}

        {/* Players Section */}
        {players.length > 0 && (
          <div className="mt-12">
            <h2 className="text-white text-xl font-bold mb-4">Players</h2>
            <div className="flex flex-wrap gap-2">
              {players.map((player) => (
                <span
                  key={player.id}
                  className="bg-[#333] text-white px-3 py-1 rounded-full text-sm hover:bg-[#444] cursor-pointer transition-colors"
                >
                  {player.name}
                  {player.country && <span className="text-gray-400 ml-1">({player.country})</span>}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Tags Section */}
        {tags.length > 0 && (
          <div className="mt-8">
            <h2 className="text-white text-xl font-bold mb-4">Tags</h2>
            <div className="flex flex-wrap gap-2">
              {tags.map((tag) => (
                <span
                  key={tag.id}
                  className="bg-[#E50914]/20 text-[#E50914] border border-[#E50914]/30 px-3 py-1 rounded-full text-sm hover:bg-[#E50914]/30 cursor-pointer transition-colors"
                >
                  {tag.name}
                </span>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
