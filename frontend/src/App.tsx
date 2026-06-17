import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import AdminRoute from './components/AdminRoute'
import LoginPage from './pages/LoginPage'
import CatalogPage from './pages/CatalogPage'
import SalesPage from './pages/SalesPage'
import DashboardPage from './pages/DashboardPage'
import EmployeesPage from './pages/EmployeesPage'
import ShiftsPage from './pages/ShiftsPage'

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Navigate to="/catalogo" replace />} />
              <Route path="/catalogo" element={<CatalogPage />} />
              <Route path="/ventas" element={<SalesPage />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route element={<AdminRoute />}>
                <Route path="/empleados" element={<EmployeesPage />} />
                <Route path="/turnos" element={<ShiftsPage />} />
              </Route>
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
