"""Envio de emails.

Suporta:
- modo "console" (EMAIL_MODE=console): o email é mostrado no terminal/log da API (ideal para desenvolvimento e testes).
- modo "smtp" (EMAIL_MODE=smtp): envio real via servidor SMTP configurado (com suporte a STARTTLS, SSL/TLS e autenticação).
"""

from collections import deque
from dataclasses import dataclass
from email.message import EmailMessage
import logging
import smtplib

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


def _criar_mensagem(config: Configuracoes, destinatario: str, assunto: str, corpo: str, corpo_html: str | None = None) -> EmailMessage:
    """Monta o objeto EmailMessage com cabeçalhos e conteúdo em texto plano / HTML."""
    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = config.remetente_email
    msg["To"] = destinatario
    msg.set_content(corpo, charset="utf-8")

    if corpo_html:
        msg.add_alternative(corpo_html, subtype="html", charset="utf-8")

    return msg


def _enviar_via_smtp(config: Configuracoes, msg: EmailMessage) -> None:
    """Conecta ao servidor SMTP, aplica criptografia (SSL ou STARTTLS), autentica e envia."""
    timeout = config.smtp_timeout
    host = config.smtp_host
    port = config.smtp_port

    usuario = config.smtp_user.strip() if config.smtp_user else ""
    senha = config.smtp_password.replace(" ", "").strip() if config.smtp_password else ""

    servidor = None
    try:
        if config.smtp_ssl:
            # Conexão direta via SSL (comum na porta 465)
            servidor = smtplib.SMTP_SSL(host, port, timeout=timeout)
        else:
            # Conexão padrão ou STARTTLS (comum na porta 587 ou 25)
            servidor = smtplib.SMTP(host, port, timeout=timeout)
            if config.smtp_tls:
                servidor.starttls()

        if usuario and senha:
            servidor.login(usuario, senha)

        servidor.send_message(msg)
    except smtplib.SMTPAuthenticationError as err:
        msg_erro = f"Falha de autenticação SMTP ({host}:{port}): verifique usuário e senha."
        logger.error(msg_erro)
        raise ErroEnvioEmail(msg_erro) from err
    except smtplib.SMTPConnectError as err:
        msg_erro = f"Não foi possível conectar ao servidor SMTP em {host}:{port}."
        logger.error(msg_erro)
        raise ErroEnvioEmail(msg_erro) from err
    except smtplib.SMTPException as err:
        msg_erro = f"Erro no protocolo SMTP ao enviar email: {err}"
        logger.error(msg_erro)
        raise ErroEnvioEmail(msg_erro) from err
    except OSError as err:
        msg_erro = f"Falha de rede/conexão com o servidor SMTP {host}:{port}: {err}"
        logger.error(msg_erro)
        raise ErroEnvioEmail(msg_erro) from err
    except Exception as err:
        msg_erro = f"Erro inesperado no envio de email: {err}"
        logger.error(msg_erro)
        raise ErroEnvioEmail(msg_erro) from err
    finally:
        if servidor is not None:
            try:
                servidor.quit()
            except Exception:
                try:
                    servidor.close()
                except Exception:
                    pass


def enviar_email(
    destinatario: str,
    assunto: str,
    corpo: str,
    corpo_html: str | None = None,
) -> None:
    """Envia um email usando a configuração ativa (console ou smtp)."""
    config = obter_configuracoes()
    modo = config.modo_email.lower().strip()

    if modo not in ("console", "smtp"):
        raise ErroEnvioEmail(
            f"EMAIL_MODE={config.modo_email!r} não é suportado. Use EMAIL_MODE=console ou EMAIL_MODE=smtp."
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

    # Modo SMTP
    mensagem = _criar_mensagem(config, destinatario, assunto, corpo, corpo_html)
    _enviar_via_smtp(config, mensagem)
    logger.info("Email enviado com sucesso via SMTP para %s (Assunto: %s)", destinatario, assunto)
