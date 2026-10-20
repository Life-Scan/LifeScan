import { Check, Lock, LockOpen } from 'lucide-react'
import { useState } from 'react'

import { mensagemDeErro } from '../../api/cliente'
import { alterarPasso, alterarStatusJornada } from '../../api/servicos'
import { useConfirmar } from '../../components/Confirmacao'
import { Alerta, Avatar, Etiqueta, estilos as ui } from '../../components/ui'
import { PASSOS, ROTULOS_PASSO, formatarData } from '../../utils/formatacao'
import estilos from './Jornada.module.css'

export default function CabecalhoJornada({ jornada, ehMedico, editavel, atualizar }) {
  const confirmar = useConfirmar()
  const [erro, setErro] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const ativa = jornada.status === 'ativa'

  async function executar(acao) {
    setErro('')
    setOcupado(true)
    try {
      await acao()
      await atualizar()
    } catch (erroAcao) {
      setErro(mensagemDeErro(erroAcao))
    } finally {
      setOcupado(false)
    }
  }

  function mudarPasso(passo) {
    if (passo === jornada.passo_atual) return
    executar(() => alterarPasso(jornada.id, passo))
  }

  async function alternarStatus() {
    const confirmado = await confirmar(
      ativa
        ? {
            titulo: 'Encerrar esta jornada?',
            mensagem: 'Ela fica disponível apenas para consulta, sem novos registros, até ser reaberta.',
            rotuloConfirmar: 'Encerrar jornada',
            perigo: true,
          }
        : {
            titulo: 'Reabrir esta jornada?',
            mensagem: 'Voltará a ser possível registrar consultas, solicitações e documentos.',
            rotuloConfirmar: 'Reabrir jornada',
          },
    )
    if (confirmado) executar(() => alterarStatusJornada(jornada.id, ativa ? 'encerrada' : 'ativa'))
  }

  const podeMudarPasso = ehMedico && editavel
  const indiceAtual = PASSOS.indexOf(jornada.passo_atual)

  return (
    <header className={`${ui.cartao} ${estilos.cabecalho}`}>
      <div className={estilos.cabecalhoTopo}>
        <div className={estilos.identificacao}>
          <Avatar nome={jornada.paciente.nome} grande />
          <div>
            <div className={estilos.tituloLinha}>
              <h1>{jornada.titulo}</h1>
              <Etiqueta variante={ativa ? 'sucesso' : 'neutra'}>{ativa ? 'Ativa' : 'Encerrada'}</Etiqueta>
            </div>
            <div className={estilos.pessoas}>
              <span>
                Paciente: <strong>{jornada.paciente.nome}</strong>
              </span>
              <span>
                Médico(a): <strong>{jornada.medico.nome}</strong>
              </span>
              <span>Aberta em {formatarData(jornada.criado_em)}</span>
            </div>
            {jornada.descricao && <p className={estilos.descricao}>{jornada.descricao}</p>}
          </div>
        </div>
        {ehMedico && (
          <button
            type="button"
            className={`${ativa ? ui.botaoPerigo : ui.botaoSecundario} ${ui.botaoPequeno}`}
            onClick={alternarStatus}
            disabled={ocupado}
          >
            {ativa ? <Lock size={14} aria-hidden="true" /> : <LockOpen size={14} aria-hidden="true" />}
            {ativa ? 'Encerrar jornada' : 'Reabrir jornada'}
          </button>
        )}
      </div>

      <div className={estilos.passoLinha}>
        <span className={estilos.rotuloPasso}>Passo atual</span>
        <ol className={estilos.passos}>
          {PASSOS.map((passo, indice) => {
            const concluido = indice < indiceAtual
            const atual = indice === indiceAtual
            const classe = [estilos.passo, concluido ? estilos.passoConcluido : '', atual ? estilos.passoAtual : '']
              .filter(Boolean)
              .join(' ')
            const conteudo = (
              <>
                <span className={estilos.numeroPasso}>
                  {concluido ? <Check size={12} strokeWidth={3} aria-hidden="true" /> : indice + 1}
                </span>
                {ROTULOS_PASSO[passo]}
              </>
            )
            return (
              <li key={passo} className={classe}>
                {podeMudarPasso ? (
                  <button
                    type="button"
                    className={estilos.botaoPasso}
                    onClick={() => mudarPasso(passo)}
                    disabled={ocupado}
                    aria-current={atual ? 'step' : undefined}
                    title={atual ? 'Passo atual' : `Mudar para ${ROTULOS_PASSO[passo]}`}
                  >
                    {conteudo}
                  </button>
                ) : (
                  <span className={estilos.botaoPasso} aria-current={atual ? 'step' : undefined}>
                    {conteudo}
                  </span>
                )}
              </li>
            )
          })}
        </ol>
        {podeMudarPasso && <span className={ui.ajuda}>Clique em uma etapa para alterar.</span>}
      </div>
      <Alerta tipo="erro">{erro}</Alerta>
    </header>
  )
}
