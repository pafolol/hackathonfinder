import { NavLink, Outlet } from 'react-router-dom'
import { useLogout } from '../api/hooks'
import type { User } from '../api/types'
import Brand from './Brand'

const LINKS = [
  { to: '/', label: 'Oportunidades', end: true },
  { to: '/proyectos', label: 'Proyectos' },
  { to: '/contexto', label: 'Contexto' },
  { to: '/busquedas', label: 'Búsquedas' },
]

export default function Layout({ user }: { user: User }) {
  const logout = useLogout()
  const links = user.role === 'admin' ? [...LINKS, { to: '/usuarios', label: 'Usuarios' }] : LINKS

  return (
    <div className="shell">
      <aside className="sidebar">
        <Brand />
        <nav className="nav">
          {links.map((link, index) => (
            <NavLink key={link.to} to={link.to} end={'end' in link}>
              <span className="nav-index">{String(index + 1).padStart(2, '0')}</span>
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="sidebar-account">
            <div className="sidebar-user">{user.name}</div>
            <div className="sidebar-email">{user.email}</div>
            <button className="link-button" onClick={() => logout.mutate()}>
              Cerrar sesión
            </button>
          </div>
        </div>
      </aside>
      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}
