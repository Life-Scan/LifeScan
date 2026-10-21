"""Testes do serviço de email (console e SMTP)."""

from email.message import EmailMessage
import smtplib
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import Configuracoes
from app.services.email import (
    ErroEnvioEmail,
    _criar_mensagem,
    _enviar_via_smtp,
    caixa_de_saida,
    enviar_email,
)


def _configuracao_mock(**kwargs) -> Configuracoes:
    padrao = {
        "DATABASE_URL": "sqlite:///:memory:",
        "JWT_SECRET": "teste-segredo-super-longo-12345678901234567890",
        "EMAIL_MODE": "smtp",
        "EMAIL_FROM": "LifeScan <nao-responda@lifescan.local>",
        "SMTP_HOST": "smtp.exemplo.com",
        "SMTP_PORT": 587,
        "SMTP_USER": "usuario@exemplo.com",
        "SMTP_PASSWORD": "senha-secreta",
        "SMTP_TLS": True,
        "SMTP_SSL": False,
        "SMTP_TIMEOUT": 10,
    }
    padrao.update(kwargs)
    return Configuracoes(**padrao)


def test_criar_mensagem_simples():
    config = _configuracao_mock()
    msg = _criar_mensagem(config, "paciente@teste.com", "Assunto Teste", "Corpo texto")

    assert msg["Subject"] == "Assunto Teste"
    assert msg["From"] == "LifeScan <nao-responda@lifescan.local>"
    assert msg["To"] == "paciente@teste.com"
    assert msg.get_content().strip() == "Corpo texto"


def test_criar_mensagem_com_html():
    config = _configuracao_mock()
    msg = _criar_mensagem(
        config,
        "paciente@teste.com",
        "Assunto",
        "Corpo texto",
        corpo_html="<p>Corpo HTML</p>",
    )

    partes = list(msg.iter_parts())
    assert len(partes) == 2
    assert partes[0].get_content_type() == "text/plain"
    assert partes[1].get_content_type() == "text/html"


def test_enviar_via_smtp_starttls():
    config = _configuracao_mock(SMTP_TLS=True, SMTP_SSL=False, SMTP_PORT=587)
    msg = EmailMessage()
    msg["Subject"] = "Teste"

    with patch("smtplib.SMTP") as mock_smtp_class:
        mock_servidor = MagicMock()
        mock_smtp_class.return_value = mock_servidor

        _enviar_via_smtp(config, msg)

        mock_smtp_class.assert_called_once_with("smtp.exemplo.com", 587, timeout=10)
        mock_servidor.starttls.assert_called_once()
        mock_servidor.login.assert_called_once_with("usuario@exemplo.com", "senha-secreta")
        mock_servidor.send_message.assert_called_once_with(msg)
        mock_servidor.quit.assert_called_once()


def test_enviar_via_smtp_ssl():
    config = _configuracao_mock(SMTP_TLS=False, SMTP_SSL=True, SMTP_PORT=465)
    msg = EmailMessage()

    with patch("smtplib.SMTP_SSL") as mock_ssl_class:
        mock_servidor = MagicMock()
        mock_ssl_class.return_value = mock_servidor

        _enviar_via_smtp(config, msg)

        mock_ssl_class.assert_called_once_with("smtp.exemplo.com", 465, timeout=10)
        mock_servidor.login.assert_called_once_with("usuario@exemplo.com", "senha-secreta")
        mock_servidor.send_message.assert_called_once_with(msg)
        mock_servidor.quit.assert_called_once()


def test_enviar_via_smtp_falha_autenticacao():
    config = _configuracao_mock()
    msg = EmailMessage()

    with patch("smtplib.SMTP") as mock_smtp_class:
        mock_servidor = MagicMock()
        mock_servidor.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication failed")
        mock_smtp_class.return_value = mock_servidor

        with pytest.raises(ErroEnvioEmail, match="Falha de autenticação SMTP"):
            _enviar_via_smtp(config, msg)


def test_enviar_via_smtp_falha_conexao():
    config = _configuracao_mock()
    msg = EmailMessage()

    with patch("smtplib.SMTP") as mock_smtp_class:
        mock_smtp_class.side_effect = OSError("Connection refused")

        with pytest.raises(ErroEnvioEmail, match="Falha de rede/conexão"):
            _enviar_via_smtp(config, msg)


def test_enviar_email_modo_console(capsys):
    caixa_de_saida.clear()
    config = _configuracao_mock(EMAIL_MODE="console")

    with patch("app.services.email.obter_configuracoes", return_value=config):
        enviar_email("destino@teste.com", "Assunto", "Texto do corpo")

        captura = capsys.readouterr()
        assert "[EMAIL - modo console, nada foi enviado]" in captura.out
        assert "destino@teste.com" in captura.out
        assert len(caixa_de_saida) == 1
        assert caixa_de_saida[0].destinatario == "destino@teste.com"


def test_enviar_email_modo_desconhecido():
    config = _configuracao_mock(EMAIL_MODE="invalido")

    with patch("app.services.email.obter_configuracoes", return_value=config):
        with pytest.raises(ErroEnvioEmail, match="não é suportado"):
            enviar_email("destino@teste.com", "Assunto", "Corpo")
