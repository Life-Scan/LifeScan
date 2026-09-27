from app.schemas.arquivo import ArquivoSaida
from app.schemas.base import DataHoraUTC, SchemaSaida
from app.schemas.usuario import UsuarioResumo


class MensagemSaida(SchemaSaida):
    id: int
    jornada_id: int
    conteudo: str | None
    criado_em: DataHoraUTC
    remetente: UsuarioResumo
    arquivo: ArquivoSaida | None
