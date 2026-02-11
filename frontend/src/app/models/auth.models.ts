export type UserRole = 'admin' | 'supervisor' | 'agent';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  is_active: boolean;
}
