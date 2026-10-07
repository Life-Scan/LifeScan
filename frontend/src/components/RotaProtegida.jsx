import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { Carregando } from './ui'

/**
 * Libera as rotas filhas apenas para usuários logados e, se `tipos` for
 * informado, apenas para esses tipos de usuário.
 *
 * Quem entrou com a senha provisória é levado à troca de senha antes de qualquer
 * outra tela (o backend também bloqueia as demais rotas nesse estado).
 */
export default function RotaProtegida({ tipos }) {
  const { usuario, carregando } = useAuth()
  const local = useLocation()

  if (carregando) return <Carregando texto="Verificando sua sessão…" />
  if (!usuario) return <Navigate to="/login" replace state={{ de: local.pathname + local.search }} />
  if (usuario.deve_trocar_senha && local.pathname !== '/trocar-senha') {
    return <Navigate to="/trocar-senha" replace />
  }
  if (tipos && !tipos.includes(usuario.tipo_usuario)) return <Navigate to="/painel" replace />
  return <Outlet />
}
