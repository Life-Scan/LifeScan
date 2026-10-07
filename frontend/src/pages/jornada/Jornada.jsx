import { Link, useParams, useSearchParams } from 'react-router-dom'

import { mensagemDeErro } from '../../api/cliente'
import * as servicos from '../../api/servicos'
import { Alerta, Carregando, ErroCarregamento, estilos as ui } from '../../components/ui'
import { useAuth } from '../../context/AuthContext'
import { useAtualizacaoPeriodica } from '../../hooks/useAtualizacaoPeriodica'
import AbaConsultas from './AbaConsultas'
import AbaExames from './AbaExames'
import AbaFicha from './AbaFicha'
import AbaLinhaDoTempo from './AbaLinhaDoTempo'
import AbaParceiros from './AbaParceiros'
import AbaSolicitacoes from './AbaSolicitacoes'
import CabecalhoJornada from './CabecalhoJornada'
import estilos from './Jornada.module.css'

const ABAS = [
  { id: 'linha', rotulo: 'Linha do tempo' },
  { id: 'ficha', rotulo: 'Ficha' },
  { id: 'consultas', rotulo: 'Consultas' },
  { id: 'solicitacoes', rotulo: 'Solicitações' },
  { id: 'exames', rotulo: 'Exames' },
  { id: 'parceiros', rotulo: 'Parceiros' },
]

// O parceiro só tem acesso à ficha do paciente e aos próprios envios
const ABAS_PARCEIRO = [
  { id: 'ficha', rotulo: 'Ficha do paciente' },
  { id: 'exames', rotulo: 'Meus envios' },
]

/** Carrega tudo o que o usuário pode ver da jornada; o polling repete essa busca a cada 30 s. */
async function carregarJornada(id, ehParceiro) {
  if (ehParceiro) {
    const [jornada, ficha, exames] = await Promise.all([
      servicos.obterJornada(id),
      servicos.obterFicha(id),
      servicos.listarExames(id),
    ])
    return { jornada, ficha, exames, linhaDoTempo: [], consultas: [], solicitacoes: [], parceiros: [] }
  }
  const [jornada, linhaDoTempo, ficha, consultas, solicitacoes, exames, parceiros] = await Promise.all([
    servicos.obterJornada(id),
    servicos.obterLinhaDoTempo(id),
    servicos.obterFicha(id),
    servicos.listarConsultas(id),
    servicos.listarSolicitacoes(id),
    servicos.listarExames(id),
    servicos.listarParceirosDaJornada(id),
  ])
  return { jornada, linhaDoTempo, ficha, consultas, solicitacoes, exames, parceiros }
}

export default function Jornada() {
  const { id } = useParams()
  const { usuario, ehMedico, ehParceiro } = useAuth()
  const [parametros, setParametros] = useSearchParams()

  const abas = ehParceiro ? ABAS_PARCEIRO : ABAS
  const abaAtual = abas.some((aba) => aba.id === parametros.get('aba')) ? parametros.get('aba') : abas[0].id

  const { dados, erro, carregando, atualizar } = useAtualizacaoPeriodica(
    () => carregarJornada(id, ehParceiro),
    undefined,
    [id, ehParceiro],
  )

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
          <Link to="/jornadas">Voltar</Link>
        </p>
      </div>
    )
  }

  const { jornada, linhaDoTempo, ficha, consultas, solicitacoes, exames, parceiros } = dados
  const editavel = jornada.status === 'ativa'
  const contexto = { jornada, usuario, ehMedico, ehParceiro, editavel, atualizar, irParaAba }

  const contagens = {
    solicitacoes: solicitacoes.filter((s) => s.status === 'pendente').length,
    exames: ehMedico ? exames.filter((e) => e.status === 'enviado' && e.enviado_por.id !== usuario.id).length : 0,
  }

  return (
    <div className={estilos.pilha}>
      <Link to="/jornadas" className={estilos.voltar}>
        ← {ehParceiro ? 'Pacientes' : 'Jornadas'}
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
        {abas.map((aba) => (
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
        {abaAtual === 'ficha' && <AbaFicha ficha={ficha} {...contexto} />}
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
        {abaAtual === 'parceiros' && <AbaParceiros parceiros={parceiros} {...contexto} />}
      </div>
    </div>
  )
}
