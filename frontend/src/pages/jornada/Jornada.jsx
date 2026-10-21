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

export default function Jornada() {
  const { id } = useParams()
  const { usuario, ehMedico, ehParceiro } = useAuth()
  const [parametros, setParametros] = useSearchParams()

  const abas = ehParceiro ? ABAS_PARCEIRO : ABAS
  const abaAtual = abas.some((aba) => aba.id === parametros.get('aba')) ? parametros.get('aba') : abas[0].id

  const { dados: jornada, erro, carregando, atualizar } = useAtualizacaoPeriodica(
    () => servicos.obterJornada(id), undefined, [id],
  )
  const { dados: contagens, atualizar: atualizarResumo } = useAtualizacaoPeriodica(
    () => servicos.obterResumoJornada(id), undefined, [id],
  )

  /** Troca de aba mantendo o histórico do navegador; `extras` vira parâmetro da URL. */
  function irParaAba(aba, extras = {}) {
    setParametros({ aba, ...extras })
  }

  if (carregando && !jornada) return <Carregando texto="Carregando a jornada…" />

  if (!jornada) {
    const status = erro?.response?.status
    return (
      <div className={estilos.pilha}>
        <Alerta tipo="erro">
          {status === 404 || status === 403
            ? mensagemDeErro(erro)
            : mensagemDeErro(erro, 'Não foi possível carregar a jornada.')}
        </Alerta>
        <p>
          <button type="button" className={ui.botaoSecundario} onClick={atualizar}>Tentar novamente</button>{' '}
          <Link to="/jornadas">Voltar</Link>
        </p>
      </div>
    )
  }

  const editavel = jornada.status === 'ativa'
  const contexto = { jornada, usuario, ehMedico, ehParceiro, editavel, atualizar: async () => { await Promise.all([atualizar(), atualizarResumo()]) }, irParaAba }

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
  const { jornada, ehMedico, atualizar: atualizarCabecalho } = contexto
  const [pagina, setPagina] = useState(1)
  const [tipos, setTipos] = useState([])
  const [recentes, setRecentes] = useState(false)
  const [categoria, setCategoria] = useState('')
  const base = `/journeys/${jornada.id}`
  const { dados, erro, carregando, atualizar } = useAtualizacaoPeriodica(async () => {
    const parametros = { pagina }
    if (aba === 'ficha') return { ficha: await servicos.obterFicha(jornada.id) }
    if (aba === 'parceiros') return { parceiros: await servicos.listarParceirosDaJornada(jornada.id) }
    if (aba === 'linha') return { lista: await servicos.obterPagina(`${base}/timeline`, { ...parametros, tipos: tipos.length ? tipos.join(',') : undefined, recentes }) }
    if (aba === 'consultas') return { lista: await servicos.obterPagina(`${base}/consultations`, parametros) }
    if (aba === 'solicitacoes') {
      const [lista, parceiros] = await Promise.all([
        servicos.obterPagina(`${base}/requests`, parametros),
        ehMedico ? servicos.listarParceirosDaJornada(jornada.id) : [],
      ])
      return { lista, parceiros }
    }
    const [lista, solicitacoes] = await Promise.all([
      servicos.obterPagina(`${base}/documents`, { ...parametros, categoria: categoria || undefined }),
      servicos.listarSolicitacoes(jornada.id, { status: 'pendente' }),
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
        {aba === 'ficha' && <AbaFicha ficha={dados.ficha} {...propriedades} />}
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
