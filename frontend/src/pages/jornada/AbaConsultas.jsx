import { Plus, Stethoscope } from 'lucide-react'
import { useState } from 'react'

import { mensagemDeErro } from '../../api/cliente'
import { registrarConsulta } from '../../api/servicos'
import { Alerta, EstadoVazio, Etiqueta, estilos as ui } from '../../components/ui'
import {
  ROTULOS_TIPO_CONSULTA,
  campoDataHoraParaIso,
  formatarDataHora,
  paraCampoDataHora,
} from '../../utils/formatacao'
import estilos from './Jornada.module.css'

const prescricaoVazia = () => ({ descricao: '', dosagem: '', instrucoes: '' })

export default function AbaConsultas({ consultas, jornada, ehMedico, editavel, atualizar }) {
  const [formularioAberto, setFormularioAberto] = useState(false)

  return (
    <div className={estilos.pilha}>
      <div className={ui.cartaoCabecalho} style={{ marginBottom: 0 }}>
        <h2>Consultas e retornos</h2>
        {ehMedico && editavel && !formularioAberto && (
          <button type="button" className={ui.botao} onClick={() => setFormularioAberto(true)}>
            <Plus size={16} aria-hidden="true" />
            Registrar consulta
          </button>
        )}
      </div>

      {formularioAberto && (
        <FormularioConsulta
          jornadaId={jornada.id}
          aoConcluir={async () => {
            setFormularioAberto(false)
            await atualizar()
          }}
          aoCancelar={() => setFormularioAberto(false)}
        />
      )}

      {consultas.length === 0 ? (
        <EstadoVazio icone={Stethoscope}>Nenhuma consulta registrada.</EstadoVazio>
      ) : (
        <ul className={ui.lista}>
          {consultas.map((consulta) => (
            <li key={consulta.id} className={ui.itemLista}>
              <div className={ui.cabecalhoItem}>
                <strong>{formatarDataHora(consulta.data)}</strong>
                <Etiqueta variante={consulta.tipo === 'retorno' ? 'info' : 'primaria'}>
                  {ROTULOS_TIPO_CONSULTA[consulta.tipo]}
                </Etiqueta>
              </div>
              {consulta.anotacoes && <p className={estilos.texto}>{consulta.anotacoes}</p>}
              {consulta.prescricoes.length > 0 && (
                <div className={estilos.prescricoes}>
                  <h3>Prescrições</h3>
                  <ul>
                    {consulta.prescricoes.map((p) => (
                      <li key={p.id}>
                        <strong>{p.descricao}</strong>
                        {p.dosagem && <span> · {p.dosagem}</span>}
                        {p.instrucoes && <div className={ui.ajuda}>{p.instrucoes}</div>}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function FormularioConsulta({ jornadaId, aoConcluir, aoCancelar }) {
  const [tipo, setTipo] = useState('consulta')
  const [data, setData] = useState(() => paraCampoDataHora(new Date()))
  const [anotacoes, setAnotacoes] = useState('')
  const [prescricoes, setPrescricoes] = useState([])
  const [erro, setErro] = useState('')
  const [enviando, setEnviando] = useState(false)

  const alterarPrescricao = (indice, campo, valor) =>
    setPrescricoes((atuais) => atuais.map((p, i) => (i === indice ? { ...p, [campo]: valor } : p)))

  async function aoEnviar(evento) {
    evento.preventDefault()
    setErro('')
    setEnviando(true)
    try {
      await registrarConsulta(jornadaId, {
        tipo,
        data: campoDataHoraParaIso(data),
        anotacoes: anotacoes.trim() || null,
        prescricoes: prescricoes
          .filter((p) => p.descricao.trim())
          .map((p) => ({
            descricao: p.descricao.trim(),
            dosagem: p.dosagem.trim() || null,
            instrucoes: p.instrucoes.trim() || null,
          })),
      })
      await aoConcluir()
    } catch (erroEnvio) {
      setErro(mensagemDeErro(erroEnvio))
      setEnviando(false)
    }
  }

  return (
    <form className={`${ui.formulario} ${estilos.formularioDestaque}`} onSubmit={aoEnviar}>
      <h3>Nova consulta</h3>
      <Alerta tipo="erro">{erro}</Alerta>
      <div className={ui.linhaCampos}>
        <div>
          <label htmlFor="consulta-tipo">Tipo</label>
          <select id="consulta-tipo" value={tipo} onChange={(e) => setTipo(e.target.value)}>
            <option value="consulta">Consulta</option>
            <option value="retorno">Retorno</option>
          </select>
        </div>
        <div>
          <label htmlFor="consulta-data">Data e hora</label>
          <input id="consulta-data" type="datetime-local" value={data} onChange={(e) => setData(e.target.value)} required />
        </div>
      </div>
      <div>
        <label htmlFor="consulta-anotacoes">Anotações</label>
        <textarea
          id="consulta-anotacoes"
          value={anotacoes}
          onChange={(e) => setAnotacoes(e.target.value)}
          placeholder="Queixas, exame físico, conduta…"
        />
      </div>

      <fieldset className={estilos.grupoPrescricoes}>
        <legend>Prescrições</legend>
        {prescricoes.length === 0 && <p className={ui.ajuda}>Nenhuma prescrição adicionada.</p>}
        {prescricoes.map((prescricao, indice) => (
          <div key={indice} className={estilos.linhaPrescricao}>
            <div>
              <label htmlFor={`presc-desc-${indice}`}>Medicamento / orientação</label>
              <input
                id={`presc-desc-${indice}`}
                value={prescricao.descricao}
                onChange={(e) => alterarPrescricao(indice, 'descricao', e.target.value)}
                required
                minLength={2}
              />
            </div>
            <div>
              <label htmlFor={`presc-dose-${indice}`}>Dosagem</label>
              <input
                id={`presc-dose-${indice}`}
                value={prescricao.dosagem}
                onChange={(e) => alterarPrescricao(indice, 'dosagem', e.target.value)}
              />
            </div>
            <div>
              <label htmlFor={`presc-inst-${indice}`}>Instruções</label>
              <input
                id={`presc-inst-${indice}`}
                value={prescricao.instrucoes}
                onChange={(e) => alterarPrescricao(indice, 'instrucoes', e.target.value)}
              />
            </div>
            <button
              type="button"
              className={`${ui.botaoPerigo} ${ui.botaoPequeno}`}
              onClick={() => setPrescricoes((atuais) => atuais.filter((_, i) => i !== indice))}
              aria-label={`Remover prescrição ${indice + 1}`}
            >
              Remover
            </button>
          </div>
        ))}
        <button
          type="button"
          className={`${ui.botaoSecundario} ${ui.botaoPequeno}`}
          onClick={() => setPrescricoes((atuais) => [...atuais, prescricaoVazia()])}
        >
          <Plus size={14} aria-hidden="true" />
          Adicionar prescrição
        </button>
      </fieldset>

      <div className={ui.acoes}>
        <button type="submit" className={ui.botao} disabled={enviando}>
          {enviando ? 'Salvando…' : 'Salvar consulta'}
        </button>
        <button type="button" className={ui.botaoSecundario} onClick={aoCancelar} disabled={enviando}>
          Cancelar
        </button>
      </div>
    </form>
  )
}
