// WSOPTV API Types

// User & Auth
export type UserStatus = 'pending' | 'active' | 'suspended';
export type UserRole = 'user' | 'admin' | 'moderator';

export interface User {
  id: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

// Content
export interface Content {
  id: string;
  title: string;
  description?: string;
  duration_seconds: number;
  file_size_bytes: number;
  codec?: string;
  resolution?: string;
  thumbnail_url?: string;
  created_at: string;
  // Netflix-style UI fields
  category?: string;
  year?: number;
  quality?: string;
  tags?: string[];
  backdrop_url?: string;
}

export interface Catalog {
  items: Content[];
  total: number;
  page: number;
  size: number;
}

export interface WatchProgress {
  content_id: string;
  user_id: string;
  position_seconds: number;
  total_seconds: number;
  percentage: number;
}

// Search
export interface SearchQuery {
  keyword: string;
  page?: number;
  size?: number;
  filters?: Record<string, string>;
}

export interface SearchItem {
  id: string;
  title: string;
  description?: string;
  duration_seconds: number;
  thumbnail_url?: string;
  score: number;
}

export interface SearchResult {
  items: SearchItem[];
  total: number;
  query: string;
  took_ms: number;
}

// Stream
export interface StreamInfo {
  url: string;
  content_type: string;
  content_id: string;
}

export interface StreamResult {
  allowed: boolean;
  error?: string;
}

export interface BandwidthInfo {
  limit_mbps: number;
  current_mbps: number;
}

// Admin
export interface DashboardData {
  users: {
    total: number;
    active: number;
    pending: number;
    suspended: number;
  };
  content: {
    total: number;
    total_size_gb: number;
  };
  streams: {
    active: number;
    total_bandwidth_mbps: number;
  };
  cache: {
    l1_usage_percent: number;
    l2_usage_percent: number;
    l4_usage_percent: number;
  };
}

export interface ActiveStream {
  user_id: string;
  user_email: string;
  content_id: string;
  content_title: string;
  started_at: string;
  bandwidth_mbps: number;
}

// API Response wrapper
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

// ==================== Catalog Types (wsoptv_v2_db) ====================

export type ProjectCode = 'WSOP' | 'HCL' | 'GGMILLIONS' | 'MPP' | 'PAD' | 'GOG' | 'OTHER';

export interface Project {
  id: string;
  code: ProjectCode;
  name: string;
  description?: string;
  nas_base_path?: string;
  filename_pattern?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Season {
  id: string;
  project_id: string;
  year: number;
  name: string;
  location?: string;
  sub_category?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Event {
  id: string;
  season_id: string;
  event_number?: number;
  name: string;
  name_short?: string;
  event_type?: string;
  game_type?: string;
  buy_in?: number;
  gtd_amount?: number;
  venue?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Episode {
  id: string;
  event_id: string;
  episode_number?: number;
  day_number?: number;
  part_number?: number;
  title?: string;
  episode_type?: string;
  table_type?: string;
  duration_seconds?: number;
  created_at: string;
  updated_at: string;
}

export interface VideoFile {
  id: string;
  episode_id?: string;
  file_name: string;
  file_path: string;
  file_size_bytes: number;
  version_type: string;
  duration_seconds?: number;
  resolution?: string;
  codec?: string;
  created_at: string;
  updated_at: string;
}

// NAS Inventory Types
export interface NASFolder {
  id: string;
  folder_path: string;
  folder_name: string;
  parent_path?: string;
  depth: number;
  file_count: number;
  folder_count: number;
  total_size_bytes: number;
  is_empty: boolean;
  is_hidden_folder: boolean;
  created_at: string;
  updated_at: string;
}

export interface NASFile {
  id: string;
  file_path: string;
  file_name: string;
  file_size_bytes: number;
  file_extension?: string;
  file_mtime?: string;
  file_category: string;
  is_hidden_file: boolean;
  video_file_id?: string;
  folder_id?: string;
  created_at: string;
  updated_at: string;
}

// Catalog Tree
export interface CatalogTree {
  projects: Array<Project & {
    seasons: Array<Season & {
      events: Array<Event & {
        episodes: Episode[];
      }>;
    }>;
  }>;
}

// ==================== Block F: Flat Catalog Types ====================

/**
 * CatalogItem - Block F 단일 계층 카탈로그 아이템
 * 4단계 계층(Project → Season → Event → Episode)을 대체하는 단일 모델
 */
export interface CatalogItem {
  id: string;
  nas_file_id: string | null;
  display_title: string;        // Title Generator 생성
  short_title: string;          // 축약 제목
  thumbnail_url: string | null;
  project_code: ProjectCode;    // WSOP, HCL, GGMILLIONS, GOG, MPP, PAD, OTHER
  year: number | null;
  category_tags: string[];      // [NLHE, Main Event, Final Table, ...]
  file_path: string;
  file_name: string;
  file_size_bytes: number;
  file_size_formatted: string;  // "2.1 GB"
  file_extension: string;
  duration_seconds: number | null;
  quality: string | null;
  is_visible: boolean;
  confidence: number;           // 0.0 ~ 1.0 (Title Generator 신뢰도)
  created_at: string;
  updated_at: string;
}

/**
 * CatalogListResponse - 카탈로그 목록 응답
 */
export interface CatalogListResponse {
  items: CatalogItem[];
  total: number;
  skip: number;
  limit: number;
}

/**
 * CatalogStats - 카탈로그 통계
 */
export interface CatalogStats {
  total_items: number;
  visible_items: number;
  projects: Array<{ code: string; count: number }>;
  years: number[];
}

/**
 * CatalogSearchParams - 카탈로그 검색/필터 파라미터
 */
export interface CatalogSearchParams {
  project_code?: ProjectCode;
  year?: number;
  visible_only?: boolean;
  skip?: number;
  limit?: number;
}
