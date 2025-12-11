// Auth API

import apiClient from './client';
import type { LoginRequest, LoginResponse, RegisterRequest, User } from '@/types/api';

export const authApi = {
  /**
   * 로그인
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/auth/login', credentials);
    apiClient.setToken(response.token);
    return response;
  },

  /**
   * 회원가입
   */
  async register(data: RegisterRequest): Promise<User> {
    return apiClient.post<User>('/auth/register', data);
  },

  /**
   * 로그아웃
   */
  async logout(): Promise<void> {
    await apiClient.post('/auth/logout');
    apiClient.setToken(null);
  },

  /**
   * 현재 사용자 정보
   */
  async me(): Promise<User> {
    return apiClient.get<User>('/auth/me');
  },

  /**
   * 사용자 승인 (관리자)
   */
  async approveUser(userId: string): Promise<User> {
    return apiClient.post<User>(`/auth/users/${userId}/approve`);
  },
};

export default authApi;
