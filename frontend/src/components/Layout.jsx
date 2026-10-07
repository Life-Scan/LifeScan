import { LayoutDashboard, LogOut, Route, Users } from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import estilos from './Layout.module.css'
import { Avatar } from './ui'

const ROTULOS_TIPO = { medico: 'Médico(a)', paciente: 'Paciente' }

export default function Layout() {
  const { usuario, ehMedico, ehParceiro, sair } = useAuth()
  const navegar = useNavigate()

  function aoSair() {
    sair()
    navegar('/login', { replace: true })
  }

  const classeLink = ({ isActive }) => (isActive ? `${estilos.link} ${estilos.ativo}` : estilos.link)

  return (
    <div className={estilos.pagina}>
      <aside className={estilos.menu}>
        <NavLink to="/painel" className={estilos.marca}>
          <img src="/favicon.svg" alt="" width="30" height="30" />
          LifeScan
        </NavLink>

        <nav className={estilos.navegacao} aria-label="Principal">
          <NavLink to="/painel" className={classeLink}>
            <LayoutDashboard size={18} aria-hidden="true" />
            Painel
          </NavLink>
          {ehMedico && (
            <NavLink to="/usuarios" className={classeLink}>
              <Users size={18} aria-hidden="true" />
              Pacientes e parceiros
            </NavLink>
          )}
          <NavLink to="/jornadas" className={classeLink}>
            <Route size={18} aria-hidden="true" />
            {ehMedico ? 'Jornadas' : ehParceiro ? 'Pacientes' : 'Minha jornada'}
          </NavLink>
        </nav>

        <div className={estilos.usuario}>
          <Avatar nome={usuario.nome} tipo={usuario.tipo_usuario} />
          <span className={estilos.nomeUsuario}>
            <span className={estilos.nome}>{usuario.nome}</span>
            {/* Parceiros são identificados pela profissão (ex.: Nutricionista) */}
            <small>{ROTULOS_TIPO[usuario.tipo_usuario] || usuario.profissao}</small>
          </span>
          <button type="button" className={estilos.sair} onClick={aoSair} title="Sair" aria-label="Sair">
            <LogOut size={17} aria-hidden="true" />
          </button>
        </div>
      </aside>

      <main className={estilos.conteudo}>
        <div className={estilos.miolo}>
          <Outlet />
        </div>
      </main>
    </div>
  )
}
