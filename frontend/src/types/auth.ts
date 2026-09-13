export type Role = 'ADMIN' | 'AP_CLERK' | 'APPROVER' | 'FINANCE' | 'CFO' | 'VENDOR';

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  role: Role;
  department?: string;
  phone_number?: string;
  is_staff?: boolean;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: User;
}

export interface ApiError {
  code: string;
  message: string;
  details?: any;
}
