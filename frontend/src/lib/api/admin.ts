// Admin API

import apiClient from './client';
import type { DashboardData, ActiveStream, User } from '@/types/api';

export const adminApi = {
  /**
   * 대시보드 데이터 조회
   */
  async getDashboard(): Promise<DashboardData> {
    return apiClient.get<DashboardData>('/admin/dashboard');
  },

  /**
   * 사용자 목록 조회
   */
  async getUsers(params?: {
    status?: string;
    role?: string;
    page?: number;
    size?: number;
  }): Promise<{ users: User[]; total: number }> {
    const queryParams: Record<string, string> = {};
    if (params?.status) queryParams.status = params.status;
    if (params?.role) queryParams.role = params.role;
    if (params?.page) queryParams.page = String(params.page);
    if (params?.size) queryParams.size = String(params.size);

    return apiClient.get('/admin/users', queryParams);
  },

  /**
   * 사용자 승인
   */
  async approveUser(userId: string): Promise<User> {
    return apiClient.post<User>(`/admin/users/${userId}/approve`);
  },

  /**
   * 사용자 정지
   */
  async suspendUser(userId: string): Promise<User> {
    return apiClient.post<User>(`/admin/users/${userId}/suspend`);
  },

  /**
   * 시스템 상태 조회
   */
  async getSystemStatus(): Promise<{
    status: string;
    blocks: Record<string, { healthy: boolean; version: string }>;
  }> {
    return apiClient.get('/admin/system');
  },

  /**
   * 활성 스트림 목록
   */
  async getActiveStreams(): Promise<{ streams: ActiveStream[]; total: number }> {
    return apiClient.get('/admin/streams');
  },
};

export default adminApi;
