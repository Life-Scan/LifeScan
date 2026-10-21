import { ArrowLeft } from 'lucide-react'
import { useEffect, useState } from 'react'
import Paginacao from '../../components/Paginacao'
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
  { id: 'anamnese', rotulo: 'Anamnese' },
  { id: 'solicitacoes', rotulo: 'Solicitações' },
  { id: 'documentos', rotulo: 'Meus envios' },
]

export default function Acompanhamento() {
  const { id } = useParams()
  const { usuario, ehMedico, ehParceiro } = useAuth()
  const [parametros, setParametros] = useSearchParams()

  const abas = ehParceiro ? ABAS_PARCEIRO : ABAS
  const abaAtual = abas.some((aba) => aba.id === parametros.get('aba')) ? parametros.get('aba') : abas[0].id

  const { dados: acompanhamento, erro, carregando, atualizar } = useAtualizacaoPeriodica(
    () => servicos.obterAcompanhamento(id), undefined, [id],
  )
  const { dados: contagens, atualizar: atualizarResumo } = useAtualizacaoPeriodica(
    () => servicos.obterResumoAcompanhamento(id), undefined, [id],
  )

  /** Troca de aba mantendo o histórico do navegador; `extras` vira parâmetro da URL. */
  function irParaAba(aba, extras = {}) {
    setParametros({ aba, ...extras })
  }

  if (carregando && !acompanhamento) return <Carregando texto="Carregando o acompanhamento…" />

  if (!acompanhamento) {
    const status = erro?.response?.status
    return (
      <div className={estilos.pilha}>
        <Alerta tipo="erro">
          {status === 404 || status === 403
            ? mensagemDeErro(erro)
            : mensagemDeErro(erro, 'Não foi possível carregar o acompanhamento.')}
        </Alerta>
        <p>
          <button type="button" className={ui.botaoSecundario} onClick={atualizar}>Tentar novamente</button>{' '}
          <Link to="/acompanhamentos">Voltar</Link>
        </p>
      </div>
    )
  }

  const editavel = acompanhamento.status === 'ativo'
  const contexto = { acompanhamento, usuario, ehMedico, ehParceiro, editavel, atualizar: async () => { await Promise.all([atualizar(), atualizarResumo()]) }, irParaAba }

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
            {contagens?.[aba.id] > 0 && <span className={estilos.contador}>{contagens[aba.id]}</span>}
          </button>
        ))}
      </div>

      <div role="tabpanel" id={`painel-${abaAtual}`} aria-labelledby={`aba-${abaAtual}`} className={ui.cartao}>
        <ConteudoAba key={`${id}-${abaAtual}-${usuario.id}`} aba={abaAtual} solicitacaoInicial={parametros.get('solicitacao')} {...contexto} />
      </div>
    </div>
  )
}

/** Cada aba busca apenas o que precisa; o histórico completo nunca bloqueia o cabeçalho. */
function ConteudoAba({ aba, solicitacaoInicial, ...contexto }) {
  const { acompanhamento, ehMedico, atualizar: atualizarCabecalho } = contexto
  const [pagina, setPagina] = useState(1)
  const [tipos, setTipos] = useState([])
  const [recentes, setRecentes] = useState(false)
  const [categoria, setCategoria] = useState('')
  const base = `/follow-ups/${acompanhamento.id}`
  const { dados, erro, carregando, atualizar } = useAtualizacaoPeriodica(async () => {
    const parametros = { pagina }
    if (aba === 'anamnese') return { anamnese: await servicos.obterAnamnese(acompanhamento.id) }
    if (aba === 'parceiros') return { parceiros: await servicos.listarParceirosDoAcompanhamento(acompanhamento.id) }
    if (aba === 'linha') return { lista: await servicos.obterPagina(`${base}/timeline`, { ...parametros, tipos: tipos.length ? tipos.join(',') : undefined, recentes }) }
    if (aba === 'consultas') return { lista: await servicos.obterPagina(`${base}/consultations`, parametros) }
    if (aba === 'solicitacoes') {
      const [lista, parceiros] = await Promise.all([
        servicos.obterPagina(`${base}/requests`, parametros),
        ehMedico ? servicos.listarParceirosDoAcompanhamento(acompanhamento.id) : [],
      ])
      return { lista, parceiros }
    }
    const [lista, solicitacoes] = await Promise.all([
      servicos.obterPagina(`${base}/documents`, { ...parametros, categoria: categoria || undefined }),
      servicos.listarSolicitacoes(acompanhamento.id, { status: 'pendente' }),
    ])
    return { lista, solicitacoes }
  }, undefined, [pagina, tipos.join(','), recentes, categoria])
  useEffect(() => { if (dados?.lista) setPagina(dados.lista.pagina) }, [dados?.lista?.pagina])

  const atualizarTudo = async () => { await Promise.all([atualizar(), atualizarCabecalho()]) }
  const propriedades = { ...contexto, atualizar: atualizarTudo }
  function mudarFiltro(acao, valor) { acao(valor); setPagina(1) }

  return (
    <>
      <ErroCarregamento erro={erro} />
      {erro && !dados && <button type="button" className={ui.botaoSecundario} onClick={atualizar}>Tentar novamente</button>}
      {carregando && !dados && <Carregando texto="Carregando esta seção…" />}
      {dados && <>
        {aba === 'anamnese' && <AbaAnamnese anamnese={dados.anamnese} {...propriedades} />}
        {aba === 'parceiros' && <AbaParceiros parceiros={dados.parceiros} {...propriedades} />}
        {aba === 'linha' && <AbaLinhaDoTempo eventos={dados.lista.itens} filtro={tipos} setFiltro={(valor) => mudarFiltro(setTipos, valor)} recentesPrimeiro={recentes} setRecentesPrimeiro={(valor) => mudarFiltro(setRecentes, valor)} {...propriedades} />}
        {aba === 'consultas' && <AbaConsultas consultas={dados.lista.itens} {...propriedades} />}
        {aba === 'solicitacoes' && <AbaSolicitacoes solicitacoes={dados.lista.itens} parceiros={dados.parceiros} {...propriedades} />}
        {aba === 'documentos' && <AbaDocumentos documentos={dados.lista.itens} solicitacoes={dados.solicitacoes} solicitacaoInicial={solicitacaoInicial} filtro={categoria} setFiltro={(valor) => mudarFiltro(setCategoria, valor)} {...propriedades} />}
      </>}
      <Paginacao dados={dados?.lista} aoMudar={setPagina} carregando={carregando} />
    </>
  )
}
