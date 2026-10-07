import { Navigate, Route, Routes } from 'react-router-dom'

import Layout from './components/Layout'
import RotaProtegida from './components/RotaProtegida'
import { useAuth } from './context/AuthContext'
import Contas from './pages/Contas'
import EsqueciSenha from './pages/EsqueciSenha'
import Jornada from './pages/jornada/Jornada'
import Jornadas from './pages/Jornadas'
import Login from './pages/Login'
import NaoEncontrada from './pages/NaoEncontrada'
import NovaJornada from './pages/NovaJornada'
import Painel from './pages/Painel'
import TrocarSenha from './pages/TrocarSenha'

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
        {/* Fora do Layout: no primeiro acesso a pessoa só pode trocar a senha */}
        <Route path="/trocar-senha" element={<TrocarSenha />} />

        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/painel" replace />} />
          <Route path="/painel" element={<Painel />} />

          <Route path="/jornadas" element={<Jornadas />} />
          <Route path="/jornadas/:id" element={<Jornada />} />

          <Route element={<RotaProtegida tipos={['medico']} />}>
            <Route path="/pacientes" element={<Contas tipo="paciente" />} />
            <Route path="/parceiros" element={<Contas tipo="parceiro" />} />
            <Route path="/jornadas/nova" element={<NovaJornada />} />
          </Route>

          <Route path="*" element={<NaoEncontrada />} />
        </Route>
      </Route>
    </Routes>
  )
}
