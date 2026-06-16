import { apiClient } from './client'

export interface UserInfo {
  id: number
  username: string
  role: 'admin' | 'cashier'
}

interface LoginResponse {
  access_token: string
  token_type: string
}

export async function getMe(token: string): Promise<UserInfo> {
  const res = await fetch('/api/auth/me', {
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  })
  if (!res.ok) throw new Error('Failed to get user')
  return res.json()
}

export async function login(
  username: string,
  password: string,
): Promise<{ token: string; user: UserInfo }> {
  const { access_token } = await apiClient.post<LoginResponse>('/auth/login', {
    username,
    password,
  })
  const user = await getMe(access_token)
  return { token: access_token, user }
}
