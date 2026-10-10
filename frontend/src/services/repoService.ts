import api from './api';
import type { GitHubRepo } from '../types';

export async function fetchMyRepos(): Promise<GitHubRepo[]> {
  const { data } = await api.get<GitHubRepo[]>('/repos');
  return data;
}
