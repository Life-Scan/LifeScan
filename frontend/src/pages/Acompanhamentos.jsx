import { Plus, Route } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'

import { obterPagina } from '../api/servicos'
import Paginacao from '../components/Paginacao'
import { Avatar, ErroCarregamento, EsqueletoLista, EstadoVazio, Etiqueta, estilos as ui } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useAtualizacaoPeriodica } from '../hooks/useAtualizacaoPeriodica'
import { ROTULOS_PASSO, formatarData } from '../utils/formatacao'
import { estilos } from './estilosPaginas'

export default function Acompanhamentos() {
  const { ehMedico, ehParceiro } = useAuth()
  const [pagina, setPagina] = useState(1)
  const { dados, erro, carregando } = useAtualizacaoPeriodica(() => obterPagina('/follow-ups', { pagina }), undefined, [pagina])
  const acompanhamentos = dados?.itens
  useEffect(() => { if (dados) setPagina(dados.pagina) }, [dados?.pagina])

  return (
    <div className={estilos.pilha}>
      <div className={estilos.cabecalho}>
        <div>
          <p className={ui.sobretitulo}>Cuidado</p>
          <h1>{ehMedico ? 'Acompanhamentos' : ehParceiro ? 'Pacientes' : 'Meu acompanhamento'}</h1>
          <p className={estilos.subtitulo}>
            {ehMedico
              ? 'Acompanhe o tratamento de cada paciente.'
              : ehParceiro
                ? 'Pacientes em cujo tratamento o médico incluiu você.'
                : 'O acompanhamento do seu tratamento com o seu médico.'}
          </p>
        </div>
        {ehMedico && (
          <Link to="/acompanhamentos/novo" className={ui.botao}>
            <Plus size={16} aria-hidden="true" />
            Novo acompanhamento
          </Link>
        )}
      </div>

      <ErroCarregamento erro={erro} />
      {carregando && !acompanhamentos && <EsqueletoLista avatar texto="Carregando acompanhamentos…" />}
      {acompanhamentos?.length === 0 && (
        <EstadoVazio
          icone={Route}
          titulo={ehMedico ? 'Nenhum acompanhamento aberto' : ehParceiro ? 'Nenhum paciente atribuído' : 'Nenhum acompanhamento ainda'}
        >
          {ehMedico ? (
            <>
              Cadastre um paciente no <Link to="/painel">Painel</Link> e abra o acompanhamento dele em &quot;Novo
              acompanhamento&quot;.
            </>
          ) : ehParceiro ? (
            'Quando um médico atribuir você a um tratamento, o paciente aparece aqui.'
          ) : (
            'Seu médico ainda não abriu um acompanhamento para você.'
          )}
        </EstadoVazio>
      )}
      {acompanhamentos?.length > 0 && (
        <ul className={ui.lista}>
          {acompanhamentos.map((acompanhamento) => (
            <li key={acompanhamento.id} className={ui.itemLista}>
              <div className={ui.cabecalhoItem}>
                <div className={ui.pessoa}>
                  <Avatar nome={acompanhamento.paciente.nome} />
                  <div>
                    <Link to={`/acompanhamentos/${acompanhamento.id}`} className={estilos.linkItem}>
                      {ehParceiro ? acompanhamento.paciente.nome : acompanhamento.titulo}
                    </Link>
                    <div className={estilos.meta}>
                      {ehParceiro && <span>{acompanhamento.titulo}</span>}
                      <span>{ehMedico ? acompanhamento.paciente.nome : `Médico(a): ${acompanhamento.medico.nome}`}</span>
                      <span>Aberto em {formatarData(acompanhamento.criado_em)}</span>
                      <span>Atualizado em {formatarData(acompanhamento.atualizado_em)}</span>
                    </div>
                  </div>
                </div>
                <div className={ui.acoes}>
                  <Etiqueta variante="primaria">Passo: {ROTULOS_PASSO[acompanhamento.passo_atual]}</Etiqueta>
                  {acompanhamento.status === 'encerrada' && <Etiqueta>Encerrada</Etiqueta>}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
      <Paginacao dados={dados} aoMudar={setPagina} carregando={carregando} />
    </div>
  )
}
