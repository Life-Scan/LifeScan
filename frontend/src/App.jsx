import { Navigate, Route, Routes } from 'react-router-dom'

import Layout from './components/Layout'
import RotaProtegida from './components/RotaProtegida'
import { useAuth } from './context/AuthContext'
import Cadastro from './pages/Cadastro'
import Jornada from './pages/jornada/Jornada'
import Jornadas from './pages/Jornadas'
import Login from './pages/Login'
import NaoEncontrada from './pages/NaoEncontrada'
import NovaJornada from './pages/NovaJornada'
import Pacientes from './pages/Pacientes'
import Painel from './pages/Painel'

/** Login e cadastro: quem já está logado vai direto para o painel. */
function SomenteVisitante({ children }) {
  const { usuario, carregando } = useAuth()
  if (carregando) return null
  return usuario ? <Navigate to="/painel" replace /> : children
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<SomenteVisitante><Login /></SomenteVisitante>} />
      <Route path="/cadastro" element={<SomenteVisitante><Cadastro /></SomenteVisitante>} />

      <Route element={<RotaProtegida />}>
        <Route element={<Layout />}>
          <Route path="/" element={<Navigate to="/painel" replace />} />
          <Route path="/painel" element={<Painel />} />
          <Route path="/jornadas" element={<Jornadas />} />
          <Route path="/jornadas/:id" element={<Jornada />} />

          <Route element={<RotaProtegida papeis={['medico']} />}>
            <Route path="/pacientes" element={<Pacientes />} />
            <Route path="/jornadas/nova" element={<NovaJornada />} />
          </Route>

          <Route path="*" element={<NaoEncontrada />} />
        </Route>
      </Route>
    </Routes>
  )
}
