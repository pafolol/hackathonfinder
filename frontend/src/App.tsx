import { Navigate, Route, Routes } from 'react-router-dom'
import { useMe } from './api/hooks'
import Layout from './components/Layout'
import Busquedas from './pages/Busquedas'
import Contexto from './pages/Contexto'
import Login from './pages/Login'
import OportunidadDetalle from './pages/OportunidadDetalle'
import Oportunidades from './pages/Oportunidades'
import Proyectos from './pages/Proyectos'
import Usuarios from './pages/Usuarios'

export default function App() {
  const me = useMe()

  if (me.isPending) return <div className="splash">Cargando…</div>
  if (me.isError) return <div className="splash">No se pudo conectar con el servidor. Revisa que la API esté en marcha.</div>
  if (!me.data) return <Login />

  return (
    <Routes>
      <Route element={<Layout user={me.data} />}>
        <Route index element={<Oportunidades />} />
        <Route path="oportunidades/:id" element={<OportunidadDetalle />} />
        <Route path="proyectos" element={<Proyectos />} />
        <Route path="contexto" element={<Contexto />} />
        <Route path="busquedas" element={<Busquedas />} />
        {me.data.role === 'admin' && <Route path="usuarios" element={<Usuarios />} />}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
