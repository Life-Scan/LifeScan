"""Senhas provisórias e emails de acesso das contas criadas pelo médico."""

import secrets
from datetime import timedelta

from app.core.config import obter_configuracoes
from app.core.seguranca import gerar_hash_senha, verificar_senha
from app.db.base import agora_utc
from app.models.usuario import Usuario
from app.services.email import enviar_email

# Sem caracteres fáceis de confundir (0/O, 1/l/I), já que a pessoa vai digitar a senha
ALFABETO_SENHA = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TAMANHO_SENHA_PROVISORIA = 10


def gerar_senha_provisoria() -> str:
    return "".join(secrets.choice(ALFABETO_SENHA) for _ in range(TAMANHO_SENHA_PROVISORIA))


def definir_senha_provisoria(usuario: Usuario, validade: timedelta) -> str:
    """Grava uma nova senha provisória (só o hash) e devolve o texto para ir no email."""
    senha = gerar_senha_provisoria()
    usuario.senha_provisoria_hash = gerar_hash_senha(senha)
    usuario.senha_provisoria_expira_em = agora_utc() + validade
    return senha


def senha_provisoria_confere(usuario: Usuario, senha: str) -> bool:
    """A senha bate com a provisória, independentemente de ela ter expirado."""
    return usuario.senha_provisoria_hash is not None and verificar_senha(
        senha, usuario.senha_provisoria_hash
    )


def senha_provisoria_expirada(usuario: Usuario) -> bool:
    return (
        usuario.senha_provisoria_expira_em is None
        or usuario.senha_provisoria_expira_em < agora_utc()
    )


def limpar_senha_provisoria(usuario: Usuario) -> None:
    usuario.senha_provisoria_hash = None
    usuario.senha_provisoria_expira_em = None


def _formatar_validade(validade: timedelta) -> str:
    minutos = int(validade.total_seconds() // 60)
    if minutos >= 2 * 24 * 60:
        return f"{minutos // (24 * 60)} dias"
    if minutos >= 120:
        return f"{minutos // 60} horas"
    return f"{minutos} minutos"


def enviar_acesso_da_conta(usuario: Usuario) -> None:
    """Cria a senha provisória de uma conta (nova ou com acesso reenviado) e manda por email."""
    config = obter_configuracoes()
    validade = timedelta(days=config.dias_senha_provisoria)
    senha = definir_senha_provisoria(usuario, validade)
    tempo_validade = _formatar_validade(validade)

    corpo_texto = (
        f"Olá, {usuario.nome}!\n\n"
        "Seu médico criou um acesso para você no LifeScan, onde o seu tratamento é acompanhado.\n\n"
        f"Endereço: {config.url_frontend}/login\n"
        f"Email:    {usuario.email}\n"
        f"Senha provisória: {senha}\n\n"
        f"A senha provisória vale por {tempo_validade}. "
        "No primeiro acesso você vai escolher uma senha só sua."
    )

    corpo_html = (
        f"<div style=\"font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; "
        f"max-width: 580px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; color: #1e293b;\">\n"
        f"  <div style=\"border-bottom: 2px solid #0d9488; padding-bottom: 12px; margin-bottom: 20px;\">\n"
        f"    <h1 style=\"color: #0d9488; font-size: 24px; margin: 0;\">LifeScan</h1>\n"
        f"  </div>\n"
        f"  <p style=\"font-size: 16px;\">Olá, <strong>{usuario.nome}</strong>!</p>\n"
        f"  <p style=\"font-size: 15px; color: #475569;\">Seu médico criou um acesso para você no sistema <strong>LifeScan</strong>, onde seu tratamento e histórico são acompanhados.</p>\n"
        f"  <div style=\"background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 16px; margin: 24px 0;\">\n"
        f"    <p style=\"margin: 0 0 8px 0; font-size: 14px;\"><strong>Email de acesso:</strong> {usuario.email}</p>\n"
        f"    <p style=\"margin: 0; font-size: 14px;\"><strong>Senha provisória:</strong> <code style=\"background-color: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-size: 16px; font-weight: bold;\">{senha}</code></p>\n"
        f"  </div>\n"
        f"  <p style=\"font-size: 14px; color: #64748b;\">Esta senha provisória é válida por <strong>{tempo_validade}</strong>. Ao acessar pela primeira vez, você definirá sua senha definitiva.</p>\n"
        f"  <div style=\"margin: 28px 0; text-align: center;\">\n"
        f"    <a href=\"{config.url_frontend}/login\" style=\"background-color: #0d9488; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;\">Acessar o LifeScan</a>\n"
        f"  </div>\n"
        f"  <hr style=\"border: 0; border-top: 1px solid #f1f5f9; margin: 24px 0;\" />\n"
        f"  <p style=\"font-size: 12px; color: #94a3b8; text-align: center;\">Se você não esperava este email, por favor ignore esta mensagem.</p>\n"
        f"</div>"
    )

    enviar_email(
        usuario.email,
        "Seu acesso ao LifeScan",
        corpo_texto,
        corpo_html=corpo_html,
    )


def enviar_senha_de_redefinicao(usuario: Usuario) -> None:
    """Fluxo do "esqueci minha senha": manda uma senha provisória de curta duração."""
    config = obter_configuracoes()
    validade = timedelta(minutes=config.minutos_redefinicao_senha)
    senha = definir_senha_provisoria(usuario, validade)
    tempo_validade = _formatar_validade(validade)

    corpo_texto = (
        f"Olá, {usuario.nome}!\n\n"
        "Recebemos um pedido para redefinir a sua senha do LifeScan.\n\n"
        f"Endereço: {config.url_frontend}/login\n"
        f"Senha provisória: {senha}\n\n"
        f"Ela vale por {tempo_validade}. Ao entrar, você vai escolher uma nova senha.\n"
        "Se não foi você quem pediu, ignore este email: sua senha atual continua funcionando."
    )

    corpo_html = (
        f"<div style=\"font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; "
        f"max-width: 580px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px; color: #1e293b;\">\n"
        f"  <div style=\"border-bottom: 2px solid #0d9488; padding-bottom: 12px; margin-bottom: 20px;\">\n"
        f"    <h1 style=\"color: #0d9488; font-size: 24px; margin: 0;\">LifeScan</h1>\n"
        f"  </div>\n"
        f"  <p style=\"font-size: 16px;\">Olá, <strong>{usuario.nome}</strong>!</p>\n"
        f"  <p style=\"font-size: 15px; color: #475569;\">Recebemos um pedido para redefinir a sua senha de acesso ao <strong>LifeScan</strong>.</p>\n"
        f"  <div style=\"background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 16px; margin: 24px 0;\">\n"
        f"    <p style=\"margin: 0; font-size: 14px;\"><strong>Senha provisória:</strong> <code style=\"background-color: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 4px; font-size: 16px; font-weight: bold;\">{senha}</code></p>\n"
        f"  </div>\n"
        f"  <p style=\"font-size: 14px; color: #64748b;\">Ela é válida por <strong>{tempo_validade}</strong>. Ao entrar com ela, você deverá criar sua nova senha.</p>\n"
        f"  <div style=\"margin: 28px 0; text-align: center;\">\n"
        f"    <a href=\"{config.url_frontend}/login\" style=\"background-color: #0d9488; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;\">Entrar e Redefinir Senha</a>\n"
        f"  </div>\n"
        f"  <hr style=\"border: 0; border-top: 1px solid #f1f5f9; margin: 24px 0;\" />\n"
        f"  <p style=\"font-size: 12px; color: #94a3b8; text-align: center;\">Se não foi você quem pediu, fique tranquilo: sua senha atual continua funcionando normalmente.</p>\n"
        f"</div>"
    )

    enviar_email(
        usuario.email,
        "Redefinição de senha do LifeScan",
        corpo_texto,
        corpo_html=corpo_html,
    )
