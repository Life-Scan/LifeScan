import { Plus, Route } from 'lucide-react'
import { Link } from 'react-router-dom'

import { listarAcompanhamentos } from '../api/servicos'
import { Avatar, Carregando, ErroCarregamento, EstadoVazio, Etiqueta, estilos as ui } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useAtualizacaoPeriodica } from '../hooks/useAtualizacaoPeriodica'
import { ROTULOS_PASSO, formatarData } from '../utils/formatacao'
import estilos from './Paginas.module.css'

export default function Acompanhamentos() {
  const { ehMedico, ehParceiro } = useAuth()
  const { dados: acompanhamentos, erro, carregando } = useAtualizacaoPeriodica(listarAcompanhamentos)

  return (
    <div className={estilos.pilha}>
      <div className={estilos.cabecalho}>
        <div>
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
      {carregando && !acompanhamentos && <Carregando />}
      {acompanhamentos?.length === 0 && (
        <EstadoVazio icone={Route}>
          {ehMedico ? (
            <>
              Nenhum acompanhamento aberto. Cadastre um paciente em <Link to="/usuarios">Pacientes e parceiros</Link> e abra a
              acompanhamento dele.
            </>
          ) : ehParceiro ? (
            'Nenhum paciente atribuído a você no momento.'
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
                  {acompanhamento.status === 'encerrado' && <Etiqueta>Encerrado</Etiqueta>}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
