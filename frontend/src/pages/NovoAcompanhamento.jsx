import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { mensagemDeErro } from '../api/cliente'
import { criarAcompanhamento, listarContas } from '../api/servicos'
import { ArrowLeft, UserPlus, Users } from 'lucide-react'

import { Alerta, EsqueletoFormulario, EstadoVazio, Faixa, estilos as ui } from '../components/ui'
import { estilos } from './estilosPaginas'

export default function NovoAcompanhamento() {
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
    listarContas('paciente')
      // Cada paciente tem um único acompanhamento: só aparecem contas ativas ainda sem acompanhamento.
      // Não importa se o paciente já acessou o sistema.
      .then((contas) => setDisponiveis(contas.filter((conta) => conta.ativo && !conta.acompanhamento_id)))
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
      const acompanhamento = await criarAcompanhamento({
        paciente_id: Number(formulario.pacienteId),
        titulo: formulario.titulo,
        descricao: formulario.descricao.trim() || null,
      })
      navegar(`/acompanhamentos/${acompanhamento.id}`, { replace: true })
    } catch (erroCriacao) {
      setErro(mensagemDeErro(erroCriacao))
      setEnviando(false)
    }
  }

  return (
    <div className={estilos.pilha}>
      <Faixa como="header" aria-labelledby="titulo-novo-acompanhamento">
        <div className={estilos.faixaTopo}>
          <div>
            {/* O sobretítulo é a área de cima: leva de volta à lista, como no acompanhamento */}
            <Link to="/acompanhamentos" className={ui.sobretituloFaixaLink}>
              <ArrowLeft size={13} aria-hidden="true" />
              Acompanhamentos
            </Link>
            <h1 id="titulo-novo-acompanhamento" className={estilos.tituloFaixa}>
              Novo acompanhamento
            </h1>
            <p className={estilos.subtituloFaixa}>Abra o acompanhamento de tratamento de um paciente cadastrado.</p>
          </div>
        </div>
      </Faixa>

      <section className={ui.cartao} style={{ maxWidth: 640 }}>
        {disponiveis === null && <EsqueletoFormulario texto="Carregando pacientes…" />}
        {disponiveis?.length === 0 && !erro && (
          <EstadoVazio
            icone={Users}
            titulo="Nenhum paciente disponível"
            acao={
              <Link to="/painel" className={ui.botao}>
                <UserPlus size={16} aria-hidden="true" />
                Cadastrar paciente no Painel
              </Link>
            }
          >
            Todos os seus pacientes já têm acompanhamento, ou você ainda não cadastrou nenhum.
          </EstadoVazio>
        )}
        {disponiveis?.length > 0 && (
          <form className={ui.formulario} onSubmit={aoEnviar}>
            <Alerta tipo="erro">{erro}</Alerta>
            <div>
              <label htmlFor="paciente">Paciente</label>
              <select id="paciente" value={formulario.pacienteId} onChange={alterar('pacienteId')} required>
                <option value="">Selecione…</option>
                {disponiveis.map((paciente) => (
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
                {enviando ? 'Abrindo…' : 'Abrir acompanhamento'}
              </button>
              <Link to="/acompanhamentos" className={ui.botaoSecundario}>
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
