import { Handshake, IdCard, LayoutDashboard, LogOut, Route, Users } from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { Avatar } from './ui'

const ROTULOS_TIPO = { medico: 'Médico(a)', paciente: 'Paciente', colaborador: 'Colaborador(a)' }

/* Menu lateral fixo em telas largas; até 900px vira barra no topo com a navegação rolando na horizontal. */
const LINK =
  'flex items-center gap-[0.65rem] rounded-raio-pequeno px-[0.7rem] py-[0.55rem] text-[0.93rem] font-semibold ' +
  'no-underline transition-[background,color] duration-150 ease-[ease] ate-900:px-[0.65rem] ate-900:py-[0.45rem] ate-900:whitespace-nowrap'
const LINK_INATIVO = `${LINK} text-texto-suave hover:bg-superficie-suave hover:text-texto`
// O ativo não muda no hover
const LINK_ATIVO = `${LINK} bg-primaria-clara text-primaria-escura`

export default function Layout() {
  const { usuario, ehMedico, ehParceiro, ehColaborador, sair } = useAuth()
  const navegar = useNavigate()

  function aoSair() {
    sair()
    navegar('/login', { replace: true })
  }

  const classeLink = ({ isActive }) => (isActive ? LINK_ATIVO : LINK_INATIVO)

  return (
    <div className="grid min-h-screen grid-cols-[var(--largura-menu)_minmax(0,1fr)] ate-900:block">
      <aside className="sticky top-0 flex h-screen flex-col gap-6 border-r border-borda bg-superficie px-[0.9rem] pt-5 pb-4 ate-900:z-10 ate-900:h-auto ate-900:flex-row ate-900:flex-wrap ate-900:items-center ate-900:gap-x-3 ate-900:gap-y-2 ate-900:border-r-0 ate-900:border-b ate-900:py-[0.6rem]">
        <NavLink
          to="/painel"
          className="inline-flex items-center gap-[0.6rem] px-2 text-[1.2rem] font-bold tracking-[-0.01em] text-texto no-underline ate-900:p-0 ate-900:text-[1.1rem]"
        >
          <img src="/favicon.svg" alt="" width="30" height="30" />
          LifeScan
        </NavLink>

        <nav
          className="grid flex-1 content-start gap-[0.2rem] ate-900:order-3 ate-900:flex ate-900:basis-full ate-900:gap-1 ate-900:overflow-x-auto"
          aria-label="Principal"
        >
          <NavLink to="/painel" className={classeLink}>
            <LayoutDashboard size={18} aria-hidden="true" />
            Painel
          </NavLink>
          {ehMedico && (
            <>
              <NavLink to="/pacientes" className={classeLink}>
                <Users size={18} aria-hidden="true" />
                Pacientes
              </NavLink>
              <NavLink to="/parceiros" className={classeLink}>
                <Handshake size={18} aria-hidden="true" />
                Parceiros
              </NavLink>
              <NavLink to="/colaboradores" className={classeLink}>
                <IdCard size={18} aria-hidden="true" />
                Colaboradores
              </NavLink>
            </>
          )}
          {!ehColaborador && (
            <NavLink to="/acompanhamentos" className={classeLink}>
              <Route size={18} aria-hidden="true" />
              {ehMedico ? 'Acompanhamentos' : ehParceiro ? 'Pacientes' : 'Meu acompanhamento'}
            </NavLink>
          )}
        </nav>

        <div className="flex items-center gap-[0.6rem] border-t border-borda px-2 pt-3 ate-900:ml-auto ate-900:border-t-0 ate-900:p-0">
          <Avatar nome={usuario.nome} tipo={usuario.tipo_usuario} />
          <span className="grid min-w-0 flex-1 leading-[1.25] ate-900:hidden">
            <span className="truncate text-[0.9rem] font-semibold">{usuario.nome}</span>
            {/* Parceiros são identificados pela profissão (ex.: Nutricionista) */}
            <small className="truncate text-[0.78rem] text-texto-suave">{ROTULOS_TIPO[usuario.tipo_usuario] || usuario.profissao}</small>
          </span>
          <button
            type="button"
            className="inline-grid size-[2.1rem] shrink-0 cursor-pointer place-items-center rounded-raio-pequeno border border-transparent bg-transparent text-texto-suave hover:bg-perigo-clara hover:text-perigo"
            onClick={aoSair}
            title="Sair"
            aria-label="Sair"
          >
            <LogOut size={17} aria-hidden="true" />
          </button>
        </div>
      </aside>

      <main className="min-w-0 px-8 pt-8 pb-12 ate-900:px-[0.9rem] ate-900:pt-[1.1rem] ate-900:pb-10">
        <div className="mx-auto max-w-[1040px]">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
