import { useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { Alerta, estilos as ui } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import estilos from './Auth.module.css'

export default function Login() {
  const { entrar } = useAuth()
  const navegar = useNavigate()
  const local = useLocation()
  const [parametros] = useSearchParams()

  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      const usuario = await entrar(email, senha)
      // Quem entrou com a senha provisória precisa definir a própria senha antes de tudo
      navegar(usuario.deve_trocar_senha ? '/trocar-senha' : local.state?.de || '/painel', { replace: true })
    } catch (erroLogin) {
      setErro(mensagemDeErro(erroLogin))
      setEnviando(false)
    }
  }

  return (
    <div className={estilos.fundo}>
      <div className={estilos.caixa}>
        <div className={estilos.marca}>
          <img src="/favicon.svg" alt="" width="36" height="36" />
          LifeScan
        </div>
        <p className={estilos.slogan}>Seu tratamento acompanhado de perto, entre uma consulta e outra.</p>

        <div className={ui.cartao}>
          <h1 className={estilos.titulo}>Entrar</h1>
          <form className={ui.formulario} onSubmit={aoEnviar}>
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
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>
            <div>
              <label htmlFor="senha">Senha</label>
              <input
                id="senha"
                type="password"
                autoComplete="current-password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                required
              />
            </div>
            <button type="submit" className={ui.botao} disabled={enviando}>
              {enviando ? 'Entrando…' : 'Entrar'}
            </button>
          </form>
          <p className={estilos.rodape}>
            <Link to="/esqueci-senha">Esqueci minha senha</Link>
          </p>
          <p className={estilos.nota}>
            O acesso é criado pelo seu médico. Se você recebeu um email com uma senha provisória, use-a aqui.
          </p>
        </div>
      </div>
    </div>
  )
}
