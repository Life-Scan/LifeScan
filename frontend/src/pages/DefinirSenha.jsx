import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { Alerta, estilos as ui } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import estilos from './Auth.module.css'

/**
 * Primeiro acesso (ou volta do "esqueci minha senha"): a pessoa entrou com a senha
 * provisória e escolhe aqui a própria senha. Não existe troca de senha fora desse momento.
 */
export default function DefinirSenha() {
  const { usuario, definirSenha, sair } = useAuth()
  const navegar = useNavigate()

  const [novaSenha, setNovaSenha] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  if (!usuario.deve_trocar_senha) return <Navigate to="/painel" replace />

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    if (novaSenha !== confirmacao) {
      setErro('As senhas não conferem.')
      return
    }
    setEnviando(true)
    try {
      await definirSenha(novaSenha)
      navegar('/painel', { replace: true })
    } catch (erroDefinicao) {
      setErro(mensagemDeErro(erroDefinicao))
      setEnviando(false)
    }
  }

  function aoSair() {
    sair()
    navegar('/login', { replace: true })
  }

  return (
    <div className={estilos.fundo}>
      <div className={estilos.caixa}>
        <div className={estilos.marca}>
          <img src="/favicon.svg" alt="" width="36" height="36" />
          LifeScan
        </div>
        <p className={estilos.slogan}>
          Olá, {usuario.nome.split(' ')[0]}! Antes de continuar, escolha uma senha só sua.
        </p>

        <div className={ui.cartao}>
          <h1 className={estilos.titulo}>Defina sua senha</h1>
          <form className={ui.formulario} onSubmit={aoEnviar}>
            <Alerta tipo="erro">{erro}</Alerta>
            <div>
              <label htmlFor="nova-senha">Nova senha</label>
              <input
                id="nova-senha"
                type="password"
                autoComplete="new-password"
                value={novaSenha}
                onChange={(e) => setNovaSenha(e.target.value)}
                required
                minLength={6}
                autoFocus
              />
            </div>
            <div>
              <label htmlFor="confirmacao">Confirmar nova senha</label>
              <input
                id="confirmacao"
                type="password"
                autoComplete="new-password"
                value={confirmacao}
                onChange={(e) => setConfirmacao(e.target.value)}
                required
              />
            </div>
            <p className={ui.ajuda}>
              Pelo menos 6 caracteres. A senha provisória que você recebeu por email deixa de valer.
            </p>
            <button type="submit" className={ui.botao} disabled={enviando}>
              {enviando ? 'Salvando…' : 'Salvar e entrar'}
            </button>
          </form>
          <p className={estilos.rodape}>
            <button type="button" className={ui.botaoLink} onClick={aoSair}>
              Sair
            </button>
          </p>
        </div>
      </div>
    </div>
  )
}
