from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import obter_usuario_autenticado
from app.core.seguranca import criar_token_acesso, gerar_hash_senha, verificar_senha
from app.db.base import agora_utc
from app.db.sessao import obter_sessao
from app.models.consentimento import Consentimento
from app.models.usuario import TipoUsuario, Usuario
from app.schemas.auth import (
    DefinicaoSenhaEntrada,
    EsqueciSenhaEntrada,
    LoginEntrada,
    MensagemSaida,
    TokenSaida,
    UsuarioSaida,
)
from app.services.contas import (
    enviar_senha_de_redefinicao,
    limpar_senha_provisoria,
    senha_provisoria_confere,
    senha_provisoria_expirada,
)
from app.services.email import ErroEnvioEmail

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


@router.post("/set-password", response_model=UsuarioSaida)
def definir_senha(
    dados: DefinicaoSenhaEntrada,
    request: Request,
    usuario: Usuario = Depends(obter_usuario_autenticado),
    sessao: Session = Depends(obter_sessao),
) -> Usuario:
    """Define a senha da própria pessoa depois de entrar com a senha provisória.

    Só funciona nesse momento (primeiro acesso ou "esqueci minha senha"): a pessoa acabou
    de provar que tem a provisória, então não é pedida de novo. Não existe troca de senha
    fora desse fluxo; quem quiser trocar usa "esqueci minha senha".
    """
    if not usuario.deve_trocar_senha:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            'Para trocar a senha, saia e use "Esqueci minha senha" na tela de login.',
        )
    if senha_provisoria_confere(usuario, dados.nova_senha):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Escolha uma senha diferente da senha provisória.",
        )
    # LGPD (art. 11): o paciente é o titular dos dados de saúde; o consentimento
    # específico dele é registrado no momento em que ele assume a própria conta
    if usuario.tipo_usuario is TipoUsuario.paciente and not dados.aceite_lgpd:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "É preciso aceitar o termo de tratamento de dados para continuar.",
        )

    usuario.senha_hash = gerar_hash_senha(dados.nova_senha)
    limpar_senha_provisoria(usuario)
    usuario.deve_trocar_senha = False
    if usuario.tipo_usuario is TipoUsuario.paciente:
        ip = request.client.host if request.client else None
        sessao.add(Consentimento(usuario_id=usuario.id, ip_aceite=ip))
    sessao.commit()
    return usuario


@router.post("/forgot-password", response_model=MensagemSaida)
def esqueci_senha(dados: EsqueciSenhaEntrada, sessao: Session = Depends(obter_sessao)) -> MensagemSaida:
    """Envia uma senha provisória por email.

    A resposta é sempre a mesma, exista ou não a conta, para não revelar quem tem cadastro.
    """
    usuario = sessao.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is not None and usuario.ativo:
        try:
            enviar_senha_de_redefinicao(usuario)
            sessao.commit()
        except ErroEnvioEmail as err:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                f"Falha ao enviar email por SMTP: {err}",
            ) from err
    return MensagemSaida(
        mensagem="Se este email tiver uma conta ativa, enviaremos uma senha provisória para ele."
    )
