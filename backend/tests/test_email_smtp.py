"""Testes do serviço de email (console e Brevo)."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.core.config import Configuracoes
from app.services.email import (
    ErroEnvioEmail,
    _enviar_via_brevo,
    _montar_payload_brevo,
    caixa_de_saida,
    enviar_email,
)


def _configuracao_mock(**kwargs) -> Configuracoes:
    padrao = {
        "DATABASE_URL": "sqlite:///:memory:",
        "JWT_SECRET": "teste-segredo-super-longo-12345678901234567890",
        "EMAIL_MODE": "brevo",
        "EMAIL_FROM": "LifeScan <nao-responda@lifescan.local>",
        "BREVO_API_KEY": "xkeysib-teste-123",
        "BREVO_API_URL": "https://api.brevo.com/v3/smtp/email",
        "BREVO_TIMEOUT": 10,
    }
    padrao.update(kwargs)
    return Configuracoes(**padrao)


def test_montar_payload_brevo_simples():
    config = _configuracao_mock()
    payload = _montar_payload_brevo(config, "paciente@teste.com", "Assunto Teste", "Corpo texto")

    assert payload == {
        "sender": {"name": "LifeScan", "email": "nao-responda@lifescan.local"},
        "to": [{"email": "paciente@teste.com"}],
        "subject": "Assunto Teste",
        "textContent": "Corpo texto",
    }


def test_montar_payload_brevo_com_html_e_remetente_simples():
    config = _configuracao_mock(EMAIL_FROM="nao-responda@lifescan.local")
    payload = _montar_payload_brevo(
        config,
        "paciente@teste.com",
        "Assunto",
        "Corpo texto",
        corpo_html="<p>Corpo HTML</p>",
    )

    assert payload["sender"] == {"email": "nao-responda@lifescan.local"}
    assert payload["htmlContent"] == "<p>Corpo HTML</p>"


def test_enviar_via_brevo_sucesso():
    config = _configuracao_mock()
    payload = _montar_payload_brevo(config, "paciente@teste.com", "Teste", "Corpo")

    mock_resposta = MagicMock(status_code=201, is_error=False)
    with patch("app.services.email.httpx.post", return_value=mock_resposta) as mock_post:
        _enviar_via_brevo(config, payload)

        mock_post.assert_called_once_with(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": "xkeysib-teste-123",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json=payload,
            timeout=10,
        )


def test_enviar_via_brevo_sem_api_key():
    config = _configuracao_mock(BREVO_API_KEY="   ")
    payload = _montar_payload_brevo(config, "paciente@teste.com", "Teste", "Corpo")

    with pytest.raises(ErroEnvioEmail, match="BREVO_API_KEY não configurada"):
        _enviar_via_brevo(config, payload)


def test_enviar_via_brevo_falha_autenticacao():
    config = _configuracao_mock()
    payload = _montar_payload_brevo(config, "paciente@teste.com", "Teste", "Corpo")

    mock_resposta = MagicMock(status_code=401, is_error=True, text="Unauthorized")
    with patch("app.services.email.httpx.post", return_value=mock_resposta):
        with pytest.raises(ErroEnvioEmail, match="Falha de autenticação na API do Brevo"):
            _enviar_via_brevo(config, payload)


def test_enviar_via_brevo_erro_http():
    config = _configuracao_mock()
    payload = _montar_payload_brevo(config, "paciente@teste.com", "Teste", "Corpo")

    mock_resposta = MagicMock(status_code=400, is_error=True, text='{"message":"invalid"}')
    with patch("app.services.email.httpx.post", return_value=mock_resposta):
        with pytest.raises(ErroEnvioEmail, match="HTTP 400"):
            _enviar_via_brevo(config, payload)


def test_enviar_via_brevo_timeout():
    config = _configuracao_mock()
    payload = _montar_payload_brevo(config, "paciente@teste.com", "Teste", "Corpo")

    with patch("app.services.email.httpx.post", side_effect=httpx.TimeoutException("timeout")):
        with pytest.raises(ErroEnvioEmail, match="Tempo esgotado"):
            _enviar_via_brevo(config, payload)


def test_enviar_via_brevo_falha_conexao():
    config = _configuracao_mock()
    payload = _montar_payload_brevo(config, "paciente@teste.com", "Teste", "Corpo")

    with patch("app.services.email.httpx.post", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(ErroEnvioEmail, match="Falha de rede/conexão"):
            _enviar_via_brevo(config, payload)


def test_enviar_email_modo_brevo():
    caixa_de_saida.clear()
    config = _configuracao_mock(EMAIL_MODE="brevo")
    mock_resposta = MagicMock(status_code=201, is_error=False)

    with (
        patch("app.services.email.obter_configuracoes", return_value=config),
        patch("app.services.email.httpx.post", return_value=mock_resposta) as mock_post,
    ):
        enviar_email("destino@teste.com", "Assunto", "Texto do corpo", "<p>HTML</p>")

        mock_post.assert_called_once()
        assert len(caixa_de_saida) == 1
        assert caixa_de_saida[0].destinatario == "destino@teste.com"


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
