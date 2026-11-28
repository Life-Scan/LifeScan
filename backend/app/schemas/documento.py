from pydantic import BaseModel, Field, field_validator

from app.models.documento import CategoriaDocumento, StatusDocumento
from app.schemas.arquivo import ArquivoSaida
from app.schemas.base import DataHoraUTC, SchemaSaida
from app.schemas.usuario import UsuarioResumo


class RevisaoEntrada(BaseModel):
    observacao_revisao: str | None = None


class DocumentoEdicao(BaseModel):
    """Edição básica: só título e categoria. Trocar o arquivo = excluir e enviar de novo."""

    titulo: str | None = Field(None, max_length=150)
    categoria: CategoriaDocumento | None = None

    @field_validator("titulo")
    @classmethod
    def _titulo_com_conteudo(cls, valor: str | None) -> str | None:
        # Mesma regra do envio (3 a 150 caracteres), contada sem os espaços das pontas
        if valor is None:
            return None
        valor = valor.strip()
        if len(valor) < 3:
            raise ValueError("O título precisa ter pelo menos 3 caracteres.")
        return valor


class DocumentoSaida(SchemaSaida):
    id: int
    acompanhamento_id: int
    solicitacao_id: int | None
    categoria: CategoriaDocumento
    titulo: str
    status: StatusDocumento
    observacao_revisao: str | None
    revisado_em: DataHoraUTC | None
    criado_em: DataHoraUTC
    enviado_por: UsuarioResumo
    arquivo: ArquivoSaida
