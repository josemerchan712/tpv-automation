import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { UserInfo } from '../api/auth'

interface AuthState {
  token: string | null
  user: UserInfo | null
  setAuth: (token: string, user: UserInfo) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      setAuth: (token, user) => set({ token, user }),
      logout: () => set({ token: null, user: null }),
    }),
    { name: 'auth-storage' },
  ),
)
