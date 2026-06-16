import { useAuthStore } from '../store/authStore'

const BASE = '/api'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = useAuthStore.getState().token
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(`${BASE}${path}`, { ...options, headers })

  if (res.status === 401) {
    useAuthStore.getState().logout()
    window.location.href = '/login'
    throw new Error('Unauthorized')
  }

  if (res.status === 204) return null as T

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    const raw = body?.detail
    const message =
      typeof raw === 'string' && raw.length > 0
        ? raw
        : Array.isArray(raw)
          ? (raw as { msg?: string }[]).map((e) => e.msg ?? String(e)).join('; ')
          : `Error ${res.status}`
    throw new Error(message)
  }

  return res.json()
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  delete: (path: string) => request<void>(path, { method: 'DELETE' }),
}
