import { useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { Alerta } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import estilos from './Login.module.css'

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
      await entrar(email, senha)
      navegar(local.state?.de || '/painel', { replace: true })
    } catch (erroLogin) {
      setErro(mensagemDeErro(erroLogin))
      setEnviando(false)
    }
  }

  return (
    <main className={estilos.fundo}>
      <div className={estilos.caixa}>
        <section className={estilos.apresentacao} aria-labelledby="titulo-apresentacao">
          <div className={estilos.marca}>
            <img src="/favicon.svg" alt="" width="44" height="44" />
            <span>LifeScan<span className={estilos.descricaoMarca}>CUIDADO QUE CONECTA</span></span>
          </div>
          <div className={estilos.mensagem}>
            <p className={estilos.sobretitulo}>CADA ETAPA IMPORTA</p>
            <h2 id="titulo-apresentacao">Mais perto.{' '}<br />Em cada passo{' '}<br />do seu cuidado.</h2>
            <p>Seu tratamento acompanhado de perto, entre uma consulta e outra.</p>
          </div>
          <div className={estilos.jornada}>
            <svg className={estilos.batimento} viewBox="0 0 400 100" fill="none" aria-hidden="true">
              <path d="M0 50H105L135 12L185 88L215 50H400" />
            </svg>
            <ol className={estilos.etapas}>
              <li><span>01</span>Consulta</li>
              <li><span>02</span>Exame</li>
              <li><span>03</span>Retorno</li>
            </ol>
          </div>
          <p className={estilos.nota}>Médico e paciente. Uma jornada compartilhada.</p>
        </section>

        <section className={estilos.acesso} aria-labelledby="titulo-login">
          <div className={estilos.formularioCaixa}>
            <span className={estilos.simbolo} aria-hidden="true"><img src="/favicon.svg" alt="" width="48" height="48" /></span>
            <p className={estilos.sobretitulo}>BEM-VINDO AO LIFESCAN</p>
            <h1 id="titulo-login" className={estilos.titulo}>Vamos continuar<br />sua jornada?</h1>
            <p className={estilos.subtitulo}>Entre na sua conta para acompanhar seu cuidado.</p>
            <form className={estilos.formulario} onSubmit={aoEnviar}>
              {parametros.get('sessao') === 'expirada' && !erro && (
                <Alerta tipo="info">Sua sessão expirou. Entre novamente.</Alerta>
              )}
              <Alerta tipo="erro">{erro}</Alerta>
              <div>
                <label htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  placeholder="voce@exemplo.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  autoFocus
                />
              </div>
            <div>
              <label htmlFor="senha">Senha</label>
              <div className={estilos.campoSenha}>
              <input
                id="senha"
                type={senhaVisivel ? 'text' : 'password'}
                autoComplete="current-password"
                placeholder="Digite sua senha"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                required
              />
              <button type="button" className={estilos.mostrarSenha} onClick={() => setSenhaVisivel((visivel) => !visivel)} aria-label={senhaVisivel ? 'Ocultar senha' : 'Mostrar senha'} aria-pressed={senhaVisivel}>
                {senhaVisivel ? 'Ocultar' : 'Mostrar'}
              </button>
              </div>
            </div>
            <button type="submit" className={estilos.botao} disabled={enviando}>
              {enviando ? 'Entrando…' : 'Entrar na minha conta'}<span aria-hidden="true">→</span>
            </button>
          </form>
          <p className={estilos.rodape}>
            Ainda não tem conta? <Link to="/cadastro">Criar uma conta</Link>
          </p>
          <p className={estilos.assinatura}>Seu cuidado tem continuidade aqui.</p>
          </div>
        </section>
      </div>
    </main>
  )
}
