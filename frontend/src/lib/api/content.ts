// Content API

import apiClient from './client';
import type { Content, Catalog, WatchProgress } from '@/types/api';

export const contentApi = {
  /**
   * 콘텐츠 상세 조회
   */
  async getContent(contentId: string): Promise<Content> {
    return apiClient.get<Content>(`/content/${contentId}`);
  },

  /**
   * 카탈로그 조회 (페이지네이션)
   */
  async getCatalog(page = 1, size = 20): Promise<Catalog> {
    return apiClient.get<Catalog>('/content/', {
      page: String(page),
      size: String(size),
    });
  },

  /**
   * 시청 진행률 업데이트
   */
  async updateProgress(
    contentId: string,
    userId: string,
    positionSeconds: number,
    totalSeconds: number
  ): Promise<void> {
    const params = new URLSearchParams({
      user_id: userId,
      position_seconds: String(positionSeconds),
      total_seconds: String(totalSeconds),
    });
    await apiClient.post(`/content/${contentId}/progress?${params}`, null);
  },

  /**
   * 시청 진행률 조회
   */
  async getProgress(contentId: string, userId: string): Promise<WatchProgress> {
    return apiClient.get<WatchProgress>(`/content/${contentId}/progress`, {
      user_id: userId,
    });
  },
};

export default contentApi;
