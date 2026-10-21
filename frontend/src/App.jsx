import { Navigate, Route, Routes } from 'react-router-dom'

import Layout from './components/Layout'
import RotaProtegida from './components/RotaProtegida'
import { useAuth } from './context/AuthContext'
import DefinirSenha from './pages/DefinirSenha'
import EsqueciSenha from './pages/EsqueciSenha'
import Acompanhamento from './pages/acompanhamento/Acompanhamento'
import Acompanhamentos from './pages/Acompanhamentos'
import Login from './pages/Login'
import NaoEncontrada from './pages/NaoEncontrada'
import NovoAcompanhamento from './pages/NovoAcompanhamento'
import Painel from './pages/Painel'
import Usuarios from './pages/Usuarios'

/** Login e "esqueci minha senha": quem já está logado vai direto para o painel. */
function SomenteVisitante({ children }) {
  const { usuario, carregando } = useAuth()
  if (carregando) return null
  return usuario ? <Navigate to="/painel" replace /> : children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<SomenteVisitante><Login /></SomenteVisitante>} />
      <Route path="/esqueci-senha" element={<SomenteVisitante><EsqueciSenha /></SomenteVisitante>} />

      <Route element={<RotaProtegida />}>
        {/* Fora do Layout: no primeiro acesso a pessoa só pode definir a senha */}
        <Route path="/definir-senha" element={<DefinirSenha />} />

        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/painel" replace />} />
          <Route path="/painel" element={<Painel />} />

          <Route path="/acompanhamentos" element={<Acompanhamentos />} />
          <Route path="/acompanhamentos/:id" element={<Acompanhamento />} />

          <Route element={<RotaProtegida tipos={['medico']} />}>
            <Route path="/usuarios" element={<Usuarios />} />
            <Route path="/acompanhamentos/novo" element={<NovoAcompanhamento />} />
          </Route>

          <Route path="*" element={<NaoEncontrada />} />
        </Route>
      </Route>
    </Routes>
  )
}
