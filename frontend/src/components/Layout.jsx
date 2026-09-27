import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import estilos from './Layout.module.css'

export default function Layout() {
  const { usuario, ehMedico, sair } = useAuth()
  const navegar = useNavigate()

  function aoSair() {
    sair()
    navegar('/login', { replace: true })
  }

  const classeLink = ({ isActive }) => (isActive ? `${estilos.link} ${estilos.ativo}` : estilos.link)

  return (
    <div className={estilos.pagina}>
      <header className={estilos.topo}>
        <div className={estilos.topoConteudo}>
          <NavLink to="/painel" className={estilos.marca}>
            <img src="/favicon.svg" alt="" width="28" height="28" />
            LifeScan
          </NavLink>

          <nav className={estilos.navegacao} aria-label="Principal">
            <NavLink to="/painel" className={classeLink}>
              Painel
            </NavLink>
            {ehMedico && (
              <NavLink to="/pacientes" className={classeLink}>
                Pacientes
              </NavLink>
            )}
            <NavLink to="/jornadas" className={classeLink}>
              {ehMedico ? 'Jornadas' : 'Minha jornada'}
            </NavLink>
          </nav>

          <div className={estilos.usuario}>
            <span className={estilos.nomeUsuario}>
              {usuario.nome}
              <small>{ehMedico ? 'Médico(a)' : 'Paciente'}</small>
            </span>
            <button type="button" className={estilos.sair} onClick={aoSair}>
              Sair
            </button>
          </div>
        </div>
      </header>

      <main className={estilos.conteudo}>
        <Outlet />
      </main>
    </div>
  )
}
