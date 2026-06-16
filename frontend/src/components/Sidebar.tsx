import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const initials = user?.username.slice(0, 2).toUpperCase() ?? '??'

  return (
    <aside className="w-56 bg-white border-r border-gray-200 flex flex-col shrink-0">
      <div className="p-4 border-b border-gray-200">
        <span className="font-bold text-lg text-indigo-600">TPV</span>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-indigo-50 text-indigo-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`
          }
        >
          Dashboard
        </NavLink>

        <NavLink
          to="/catalogo"
          className={({ isActive }) =>
            `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-indigo-50 text-indigo-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`
          }
        >
          Catálogo
        </NavLink>

        <NavLink
          to="/ventas"
          className={({ isActive }) =>
            `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-indigo-50 text-indigo-700'
                : 'text-gray-600 hover:bg-gray-100'
            }`
          }
        >
          Ventas
        </NavLink>
      </nav>

      <div className="p-3 border-t border-gray-200">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-8 h-8 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-xs font-bold shrink-0">
            {initials}
          </div>
          <span className="text-sm text-gray-700 truncate">{user?.username}</span>
        </div>
        <button
          onClick={handleLogout}
          className="text-sm text-gray-500 hover:text-red-500 transition-colors"
        >
          Cerrar sesión
        </button>
      </div>
    </aside>
  )
}
