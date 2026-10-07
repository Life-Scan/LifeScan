"""Configurações da aplicação, lidas do arquivo .env e de variáveis de ambiente."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PASTA_BACKEND = Path(__file__).resolve().parents[2]


class Configuracoes(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PASTA_BACKEND / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    url_banco: str = Field(validation_alias="DATABASE_URL")
    segredo_jwt: str = Field(validation_alias="JWT_SECRET")
    minutos_expiracao_jwt: int = Field(480, validation_alias="JWT_EXPIRE_MINUTES")
    # Custo do bcrypt; os testes usam o mínimo (4) para rodarem rápido
    rodadas_bcrypt: int = Field(12, ge=4, le=31, validation_alias="BCRYPT_ROUNDS")
    origens_cors_texto: str = Field("http://localhost:5173", validation_alias="CORS_ORIGINS")
    pasta_uploads_texto: str = Field("uploads", validation_alias="UPLOAD_DIR")
    tamanho_maximo_upload_mb: int = Field(30, validation_alias="MAX_UPLOAD_MB")
    dias_prazo_proximo: int = Field(3, validation_alias="DUE_SOON_DAYS")

    # Email: por enquanto só o modo "console", que mostra o email no terminal da API
    modo_email: str = Field("console", validation_alias="EMAIL_MODE")
    remetente_email: str = Field("LifeScan <nao-responda@lifescan.local>", validation_alias="EMAIL_FROM")
    # Endereço do frontend, usado nos links dos emails
    url_frontend: str = Field("http://localhost:5173", validation_alias="FRONTEND_URL")
    # Validade da senha provisória de uma conta nova e da enviada pelo "esqueci minha senha"
    dias_senha_provisoria: int = Field(7, validation_alias="ACCESS_PASSWORD_DAYS")
    minutos_redefinicao_senha: int = Field(60, validation_alias="RESET_PASSWORD_MINUTES")

    @property
    def origens_cors(self) -> list[str]:
        """Lista de origens do CORS (o .env traz os valores separados por vírgula)."""
        return [origem.strip() for origem in self.origens_cors_texto.split(",") if origem.strip()]

    @property
    def pasta_uploads(self) -> Path:
        """Pasta de uploads; caminhos relativos partem da pasta backend."""
        pasta = Path(self.pasta_uploads_texto)
        return pasta if pasta.is_absolute() else PASTA_BACKEND / pasta

    @property
    def tamanho_maximo_upload_bytes(self) -> int:
        return self.tamanho_maximo_upload_mb * 1024 * 1024


@lru_cache
def obter_configuracoes() -> Configuracoes:
    return Configuracoes()
