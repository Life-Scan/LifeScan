import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { Alerta, estilos as ui } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import estilos from './Auth.module.css'

export default function TrocarSenha() {
  const { usuario, trocarSenha, sair } = useAuth()
  const navegar = useNavigate()
  // Obrigatória quando a pessoa entrou com a senha provisória recebida por email
  const obrigatoria = usuario.deve_trocar_senha

  const [senhaAtual, setSenhaAtual] = useState('')
  const [novaSenha, setNovaSenha] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    if (novaSenha !== confirmacao) {
      setErro('As senhas não conferem.')
      return
    }
    setEnviando(true)
    try {
      await trocarSenha(senhaAtual, novaSenha)
      navegar('/painel', { replace: true })
    } catch (erroTroca) {
      setErro(mensagemDeErro(erroTroca))
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
          {obrigatoria ? `Olá, ${usuario.nome.split(' ')[0]}! Antes de continuar, escolha uma senha só sua.` : 'Altere a sua senha de acesso.'}
        </p>

        <div className={ui.cartao}>
          <h1 className={estilos.titulo}>{obrigatoria ? 'Defina sua senha' : 'Alterar senha'}</h1>
          <form className={ui.formulario} onSubmit={aoEnviar}>
            <Alerta tipo="erro">{erro}</Alerta>
            <div>
              <label htmlFor="senha-atual">{obrigatoria ? 'Senha provisória (recebida por email)' : 'Senha atual'}</label>
              <input
                id="senha-atual"
                type="password"
                autoComplete="current-password"
                value={senhaAtual}
                onChange={(e) => setSenhaAtual(e.target.value)}
                required
                autoFocus
              />
            </div>
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
            <p className={ui.ajuda}>A senha precisa ter pelo menos 6 caracteres.</p>
            <button type="submit" className={ui.botao} disabled={enviando}>
              {enviando ? 'Salvando…' : 'Salvar nova senha'}
            </button>
          </form>
          <p className={estilos.rodape}>
            {obrigatoria ? (
              <button type="button" className={ui.botaoLink} onClick={aoSair}>
                Sair
              </button>
            ) : (
              <Link to="/painel">Cancelar</Link>
            )}
          </p>
        </div>
      </div>
    </div>
  )
}
