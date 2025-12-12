'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

const CATALOG_API_URL = process.env.NEXT_PUBLIC_CATALOG_API_URL || 'http://localhost:8002';

interface NASStats {
  total_files: number;
  total_size_bytes: number;
  by_category: Record<string, number>;
  linked_count: number;
  unlinked_count: number;
}

interface SyncLog {
  id: string;
  sync_type: string;
  status: string;
  started_at: string;
  completed_at?: string;
  files_scanned: number;
  files_created: number;
  files_updated: number;
  files_deleted: number;
  total_size_bytes: number;
  error_message?: string;
}

interface DashboardStats {
  totalFiles: number;
  totalSize: string;
  totalFolders: number;
  linkedFiles: number;
  unlinkedFiles: number;
  handClips: number;
  lastSync?: string;
}

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// User type from localStorage
interface LocalUser {
  id: string;
  username: string;
  password: string;
  role: 'admin' | 'user';
  status: 'pending' | 'active' | 'rejected' | 'suspended';
  created_at: string;
}

function getUsers(): LocalUser[] {
  if (typeof window === 'undefined') return [];
  const users = localStorage.getItem('wsoptv_users');
  return users ? JSON.parse(users) : [];
}

function saveUsers(users: LocalUser[]): void {
  localStorage.setItem('wsoptv_users', JSON.stringify(users));
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    active: 'bg-[#46D369]/20 text-[#46D369]',
    pending: 'bg-yellow-500/20 text-yellow-500',
    suspended: 'bg-[#E50914]/20 text-[#E50914]',
    rejected: 'bg-red-900/20 text-red-400',
    published: 'bg-[#46D369]/20 text-[#46D369]',
    draft: 'bg-gray-500/20 text-gray-400',
  };

  const labels: Record<string, string> = {
    active: 'Active',
    pending: 'Pending',
    suspended: 'Suspended',
    rejected: 'Rejected',
    published: 'Published',
    draft: 'Draft',
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium ${styles[status] || 'bg-gray-500/20 text-gray-400'}`}>
      {labels[status] || status}
    </span>
  );
}

export default function AdminPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<'dashboard' | 'users' | 'nas' | 'sync'>('dashboard');
  const [users, setUsers] = useState<LocalUser[]>([]);
  const [selectedUser, setSelectedUser] = useState<LocalUser | null>(null);
  const [showDialog, setShowDialog] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [syncLogs, setSyncLogs] = useState<SyncLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);

  // Load users from localStorage
  const loadUsers = () => {
    const localUsers = getUsers();
    setUsers(localUsers);
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');

    if (!token) {
      router.push('/login');
      return;
    }

    if (userData) {
      const user = JSON.parse(userData);
      if (user.role !== 'admin') {
        router.push('/catalog');
      }
    }

    // Load users from localStorage
    loadUsers();

    // Load dashboard data
    loadDashboardData();
  }, [router]);

  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      // Fetch NAS stats
      const statsRes = await fetch(`${CATALOG_API_URL}/api/v1/nas/files/stats`);
      let nasStats: NASStats | null = null;
      if (statsRes.ok) {
        nasStats = await statsRes.json();
      }

      // Fetch folder count
      const foldersRes = await fetch(`${CATALOG_API_URL}/api/v1/nas/folders?limit=1`);
      let folderCount = 0;
      if (foldersRes.ok) {
        const foldersData = await foldersRes.json();
        // Get total from pagination or count
        const countRes = await fetch(`${CATALOG_API_URL}/api/v1/nas/folders/count`);
        if (countRes.ok) {
          const countData = await countRes.json();
          folderCount = countData.count || 0;
        }
      }

      // Fetch hand clips count
      const clipsRes = await fetch(`${CATALOG_API_URL}/api/v1/hand-clips/linkage-stats`);
      let handClipsCount = 0;
      if (clipsRes.ok) {
        const clipsData = await clipsRes.json();
        handClipsCount = clipsData.total_clips || 0;
      }

      // Fetch sync logs
      const logsRes = await fetch(`${CATALOG_API_URL}/api/v1/nas/sync/history?limit=10`);
      if (logsRes.ok) {
        const logsData = await logsRes.json();
        setSyncLogs(logsData);
      }

      // Set combined stats
      setStats({
        totalFiles: nasStats?.total_files || 0,
        totalSize: formatSize(nasStats?.total_size_bytes || 0),
        totalFolders: folderCount,
        linkedFiles: nasStats?.linked_count || 0,
        unlinkedFiles: nasStats?.unlinked_count || 0,
        handClips: handClipsCount,
        lastSync: syncLogs[0]?.completed_at,
      });
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSync = async (syncType: 'full' | 'incremental') => {
    setIsSyncing(true);
    setSyncError(null);
    try {
      const res = await fetch(`${CATALOG_API_URL}/api/v1/nas/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_scan: syncType === 'full',
          scan_path: '',
        }),
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || 'Sync failed');
      }

      // Reload data after sync
      await loadDashboardData();
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : 'Sync failed');
    } finally {
      setIsSyncing(false);
    }
  };

  const handleUserStatusChange = () => {
    if (!selectedUser || !newStatus) return;

    // Update user status in localStorage
    const updatedUsers = users.map(u =>
      u.id === selectedUser.id ? { ...u, status: newStatus as LocalUser['status'] } : u
    );
    saveUsers(updatedUsers);
    setUsers(updatedUsers);

    setShowDialog(false);
    setSelectedUser(null);
    setNewStatus('');
  };

  const handleApprove = (user: LocalUser) => {
    const updatedUsers = users.map(u =>
      u.id === user.id ? { ...u, status: 'active' as const } : u
    );
    saveUsers(updatedUsers);
    setUsers(updatedUsers);
  };

  const handleReject = (user: LocalUser) => {
    const updatedUsers = users.map(u =>
      u.id === user.id ? { ...u, status: 'rejected' as const } : u
    );
    saveUsers(updatedUsers);
    setUsers(updatedUsers);
  };

  const openStatusDialog = (user: LocalUser) => {
    setSelectedUser(user);
    setNewStatus(user.status);
    setShowDialog(true);
  };

  const pendingCount = users.filter(u => u.status === 'pending').length;

  return (
    <div className="min-h-screen bg-[#141414]">
      {/* Header */}
      <header className="bg-black/80 border-b border-[#333]">
        <div className="flex items-center justify-between px-8 py-4">
          <div className="flex items-center gap-4">
            <Link href="/catalog" className="text-[#E50914] font-bold text-2xl tracking-tight">
              WSOPTV
            </Link>
            <span className="bg-[#E50914] text-white text-xs px-2 py-1 rounded font-semibold">
              ADMIN
            </span>
          </div>
          <Link
            href="/catalog"
            className="text-gray-300 hover:text-white text-sm transition-colors"
          >
            Back to Catalog
          </Link>
        </div>
      </header>

      <main className="p-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
          {[
            { label: 'Total Files', value: isLoading ? '...' : stats?.totalFiles.toLocaleString() || '0', color: 'text-white' },
            { label: 'Total Size', value: isLoading ? '...' : stats?.totalSize || '0 B', color: 'text-[#46D369]' },
            { label: 'Folders', value: isLoading ? '...' : stats?.totalFolders.toLocaleString() || '0', color: 'text-white' },
            { label: 'Linked', value: isLoading ? '...' : stats?.linkedFiles.toLocaleString() || '0', color: 'text-[#46D369]' },
            { label: 'Unlinked', value: isLoading ? '...' : stats?.unlinkedFiles.toLocaleString() || '0', color: 'text-yellow-500' },
            { label: 'Hand Clips', value: isLoading ? '...' : stats?.handClips.toLocaleString() || '0', color: 'text-white' },
          ].map((stat) => (
            <div key={stat.label} className="bg-[#181818] rounded-lg p-4 border border-[#333]">
              <p className="text-gray-400 text-xs mb-1">{stat.label}</p>
              <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="flex gap-1 bg-[#181818] rounded-lg p-1 inline-flex">
            {[
              { id: 'dashboard', label: 'Dashboard' },
              { id: 'nas', label: 'NAS Files' },
              { id: 'sync', label: 'Sync' },
              { id: 'users', label: 'Users', badge: pendingCount > 0 ? pendingCount : null },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'dashboard' | 'users' | 'nas' | 'sync')}
                className={`px-4 py-2 rounded text-sm font-medium transition-colors flex items-center gap-2 ${
                  activeTab === tab.id
                    ? 'bg-[#E50914] text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                {tab.label}
                {tab.badge && (
                  <span className="bg-[#E50914] text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
                    {tab.badge}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            {/* Pending Users Section */}
            {pendingCount > 0 && (
              <div className="bg-[#181818] rounded-lg border border-yellow-500/30 overflow-hidden">
                <div className="p-4 border-b border-[#333] bg-yellow-500/10">
                  <h2 className="text-yellow-500 font-semibold flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Pending Approval ({pendingCount})
                  </h2>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-[#0D0D0D]">
                      <tr>
                        <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Username</th>
                        <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Registered</th>
                        <th className="text-right text-gray-400 text-xs font-medium px-4 py-3">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.filter(u => u.status === 'pending').map((user) => (
                        <tr key={user.id} className="border-t border-[#333] hover:bg-[#222]">
                          <td className="px-4 py-3 text-white text-sm font-medium">{user.username}</td>
                          <td className="px-4 py-3 text-gray-400 text-sm">{formatDate(user.created_at)}</td>
                          <td className="px-4 py-3 text-right space-x-2">
                            <button
                              onClick={() => handleApprove(user)}
                              className="bg-[#46D369] hover:bg-[#3fc25d] text-white text-xs px-4 py-1.5 rounded transition-colors font-medium"
                            >
                              Approve
                            </button>
                            <button
                              onClick={() => handleReject(user)}
                              className="bg-[#E50914] hover:bg-[#F40612] text-white text-xs px-4 py-1.5 rounded transition-colors font-medium"
                            >
                              Reject
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* All Users Section */}
            <div className="bg-[#181818] rounded-lg border border-[#333] overflow-hidden">
              <div className="p-4 border-b border-[#333]">
                <h2 className="text-white font-semibold">All Users ({users.length})</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-[#0D0D0D]">
                    <tr>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Username</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Role</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Status</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Joined</th>
                      <th className="text-right text-gray-400 text-xs font-medium px-4 py-3">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                          No users found
                        </td>
                      </tr>
                    ) : (
                      users.map((user) => (
                        <tr key={user.id} className="border-t border-[#333] hover:bg-[#222]">
                          <td className="px-4 py-3 text-white text-sm font-medium">{user.username}</td>
                          <td className="px-4 py-3">
                            <span className={`text-xs font-medium ${user.role === 'admin' ? 'text-[#E50914]' : 'text-gray-400'}`}>
                              {user.role === 'admin' ? 'Admin' : 'User'}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <StatusBadge status={user.status} />
                          </td>
                          <td className="px-4 py-3 text-gray-400 text-sm">{formatDate(user.created_at)}</td>
                          <td className="px-4 py-3 text-right space-x-2">
                            {user.status === 'pending' && (
                              <>
                                <button
                                  onClick={() => handleApprove(user)}
                                  className="bg-[#46D369] hover:bg-[#3fc25d] text-white text-xs px-3 py-1.5 rounded transition-colors"
                                >
                                  Approve
                                </button>
                                <button
                                  onClick={() => handleReject(user)}
                                  className="bg-[#E50914]/80 hover:bg-[#E50914] text-white text-xs px-3 py-1.5 rounded transition-colors"
                                >
                                  Reject
                                </button>
                              </>
                            )}
                            {user.role !== 'admin' && user.status !== 'pending' && (
                              <button
                                onClick={() => openStatusDialog(user)}
                                className="bg-[#333] hover:bg-[#444] text-white text-xs px-3 py-1.5 rounded transition-colors"
                              >
                                Change Status
                              </button>
                            )}
                            {user.role === 'admin' && (
                              <span className="text-gray-500 text-xs">Admin</span>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="space-y-6">
            {/* Quick Actions */}
            <div className="bg-[#181818] rounded-lg border border-[#333] p-6">
              <h2 className="text-white font-semibold mb-4">Quick Actions</h2>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => handleSync('incremental')}
                  disabled={isSyncing}
                  className="bg-[#46D369] hover:bg-[#3fc25d] text-white px-4 py-2 rounded font-medium transition-colors disabled:opacity-50"
                >
                  {isSyncing ? 'Syncing...' : 'Incremental Sync'}
                </button>
                <button
                  onClick={() => handleSync('full')}
                  disabled={isSyncing}
                  className="bg-[#E50914] hover:bg-[#F40612] text-white px-4 py-2 rounded font-medium transition-colors disabled:opacity-50"
                >
                  {isSyncing ? 'Syncing...' : 'Full Sync'}
                </button>
                <button
                  onClick={loadDashboardData}
                  className="bg-[#333] hover:bg-[#444] text-white px-4 py-2 rounded font-medium transition-colors"
                >
                  Refresh Stats
                </button>
              </div>
              {syncError && (
                <p className="text-red-500 text-sm mt-3">{syncError}</p>
              )}
            </div>

            {/* Recent Sync History */}
            <div className="bg-[#181818] rounded-lg border border-[#333] overflow-hidden">
              <div className="p-4 border-b border-[#333]">
                <h2 className="text-white font-semibold">Recent Sync History</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-[#0D0D0D]">
                    <tr>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Type</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Status</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Started</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Files</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Size</th>
                    </tr>
                  </thead>
                  <tbody>
                    {syncLogs.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                          No sync history found
                        </td>
                      </tr>
                    ) : (
                      syncLogs.map((log) => (
                        <tr key={log.id} className="border-t border-[#333] hover:bg-[#222]">
                          <td className="px-4 py-3 text-white text-sm">{log.sync_type}</td>
                          <td className="px-4 py-3">
                            <StatusBadge status={log.status === 'completed' ? 'active' : log.status === 'failed' ? 'suspended' : 'pending'} />
                          </td>
                          <td className="px-4 py-3 text-gray-400 text-sm">{formatDate(log.started_at)}</td>
                          <td className="px-4 py-3 text-gray-300 text-sm">
                            {log.files_scanned} scanned / {log.files_created} new
                          </td>
                          <td className="px-4 py-3 text-gray-400 text-sm">{formatSize(log.total_size_bytes)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* NAS Files Tab */}
        {activeTab === 'nas' && (
          <div className="bg-[#181818] rounded-lg border border-[#333] p-6">
            <h2 className="text-white font-semibold mb-4">NAS File Browser</h2>
            <p className="text-gray-400 mb-4">
              Browse NAS files directly from the Catalog page. This tab shows a summary of NAS contents.
            </p>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="bg-[#0D0D0D] rounded-lg p-4">
                <p className="text-gray-400 text-sm">Video Files</p>
                <p className="text-white text-xl font-bold">{stats?.totalFiles.toLocaleString() || 0}</p>
              </div>
              <div className="bg-[#0D0D0D] rounded-lg p-4">
                <p className="text-gray-400 text-sm">Total Size</p>
                <p className="text-white text-xl font-bold">{stats?.totalSize || '0 B'}</p>
              </div>
              <div className="bg-[#0D0D0D] rounded-lg p-4">
                <p className="text-gray-400 text-sm">Folders</p>
                <p className="text-white text-xl font-bold">{stats?.totalFolders.toLocaleString() || 0}</p>
              </div>
            </div>
            <div className="mt-6">
              <Link
                href="/catalog"
                className="inline-block bg-[#E50914] hover:bg-[#F40612] text-white px-4 py-2 rounded font-medium transition-colors"
              >
                Go to Catalog
              </Link>
            </div>
          </div>
        )}

        {/* Sync Tab */}
        {activeTab === 'sync' && (
          <div className="space-y-6">
            {/* Sync Controls */}
            <div className="bg-[#181818] rounded-lg border border-[#333] p-6">
              <h2 className="text-white font-semibold mb-4">NAS Synchronization</h2>
              <p className="text-gray-400 text-sm mb-4">
                Sync NAS files to the catalog database. Incremental sync only updates changed files.
                Full sync rescans everything.
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => handleSync('incremental')}
                  disabled={isSyncing}
                  className="bg-[#46D369] hover:bg-[#3fc25d] text-white px-6 py-3 rounded font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                  </svg>
                  {isSyncing ? 'Syncing...' : 'Incremental Sync'}
                </button>
                <button
                  onClick={() => handleSync('full')}
                  disabled={isSyncing}
                  className="bg-[#E50914] hover:bg-[#F40612] text-white px-6 py-3 rounded font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                  </svg>
                  {isSyncing ? 'Syncing...' : 'Full Sync'}
                </button>
              </div>
              {syncError && (
                <div className="mt-4 p-3 bg-red-900/30 border border-red-500 rounded text-red-300 text-sm">
                  {syncError}
                </div>
              )}
              {isSyncing && (
                <div className="mt-4 p-3 bg-blue-900/30 border border-blue-500 rounded text-blue-300 text-sm flex items-center gap-2">
                  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Synchronization in progress... This may take several minutes.
                </div>
              )}
            </div>

            {/* Full Sync History */}
            <div className="bg-[#181818] rounded-lg border border-[#333] overflow-hidden">
              <div className="p-4 border-b border-[#333]">
                <h2 className="text-white font-semibold">Sync History</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-[#0D0D0D]">
                    <tr>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Type</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Status</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Started</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Completed</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Scanned</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Created</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Updated</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Deleted</th>
                      <th className="text-left text-gray-400 text-xs font-medium px-4 py-3">Size</th>
                    </tr>
                  </thead>
                  <tbody>
                    {syncLogs.length === 0 ? (
                      <tr>
                        <td colSpan={9} className="px-4 py-8 text-center text-gray-500">
                          No sync history found. Run a sync to see results here.
                        </td>
                      </tr>
                    ) : (
                      syncLogs.map((log) => (
                        <tr key={log.id} className="border-t border-[#333] hover:bg-[#222]">
                          <td className="px-4 py-3 text-white text-sm">{log.sync_type}</td>
                          <td className="px-4 py-3">
                            <StatusBadge status={log.status === 'completed' ? 'active' : log.status === 'failed' ? 'suspended' : 'pending'} />
                          </td>
                          <td className="px-4 py-3 text-gray-400 text-sm">{formatDate(log.started_at)}</td>
                          <td className="px-4 py-3 text-gray-400 text-sm">
                            {log.completed_at ? formatDate(log.completed_at) : '-'}
                          </td>
                          <td className="px-4 py-3 text-gray-300 text-sm">{log.files_scanned.toLocaleString()}</td>
                          <td className="px-4 py-3 text-[#46D369] text-sm">{log.files_created.toLocaleString()}</td>
                          <td className="px-4 py-3 text-yellow-500 text-sm">{log.files_updated.toLocaleString()}</td>
                          <td className="px-4 py-3 text-[#E50914] text-sm">{log.files_deleted.toLocaleString()}</td>
                          <td className="px-4 py-3 text-gray-400 text-sm">{formatSize(log.total_size_bytes)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Status Change Dialog */}
      {showDialog && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="bg-[#181818] rounded-lg border border-[#333] p-6 w-full max-w-md">
            <h3 className="text-white text-lg font-semibold mb-2">Change User Status</h3>
            <p className="text-gray-400 text-sm mb-4">Update status for {selectedUser?.username}</p>
            <select
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value)}
              className="w-full bg-[#333] text-white rounded px-4 py-3 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-[#E50914] border border-transparent"
            >
              <option value="active">Active</option>
              <option value="pending">Pending</option>
              <option value="rejected">Rejected</option>
              <option value="suspended">Suspended</option>
            </select>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowDialog(false)}
                className="bg-[#333] hover:bg-[#444] text-white px-4 py-2 rounded font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleUserStatusChange}
                className="bg-[#E50914] hover:bg-[#F40612] text-white px-4 py-2 rounded font-medium transition-colors"
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
