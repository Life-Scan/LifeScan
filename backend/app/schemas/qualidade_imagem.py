"""Schemas da verificação de qualidade de fotos de documentos (componente de IA)."""

from typing import Literal

from pydantic import BaseModel, Field

ClasseQualidade = Literal["boa", "torta", "borrada", "iluminacao", "baixa_resolucao"]


class IndicadoresSaida(BaseModel):
    """Medidas usadas na classificação — úteis para depurar e para o relatório."""

    nitidez: float = Field(..., description="Variância do Laplaciano (bordas nítidas = valor alto).")
    brilho: float = Field(..., description="Média dos tons de cinza (0 a 255).")
    contraste: float = Field(..., description="Desvio-padrão dos tons de cinza.")
    resolucao_px: int = Field(..., description="Menor lado da imagem original, em pixels.")
    altura_texto_relativa: float = Field(
        ..., description="Altura mediana das linhas de texto dividida pela altura da imagem."
    )
    angulo: float = Field(..., description="Inclinação mediana das linhas de texto, em graus.")


class QualidadeImagemSaida(BaseModel):
    """Resultado do componente de IA para uma foto de documento."""

    legivel: bool = Field(..., description="A foto permite ler o documento?")
    classe: ClasseQualidade
    motivo: str = Field(..., description="Mensagem para o usuário; vazia quando a foto está boa.")
    confianca: float = Field(..., ge=0, le=1, description="Confiança da classificação, de 0 a 1.")
    indicadores: IndicadoresSaida
