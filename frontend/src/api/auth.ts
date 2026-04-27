import client from "./client";
import type { LoginResponse } from "../types/auth";
import type { UserRole } from "../types/auth";

export interface UserResponse {
  uid: string;
  username: string;
  role: UserRole;
  is_active: boolean;
}

export interface UpdateUser {
  username?: string;
  password?: string;
  role?: UserRole;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const form = new URLSearchParams({ username, password });
  const { data } = await client.post<LoginResponse>("/auth/login", form);
  return data;
}

export async function register(username: string, password: string, role: UserRole): Promise<UserResponse> {
  const { data } = await client.post<UserResponse>("/auth/register", { username, password, role });
  return data;
}

export async function listUsers(): Promise<UserResponse[]> {
  const { data } = await client.get<UserResponse[]>("/users/");
  return data;
}

export async function updateUser(uid: string, updates: UpdateUser): Promise<UserResponse> {
  const { data } = await client.put<UserResponse>(`/users/${uid}`, updates);
  return data;
}
