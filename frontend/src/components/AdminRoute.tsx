import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function AdminRoute() {
  const role = useAuthStore(s => s.user?.role)
  if (role !== 'admin') return <Navigate to="/catalogo" replace />
  return <Outlet />
}
