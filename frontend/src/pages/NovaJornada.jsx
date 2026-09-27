import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { criarJornada, listarVinculos } from '../api/servicos'
import { Alerta, Carregando, EstadoVazio, estilos as ui } from '../components/ui'
import estilos from './Paginas.module.css'

export default function NovaJornada() {
  const navegar = useNavigate()
  const [parametros] = useSearchParams()

  const [disponiveis, setDisponiveis] = useState(null)
  const [formulario, setFormulario] = useState({
    pacienteId: parametros.get('paciente') || '',
    titulo: '',
    descricao: '',
  })
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    listarVinculos()
      // Cada paciente tem uma única jornada: só aparecem vínculos ativos ainda sem jornada
      .then((vinculos) => setDisponiveis(vinculos.filter((v) => v.ativo && !v.jornada_id)))
      .catch((erroLista) => {
        setErro(mensagemDeErro(erroLista))
        setDisponiveis([])
      })
  }, [])

  const alterar = (campo) => (evento) => setFormulario((atual) => ({ ...atual, [campo]: evento.target.value }))

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      const jornada = await criarJornada({
        paciente_id: Number(formulario.pacienteId),
        titulo: formulario.titulo,
        descricao: formulario.descricao.trim() || null,
      })
      navegar(`/jornadas/${jornada.id}`, { replace: true })
    } catch (erroCriacao) {
      setErro(mensagemDeErro(erroCriacao))
      setEnviando(false)
    }
  }

  return (
    <div className={estilos.pilha}>
      <div className={estilos.cabecalho}>
        <div>
          <h1>Nova jornada</h1>
          <p className={estilos.subtitulo}>Abra a jornada de tratamento de um paciente vinculado a você.</p>
        </div>
      </div>

      <section className={ui.cartao} style={{ maxWidth: 640 }}>
        {disponiveis === null && <Carregando />}
        {disponiveis?.length === 0 && !erro && (
          <EstadoVazio>
            Todos os seus pacientes já têm jornada, ou você ainda não vinculou nenhum.{' '}
            <Link to="/pacientes">Vincular paciente</Link>
          </EstadoVazio>
        )}
        {disponiveis?.length > 0 && (
          <form className={ui.formulario} onSubmit={aoEnviar}>
            <Alerta tipo="erro">{erro}</Alerta>
            <div>
              <label htmlFor="paciente">Paciente</label>
              <select id="paciente" value={formulario.pacienteId} onChange={alterar('pacienteId')} required>
                <option value="">Selecione…</option>
                {disponiveis.map(({ paciente }) => (
                  <option key={paciente.id} value={paciente.id}>
                    {paciente.nome} ({paciente.email})
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="titulo">Título</label>
              <input
                id="titulo"
                placeholder="Ex.: Controle da hipertensão"
                value={formulario.titulo}
                onChange={alterar('titulo')}
                required
                minLength={3}
                maxLength={150}
              />
            </div>
            <div>
              <label htmlFor="descricao">Descrição (opcional)</label>
              <textarea id="descricao" value={formulario.descricao} onChange={alterar('descricao')} />
            </div>
            <div className={ui.acoes}>
              <button type="submit" className={ui.botao} disabled={enviando}>
                {enviando ? 'Abrindo…' : 'Abrir jornada'}
              </button>
              <Link to="/jornadas" className={ui.botaoSecundario}>
                Cancelar
              </Link>
            </div>
          </form>
        )}
        {disponiveis?.length === 0 && <Alerta tipo="erro">{erro}</Alerta>}
      </section>
    </div>
  )
}
