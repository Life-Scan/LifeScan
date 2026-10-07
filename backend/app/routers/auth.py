from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import obter_usuario_autenticado
from app.core.seguranca import criar_token_acesso, gerar_hash_senha, verificar_senha
from app.db.base import agora_utc
from app.db.sessao import obter_sessao
from app.models.usuario import Usuario
from app.schemas.auth import (
    EsqueciSenhaEntrada,
    LoginEntrada,
    MensagemSaida,
    TokenSaida,
    TrocaSenhaEntrada,
    UsuarioSaida,
)
from app.services.contas import (
    enviar_senha_de_redefinicao,
    limpar_senha_provisoria,
    senha_provisoria_confere,
    senha_provisoria_expirada,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])

CREDENCIAIS_INVALIDAS = "Email ou senha inválidos."


def _senha_definitiva_confere(usuario: Usuario, senha: str) -> bool:
    return usuario.senha_hash is not None and verificar_senha(senha, usuario.senha_hash)


@router.post("/login", response_model=TokenSaida)
def entrar(dados: LoginEntrada, sessao: Session = Depends(obter_sessao)) -> TokenSaida:
    """Login com a senha definitiva ou com a senha provisória recebida por email."""
    usuario = sessao.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, CREDENCIAIS_INVALIDAS)

    com_definitiva = _senha_definitiva_confere(usuario, dados.senha)
    com_provisoria = not com_definitiva and senha_provisoria_confere(usuario, dados.senha)
    if not com_definitiva and not com_provisoria:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, CREDENCIAIS_INVALIDAS)

    # A partir daqui a pessoa provou que conhece uma senha da conta,
    # então as mensagens podem ser específicas
    if com_provisoria and senha_provisoria_expirada(usuario):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Sua senha provisória expirou. Use \"Esqueci minha senha\" ou peça um novo acesso ao médico.",
        )
    if not usuario.ativo:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Sua conta está desativada. Procure o seu médico.",
        )

    usuario.deve_trocar_senha = com_provisoria
    usuario.ultimo_login_em = agora_utc()
    sessao.commit()
    return TokenSaida(
        token_acesso=criar_token_acesso(usuario.id, usuario.tipo_usuario.value),
        usuario=UsuarioSaida.model_validate(usuario),
    )


@router.get("/me", response_model=UsuarioSaida)
def obter_eu(usuario: Usuario = Depends(obter_usuario_autenticado)) -> Usuario:
    return usuario


@router.post("/change-password", response_model=UsuarioSaida)
def trocar_senha(
    dados: TrocaSenhaEntrada,
    usuario: Usuario = Depends(obter_usuario_autenticado),
    sessao: Session = Depends(obter_sessao),
) -> Usuario:
    """Define a senha da própria pessoa. Obrigatório depois de entrar com a provisória."""
    provisoria_valida = senha_provisoria_confere(usuario, dados.senha_atual) and not senha_provisoria_expirada(usuario)
    if not _senha_definitiva_confere(usuario, dados.senha_atual) and not provisoria_valida:
        # 400 e não 401: a sessão continua válida, só a senha digitada está errada
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A senha atual está incorreta.")
    if dados.nova_senha == dados.senha_atual:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "A nova senha precisa ser diferente da atual.",
        )

    usuario.senha_hash = gerar_hash_senha(dados.nova_senha)
    limpar_senha_provisoria(usuario)
    usuario.deve_trocar_senha = False
    sessao.commit()
    return usuario


@router.post("/forgot-password", response_model=MensagemSaida)
def esqueci_senha(dados: EsqueciSenhaEntrada, sessao: Session = Depends(obter_sessao)) -> MensagemSaida:
    """Envia uma senha provisória por email.

    A resposta é sempre a mesma, exista ou não a conta, para não revelar quem tem cadastro.
    """
    usuario = sessao.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is not None and usuario.ativo:
        enviar_senha_de_redefinicao(usuario)
        sessao.commit()
    return MensagemSaida(
        mensagem="Se este email tiver uma conta ativa, enviaremos uma senha provisória para ele."
    )
