import { useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { Alerta } from '../components/ui'
import { useAuth } from '../context/AuthContext'

/*
 * Visual próprio de "porta de entrada" (ver DESIGN.md, Exceções conhecidas): painel verde-escuro à
 * esquerda, formulário à direita. Abaixo de 900px os espaços diminuem; abaixo de 680px vira uma
 * coluna só, sem as etapas e sem o símbolo.
 */
const SOBRETITULO = 'text-[10px] font-bold tracking-[2px]'
const ROTULO = 'mb-2 text-[13px] font-semibold text-[#304c44]'
const CAMPO =
  'min-h-[52px] py-[13px] pl-[15px] border-[#d8e3de] rounded-[10px] bg-[#fcfefd] text-[14px] placeholder:text-[#7d8d86]'
const NUMERO_ETAPA = 'mb-[5px] block text-[10px] tracking-[1px] text-[#aad5c9]'

export default function Login() {
  const { entrar } = useAuth()
  const navegar = useNavigate()
  const local = useLocation()
  const [parametros] = useSearchParams()

  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)
  const [senhaVisivel, setSenhaVisivel] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      const usuario = await entrar(email, senha)
      // Quem entrou com a senha provisória precisa definir a própria senha antes de tudo
      navegar(usuario.deve_trocar_senha ? '/definir-senha' : local.state?.de || '/painel', { replace: true })
    } catch (erroLogin) {
      setErro(mensagemDeErro(erroLogin))
      setEnviando(false)
    }
  }

  return (
    <main className="grid min-h-svh place-items-center bg-[#edf3f1] p-10 ate-900:p-6 ate-680:block ate-680:bg-white ate-680:p-0">
      <div className="grid w-full max-w-[1120px] min-h-[710px] grid-cols-[1fr_1fr] overflow-hidden rounded-[28px] border border-[#dce7e2] shadow-[0_24px_80px_#183e3020] ate-680:min-h-svh ate-680:grid-cols-[1fr] ate-680:rounded-none ate-680:border-0 ate-680:shadow-none">
        <section
          className="relative flex flex-col p-12 text-white [background:radial-gradient(ellipse_at_100%_100%,#218c7b_0,transparent_65%),#0b514d] ate-900:p-9 ate-680:px-7 ate-680:pt-[26px] ate-680:pb-[30px]"
          aria-labelledby="titulo-apresentacao"
        >
          <div className="flex items-center gap-3 text-[27px] font-[650] tracking-[-1px] ate-680:text-[24px]">
            <img src="/favicon.svg" alt="" width="44" height="44" className="rounded-[12px] border border-[#ffffff30]" />
            <span>
              LifeScan
              <span className="mt-[2px] block text-[9px] tracking-[2px] text-[#b4ded2]">CUIDADO QUE CONECTA</span>
            </span>
          </div>
          <div className="mt-[78px] ate-680:mt-[30px]">
            <p className={`${SOBRETITULO} text-[#a9ddcc] ate-680:hidden`}>CADA ETAPA IMPORTA</p>
            <h2
              id="titulo-apresentacao"
              className="mt-[18px] text-[length:clamp(36px,3.6vw,49px)] leading-[1.14] font-[550] tracking-[-1.8px] ate-680:text-[34px] ate-680:[&_br]:hidden"
            >
              Mais perto.{' '}<br />Em cada passo{' '}<br />do seu cuidado.
            </h2>
            <p className="mt-[22px] max-w-[310px] text-[15px] leading-[1.75] text-[#c4e0da] ate-680:mt-[14px] ate-680:max-w-full ate-680:text-[14px]">
              Seu tratamento acompanhado de perto, entre uma consulta e outra.
            </p>
          </div>
          <div className="mt-9 ate-680:hidden">
            <svg className="block h-[85px] w-full overflow-visible" viewBox="0 0 400 100" fill="none" aria-hidden="true">
              <path
                className="stroke-[#a7e3cc] stroke-2 [stroke-linecap:round] [stroke-linejoin:round]"
                d="M0 50H105L135 12L185 88L215 50H400"
              />
            </svg>
            <ol className="m-0 flex list-none justify-between border-t border-[#ffffff25] px-0 pt-[18px] pb-0 text-[12px] text-[#e2f2ec]">
              <li><span className={NUMERO_ETAPA}>01</span>Consulta</li>
              <li><span className={NUMERO_ETAPA}>02</span>Exame</li>
              <li><span className={NUMERO_ETAPA}>03</span>Retorno</li>
            </ol>
          </div>
          <p className="mt-auto pt-[38px] text-[11px] text-[#bdddd3] ate-680:hidden">
            Médico e paciente. Um acompanhamento compartilhado.
          </p>
        </section>

        <section
          className="grid place-items-center bg-white px-[52px] py-[55px] ate-900:px-[30px] ate-900:py-10 ate-680:px-7 ate-680:py-[34px]"
          aria-labelledby="titulo-login"
        >
          <div className="w-full max-w-[360px]">
            <span
              className="mb-[26px] inline-flex rounded-[18px] border border-[#dcece5] bg-[#f0f7f4] p-2 ate-680:hidden"
              aria-hidden="true"
            >
              <img src="/favicon.svg" alt="" width="48" height="48" />
            </span>
            <p className={`${SOBRETITULO} text-primaria`}>BEM-VINDO AO LIFESCAN</p>
            <h1
              id="titulo-login"
              className="mt-[14px] text-[34px] leading-[1.2] font-[650] tracking-[-1.2px] text-[#173c36] ate-680:text-[30px]"
            >
              Vamos continuar<br />seu acompanhamento?
            </h1>
            <p className="mt-[14px] text-[14px] leading-[1.65] text-[#687b75]">Entre na sua conta para acompanhar seu cuidado.</p>
            <form className="mt-8 grid gap-[22px]" onSubmit={aoEnviar}>
              {parametros.get('sessao') === 'expirada' && !erro && (
                <Alerta tipo="info">Sua sessão expirou. Entre novamente.</Alerta>
              )}
              <Alerta tipo="erro">{erro}</Alerta>
              <div>
                <label htmlFor="email" className={ROTULO}>Email</label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="voce@exemplo.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoFocus
                  className={`${CAMPO} pr-[15px]`}
                />
              </div>
              <div>
                <label htmlFor="senha" className={ROTULO}>Senha</label>
                <div className="relative">
                  <input
                    id="senha"
                    type={senhaVisivel ? 'text' : 'password'}
                    autoComplete="current-password"
                    placeholder="Digite sua senha"
                    value={senha}
                    onChange={(e) => setSenha(e.target.value)}
                    required
                    className={`${CAMPO} pr-[82px]`}
                  />
                  <button
                    type="button"
                    className="absolute top-1/2 right-3 -translate-y-1/2 cursor-pointer border-0 bg-transparent px-[3px] py-[7px] text-[12px] font-semibold text-primaria"
                    onClick={() => setSenhaVisivel((visivel) => !visivel)}
                    aria-label={senhaVisivel ? 'Ocultar senha' : 'Mostrar senha'}
                    aria-pressed={senhaVisivel}
                  >
                    {senhaVisivel ? 'Ocultar' : 'Mostrar'}
                  </button>
                </div>
              </div>
              <button
                type="submit"
                className="mt-[3px] flex min-h-[52px] cursor-pointer items-center justify-center gap-[18px] rounded-[10px] border-0 bg-primaria text-[14px] font-[650] text-white transition-[background] duration-150 ease-[ease] hover:not-disabled:bg-primaria-escura disabled:cursor-wait disabled:opacity-60"
                disabled={enviando}
              >
                {enviando ? 'Entrando…' : 'Entrar na minha conta'}
                <span aria-hidden="true" className="text-[22px] font-normal">→</span>
              </button>
            </form>
            <p className="mt-5 text-center text-[14px]">
              <Link to="/esqueci-senha">Esqueci minha senha</Link>
            </p>
            <p className="mt-3 text-center text-[12px] leading-[1.6] text-texto-suave">
              O acesso é criado pelo seu médico. Se você recebeu um email com uma senha provisória, use-a aqui.
            </p>
            <p className="mt-[42px] border-t border-[#e8efeb] pt-[22px] text-center text-[11px] text-[#687b75] ate-680:mt-[30px]">
              Seu cuidado tem continuidade aqui.
            </p>
          </div>
        </section>
      </div>
    </main>
  )
}
