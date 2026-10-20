import { Handshake, UserPlus, UserX } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { mensagemDeErro } from '../../api/cliente'
import { atribuirParceiro, listarContas, removerParceiro } from '../../api/servicos'
import { useConfirmar } from '../../components/Confirmacao'
import { Alerta, Avatar, EstadoVazio, estilos as ui } from '../../components/ui'
import { formatarData } from '../../utils/formatacao'
import estilos from './Jornada.module.css'

export default function AbaParceiros({ parceiros, jornada, ehMedico, editavel, atualizar }) {
  const confirmar = useConfirmar()
  const [erro, setErro] = useState('')

  async function remover({ parceiro }) {
    const confirmado = await confirmar({
      titulo: `Remover ${parceiro.nome} desta jornada?`,
      mensagem: 'O acesso à ficha do paciente é retirado. Os documentos que já foram enviados permanecem.',
      rotuloConfirmar: 'Remover parceiro',
      perigo: true,
    })
    if (!confirmado) return
    setErro('')
    try {
      await removerParceiro(jornada.id, parceiro.id)
      await atualizar()
    } catch (erroRemocao) {
      setErro(mensagemDeErro(erroRemocao))
    }
  }

  return (
    <div className={estilos.pilha}>
      <div>
        <h2>Parceiros</h2>
        <p className={ui.ajuda}>
          Profissionais que colaboram neste tratamento. Eles veem a ficha do paciente e enviam documentos da sua
          área; não têm acesso a consultas, prescrições ou exames.
        </p>
      </div>

      {ehMedico && editavel && (
        <FormularioAtribuicao jornadaId={jornada.id} atribuidos={parceiros} aoAtribuir={atualizar} />
      )}

      <Alerta tipo="erro">{erro}</Alerta>

      {parceiros.length === 0 ? (
        <EstadoVazio icone={Handshake}>Nenhum parceiro atribuído a esta jornada.</EstadoVazio>
      ) : (
        <ul className={ui.lista}>
          {parceiros.map((atribuicao) => (
            <li key={atribuicao.id} className={ui.itemLista}>
              <div className={ui.linhaComAcoes}>
                <div className={ui.pessoa}>
                  <Avatar nome={atribuicao.parceiro.nome} tipo="parceiro" />
                  <div>
                    <strong>{atribuicao.parceiro.nome}</strong>
                    <div className={estilos.meta}>
                      <span>{atribuicao.parceiro.profissao}</span>
                      <span>{atribuicao.parceiro.email}</span>
                      <span>Desde {formatarData(atribuicao.criado_em)}</span>
                    </div>
                  </div>
                </div>
                {ehMedico && (
                  <button
                    type="button"
                    className={`${ui.botaoPerigo} ${ui.botaoPequeno}`}
                    onClick={() => remover(atribuicao)}
                  >
                    <UserX size={14} aria-hidden="true" />
                    Remover
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function FormularioAtribuicao({ jornadaId, atribuidos, aoAtribuir }) {
  const [contas, setContas] = useState(null)
  const [parceiroId, setParceiroId] = useState('')
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  useEffect(() => {
    listarContas('parceiro')
      .then(setContas)
      .catch((erroLista) => {
        setErro(mensagemDeErro(erroLista))
        setContas([])
      })
  }, [])

  if (contas === null) return null

  const idsAtribuidos = new Set(atribuidos.map((a) => a.parceiro.id))
  const disponiveis = contas.filter((conta) => conta.ativo && !idsAtribuidos.has(conta.id))

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await atribuirParceiro(jornadaId, Number(parceiroId))
      setParceiroId('')
      await aoAtribuir()
    } catch (erroAtribuicao) {
      setErro(mensagemDeErro(erroAtribuicao))
    } finally {
      setEnviando(false)
    }
  }

  if (disponiveis.length === 0) {
    return (
      <div className={estilos.pilha}>
        <p className={ui.ajuda}>
          {contas.length === 0
            ? 'Você ainda não cadastrou parceiros. '
            : 'Todos os parceiros ativos já estão nesta jornada. '}
          <Link to="/usuarios">Cadastrar parceiro</Link>
        </p>
        <Alerta tipo="erro">{erro}</Alerta>
      </div>
    )
  }

  return (
    <form className={`${ui.formulario} ${estilos.formularioDestaque}`} onSubmit={aoEnviar}>
      <Alerta tipo="erro">{erro}</Alerta>
      <div className={ui.acoes} style={{ alignItems: 'flex-end' }}>
        <div style={{ flex: '1 1 260px' }}>
          <label htmlFor="atribuir-parceiro">Atribuir parceiro</label>
          <select id="atribuir-parceiro" value={parceiroId} onChange={(e) => setParceiroId(e.target.value)} required>
            <option value="">Selecione…</option>
            {disponiveis.map((conta) => (
              <option key={conta.id} value={conta.id}>
                {conta.nome} ({conta.profissao})
              </option>
            ))}
          </select>
        </div>
        <button type="submit" className={ui.botao} disabled={enviando || !parceiroId}>
          <UserPlus size={16} aria-hidden="true" />
          {enviando ? 'Atribuindo…' : 'Atribuir'}
        </button>
      </div>
    </form>
  )
}
