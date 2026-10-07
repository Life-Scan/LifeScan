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
    enviar_email(
        usuario.email,
        "Seu acesso ao LifeScan",
        f"Olá, {usuario.nome}!\n\n"
        "Seu médico criou um acesso para você no LifeScan, onde o seu tratamento é acompanhado.\n\n"
        f"Endereço: {config.url_frontend}/login\n"
        f"Email:    {usuario.email}\n"
        f"Senha provisória: {senha}\n\n"
        f"A senha provisória vale por {_formatar_validade(validade)}. "
        "No primeiro acesso você vai escolher uma senha só sua.",
    )


def enviar_senha_de_redefinicao(usuario: Usuario) -> None:
    """Fluxo do "esqueci minha senha": manda uma senha provisória de curta duração.

    A senha atual continua valendo até a pessoa entrar e escolher outra.
    """
    config = obter_configuracoes()
    validade = timedelta(minutes=config.minutos_redefinicao_senha)
    senha = definir_senha_provisoria(usuario, validade)
    enviar_email(
        usuario.email,
        "Redefinição de senha do LifeScan",
        f"Olá, {usuario.nome}!\n\n"
        "Recebemos um pedido para redefinir a sua senha do LifeScan.\n\n"
        f"Endereço: {config.url_frontend}/login\n"
        f"Senha provisória: {senha}\n\n"
        f"Ela vale por {_formatar_validade(validade)}. Ao entrar, você vai escolher uma nova senha.\n"
        "Se não foi você quem pediu, ignore este email: sua senha atual continua funcionando.",
    )
