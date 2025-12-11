// Catalog API - wsoptv_v2_db 백엔드 연동

import apiClient from './client';
import type { Project, Season, Event, Episode, NASFolder, NASFile } from '@/types/api';

// Catalog DB API base (다른 포트 사용 가능)
const CATALOG_API_URL = process.env.NEXT_PUBLIC_CATALOG_API_URL || 'http://localhost:8000';

class CatalogApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || 'Request failed');
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // Projects
  async getProjects(): Promise<Project[]> {
    return this.request<Project[]>('/api/v1/projects');
  }

  async getProject(projectId: string): Promise<Project> {
    return this.request<Project>(`/api/v1/projects/${projectId}`);
  }

  async getProjectByCode(code: string): Promise<Project> {
    return this.request<Project>(`/api/v1/projects/code/${code}`);
  }

  // Seasons
  async getSeasons(projectId?: string): Promise<Season[]> {
    const url = projectId
      ? `/api/v1/seasons?project_id=${projectId}`
      : '/api/v1/seasons';
    return this.request<Season[]>(url);
  }

  async getSeason(seasonId: string): Promise<Season> {
    return this.request<Season>(`/api/v1/seasons/${seasonId}`);
  }

  // Events
  async getEvents(seasonId?: string): Promise<Event[]> {
    const url = seasonId
      ? `/api/v1/events?season_id=${seasonId}`
      : '/api/v1/events';
    return this.request<Event[]>(url);
  }

  async getEvent(eventId: string): Promise<Event> {
    return this.request<Event>(`/api/v1/events/${eventId}`);
  }

  // Episodes
  async getEpisodes(eventId?: string): Promise<Episode[]> {
    const url = eventId
      ? `/api/v1/episodes?event_id=${eventId}`
      : '/api/v1/episodes';
    return this.request<Episode[]>(url);
  }

  async getEpisode(episodeId: string): Promise<Episode> {
    return this.request<Episode>(`/api/v1/episodes/${episodeId}`);
  }

  // NAS Folders
  async getNASFolders(depth?: number): Promise<NASFolder[]> {
    const url = depth !== undefined
      ? `/api/v1/nas/folders?depth=${depth}`
      : '/api/v1/nas/folders';
    return this.request<NASFolder[]>(url);
  }

  async getNASRootFolders(): Promise<NASFolder[]> {
    return this.request<NASFolder[]>('/api/v1/nas/folders/root');
  }

  async getNASFolderChildren(folderId: string): Promise<NASFolder[]> {
    return this.request<NASFolder[]>(`/api/v1/nas/folders/${folderId}/children`);
  }

  async getNASFolderFiles(folderId: string): Promise<NASFile[]> {
    return this.request<NASFile[]>(`/api/v1/nas/folders/${folderId}/files`);
  }

  // NAS Files
  async getNASFiles(category?: string): Promise<NASFile[]> {
    const url = category
      ? `/api/v1/nas/files?category=${category}`
      : '/api/v1/nas/files';
    return this.request<NASFile[]>(url);
  }

  async getNASVideoFiles(): Promise<NASFile[]> {
    return this.request<NASFile[]>('/api/v1/nas/files/videos');
  }

  async searchNASFiles(query: string): Promise<NASFile[]> {
    return this.request<NASFile[]>(`/api/v1/nas/files/search?q=${encodeURIComponent(query)}`);
  }

  // NAS Scan/Sync
  async testNASConnection(): Promise<{
    status: string;
    server: string;
    share: string;
    base_path: string;
  }> {
    return this.request('/api/v1/nas/connection-test');
  }

  async scanNAS(path: string = '', recursive: boolean = false): Promise<{
    path: string;
    items: Array<{
      path: string;
      name: string;
      is_directory: boolean;
      size_bytes: number;
      is_hidden: boolean;
    }>;
    total_folders: number;
    total_files: number;
    total_size_bytes: number;
  }> {
    return this.request('/api/v1/nas/scan', {
      method: 'POST',
      body: JSON.stringify({ path, recursive, max_depth: 5 }),
    });
  }

  async syncNAS(projectCode?: string): Promise<{
    folders_created: number;
    files_created: number;
    files_updated: number;
    duration_seconds: number;
  }> {
    return this.request('/api/v1/nas/sync', {
      method: 'POST',
      body: JSON.stringify({ project_code: projectCode, max_depth: 5 }),
    });
  }

  // Stats
  async getNASFileStats(): Promise<{
    total_files: number;
    total_size_bytes: number;
    by_category: Record<string, number>;
    by_extension: Record<string, number>;
    linked_count: number;
    unlinked_count: number;
  }> {
    return this.request('/api/v1/nas/files/stats');
  }
}

export const catalogApi = new CatalogApiClient(CATALOG_API_URL);
export default catalogApi;
