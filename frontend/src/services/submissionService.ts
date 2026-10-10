import axios from 'axios';
import api from './api';
import type { Submission, SubmissionCreateRequest, SubmissionListResponse } from '../types';

export function extractErrorMessage(error: unknown, fallback = 'Something went wrong. Please try again.'): string {
  if (axios.isAxiosError(error)) {
    const data: unknown = error.response?.data;
    if (typeof data === 'object' && data !== null && 'detail' in data) {
      const detail = (data as { detail: unknown }).detail;
      if (typeof detail === 'string') return detail;
      if (Array.isArray(detail)) {
        const msgs = detail
          .map((d: unknown) => (typeof d === 'object' && d !== null && 'msg' in d ? String((d as { msg: unknown }).msg) : ''))
          .filter((m) => m.length > 0);
        if (msgs.length > 0) return msgs.join('; ');
      }
    }
    if (error.response?.status === 429) return 'Daily submission limit reached. Come back tomorrow!';
    if (!error.response) return 'Cannot reach the server. Check your connection.';
  }
  return fallback;
}

export async function createSubmission(payload: SubmissionCreateRequest): Promise<Submission> {
  const { data } = await api.post<Submission>('/submissions', payload);
  return data;
}

export async function listSubmissions(skip = 0, limit = 20): Promise<SubmissionListResponse> {
  const { data } = await api.get<SubmissionListResponse>('/submissions', { params: { skip, limit } });
  return data;
}

export async function getSubmission(id: number): Promise<Submission> {
  const { data } = await api.get<Submission>(`/submissions/${id}`);
  return data;
}

export async function deleteSubmission(id: number): Promise<void> {
  await api.delete(`/submissions/${id}`);
}

export async function retrySubmission(id: number): Promise<Submission> {
  const { data } = await api.post<Submission>(`/submissions/${id}/retry`);
  return data;
}
