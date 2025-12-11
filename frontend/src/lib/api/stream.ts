// Stream API

import apiClient from './client';
import type { StreamInfo, StreamResult, BandwidthInfo } from '@/types/api';

export const streamApi = {
  /**
   * 스트리밍 URL 획득
   */
  async getStreamUrl(contentId: string): Promise<StreamInfo> {
    return apiClient.get<StreamInfo>(`/stream/${contentId}`);
  },

  /**
   * 스트리밍 시작
   */
  async startStream(contentId: string): Promise<StreamResult> {
    return apiClient.post<StreamResult>(`/stream/${contentId}/start`);
  },

  /**
   * 스트리밍 종료
   */
  async endStream(contentId: string): Promise<{ status: string }> {
    return apiClient.post<{ status: string }>(`/stream/${contentId}/end`);
  },

  /**
   * 대역폭 조회
   */
  async getBandwidth(contentId: string): Promise<BandwidthInfo> {
    return apiClient.get<BandwidthInfo>(`/stream/${contentId}/bandwidth`);
  },

  /**
   * 비디오 스트리밍 URL (HTTP Range 지원)
   */
  getVideoUrl(contentId: string): string {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';
    return `${baseUrl}/stream/${contentId}/video`;
  },
};

export default streamApi;
