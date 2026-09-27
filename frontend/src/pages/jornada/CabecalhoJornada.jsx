import { useState } from 'react'

import { mensagemDeErro } from '../../api/cliente'
import { alterarPasso, alterarStatusJornada } from '../../api/servicos'
import { Alerta, Etiqueta, estilos as ui } from '../../components/ui'
import { PASSOS, ROTULOS_PASSO, formatarData } from '../../utils/formatacao'
import estilos from './Jornada.module.css'

export default function CabecalhoJornada({ jornada, ehMedico, editavel, atualizar }) {
  const [erro, setErro] = useState('')
  const [ocupado, setOcupado] = useState(false)

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

  function alternarStatus() {
    const encerrar = jornada.status === 'ativa'
    const confirmacao = encerrar
      ? 'Encerrar esta jornada? Ela ficará somente para consulta até ser reaberta.'
      : 'Reabrir esta jornada?'
    if (!window.confirm(confirmacao)) return
    executar(() => alterarStatusJornada(jornada.id, encerrar ? 'encerrada' : 'ativa'))
  }

  const podeMudarPasso = ehMedico && editavel
  const indiceAtual = PASSOS.indexOf(jornada.passo_atual)

  return (
    <header className={`${ui.cartao} ${estilos.cabecalho}`}>
      <div className={estilos.cabecalhoTopo}>
        <div>
          <div className={ui.acoes}>
            <h1>{jornada.titulo}</h1>
            <Etiqueta variante={jornada.status === 'ativa' ? 'sucesso' : 'neutra'}>
              {jornada.status === 'ativa' ? 'Ativa' : 'Encerrada'}
            </Etiqueta>
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
        {ehMedico && (
          <button
            type="button"
            className={`${jornada.status === 'ativa' ? ui.botaoPerigo : ui.botaoSecundario} ${ui.botaoPequeno}`}
            onClick={alternarStatus}
            disabled={ocupado}
          >
            {jornada.status === 'ativa' ? 'Encerrar jornada' : 'Reabrir jornada'}
          </button>
        )}
      </div>

      <div>
        <p className={estilos.rotuloPasso}>
          Passo atual{podeMudarPasso && <span className={ui.suave}> (clique para alterar)</span>}
        </p>
        <ol className={estilos.passos}>
          {PASSOS.map((passo, indice) => {
            const classe = [
              estilos.passo,
              indice < indiceAtual ? estilos.passoConcluido : '',
              indice === indiceAtual ? estilos.passoAtual : '',
            ].join(' ')
            return (
              <li key={passo} className={classe}>
                {podeMudarPasso ? (
                  <button
                    type="button"
                    className={estilos.botaoPasso}
                    onClick={() => mudarPasso(passo)}
                    disabled={ocupado}
                    aria-current={indice === indiceAtual ? 'step' : undefined}
                  >
                    <span className={estilos.numeroPasso}>{indice + 1}</span>
                    {ROTULOS_PASSO[passo]}
                  </button>
                ) : (
                  <span className={estilos.botaoPasso} aria-current={indice === indiceAtual ? 'step' : undefined}>
                    <span className={estilos.numeroPasso}>{indice + 1}</span>
                    {ROTULOS_PASSO[passo]}
                  </span>
                )}
              </li>
            )
          })}
        </ol>
      </div>
      <Alerta tipo="erro">{erro}</Alerta>
    </header>
  )
}
