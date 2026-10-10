import axios from 'axios';
import api from './api';
import type {
  AdminListResponse,
  AdminStatsData,
  AdminSubmission,
  AdminUser,
  AdminUserUpdate,
  SubmissionStatus,
} from '../types';

export interface UserListParams {
  skip: number;
  limit: number;
  search?: string;
}

export interface SubmissionListParams {
  skip: number;
  limit: number;
  status?: SubmissionStatus;
  user_id?: number;
}

export async function getAdminStats(): Promise<AdminStatsData> {
  const { data } = await api.get<AdminStatsData>('/admin/stats');
  return data;
}

export async function listAdminUsers(params: UserListParams): Promise<AdminListResponse<AdminUser>> {
  const { data } = await api.get<AdminListResponse<AdminUser>>('/admin/users', {
    params: { ...params, search: params.search || undefined },
  });
  return data;
}

export async function updateAdminUser(id: number, update: AdminUserUpdate): Promise<AdminUser> {
  const { data } = await api.put<AdminUser>(`/admin/users/${id}`, update);
  return data;
}

export async function listAdminSubmissions(
  params: SubmissionListParams,
): Promise<AdminListResponse<AdminSubmission>> {
  const { data } = await api.get<AdminListResponse<AdminSubmission>>('/admin/submissions', { params });
  return data;
}

interface ErrorBody {
  detail?: unknown;
}

export function getErrorMessage(error: unknown, fallback = 'Something went wrong'): string {
  if (axios.isAxiosError<ErrorBody>(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string') return detail;
  }
  return fallback;
}
