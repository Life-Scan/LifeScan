import { useState } from 'react'
import { Link } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { esqueciSenha } from '../api/servicos'
import { CampoEmail } from '../components/CamposMascarados'
import TelaAcesso from '../components/TelaAcesso'
import { Alerta, estilos as ui } from '../components/ui'

export default function EsqueciSenha() {
  const [email, setEmail] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      const { mensagem } = await esqueciSenha(email)
      setConfirmacao(mensagem)
    } catch (erroEnvio) {
      setErro(mensagemDeErro(erroEnvio))
    } finally {
      setEnviando(false)
    }
  }

  return (
    <TelaAcesso
      slogan="Vamos enviar uma senha provisória para o seu email."
      titulo="Esqueci minha senha"
      rodape={!confirmacao && <Link to="/login">Voltar para o login</Link>}
    >
      {confirmacao ? (
        <div className={ui.formulario}>
          <Alerta tipo="sucesso">{confirmacao}</Alerta>
          <p className={ui.ajuda}>
            Entre com a senha provisória recebida; em seguida você escolhe uma nova senha. Sua senha antiga
            continua valendo até lá.
          </p>
          <Link to="/login" className={ui.botao}>
            Voltar para o login
          </Link>
        </div>
      ) : (
        <form className={ui.formulario} onSubmit={aoEnviar}>
          <Alerta tipo="erro">{erro}</Alerta>
          <div>
            <label htmlFor="email">Email da sua conta</label>
            <CampoEmail
              id="email"
              autoComplete="email"
              placeholder="voce@exemplo.com"
              value={email}
              onChange={setEmail}
              required
              autoFocus
            />
          </div>
          <button type="submit" className={ui.botao} disabled={enviando}>
            {enviando ? 'Enviando…' : 'Enviar senha provisória'}
          </button>
        </form>
      )}
    </TelaAcesso>
  )
}
