/** Campos de formulário com máscaras automáticas e validação consistente. */
import { useEffect, useRef, useState } from 'react'

import {
  dataBrParaIso,
  dataHoraBrParaIso,
  dataHoraIsoParaBr,
  dataIsoParaBr,
  mascaraData,
  mascaraDataHora,
  mascaraEmail,
  mascaraTelefone,
} from '../utils/mascaras'

function validarLimites(iso, min, max, formatarLimite) {
  if (!iso) return ''
  if (min && iso < min) return `Informe uma data a partir de ${formatarLimite(min)}.`
  if (max && iso > max) return `Informe uma data até ${formatarLimite(max)}.`
  return ''
}

function CampoTemporal({
  value,
  onChange,
  min,
  max,
  mascara,
  isoParaBr,
  brParaIso,
  mensagemInvalida,
  placeholder,
  maxLength,
  ...props
}) {
  const entrada = useRef(null)
  const valorAtual = value || ''
  const [rascunho, setRascunho] = useState(() => ({
    texto: isoParaBr(valorAtual),
    valorBase: valorAtual,
  }))

  const texto =
    rascunho.valorBase === valorAtual || (!valorAtual && !brParaIso(rascunho.texto))
      ? rascunho.texto
      : isoParaBr(valorAtual)

  useEffect(() => {
    if (!entrada.current) return
    if (!texto) {
      entrada.current.setCustomValidity('')
      return
    }
    const iso = brParaIso(texto)
    if (!iso) {
      entrada.current.setCustomValidity(mensagemInvalida)
      return
    }
    entrada.current.setCustomValidity(validarLimites(iso, min, max, isoParaBr))
  }, [texto, min, max, brParaIso, isoParaBr, mensagemInvalida])

  function aoAlterar(evento) {
    const mascarado = mascara(evento.target.value)
    if (!mascarado) {
      setRascunho({ texto: '', valorBase: '' })
      onChange('')
      return
    }
    const iso = brParaIso(mascarado) ?? ''
    setRascunho({ texto: mascarado, valorBase: iso })
    onChange(iso)
  }

  return (
    <input
      ref={entrada}
      type="text"
      inputMode="numeric"
      placeholder={placeholder}
      maxLength={maxLength}
      value={texto}
      onChange={aoAlterar}
      {...props}
    />
  )
}

/** Campo de e-mail com sanitização automática (minúsculas e sem espaços). */
export function CampoEmail({ value, onChange, ...props }) {
  function aoAlterar(evento) {
    onChange(mascaraEmail(evento.target.value))
  }

  return (
    <input
      type="email"
      inputMode="email"
      autoCapitalize="none"
      spellCheck={false}
      value={value}
      onChange={aoAlterar}
      {...props}
    />
  )
}

/** Campo de telefone com máscara automática (XX) XXXXX-XXXX. */
export function CampoTelefone({ value, onChange, ...props }) {
  function aoAlterar(evento) {
    onChange(mascaraTelefone(evento.target.value))
  }

  return (
    <input
      type="tel"
      inputMode="tel"
      placeholder="(11) 99999-9999"
      maxLength={15}
      value={value}
      onChange={aoAlterar}
      {...props}
    />
  )
}

/** Campo de data (DD/MM/AAAA) que lê e emite string ISO sem hora ("YYYY-MM-DD"). */
export function CampoData(props) {
  return (
    <CampoTemporal
      mascara={mascaraData}
      isoParaBr={dataIsoParaBr}
      brParaIso={dataBrParaIso}
      mensagemInvalida="Informe uma data válida no formato DD/MM/AAAA."
      placeholder="DD/MM/AAAA"
      maxLength={10}
      {...props}
    />
  )
}

/** Campo de data e hora (DD/MM/AAAA HH:MM) que lê e emite "YYYY-MM-DDTHH:MM". */
export function CampoDataHora(props) {
  return (
    <CampoTemporal
      mascara={mascaraDataHora}
      isoParaBr={dataHoraIsoParaBr}
      brParaIso={dataHoraBrParaIso}
      mensagemInvalida="Informe data e hora válidas no formato DD/MM/AAAA HH:MM."
      placeholder="DD/MM/AAAA HH:MM"
      maxLength={16}
      {...props}
    />
  )
}
