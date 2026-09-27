import { useState } from 'react'
import { Link } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { alterarVinculo, buscarPaciente, criarVinculo, listarVinculos } from '../api/servicos'
import { Alerta, Carregando, ErroCarregamento, EstadoVazio, Etiqueta, estilos as ui } from '../components/ui'
import { useAtualizacaoPeriodica } from '../hooks/useAtualizacaoPeriodica'
import { formatarData } from '../utils/formatacao'
import estilos from './Paginas.module.css'

export default function Pacientes() {
  const { dados: vinculos, erro, carregando, atualizar } = useAtualizacaoPeriodica(listarVinculos)

  return (
    <div className={estilos.pilha}>
      <div className={estilos.cabecalho}>
        <div>
          <h1>Meus pacientes</h1>
          <p className={estilos.subtitulo}>Busque pacientes cadastrados pelo email e vincule-os a você.</p>
        </div>
      </div>

      <BuscaPaciente aoVincular={atualizar} />

      <section className={ui.cartao}>
        <div className={ui.cartaoCabecalho}>
          <h2>Pacientes vinculados</h2>
        </div>
        <ErroCarregamento erro={erro} />
        {carregando && !vinculos && <Carregando />}
        {vinculos?.length === 0 && <EstadoVazio>Você ainda não tem pacientes vinculados.</EstadoVazio>}
        {vinculos?.length > 0 && (
          <ul className={ui.lista}>
            {vinculos.map((vinculo) => (
              <ItemVinculo key={vinculo.id} vinculo={vinculo} aoAlterar={atualizar} />
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

function BuscaPaciente({ aoVincular }) {
  const [email, setEmail] = useState('')
  const [resultado, setResultado] = useState(null)
  const [erro, setErro] = useState('')
  const [sucesso, setSucesso] = useState('')
  const [ocupado, setOcupado] = useState(false)

  async function aoBuscar(evento) {
    evento.preventDefault()
    setErro('')
    setSucesso('')
    setResultado(null)
    setOcupado(true)
    try {
      setResultado(await buscarPaciente(email))
    } catch (erroBusca) {
      setErro(mensagemDeErro(erroBusca))
    } finally {
      setOcupado(false)
    }
  }

  async function aoVincularPaciente() {
    setErro('')
    setOcupado(true)
    try {
      await criarVinculo(resultado.id)
      setSucesso(`${resultado.nome} foi vinculado(a) a você.`)
      setResultado(null)
      setEmail('')
      aoVincular()
    } catch (erroVinculo) {
      setErro(mensagemDeErro(erroVinculo))
    } finally {
      setOcupado(false)
    }
  }

  return (
    <section className={ui.cartao}>
      <div className={ui.cartaoCabecalho}>
        <h2>Vincular paciente</h2>
      </div>
      <form className={ui.formulario} onSubmit={aoBuscar}>
        <div className={ui.acoes}>
          <div style={{ flex: '1 1 260px' }}>
            <label htmlFor="busca-email" className="visualmente-oculto">
              Email do paciente
            </label>
            <input
              id="busca-email"
              type="email"
              placeholder="email@paciente.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <button type="submit" className={ui.botao} disabled={ocupado}>
            Buscar
          </button>
        </div>
        <Alerta tipo="erro">{erro}</Alerta>
        <Alerta tipo="sucesso">{sucesso}</Alerta>
      </form>

      {resultado && (
        <div className={ui.itemLista} style={{ marginTop: '1rem' }}>
          <div className={ui.cabecalhoItem}>
            <div>
              <strong>{resultado.nome}</strong>
              <div className={estilos.meta}>{resultado.email}</div>
            </div>
            {resultado.vinculado_a_mim && <Etiqueta variante="sucesso">Já vinculado a você</Etiqueta>}
            {resultado.vinculado_a_outro_medico && (
              <Etiqueta variante="alerta">Já acompanhado por outro médico</Etiqueta>
            )}
            {!resultado.vinculado_a_mim && !resultado.vinculado_a_outro_medico && (
              <button type="button" className={ui.botao} onClick={aoVincularPaciente} disabled={ocupado}>
                Vincular
              </button>
            )}
          </div>
        </div>
      )}
    </section>
  )
}

function ItemVinculo({ vinculo, aoAlterar }) {
  const [erro, setErro] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const { paciente, ativo, jornada_id: jornadaId } = vinculo

  async function alternarAtivo() {
    const mensagem = ativo
      ? `Desativar o vínculo com ${paciente.nome}? A jornada ficará inacessível até você reativar.`
      : `Reativar o vínculo com ${paciente.nome}?`
    if (!window.confirm(mensagem)) return
    setErro('')
    setOcupado(true)
    try {
      await alterarVinculo(vinculo.id, !ativo)
      await aoAlterar()
    } catch (erroAlteracao) {
      setErro(mensagemDeErro(erroAlteracao))
    } finally {
      setOcupado(false)
    }
  }

  return (
    <li className={ui.itemLista}>
      <div className={ui.cabecalhoItem}>
        <div>
          <strong>{paciente.nome}</strong> {!ativo && <Etiqueta>Vínculo inativo</Etiqueta>}
          <div className={estilos.meta}>
            <span>{paciente.email}</span>
            <span>Vinculado em {formatarData(vinculo.criado_em)}</span>
          </div>
        </div>
        <div className={ui.acoes}>
          {ativo && jornadaId && (
            <Link to={`/jornadas/${jornadaId}`} className={`${ui.botao} ${ui.botaoPequeno}`}>
              Abrir jornada
            </Link>
          )}
          {ativo && !jornadaId && (
            <Link to={`/jornadas/nova?paciente=${paciente.id}`} className={`${ui.botaoSecundario} ${ui.botaoPequeno}`}>
              Abrir nova jornada
            </Link>
          )}
          <button
            type="button"
            className={`${ativo ? ui.botaoPerigo : ui.botaoSecundario} ${ui.botaoPequeno}`}
            onClick={alternarAtivo}
            disabled={ocupado}
          >
            {ativo ? 'Desativar vínculo' : 'Reativar vínculo'}
          </button>
        </div>
      </div>
      <Alerta tipo="erro">{erro}</Alerta>
    </li>
  )
}
