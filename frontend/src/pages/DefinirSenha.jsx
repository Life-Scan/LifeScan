import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import TelaAcesso from '../components/TelaAcesso'
import { Alerta, estilos as ui } from '../components/ui'
import { useAuth } from '../context/AuthContext'

/**
 * Primeiro acesso (ou volta do "esqueci minha senha"): a pessoa entrou com a senha
 * provisória e escolhe aqui a própria senha. Não existe troca de senha fora desse momento.
 */
export default function DefinirSenha() {
  const { usuario, definirSenha, sair } = useAuth()
  const navegar = useNavigate()

  const [novaSenha, setNovaSenha] = useState('')
  const [confirmacao, setConfirmacao] = useState('')
  const [aceiteLgpd, setAceiteLgpd] = useState(false)
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  // LGPD: o consentimento de tratamento de dados só é pedido a quem é titular
  // dos dados de saúde (o paciente); médicos e parceiros só definem a senha
  const ehPaciente = usuario.tipo_usuario === 'paciente'

  if (!usuario.deve_trocar_senha) return <Navigate to="/painel" replace />

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    if (novaSenha !== confirmacao) {
      setErro('As senhas não conferem.')
      return
    }
    if (ehPaciente && !aceiteLgpd) {
      setErro('Para continuar, é preciso aceitar o termo de tratamento de dados.')
      return
    }
    setEnviando(true)
    try {
      await definirSenha(novaSenha, ehPaciente)
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
    <TelaAcesso
      slogan={`Olá, ${usuario.nome.split(' ')[0]}! Antes de continuar, escolha uma senha só sua.`}
      titulo="Defina sua senha"
      rodape={
        <button type="button" className={ui.botaoLink} onClick={aoSair}>
          Sair
        </button>
      }
    >
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
        {ehPaciente && (
          <div>
            <label className="flex items-start gap-2 font-normal">
              <input
                type="checkbox"
                checked={aceiteLgpd}
                onChange={(e) => setAceiteLgpd(e.target.checked)}
                className="mt-[3px]"
              />
              <span>
                Autorizo o tratamento dos meus dados de saúde (anamnese, consultas e documentos)
                para a finalidade de acompanhamento clínico, conforme a LGPD. Posso revogar este
                consentimento a qualquer momento.
              </span>
            </label>
          </div>
        )}
        <p className={ui.ajuda}>
          Pelo menos 6 caracteres. A senha provisória que você recebeu por email deixa de valer.
        </p>
        <button type="submit" className={ui.botao} disabled={enviando}>
          {enviando ? 'Salvando…' : 'Salvar e entrar'}
        </button>
      </form>
    </TelaAcesso>
  )
}
