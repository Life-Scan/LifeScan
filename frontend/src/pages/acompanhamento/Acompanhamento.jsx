import { ArrowLeft } from 'lucide-react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { mensagemDeErro } from '../../api/cliente'
import * as servicos from '../../api/servicos'
import { Alerta, Carregando, ErroCarregamento, estilos as ui } from '../../components/ui'
import { useAuth } from '../../context/AuthContext'
import { useAtualizacaoPeriodica } from '../../hooks/useAtualizacaoPeriodica'
import AbaConsultas from './AbaConsultas'
import AbaDocumentos from './AbaDocumentos'
import AbaAnamnese from './AbaAnamnese'
import AbaLinhaDoTempo from './AbaLinhaDoTempo'
import AbaParceiros from './AbaParceiros'
import AbaSolicitacoes from './AbaSolicitacoes'
import CabecalhoAcompanhamento from './CabecalhoAcompanhamento'
import estilos from './Acompanhamento.module.css'

const ABAS = [
  { id: 'linha', rotulo: 'Linha do tempo' },
  { id: 'anamnese', rotulo: 'Anamnese' },
  { id: 'consultas', rotulo: 'Consultas' },
  { id: 'solicitacoes', rotulo: 'Solicitações' },
  { id: 'documentos', rotulo: 'Documentos' },
  { id: 'parceiros', rotulo: 'Parceiros' },
]

// O parceiro só tem acesso à anamnese do paciente, às solicitações destinadas a ele e aos próprios envios
const ABAS_PARCEIRO = [
  { id: 'anamnese', rotulo: 'Anamnese do paciente' },
  { id: 'solicitacoes', rotulo: 'Solicitações' },
  { id: 'documentos', rotulo: 'Meus envios' },
]

/** Carrega tudo o que o usuário pode ver do acompanhamento; o polling repete essa busca a cada 30 s. */
async function carregarAcompanhamento(id, ehParceiro) {
  if (ehParceiro) {
    const [acompanhamento, anamnese, solicitacoes, documentos] = await Promise.all([
      servicos.obterAcompanhamento(id),
      servicos.obterAnamnese(id),
      servicos.listarSolicitacoes(id),
      servicos.listarDocumentos(id),
    ])
    return { acompanhamento, anamnese, solicitacoes, documentos, linhaDoTempo: [], consultas: [], parceiros: [] }
  }
  const [acompanhamento, linhaDoTempo, anamnese, consultas, solicitacoes, documentos, parceiros] = await Promise.all([
    servicos.obterAcompanhamento(id),
    servicos.obterLinhaDoTempo(id),
    servicos.obterAnamnese(id),
    servicos.listarConsultas(id),
    servicos.listarSolicitacoes(id),
    servicos.listarDocumentos(id),
    servicos.listarParceirosDoAcompanhamento(id),
  ])
  return { acompanhamento, linhaDoTempo, anamnese, consultas, solicitacoes, documentos, parceiros }
}

export default function Acompanhamento() {
  const { id } = useParams()
  const { usuario, ehMedico, ehParceiro } = useAuth()
  const [parametros, setParametros] = useSearchParams()

  const abas = ehParceiro ? ABAS_PARCEIRO : ABAS
  const abaAtual = abas.some((aba) => aba.id === parametros.get('aba')) ? parametros.get('aba') : abas[0].id

  const { dados, erro, carregando, atualizar } = useAtualizacaoPeriodica(
    () => carregarAcompanhamento(id, ehParceiro),
    undefined,
    [id, ehParceiro],
  )

  /** Troca de aba mantendo o histórico do navegador; `extras` vira parâmetro da URL. */
  function irParaAba(aba, extras = {}) {
    setParametros({ aba, ...extras })
  }

  if (carregando && !dados) return <Carregando texto="Carregando o acompanhamento…" />

  if (!dados) {
    const status = erro?.response?.status
    return (
      <div className={estilos.pilha}>
        <Alerta tipo="erro">
          {status === 404 || status === 403
            ? mensagemDeErro(erro)
            : mensagemDeErro(erro, 'Não foi possível carregar o acompanhamento.')}
        </Alerta>
        <p>
          <Link to="/acompanhamentos">Voltar</Link>
        </p>
      </div>
    )
  }

  const { acompanhamento, linhaDoTempo, anamnese, consultas, solicitacoes, documentos, parceiros } = dados
  const editavel = acompanhamento.status === 'ativo'
  const contexto = { acompanhamento, usuario, ehMedico, ehParceiro, editavel, atualizar, irParaAba }

  // Médico: tudo o que está pendente no acompanhamento. Demais: só o que cabe a eles.
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
      <Link to="/acompanhamentos" className={estilos.voltar}>
        <ArrowLeft size={15} aria-hidden="true" />
        {ehParceiro ? 'Pacientes' : 'Acompanhamentos'}
      </Link>

      <CabecalhoAcompanhamento {...contexto} />

      {/* Erro de uma atualização periódica: mantém os dados já carregados na tela */}
      <ErroCarregamento erro={erro} />

      {!editavel && (
        <Alerta tipo="alerta">
          Este acompanhamento está encerrado e fica disponível apenas para consulta.
          {ehMedico && ' Reabra o acompanhamento para registrar novas informações.'}
        </Alerta>
      )}

      <div className={estilos.abas} role="tablist" aria-label="Seções do acompanhamento">
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
        {abaAtual === 'anamnese' && <AbaAnamnese anamnese={anamnese} {...contexto} />}
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
