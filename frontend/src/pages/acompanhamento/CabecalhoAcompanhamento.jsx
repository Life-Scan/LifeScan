import { Check, Lock, LockOpen } from 'lucide-react'
import { useState } from 'react'

import { mensagemDeErro } from '../../api/cliente'
import { alterarPasso, alterarStatusAcompanhamento } from '../../api/servicos'
import { useConfirmar } from '../../components/Confirmacao'
import { Alerta, Avatar, Etiqueta, estilos as ui } from '../../components/ui'
import { PASSOS, ROTULOS_PASSO, formatarData } from '../../utils/formatacao'
import estilos from './Acompanhamento.module.css'

export default function CabecalhoAcompanhamento({ acompanhamento, ehMedico, editavel, atualizar }) {
  const confirmar = useConfirmar()
  const [erro, setErro] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const ativo = acompanhamento.status === 'ativo'

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
    if (passo === acompanhamento.passo_atual) return
    executar(() => alterarPasso(acompanhamento.id, passo))
  }

  async function alternarStatus() {
    const confirmado = await confirmar(
      ativo
        ? {
            titulo: 'Encerrar este acompanhamento?',
            mensagem: 'Ele fica disponível apenas para consulta, sem novos registros, até ser reaberto.',
            rotuloConfirmar: 'Encerrar acompanhamento',
            perigo: true,
          }
        : {
            titulo: 'Reabrir este acompanhamento?',
            mensagem: 'Voltará a ser possível registrar consultas, solicitações e documentos.',
            rotuloConfirmar: 'Reabrir acompanhamento',
          },
    )
    if (confirmado) executar(() => alterarStatusAcompanhamento(acompanhamento.id, ativo ? 'encerrado' : 'ativo'))
  }

  const podeMudarPasso = ehMedico && editavel
  const indiceAtual = PASSOS.indexOf(acompanhamento.passo_atual)

  return (
    <header className={`${ui.cartao} ${estilos.cabecalho}`}>
      <div className={estilos.cabecalhoTopo}>
        <div className={estilos.identificacao}>
          <Avatar nome={acompanhamento.paciente.nome} grande />
          <div>
            <div className={estilos.tituloLinha}>
              <h1>{acompanhamento.titulo}</h1>
              <Etiqueta variante={ativo ? 'sucesso' : 'neutra'}>{ativo ? 'Ativo' : 'Encerrado'}</Etiqueta>
            </div>
            <div className={estilos.pessoas}>
              <span>
                Paciente: <strong>{acompanhamento.paciente.nome}</strong>
              </span>
              <span>
                Médico(a): <strong>{acompanhamento.medico.nome}</strong>
              </span>
              <span>Aberto em {formatarData(acompanhamento.criado_em)}</span>
            </div>
            {acompanhamento.descricao && <p className={estilos.descricao}>{acompanhamento.descricao}</p>}
          </div>
        </div>
        {ehMedico && (
          <button
            type="button"
            className={`${ativo ? ui.botaoPerigo : ui.botaoSecundario} ${ui.botaoPequeno}`}
            onClick={alternarStatus}
            disabled={ocupado}
          >
            {ativo ? <Lock size={14} aria-hidden="true" /> : <LockOpen size={14} aria-hidden="true" />}
            {ativo ? 'Encerrar acompanhamento' : 'Reabrir acompanhamento'}
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
