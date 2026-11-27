"""Verificação de qualidade e legibilidade das fotos de documentos (componente de IA).

Eixo de **Computação Visual** do Projeto Integrador. O componente mede a imagem
com OpenCV e responde se ela é legível, apontando o motivo quando não for:

* ``boa`` — nítida, com brilho adequado e texto em tamanho suficiente;
* ``torta`` — legível, mas o documento está inclinado;
* ``borrada`` — fora de foco;
* ``iluminacao`` — escura ou estourada;
* ``baixa_resolucao`` — foto pequena ou documento longe demais.

As regras e os limiares vêm de ``ai-model/models/limiares.json``, calibrado por
``ai-model/scripts/calibrar.py``. O backend só consome o resultado da
calibração — o modelo não é treinado em tempo de execução.

O aviso é **orientativo**: quem chama decide se bloqueia o envio (o LifeScan
não bloqueia).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import median

from app.core.config import obter_configuracoes

logger = logging.getLogger(__name__)

try:  # pragma: no cover - depende das bibliotecas instaladas no ambiente
    import cv2
    import numpy as np
except ImportError:  # pragma: no cover
    cv2 = None
    np = None

# Maior lado usado na análise. A calibração foi feita em imagens de 900x1200,
# então reduzimos fotos de celular para manter os indicadores comparáveis.
LADO_MAXIMO_ANALISE = 1200

# Usados quando o arquivo do modelo não existe ou está incompleto: mantêm o
# endpoint funcionando (com aviso no log) em vez de derrubar o sistema.
LIMIARES_PADRAO: dict[str, float] = {
    "nitidez_minima": 96.02,
    "brilho_minimo": 132.08,
    "brilho_maximo": 231.45,
    "resolucao_minima_px": 600,
    # Valor conservador: o dataset sintético atual tem linhas de 6 a 11 px numa
    # página de 1200 px (0,005 a 0,009). A calibração com o dataset ampliado
    # (ai-model/scripts/calibrar.py) substitui este padrão.
    "altura_texto_relativa_minima": 0.004,
    "angulo_maximo": 8.0,
}

MOTIVOS: dict[str, str] = {
    "boa": "",
    "torta": "O documento está inclinado. Tente fotografar de frente.",
    "borrada": "A foto está fora de foco. Segure o celular firme e tente novamente.",
    "iluminacao": "A foto está escura ou com brilho demais. Procure um lugar bem iluminado.",
    "baixa_resolucao": "A foto está pequena ou o documento está longe. Aproxime o celular.",
}

CLASSES = tuple(MOTIVOS)


class ErroImagemInvalida(ValueError):
    """O conteúdo enviado não pôde ser decodificado como imagem."""


class ErroComponenteIndisponivel(RuntimeError):
    """As bibliotecas de visão computacional não estão instaladas no ambiente."""


@dataclass(frozen=True)
class Limiares:
    """Limiares calibrados que separam as classes de qualidade."""

    nitidez_minima: float
    brilho_minimo: float
    brilho_maximo: float
    resolucao_minima_px: int
    altura_texto_relativa_minima: float
    angulo_maximo: float


@dataclass(frozen=True)
class ResultadoQualidade:
    """Resposta do componente para uma foto."""

    legivel: bool
    classe: str
    motivo: str
    confianca: float
    indicadores: dict[str, float]


def carregar_limiares(caminho: Path) -> Limiares:
    """Lê o arquivo do modelo; campos ausentes ou inválidos caem no padrão."""
    dados: dict = {}
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except FileNotFoundError:
        logger.warning("Limiares de IA não encontrados em %s; usando os valores padrão.", caminho)
    except (OSError, json.JSONDecodeError) as erro:
        logger.warning("Não foi possível ler os limiares de IA em %s (%s); usando os padrão.", caminho, erro)

    valores = dict(LIMIARES_PADRAO)
    for nome in LIMIARES_PADRAO:
        valor = dados.get(nome)
        if isinstance(valor, (int, float)) and not isinstance(valor, bool):
            valores[nome] = valor
    valores["resolucao_minima_px"] = int(valores["resolucao_minima_px"])
    return Limiares(**valores)


@lru_cache(maxsize=1)
def limiares_atuais() -> Limiares:
    """Limiares carregados uma única vez por processo (o arquivo só muda ao recalibrar)."""
    return carregar_limiares(obter_configuracoes().caminho_limiares_ia)


def _exigir_bibliotecas() -> None:
    if cv2 is None or np is None:
        raise ErroComponenteIndisponivel(
            "O componente de IA precisa de opencv-python-headless e numpy instalados no backend."
        )


def _decodificar(conteudo: bytes) -> "np.ndarray":
    _exigir_bibliotecas()
    buffer = np.frombuffer(conteudo, dtype=np.uint8)
    imagem = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
    if imagem is None:
        raise ErroImagemInvalida("Não foi possível ler a imagem enviada.")
    return imagem


def _reduzir_para_analise(imagem: "np.ndarray") -> "np.ndarray":
    """Reduz o maior lado para LADO_MAXIMO_ANALISE (nunca amplia)."""
    altura, largura = imagem.shape[:2]
    lado_maior = max(altura, largura)
    if lado_maior <= LADO_MAXIMO_ANALISE:
        return imagem
    escala = LADO_MAXIMO_ANALISE / lado_maior
    return cv2.resize(
        imagem,
        (max(1, round(largura * escala)), max(1, round(altura * escala))),
        interpolation=cv2.INTER_AREA,
    )


def _normalizar_angulo(angulo: float) -> float:
    """Traz o ângulo do minAreaRect para a faixa [-45, 45] graus."""
    while angulo > 45:
        angulo -= 90
    while angulo < -45:
        angulo += 90
    return angulo


def _medir_texto(cinza: "np.ndarray") -> tuple[float, float]:
    """Devolve (altura relativa das linhas de texto, inclinação mediana em graus).

    As linhas são encontradas binarizando a imagem (Otsu) e fechando na
    horizontal, o que une as letras de uma mesma linha em uma faixa. Só entram
    faixas com pelo menos 15% da largura da imagem — isso descarta ruído e
    cantos escuros.
    """
    altura, largura = cinza.shape[:2]
    _, binaria = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(5, largura // 25), 1))
    faixas = cv2.morphologyEx(binaria, cv2.MORPH_CLOSE, kernel)

    contornos, _ = cv2.findContours(faixas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largura_minima = largura * 0.15
    alturas: list[int] = []
    angulos: list[float] = []
    for contorno in contornos:
        _, _, largura_caixa, altura_caixa = cv2.boundingRect(contorno)
        if largura_caixa <= largura_minima:
            continue
        alturas.append(altura_caixa)
        (_, _), (_, _), angulo = cv2.minAreaRect(contorno)
        angulos.append(_normalizar_angulo(float(angulo)))

    if not alturas:
        return 0.0, 0.0
    return median(alturas) / altura, median(angulos)


def extrair_indicadores(imagem: "np.ndarray", resolucao_px: int | None = None) -> dict[str, float]:
    """Calcula os seis indicadores usados na classificação."""
    _exigir_bibliotecas()
    cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    altura_texto_relativa, angulo = _medir_texto(cinza)
    return {
        "nitidez": float(cv2.Laplacian(cinza, cv2.CV_64F).var()),
        "brilho": float(cinza.mean()),
        "contraste": float(cinza.std()),
        "resolucao_px": int(resolucao_px if resolucao_px is not None else min(cinza.shape[:2])),
        "altura_texto_relativa": float(altura_texto_relativa),
        "angulo": float(angulo),
    }


def _confianca_abaixo(valor: float, limite: float) -> float:
    if limite <= 0:
        return 1.0
    return round(0.5 + 0.5 * min((limite - valor) / limite, 1.0), 2)


def _confianca_acima(valor: float, limite: float) -> float:
    if limite >= 255:
        return 1.0
    return round(0.5 + 0.5 * min((valor - limite) / (255 - limite), 1.0), 2)


def classificar(indicadores: dict[str, float], limiares: Limiares) -> tuple[str, float]:
    """Aplica as regras de decisão, na ordem em que os problemas se sobrepõem.

    A iluminação vem primeiro porque foto estourada perde nitidez; a resolução
    vem antes da nitidez porque imagem pequena não tem bordas suficientes para
    medir foco.
    """
    brilho = indicadores["brilho"]

    if brilho < limiares.brilho_minimo:
        return "iluminacao", _confianca_abaixo(brilho, limiares.brilho_minimo)
    if brilho > limiares.brilho_maximo:
        return "iluminacao", _confianca_acima(brilho, limiares.brilho_maximo)

    if indicadores["resolucao_px"] < limiares.resolucao_minima_px:
        return "baixa_resolucao", _confianca_abaixo(
            indicadores["resolucao_px"], limiares.resolucao_minima_px
        )
    if indicadores["altura_texto_relativa"] < limiares.altura_texto_relativa_minima:
        return "baixa_resolucao", _confianca_abaixo(
            indicadores["altura_texto_relativa"], limiares.altura_texto_relativa_minima
        )

    if abs(indicadores["angulo"]) > limiares.angulo_maximo:
        return "torta", _confianca_acima(abs(indicadores["angulo"]), limiares.angulo_maximo)

    if indicadores["nitidez"] < limiares.nitidez_minima:
        return "borrada", _confianca_abaixo(indicadores["nitidez"], limiares.nitidez_minima)

    margem = min(
        (indicadores["nitidez"] - limiares.nitidez_minima) / limiares.nitidez_minima,
        (brilho - limiares.brilho_minimo) / limiares.brilho_minimo,
        (limiares.brilho_maximo - brilho) / (255 - limiares.brilho_maximo),
    )
    return "boa", round(0.5 + 0.5 * min(max(margem, 0.0), 1.0), 2)


def verificar_qualidade(conteudo: bytes) -> ResultadoQualidade:
    """Analisa a foto e devolve a classe, o motivo e os indicadores medidos."""
    imagem = _decodificar(conteudo)
    resolucao_px = int(min(imagem.shape[:2]))
    indicadores = extrair_indicadores(_reduzir_para_analise(imagem), resolucao_px=resolucao_px)
    classe, confianca = classificar(indicadores, limiares_atuais())
    return ResultadoQualidade(
        legivel=classe in ("boa", "torta"),
        classe=classe,
        motivo=MOTIVOS[classe],
        confianca=confianca,
        indicadores=indicadores,
    )
