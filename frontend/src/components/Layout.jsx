import { Handshake, IdCard, LayoutDashboard, LogOut, Route, Users } from 'lucide-react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'
import { Avatar } from './ui'

const ROTULOS_TIPO = { medico: 'Médico(a)', paciente: 'Paciente', colaborador: 'Colaborador(a)' }

/*
 * Menu lateral escuro (fundo da apresentação do login), fixo em telas largas; até 900px vira barra no
 * topo, também escura, com a navegação rolando na horizontal. O conteúdo continua claro.
 */
const LINK =
  'relative flex items-center gap-[0.65rem] rounded-raio-pequeno px-[0.7rem] py-[0.55rem] text-[0.93rem] font-semibold ' +
  'no-underline transition-[background,color] duration-150 ease-[ease] ate-900:px-[0.65rem] ate-900:py-[0.45rem] ate-900:whitespace-nowrap'
const LINK_INATIVO = `${LINK} text-menu-texto hover:bg-menu-hover hover:text-menu-texto-forte`
// O ativo não muda no hover. Barra de 3px à esquerda; na barra do topo (links lado a lado), embaixo.
const LINK_ATIVO =
  `${LINK} bg-menu-ativo text-menu-texto-forte ` +
  'before:absolute before:top-[0.45rem] before:bottom-[0.45rem] before:left-0 before:w-[3px] before:rounded-full ' +
  "before:bg-menu-destaque before:content-[''] " +
  'ate-900:before:top-auto ate-900:before:right-[0.65rem] ate-900:before:bottom-0 ate-900:before:left-[0.65rem] ' +
  'ate-900:before:h-[3px] ate-900:before:w-auto'

export default function Layout() {
  const { usuario, ehMedico, ehParceiro, ehColaborador, sair } = useAuth()
  const navegar = useNavigate()
  const { pathname } = useLocation()

  function aoSair() {
    sair()
    navegar('/login', { replace: true })
  }

  const classeLink = ({ isActive }) => (isActive ? LINK_ATIVO : LINK_INATIVO)

  return (
    <div className="grid min-h-screen grid-cols-[var(--largura-menu)_minmax(0,1fr)] ate-900:block">
      {/* O foco do teclado usa o verde-claro do menu: o contorno primário some no fundo escuro. */}
      <aside className="sticky top-0 flex h-screen flex-col gap-6 border-r border-menu-borda/60 bg-menu [background-image:var(--gradiente-menu)] px-[0.9rem] pt-5 pb-4 text-menu-texto [&_:focus-visible]:outline-menu-destaque ate-900:z-10 ate-900:h-auto ate-900:flex-row ate-900:flex-wrap ate-900:items-center ate-900:gap-x-3 ate-900:gap-y-2 ate-900:border-r-0 ate-900:border-b ate-900:py-[0.6rem]">
        <NavLink
          to="/painel"
          className="flex flex-col items-center gap-[0.4rem] px-2 text-[1.15rem] font-bold tracking-[-0.01em] text-menu-texto-forte no-underline ate-900:flex-row ate-900:gap-[0.6rem] ate-900:p-0 ate-900:text-[1.1rem]"
        >
          {/*
           * Só o traço do batimento (o do favicon, sem a caixa), com brilho e um pulso que percorre a
           * linha (index.css, .logo-batimento). Nome embaixo; na barra do topo (até 900px) lado a lado.
           */}
          <svg
            viewBox="3 7 26 18"
            width="52"
            height="36"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="logo-batimento overflow-visible ate-900:h-6 ate-900:w-[35px]"
            aria-hidden="true"
          >
            <path d="M5 17h5l3-7 5 13 3-6h6" pathLength="100" stroke="var(--cor-menu-destaque)" strokeOpacity="0.45" strokeWidth="2.4" />
            <path d="M5 17h5l3-7 5 13 3-6h6" pathLength="100" stroke="#fff" strokeWidth="2.6" className="logo-batimento-pulso" />
          </svg>
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

        {/* O contorno claro destaca o avatar (o do médico é verde) sobre o fundo escuro */}
        <div className="flex items-center gap-[0.6rem] border-t border-menu-borda px-2 pt-3 [&>span:first-child]:ring-2 [&>span:first-child]:ring-menu-borda ate-900:ml-auto ate-900:border-t-0 ate-900:p-0">
          <Avatar nome={usuario.nome} tipo={usuario.tipo_usuario} />
          <span className="grid min-w-0 flex-1 leading-[1.25] ate-900:hidden">
            <span className="truncate text-[0.9rem] font-semibold text-menu-texto-forte">{usuario.nome}</span>
            {/* Parceiros são identificados pela profissão (ex.: Nutricionista) */}
            <small className="truncate text-[0.78rem] text-menu-texto">{ROTULOS_TIPO[usuario.tipo_usuario] || usuario.profissao}</small>
          </span>
          <button
            type="button"
            className="inline-grid size-[2.1rem] shrink-0 cursor-pointer place-items-center rounded-raio-pequeno border border-transparent bg-transparent text-menu-texto transition-[background,color] duration-150 ease-[ease] hover:bg-perigo-clara hover:text-perigo"
            onClick={aoSair}
            title="Sair"
            aria-label="Sair"
          >
            <LogOut size={17} aria-hidden="true" />
          </button>
        </div>
      </aside>

      <main className="@container min-w-0 px-8 pt-8 pb-12 ate-900:px-[0.9rem] ate-900:pt-[1.1rem] ate-900:pb-10">
        {/* key: a cada troca de rota a página remonta e entra com fade + 4px (só o caminho; ?aba= não conta) */}
        <div key={pathname} className="mx-auto max-w-[1040px] animate-entrar">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
