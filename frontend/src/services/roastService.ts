import api from './api';
import type { Roast } from '../types';

export interface RoastList {
  items: Roast[];
  total: number;
}

export async function getRoast(submissionId: number): Promise<Roast> {
  const { data } = await api.get<Roast>(`/roasts/${submissionId}`);
  return data;
}

export async function listRoasts(skip = 0, limit = 20): Promise<RoastList> {
  const { data } = await api.get<RoastList>('/roasts', { params: { skip, limit } });
  return data;
}
