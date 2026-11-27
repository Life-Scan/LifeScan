"""Envio de emails.

Suporta:
- modo "console" (EMAIL_MODE=console): o email é mostrado no terminal/log da API (ideal para desenvolvimento e testes).
- modo "brevo" (EMAIL_MODE=brevo): envio real via API transacional do Brevo.
"""

from collections import deque
from dataclasses import dataclass
from email.utils import parseaddr
import logging

import httpx

from app.core.config import Configuracoes, obter_configuracoes

logger = logging.getLogger(__name__)


class ErroEnvioEmail(RuntimeError):
    """Erro disparado ao falhar o envio de email."""


@dataclass(frozen=True)
class Email:
    destinatario: str
    assunto: str
    corpo: str
    corpo_html: str | None = None


# Últimos emails processados (usado pelos testes automatizados e para depuração)
caixa_de_saida: deque[Email] = deque(maxlen=50)


def _parsear_remetente(remetente: str) -> dict[str, str]:
    """Converte 'Nome <email>' ou 'email' para o formato esperado pela API do Brevo."""
    nome, endereco = parseaddr(remetente.strip())
    if not endereco:
        endereco = remetente.strip()
    if nome:
        return {"name": nome, "email": endereco}
    return {"email": endereco}


def _montar_payload_brevo(
    config: Configuracoes,
    destinatario: str,
    assunto: str,
    corpo: str,
    corpo_html: str | None = None,
) -> dict:
    """Monta o payload JSON para a API v3 de envio transacional do Brevo."""
    payload: dict = {
        "sender": _parsear_remetente(config.remetente_email),
        "to": [{"email": destinatario}],
        "subject": assunto,
        "textContent": corpo,
    }
    if corpo_html:
        payload["htmlContent"] = corpo_html
    return payload


def _enviar_via_brevo(config: Configuracoes, payload: dict) -> None:
    """Envia o email realizando uma requisição POST para a API do Brevo."""
    api_key = config.brevo_api_key.strip() if config.brevo_api_key else ""
    if not api_key:
        msg_erro = "BREVO_API_KEY não configurada para envio de email."
        logger.error(msg_erro)
        raise ErroEnvioEmail(msg_erro)

    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        resposta = httpx.post(
            config.brevo_api_url,
            headers=headers,
            json=payload,
            timeout=config.brevo_timeout,
        )
    except httpx.TimeoutException as err:
        msg_erro = f"Tempo esgotado ao conectar à API do Brevo ({config.brevo_timeout}s)."
        logger.error(msg_erro)
        raise ErroEnvioEmail(msg_erro) from err
    except httpx.RequestError as err:
        msg_erro = f"Falha de rede/conexão com a API do Brevo: {err}"
        logger.error(msg_erro)
        raise ErroEnvioEmail(msg_erro) from err

    if resposta.status_code in (401, 403):
        detalhe = resposta.text.strip()
        msg_erro = (
            f"Falha de autenticação na API do Brevo: verifique BREVO_API_KEY ({detalhe})."
            if detalhe
            else "Falha de autenticação na API do Brevo: verifique BREVO_API_KEY."
        )
        logger.error(msg_erro)
        raise ErroEnvioEmail(msg_erro)

    if resposta.is_error:
        detalhe = resposta.text.strip()
        msg_erro = f"Erro na API do Brevo (HTTP {resposta.status_code}): {detalhe}"
        logger.error(msg_erro)
        raise ErroEnvioEmail(msg_erro)


def enviar_email(
    destinatario: str,
    assunto: str,
    corpo: str,
    corpo_html: str | None = None,
) -> None:
    """Envia um email usando a configuração ativa (console ou brevo)."""
    config = obter_configuracoes()
    modo = config.modo_email.lower().strip()

    if modo not in ("console", "brevo"):
        raise ErroEnvioEmail(
            f"EMAIL_MODE={config.modo_email!r} não é suportado. Use EMAIL_MODE=console ou EMAIL_MODE=brevo."
        )

    email = Email(destinatario=destinatario, assunto=assunto, corpo=corpo, corpo_html=corpo_html)
    caixa_de_saida.append(email)

    if modo == "console":
        linha = "=" * 64
        print(
            f"\n{linha}\n[EMAIL - modo console, nada foi enviado]\n"
            f"De:      {config.remetente_email}\nPara:    {destinatario}\nAssunto: {assunto}\n\n{corpo}\n{linha}\n",
            flush=True,
        )
        return

    payload = _montar_payload_brevo(config, destinatario, assunto, corpo, corpo_html)
    _enviar_via_brevo(config, payload)
    logger.info("Email enviado com sucesso via Brevo para %s (Assunto: %s)", destinatario, assunto)
