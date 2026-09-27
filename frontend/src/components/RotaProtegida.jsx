import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { Carregando } from './ui'

/**
 * Libera as rotas filhas apenas para usuários logados e, se `papeis` for
 * informado, apenas para esses papéis (RNF03).
 */
export default function RotaProtegida({ papeis }) {
  const { usuario, carregando } = useAuth()
  const local = useLocation()

  if (carregando) return <Carregando texto="Verificando sua sessão…" />
  if (!usuario) return <Navigate to="/login" replace state={{ de: local.pathname + local.search }} />
  if (papeis && !papeis.includes(usuario.papel)) return <Navigate to="/painel" replace />
  return <Outlet />
}
