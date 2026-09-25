from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import obter_usuario_atual
from app.core.seguranca import criar_token_acesso, gerar_hash_senha, verificar_senha
from app.db.sessao import obter_sessao
from app.models.usuario import Usuario
from app.schemas.auth import CadastroEntrada, LoginEntrada, TokenSaida, UsuarioSaida

router = APIRouter(prefix="/auth", tags=["Autenticação"])


def _gerar_resposta_token(usuario: Usuario) -> TokenSaida:
    return TokenSaida(
        token_acesso=criar_token_acesso(usuario.id, usuario.papel.value),
        usuario=UsuarioSaida.model_validate(usuario),
    )


@router.post("/register", response_model=TokenSaida, status_code=status.HTTP_201_CREATED)
def cadastrar(dados: CadastroEntrada, sessao: Session = Depends(obter_sessao)) -> TokenSaida:
    """Cria a conta (médico ou paciente) e já devolve um token de acesso."""
    if sessao.scalar(select(Usuario.id).where(Usuario.email == dados.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma conta com este email.")

    usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_hash_senha(dados.senha),
        papel=dados.papel,
    )
    sessao.add(usuario)
    sessao.commit()
    return _gerar_resposta_token(usuario)


@router.post("/login", response_model=TokenSaida)
def entrar(dados: LoginEntrada, sessao: Session = Depends(obter_sessao)) -> TokenSaida:
    usuario = sessao.scalar(select(Usuario).where(Usuario.email == dados.email))
    if usuario is None or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email ou senha inválidos.")
    return _gerar_resposta_token(usuario)


@router.get("/me", response_model=UsuarioSaida)
def obter_eu(usuario: Usuario = Depends(obter_usuario_atual)) -> Usuario:
    return usuario
