export type UserRole = "admin" | "editor" | "viewer";

export interface User {
  uid: string;
  username: string;
  role: UserRole;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}
