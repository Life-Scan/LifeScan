import { ArrowLeft } from 'lucide-react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { mensagemDeErro } from '../../api/cliente'
import * as servicos from '../../api/servicos'
import { Alerta, Carregando, ErroCarregamento, estilos as ui } from '../../components/ui'
import { useAuth } from '../../context/AuthContext'
import { useAtualizacaoPeriodica } from '../../hooks/useAtualizacaoPeriodica'
import AbaConsultas from './AbaConsultas'
import AbaDocumentos from './AbaDocumentos'
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
  { id: 'documentos', rotulo: 'Documentos' },
  { id: 'parceiros', rotulo: 'Parceiros' },
]

// O parceiro só tem acesso à ficha do paciente, às solicitações destinadas a ele e aos próprios envios
const ABAS_PARCEIRO = [
  { id: 'ficha', rotulo: 'Ficha do paciente' },
  { id: 'solicitacoes', rotulo: 'Solicitações' },
  { id: 'documentos', rotulo: 'Meus envios' },
]

/** Carrega tudo o que o usuário pode ver da jornada; o polling repete essa busca a cada 30 s. */
async function carregarJornada(id, ehParceiro) {
  if (ehParceiro) {
    const [jornada, ficha, solicitacoes, documentos] = await Promise.all([
      servicos.obterJornada(id),
      servicos.obterFicha(id),
      servicos.listarSolicitacoes(id),
      servicos.listarDocumentos(id),
    ])
    return { jornada, ficha, solicitacoes, documentos, linhaDoTempo: [], consultas: [], parceiros: [] }
  }
  const [jornada, linhaDoTempo, ficha, consultas, solicitacoes, documentos, parceiros] = await Promise.all([
    servicos.obterJornada(id),
    servicos.obterLinhaDoTempo(id),
    servicos.obterFicha(id),
    servicos.listarConsultas(id),
    servicos.listarSolicitacoes(id),
    servicos.listarDocumentos(id),
    servicos.listarParceirosDaJornada(id),
  ])
  return { jornada, linhaDoTempo, ficha, consultas, solicitacoes, documentos, parceiros }
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

  const { jornada, linhaDoTempo, ficha, consultas, solicitacoes, documentos, parceiros } = dados
  const editavel = jornada.status === 'ativa'
  const contexto = { jornada, usuario, ehMedico, ehParceiro, editavel, atualizar, irParaAba }

  // Médico: tudo o que está pendente na jornada. Demais: só o que cabe a eles.
  const contagens = {
    solicitacoes: solicitacoes.filter(
      (s) => s.status === 'pendente' && (ehMedico || s.destinatario.id === usuario.id),
    ).length,
    documentos: ehMedico
      ? documentos.filter((d) => d.status === 'enviado' && d.enviado_por.id !== usuario.id).length
      : 0,
  }

  return (
    <div className={estilos.pilha}>
      <Link to="/jornadas" className={estilos.voltar}>
        <ArrowLeft size={15} aria-hidden="true" />
        {ehParceiro ? 'Pacientes' : 'Jornadas'}
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
        {abaAtual === 'solicitacoes' && (
          <AbaSolicitacoes solicitacoes={solicitacoes} parceiros={parceiros} {...contexto} />
        )}
        {abaAtual === 'documentos' && (
          <AbaDocumentos
            documentos={documentos}
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
