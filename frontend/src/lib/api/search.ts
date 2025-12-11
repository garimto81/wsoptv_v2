// Search API

import apiClient from './client';
import type { SearchResult } from '@/types/api';

export const searchApi = {
  /**
   * 검색 수행
   */
  async search(
    keyword: string,
    options?: { page?: number; size?: number }
  ): Promise<SearchResult> {
    return apiClient.get<SearchResult>('/search/', {
      keyword,
      page: String(options?.page || 1),
      size: String(options?.size || 20),
    });
  },

  /**
   * 자동완성 (빠른 검색)
   */
  async suggest(keyword: string, limit = 5): Promise<string[]> {
    const result = await apiClient.get<SearchResult>('/search/', {
      keyword,
      size: String(limit),
    });
    return result.items.map((item) => item.title);
  },
};

export default searchApi;
