import { Link, useParams, useSearchParams } from 'react-router-dom'

import { mensagemDeErro } from '../../api/cliente'
import * as servicos from '../../api/servicos'
import { Alerta, Carregando, ErroCarregamento, estilos as ui } from '../../components/ui'
import { useAuth } from '../../context/AuthContext'
import { useAtualizacaoPeriodica } from '../../hooks/useAtualizacaoPeriodica'
import AbaConsultas from './AbaConsultas'
import AbaExames from './AbaExames'
import AbaLinhaDoTempo from './AbaLinhaDoTempo'
import AbaSolicitacoes from './AbaSolicitacoes'
import CabecalhoJornada from './CabecalhoJornada'
import estilos from './Jornada.module.css'

const ABAS = [
  { id: 'linha', rotulo: 'Linha do tempo' },
  { id: 'consultas', rotulo: 'Consultas' },
  { id: 'solicitacoes', rotulo: 'Solicitações' },
  { id: 'exames', rotulo: 'Exames' },
]

/** Carrega tudo da jornada de uma vez; o polling repete essa busca a cada 30 s. */
async function carregarJornada(id) {
  const [jornada, linhaDoTempo, consultas, solicitacoes, exames] = await Promise.all([
    servicos.obterJornada(id),
    servicos.obterLinhaDoTempo(id),
    servicos.listarConsultas(id),
    servicos.listarSolicitacoes(id),
    servicos.listarExames(id),
  ])
  return { jornada, linhaDoTempo, consultas, solicitacoes, exames }
}

export default function Jornada() {
  const { id } = useParams()
  const { usuario, ehMedico } = useAuth()
  const [parametros, setParametros] = useSearchParams()
  const abaAtual = ABAS.some((aba) => aba.id === parametros.get('aba')) ? parametros.get('aba') : 'linha'

  const { dados, erro, carregando, atualizar } = useAtualizacaoPeriodica(() => carregarJornada(id), undefined, [id])

  /** Troca de aba mantendo o histórico do navegador; `extras` vira parâmetro da URL. */
  function irParaAba(aba, extras = {}) {
    setParametros({ aba, ...extras })
  }

  if (carregando && !dados) return <Carregando texto="Carregando a jornada…" />

  if (!dados) {
    const status = erro?.response?.status
    return (
      <div className={estilos.pilha}>
        <Alerta tipo="erro">
          {status === 404 || status === 403
            ? mensagemDeErro(erro)
            : mensagemDeErro(erro, 'Não foi possível carregar a jornada.')}
        </Alerta>
        <p>
          <Link to="/jornadas">Voltar para as jornadas</Link>
        </p>
      </div>
    )
  }

  const { jornada, linhaDoTempo, consultas, solicitacoes, exames } = dados
  const editavel = jornada.status === 'ativa'
  const contexto = { jornada, usuario, ehMedico, editavel, atualizar, irParaAba }

  const contagens = {
    solicitacoes: solicitacoes.filter((s) => s.status === 'pendente').length,
    exames: ehMedico ? exames.filter((e) => e.status === 'enviado' && e.enviado_por.id !== usuario.id).length : 0,
  }

  return (
    <div className={estilos.pilha}>
      <Link to="/jornadas" className={estilos.voltar}>
        ← Jornadas
      </Link>

      <CabecalhoJornada {...contexto} />

      {/* Erro de uma atualização periódica: mantém os dados já carregados na tela */}
      <ErroCarregamento erro={erro} />

      {!editavel && (
        <Alerta tipo="alerta">
          Esta jornada está encerrada e fica disponível apenas para consulta.
          {ehMedico && ' Reabra a jornada para registrar novas informações.'}
        </Alerta>
      )}

      <div className={estilos.abas} role="tablist" aria-label="Seções da jornada">
        {ABAS.map((aba) => (
          <button
            key={aba.id}
            type="button"
            role="tab"
            id={`aba-${aba.id}`}
            aria-selected={abaAtual === aba.id}
            aria-controls={`painel-${aba.id}`}
            className={abaAtual === aba.id ? `${estilos.aba} ${estilos.abaAtiva}` : estilos.aba}
            onClick={() => irParaAba(aba.id)}
          >
            {aba.rotulo}
            {contagens[aba.id] > 0 && <span className={estilos.contador}>{contagens[aba.id]}</span>}
          </button>
        ))}
      </div>

      <div role="tabpanel" id={`painel-${abaAtual}`} aria-labelledby={`aba-${abaAtual}`} className={ui.cartao}>
        {abaAtual === 'linha' && <AbaLinhaDoTempo eventos={linhaDoTempo} {...contexto} />}
        {abaAtual === 'consultas' && <AbaConsultas consultas={consultas} {...contexto} />}
        {abaAtual === 'solicitacoes' && <AbaSolicitacoes solicitacoes={solicitacoes} {...contexto} />}
        {abaAtual === 'exames' && (
          <AbaExames
            exames={exames}
            solicitacoes={solicitacoes}
            solicitacaoInicial={parametros.get('solicitacao')}
            {...contexto}
          />
        )}
      </div>
    </div>
  )
}
