import { Link } from 'react-router-dom'

import { listarJornadas } from '../api/servicos'
import { Carregando, ErroCarregamento, EstadoVazio, Etiqueta, estilos as ui } from '../components/ui'
import { useAuth } from '../context/AuthContext'
import { useAtualizacaoPeriodica } from '../hooks/useAtualizacaoPeriodica'
import { ROTULOS_PASSO, formatarData } from '../utils/formatacao'
import estilos from './Paginas.module.css'

export default function Jornadas() {
  const { ehMedico, ehParceiro } = useAuth()
  const { dados: jornadas, erro, carregando } = useAtualizacaoPeriodica(listarJornadas)

  return (
    <div className={estilos.pilha}>
      <div className={estilos.cabecalho}>
        <div>
          <h1>{ehMedico ? 'Jornadas' : ehParceiro ? 'Pacientes' : 'Minha jornada'}</h1>
          <p className={estilos.subtitulo}>
            {ehMedico
              ? 'Acompanhe o tratamento de cada paciente.'
              : ehParceiro
                ? 'Pacientes em cujo tratamento o médico incluiu você.'
                : 'O acompanhamento do seu tratamento com o seu médico.'}
          </p>
        </div>
        {ehMedico && (
          <Link to="/jornadas/nova" className={ui.botao}>
            Nova jornada
          </Link>
        )}
      </div>

      <ErroCarregamento erro={erro} />
      {carregando && !jornadas && <Carregando />}
      {jornadas?.length === 0 && (
        <EstadoVazio>
          {ehMedico ? (
            <>
              Nenhuma jornada aberta. Cadastre um paciente em <Link to="/pacientes">Pacientes</Link> e abra a
              jornada dele.
            </>
          ) : ehParceiro ? (
            'Nenhum paciente atribuído a você no momento.'
          ) : (
            'Seu médico ainda não abriu uma jornada para você.'
          )}
        </EstadoVazio>
      )}
      {jornadas?.length > 0 && (
        <ul className={ui.lista}>
          {jornadas.map((jornada) => (
            <li key={jornada.id} className={ui.itemLista}>
              <div className={ui.cabecalhoItem}>
                <div>
                  <Link to={`/jornadas/${jornada.id}`} className={estilos.linkItem}>
                    {ehParceiro ? jornada.paciente.nome : jornada.titulo}
                  </Link>
                  <div className={estilos.meta}>
                    {ehParceiro && <span>{jornada.titulo}</span>}
                    <span>{ehMedico ? `Paciente: ${jornada.paciente.nome}` : `Médico(a): ${jornada.medico.nome}`}</span>
                    <span>Aberta em {formatarData(jornada.criado_em)}</span>
                    <span>Atualizada em {formatarData(jornada.atualizado_em)}</span>
                  </div>
                </div>
                <div className={ui.acoes}>
                  <Etiqueta variante="primaria">Passo: {ROTULOS_PASSO[jornada.passo_atual]}</Etiqueta>
                  {jornada.status === 'encerrada' && <Etiqueta>Encerrada</Etiqueta>}
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
