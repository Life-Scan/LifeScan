"""Calibra os limiares de qualidade e legibilidade de imagem e avalia o componente de IA.

Para cada foto do dataset calcula seis indicadores com OpenCV (idênticos aos do backend):

* **nitidez** — variância do Laplaciano (bordas fortes = foto em foco);
* **brilho** — média dos tons de cinza (foto escura/estourada);
* **contraste** — desvio-padrão dos tons de cinza (foto "apagada");
* **resolucao_px** — menor lado da imagem original em pixels;
* **altura_texto_relativa** — mediana da altura das faixas de texto dividida pela altura;
* **angulo** — mediana da inclinação das faixas de texto em graus.

Depois procura, no conjunto de treino, os 6 limiares por busca coordenada
maximizando o F1 macro das 5 classes (``boa``, ``torta``, ``borrada``,
``iluminacao``, ``baixa_resolucao``) e mede o resultado no conjunto de teste,
comparando com o baseline "responder sempre a classe mais frequente".

Saídas:
* ``models/limiares.json`` — o "modelo salvo" (versão 2.0) que o backend carrega;
* ``resultados/`` — figuras de avaliação para o relatório.

Uso:
    python ai-model/scripts/calibrar.py
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

import cv2
import matplotlib

matplotlib.use("Agg")  # gera arquivos, sem abrir janela

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score

SEMENTE = 42
RAIZ = Path(__file__).resolve().parents[1]
PASTA_FOTOS = RAIZ / "datasets" / "fotos"
ARQUIVO_ROTULOS = RAIZ / "datasets" / "rotulos.csv"
PASTA_MODELOS = RAIZ / "models"
PASTA_RESULTADOS = RAIZ / "resultados"

LADO_MAXIMO_ANALISE = 1200

CLASSES = ("boa", "torta", "borrada", "iluminacao", "baixa_resolucao")
NOMES_LEGIVEIS = {
    "boa": "boa",
    "torta": "torta",
    "borrada": "borrada",
    "iluminacao": "iluminação",
    "baixa_resolucao": "baixa resolução",
}

LIMIARES_INICIAIS: dict[str, float | int] = {
    "nitidez_minima": 96.02,
    "brilho_minimo": 132.08,
    "brilho_maximo": 231.45,
    "resolucao_minima_px": 600,
    "altura_texto_relativa_minima": 0.004,
    "angulo_maximo": 8.0,
}


def _reduzir_para_analise(imagem: np.ndarray) -> np.ndarray:
    """Reduz o maior lado para LADO_MAXIMO_ANALISE (nunca amplia), igual ao backend."""
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


def _medir_texto(cinza: np.ndarray) -> tuple[float, float]:
    """Calcula (altura_texto_relativa, angulo) com a mesma fórmula do backend."""
    altura, largura = cinza.shape[:2]
    _, binaria = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (max(5, largura // 25), 1))
    faixas = cv2.morphologyEx(binaria, cv2.MORPH_CLOSE, kernel)
    contornos, _ = cv2.findContours(faixas, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    alturas, angulos = [], []
    for contorno in contornos:
        _, _, largura_caixa, altura_caixa = cv2.boundingRect(contorno)
        if largura_caixa <= largura * 0.15:
            continue
        alturas.append(altura_caixa)
        (_, _), (_, _), angulo = cv2.minAreaRect(contorno)
        angulos.append(_normalizar_angulo(float(angulo)))

    altura_texto_relativa = median(alturas) / altura if alturas else 0.0
    angulo = median(angulos) if angulos else 0.0
    return float(altura_texto_relativa), float(angulo)


def extrair_indicadores(caminho: Path) -> dict[str, float | int]:
    """Calcula os seis indicadores de qualidade e legibilidade de uma imagem."""
    imagem = cv2.imread(str(caminho), cv2.IMREAD_COLOR)
    if imagem is None:
        raise ValueError(f"Não foi possível ler a imagem: {caminho}")
    resolucao_px = int(min(imagem.shape[:2]))
    reduzida = _reduzir_para_analise(imagem)
    cinza = cv2.cvtColor(reduzida, cv2.COLOR_BGR2GRAY)
    altura_texto_relativa, angulo = _medir_texto(cinza)
    return {
        "nitidez": float(cv2.Laplacian(cinza, cv2.CV_64F).var()),
        "brilho": float(cinza.mean()),
        "contraste": float(cinza.std()),
        "resolucao_px": resolucao_px,
        "altura_texto_relativa": altura_texto_relativa,
        "angulo": angulo,
    }


def _confianca_abaixo(valor: float, limite: float) -> float:
    if limite <= 0:
        return 1.0
    return round(0.5 + 0.5 * min((limite - valor) / limite, 1.0), 2)


def _confianca_acima(valor: float, limite: float) -> float:
    if limite >= 255:
        return 1.0
    return round(0.5 + 0.5 * min((valor - limite) / (255 - limite), 1.0), 2)


def classificar(indicadores: dict[str, float | int], limiares: dict[str, float | int]) -> tuple[str, float]:
    """Aplica as regras de decisão na ordem do contrato e devolve (classe, confiança)."""
    brilho = float(indicadores["brilho"])

    if brilho < limiares["brilho_minimo"]:
        return "iluminacao", _confianca_abaixo(brilho, float(limiares["brilho_minimo"]))
    if brilho > limiares["brilho_maximo"]:
        return "iluminacao", _confianca_acima(brilho, float(limiares["brilho_maximo"]))

    if indicadores["resolucao_px"] < limiares["resolucao_minima_px"]:
        return "baixa_resolucao", _confianca_abaixo(
            float(indicadores["resolucao_px"]), float(limiares["resolucao_minima_px"])
        )
    if indicadores["altura_texto_relativa"] < limiares["altura_texto_relativa_minima"]:
        return "baixa_resolucao", _confianca_abaixo(
            float(indicadores["altura_texto_relativa"]), float(limiares["altura_texto_relativa_minima"])
        )

    if abs(float(indicadores["angulo"])) > limiares["angulo_maximo"]:
        return "torta", _confianca_acima(abs(float(indicadores["angulo"])), float(limiares["angulo_maximo"]))

    if indicadores["nitidez"] < limiares["nitidez_minima"]:
        return "borrada", _confianca_abaixo(float(indicadores["nitidez"]), float(limiares["nitidez_minima"]))

    margem = min(
        (float(indicadores["nitidez"]) - float(limiares["nitidez_minima"])) / float(limiares["nitidez_minima"]),
        (brilho - float(limiares["brilho_minimo"])) / float(limiares["brilho_minimo"]),
        (float(limiares["brilho_maximo"]) - brilho) / (255.0 - float(limiares["brilho_maximo"])),
    )
    return "boa", round(0.5 + 0.5 * min(max(margem, 0.0), 1.0), 2)


def _avaliar(amostras: list[dict], verdadeiros: list[str], limiares: dict[str, float | int]) -> tuple[float, float]:
    previstos = [classificar(amostra, limiares)[0] for amostra in amostras]
    f1 = float(f1_score(verdadeiros, previstos, average="macro", labels=list(CLASSES), zero_division=0))
    acuracia = float(accuracy_score(verdadeiros, previstos))
    return f1, acuracia


def calibrar(amostras: list[dict]) -> dict[str, float | int]:
    """Busca coordenada dos 6 limiares maximizando o F1 macro no conjunto de treino."""
    nitidezes = np.array([amostra["nitidez"] for amostra in amostras])
    brilhos = np.array([amostra["brilho"] for amostra in amostras])
    alturas_texto = np.array([amostra["altura_texto_relativa"] for amostra in amostras])
    verdadeiros = [amostra["classe"] for amostra in amostras]

    grade_candidatos: dict[str, list[float | int]] = {
        "nitidez_minima": [float(v) for v in np.unique(np.quantile(nitidezes, np.linspace(0.02, 0.65, 25)))],
        "brilho_minimo": [float(v) for v in np.unique(np.quantile(brilhos, np.linspace(0.02, 0.42, 15)))],
        "brilho_maximo": [float(v) for v in np.unique(np.quantile(brilhos, np.linspace(0.58, 0.98, 15)))],
        "resolucao_minima_px": [400, 500, 600, 700, 800, 900],
        "altura_texto_relativa_minima": [
            float(v) for v in np.unique(np.quantile(alturas_texto, np.linspace(0.01, 0.20, 20)))
        ],
        "angulo_maximo": [4.0, 6.0, 8.0, 10.0, 12.0, 15.0, 20.0],
    }

    melhor: dict[str, float | int] = dict(LIMIARES_INICIAIS)
    melhor_f1, melhor_acuracia = _avaliar(amostras, verdadeiros, melhor)

    for _passada in range(3):
        mudou = False
        for parametro, candidatos in grade_candidatos.items():
            opcoes = [melhor[parametro], *candidatos]
            for candidato in opcoes:
                tentativa = dict(melhor)
                tentativa[parametro] = candidato
                if tentativa["brilho_minimo"] >= tentativa["brilho_maximo"]:
                    continue
                f1, acuracia = _avaliar(amostras, verdadeiros, tentativa)
                if (f1, acuracia) > (melhor_f1, melhor_acuracia):
                    melhor = tentativa
                    melhor_f1, melhor_acuracia = f1, acuracia
                    mudou = True
        if not mudou:
            break

    melhor["resolucao_minima_px"] = int(melhor["resolucao_minima_px"])
    return melhor


def salvar_figuras(amostras: list[dict], limiares: dict[str, float | int], matriz: np.ndarray) -> None:
    """Gera as figuras de evidência exigidas pelo eixo de Computação Visual."""
    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    cores = {
        "boa": "#2e7d32",
        "torta": "#1565c0",
        "borrada": "#c62828",
        "iluminacao": "#f9a825",
        "baixa_resolucao": "#6a1b9a",
    }

    # 1) Matriz de confusão 5×5
    figura, eixo = plt.subplots(figsize=(7.5, 6.2))
    imagem = eixo.imshow(matriz, cmap="Blues")
    rotulos_legiveis = [NOMES_LEGIVEIS[c] for c in CLASSES]
    eixo.set_xticks(range(len(CLASSES)), rotulos_legiveis, rotation=20, ha="right")
    eixo.set_yticks(range(len(CLASSES)), rotulos_legiveis)
    eixo.set_xlabel("Previsto")
    eixo.set_ylabel("Real")
    eixo.set_title("Matriz de confusão (5×5) — conjunto de teste")
    limite_cor = matriz.max() / 2 if matriz.max() > 0 else 0
    for linha in range(len(CLASSES)):
        for coluna in range(len(CLASSES)):
            eixo.text(
                coluna,
                linha,
                int(matriz[linha, coluna]),
                ha="center",
                va="center",
                color="white" if matriz[linha, coluna] > limite_cor else "black",
            )
    figura.colorbar(imagem, ax=eixo, fraction=0.046, pad=0.04)
    figura.tight_layout()
    figura.savefig(PASTA_RESULTADOS / "matriz_confusao.png", dpi=150)
    plt.close(figura)

    # 2) Dispersão nitidez × brilho, colorida pela classe real
    figura, eixo = plt.subplots(figsize=(7.0, 4.8))
    for classe in CLASSES:
        pontos = [amostra for amostra in amostras if amostra["classe"] == classe]
        if not pontos:
            continue
        eixo.scatter(
            [amostra["nitidez"] for amostra in pontos],
            [amostra["brilho"] for amostra in pontos],
            label=NOMES_LEGIVEIS[classe],
            color=cores[classe],
            alpha=0.8,
            edgecolors="white",
        )
    eixo.set_xscale("log")
    eixo.axvline(limiares["nitidez_minima"], color="#555", linestyle="--", linewidth=1)
    eixo.axhline(limiares["brilho_minimo"], color="#555", linestyle=":", linewidth=1)
    eixo.axhline(limiares["brilho_maximo"], color="#555", linestyle=":", linewidth=1)
    eixo.set_xlabel("Nitidez (variância do Laplaciano, escala log)")
    eixo.set_ylabel("Brilho médio (0–255)")
    eixo.set_title("Separação das classes pelos indicadores")
    eixo.legend()
    figura.tight_layout()
    figura.savefig(PASTA_RESULTADOS / "dispersao_indicadores.png", dpi=150)
    plt.close(figura)

    # 3) Entrada e saída lado a lado: um exemplo de cada classe disponível
    exemplos = []
    for classe in CLASSES:
        exemplo = next((amostra for amostra in amostras if amostra["classe"] == classe), None)
        if exemplo is not None:
            exemplos.append((classe, exemplo))

    figura, eixos = plt.subplots(1, len(exemplos), figsize=(3.5 * len(exemplos), 4.5))
    if len(exemplos) == 1:
        eixos = [eixos]
    for eixo, (classe, exemplo) in zip(eixos, exemplos):
        imagem_foto = cv2.imread(str(PASTA_FOTOS / exemplo["arquivo"]), cv2.IMREAD_GRAYSCALE)
        previsto, confianca = classificar(exemplo, limiares)
        eixo.imshow(imagem_foto, cmap="gray", vmin=0, vmax=255)
        eixo.set_title(f"real: {NOMES_LEGIVEIS[classe]}\nprevisto: {NOMES_LEGIVEIS[previsto]} ({confianca:.0%})")
        eixo.axis("off")
    figura.suptitle("Exemplos de entrada e saída do componente de IA")
    figura.tight_layout()
    figura.savefig(PASTA_RESULTADOS / "exemplos_lado_a_lado.png", dpi=150)
    plt.close(figura)

    # 4) Distribuição da nitidez por classe
    figura, eixo = plt.subplots(figsize=(7.0, 4.2))
    for classe in CLASSES:
        valores = [amostra["nitidez"] for amostra in amostras if amostra["classe"] == classe]
        if not valores:
            continue
        eixo.hist(valores, bins=18, alpha=0.6, label=NOMES_LEGIVEIS[classe], color=cores[classe])
    eixo.axvline(limiares["nitidez_minima"], color="#333", linestyle="--", linewidth=1)
    eixo.set_xscale("log")
    eixo.set_xlabel("Nitidez (variância do Laplaciano, escala log)")
    eixo.set_ylabel("Quantidade de fotos")
    eixo.set_title("Distribuição da nitidez por classe")
    eixo.legend()
    figura.tight_layout()
    figura.savefig(PASTA_RESULTADOS / "histograma_nitidez.png", dpi=150)
    plt.close(figura)


def main() -> None:
    np.random.seed(SEMENTE)

    with ARQUIVO_ROTULOS.open(newline="", encoding="utf-8") as arquivo:
        linhas = list(csv.DictReader(arquivo))

    amostras = []
    for linha in linhas:
        indicadores = extrair_indicadores(PASTA_FOTOS / linha["arquivo"])
        amostras.append(
            {**indicadores, "classe": linha["classe"], "conjunto": linha["conjunto"], "arquivo": linha["arquivo"]}
        )

    treino = [amostra for amostra in amostras if amostra["conjunto"] == "treino"]
    teste = [amostra for amostra in amostras if amostra["conjunto"] == "teste"]
    print(f"Calibrando com {len(treino)} fotos; avaliando com {len(teste)} fotos...\n")

    limiares = calibrar(treino)

    verdadeiros = [amostra["classe"] for amostra in teste]
    previsoes = [classificar(amostra, limiares) for amostra in teste]
    previstos = [previsao[0] for previsao in previsoes]

    acuracia = accuracy_score(verdadeiros, previstos)
    f1_macro = f1_score(verdadeiros, previstos, average="macro", labels=list(CLASSES), zero_division=0)
    matriz = confusion_matrix(verdadeiros, previstos, labels=list(CLASSES))

    # Baseline simples: responder sempre a classe mais frequente no treino
    classe_mais_frequente = max(CLASSES, key=lambda classe: sum(1 for a in treino if a["classe"] == classe))
    previstos_baseline = [classe_mais_frequente] * len(verdadeiros)
    acuracia_baseline = accuracy_score(verdadeiros, previstos_baseline)
    f1_baseline = f1_score(verdadeiros, previstos_baseline, average="macro", labels=list(CLASSES), zero_division=0)

    print("Limiares calibrados:")
    for nome, valor in limiares.items():
        if isinstance(valor, int):
            print(f"  {nome:30s} {valor}")
        else:
            print(f"  {nome:30s} {valor:.4f}")
    print()
    print("Relatório no conjunto de teste:")
    print(
        classification_report(
            verdadeiros,
            previstos,
            labels=list(CLASSES),
            target_names=[NOMES_LEGIVEIS[c] for c in CLASSES],
            zero_division=0,
        )
    )
    print("Matriz de confusão 5×5 (linhas = real, colunas = previsto):")
    print(matriz)
    print()
    print(f"Acurácia do componente: {acuracia:.1%} | F1 macro: {f1_macro:.3f}")
    print(f"Baseline ({classe_mais_frequente}): acurácia {acuracia_baseline:.1%} | F1 macro: {f1_baseline:.3f}")
    print(f"Ganho sobre o baseline: +{f1_macro - f1_baseline:.3f} de F1 macro")

    PASTA_MODELOS.mkdir(parents=True, exist_ok=True)
    (PASTA_MODELOS / "limiares.json").write_text(
        json.dumps(
            {
                "versao": "2.0",
                "semente": SEMENTE,
                "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                **limiares,
                "metricas": {
                    "acuracia_teste": round(float(acuracia), 4),
                    "f1_macro_teste": round(float(f1_macro), 4),
                    "acuracia_baseline": round(float(acuracia_baseline), 4),
                    "f1_macro_baseline": round(float(f1_baseline), 4),
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    salvar_figuras(amostras, limiares, matriz)
    print(f"\nLimiares salvos em {PASTA_MODELOS / 'limiares.json'}")
    print(f"Figuras salvas em {PASTA_RESULTADOS}")


if __name__ == "__main__":
    main()
