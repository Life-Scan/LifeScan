from app.schemas.base import DataHoraUTC, SchemaSaida


class ArquivoSaida(SchemaSaida):
    id: int
    nome_original: str
    tipo_mime: str
    tamanho_bytes: int
    criado_em: DataHoraUTC
