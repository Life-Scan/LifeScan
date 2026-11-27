import { ArrowLeft, Check, Lock, LockOpen } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { mensagemDeErro } from '../../api/cliente'
import { alterarPasso, alterarStatusAcompanhamento } from '../../api/servicos'
import { useConfirmar } from '../../components/Confirmacao'
import { Alerta, Avatar, Etiqueta, Faixa, estilos as ui } from '../../components/ui'
import { cn } from '@/lib/utils'
import { PASSOS, ROTULOS_PASSO, formatarData } from '../../utils/formatacao'
import { estilos, passo as estilosPasso } from './estilosAcompanhamento'

export default function CabecalhoAcompanhamento({ acompanhamento, ehMedico, ehParceiro, editavel, atualizar }) {
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
    <>
      {/* Faixa escura: identificação do acompanhamento. O sobretítulo é o caminho de volta para a lista. */}
      <Faixa como="header" aria-labelledby="titulo-acompanhamento">
        <div className={estilos.cabecalhoTopo}>
          <div className={estilos.identificacao}>
            <Avatar nome={acompanhamento.paciente.nome} grande />
            <div>
              <Link to="/acompanhamentos" className={ui.sobretituloFaixaLink}>
                <ArrowLeft size={13} aria-hidden="true" />
                {ehParceiro ? 'Pacientes' : 'Acompanhamentos'}
              </Link>
              <div className={estilos.tituloLinha}>
                <h1 id="titulo-acompanhamento">{acompanhamento.titulo}</h1>
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
              className={cn(ui.botaoFaixa, ui.botaoPequeno)}
              onClick={alternarStatus}
              disabled={ocupado}
            >
              {ativo ? <Lock size={14} aria-hidden="true" /> : <LockOpen size={14} aria-hidden="true" />}
              {ativo ? 'Encerrar acompanhamento' : 'Reabrir acompanhamento'}
            </button>
          )}
        </div>
      </Faixa>

      {/* Etapas no fundo claro, onde as cores de estado foram pensadas */}
      <div className={`${ui.cartao} ${estilos.passoCartao}`}>
        <div className={estilos.passoLinha}>
          <span className={estilos.rotuloPasso}>Passo atual</span>
          <ol className={estilos.passos}>
            {PASSOS.map((passo, indice) => {
              const concluido = indice < indiceAtual
              const atual = indice === indiceAtual
              const estado = atual ? 'atual' : concluido ? 'concluido' : 'pendente'
              // Traço antes da etapa (menos na primeira): verde se a etapa anterior já foi concluída
              const traco =
                indice === 0
                  ? ''
                  : `${estilosPasso.traco} ${indice <= indiceAtual ? estilosPasso.tracoCor.feito : estilosPasso.tracoCor.pendente}`
              const conteudo = (
                <>
                  <span className={estilosPasso.numero[estado]}>
                    {concluido ? <Check size={12} strokeWidth={3} aria-hidden="true" /> : indice + 1}
                  </span>
                  {ROTULOS_PASSO[passo]}
                </>
              )
              return (
                <li key={passo} className={`${estilosPasso.item} ${traco}`}>
                  {podeMudarPasso ? (
                    <button
                      type="button"
                      className={`${estilosPasso.botao[estado]} ${estilosPasso.clicavel[estado]}`}
                      onClick={() => mudarPasso(passo)}
                      disabled={ocupado}
                      aria-current={atual ? 'step' : undefined}
                      title={atual ? 'Passo atual' : `Mudar para ${ROTULOS_PASSO[passo]}`}
                    >
                      {conteudo}
                    </button>
                  ) : (
                    <span className={estilosPasso.botao[estado]} aria-current={atual ? 'step' : undefined}>
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
      </div>
    </>
  )
}
