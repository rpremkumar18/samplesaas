export type SubmissionStatus = 'pending' | 'fetching' | 'analyzing' | 'completed' | 'failed';

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
  is_admin: boolean;
  oauth_provider: string | null;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface TokenRefreshRequest {
  refresh_token: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

export interface UpdateProfileRequest {
  full_name: string;
}

export interface Submission {
  id: number;
  user_id: number;
  repo_url: string;
  repo_owner: string;
  repo_name: string;
  assignment_title: string | null;
  status: SubmissionStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export type TipCategory = 'structure' | 'naming' | 'bugs' | 'security' | 'readability' | 'best_practices';

export interface ImprovementTip {
  id: number;
  category: TipCategory;
  title: string;
  description: string;
  file_path: string | null;
}

export interface Roast {
  id: number;
  submission_id: number;
  repo_url: string;
  assignment_title: string | null;
  roast_text: string;
  score: number;
  summary: string | null;
  tips: ImprovementTip[];
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface SubmissionCreateRequest {
  repo_url: string;
  assignment_title?: string;
}

export interface SubmissionListResponse {
  items: Submission[];
  total: number;
}

export interface AdminUser extends User {
  is_verified: boolean;
  oauth_provider: string | null;
}

export interface AdminUserUpdate {
  is_active?: boolean;
  is_admin?: boolean;
}

export interface AdminStatsData {
  total_users: number;
  active_users: number;
  total_submissions: number;
  completed_submissions: number;
  failed_submissions: number;
  average_score: number | null;
}

export interface AdminSubmission {
  id: number;
  user_id: number;
  repo_url: string;
  repo_owner: string | null;
  repo_name: string | null;
  assignment_title: string | null;
  status: SubmissionStatus;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  user_email: string;
  score: number | null;
}

export interface AdminListResponse<T> {
  items: T[];
  total: number;
}
