"""Calibra os limiares de qualidade de imagem e avalia o componente de IA.

Para cada foto do dataset calcula três indicadores com OpenCV:

* **nitidez** — variância do Laplaciano (bordas fortes = foto em foco);
* **brilho** — média dos tons de cinza (foto escura/estourada);
* **contraste** — desvio-padrão dos tons de cinza (foto "apagada").

Depois procura, no conjunto de calibração, os limiares que maximizam o F1
macro (a média do F1 das três classes) e mede o resultado no conjunto de
teste, comparando com o baseline "responder sempre a classe mais frequente".

Saídas:
* ``models/limiares.json`` — o "modelo salvo" que o backend carrega;
* ``resultados/`` — métricas em JSON e figuras para o relatório.

Uso:
    python ai-model/scripts/calibrar.py
"""

from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

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

CLASSES = ("boa", "borrada", "iluminacao")
NOMES_LEGIVEIS = {"boa": "boa", "borrada": "borrada", "iluminacao": "iluminação"}


def extrair_indicadores(caminho: Path) -> dict[str, float]:
    """Calcula os três indicadores de qualidade de uma imagem."""
    imagem = cv2.imread(str(caminho), cv2.IMREAD_GRAYSCALE)
    if imagem is None:
        raise ValueError(f"Não foi possível ler a imagem: {caminho}")
    return {
        "nitidez": float(cv2.Laplacian(imagem, cv2.CV_64F).var()),
        "brilho": float(imagem.mean()),
        "contraste": float(imagem.std()),
    }


def classificar(indicadores: dict[str, float], limiares: dict[str, float]) -> tuple[str, float]:
    """Aplica as regras de decisão e devolve (classe, confiança entre 0.5 e 1)."""
    nitidez = indicadores["nitidez"]
    brilho = indicadores["brilho"]

    # Iluminação primeiro: foto estourada perde nitidez (clareia as bordas),
    # então a checagem de brilho precisa vir antes da de foco.
    if brilho < limiares["brilho_minimo"]:
        distancia = (limiares["brilho_minimo"] - brilho) / limiares["brilho_minimo"]
        return "iluminacao", round(0.5 + 0.5 * min(distancia, 1.0), 2)

    if brilho > limiares["brilho_maximo"]:
        distancia = (brilho - limiares["brilho_maximo"]) / (255 - limiares["brilho_maximo"])
        return "iluminacao", round(0.5 + 0.5 * min(distancia, 1.0), 2)

    if nitidez < limiares["nitidez_minima"]:
        distancia = (limiares["nitidez_minima"] - nitidez) / limiares["nitidez_minima"]
        return "borrada", round(0.5 + 0.5 * min(distancia, 1.0), 2)

    margem = min(
        (nitidez - limiares["nitidez_minima"]) / limiares["nitidez_minima"],
        (brilho - limiares["brilho_minimo"]) / limiares["brilho_minimo"],
        (limiares["brilho_maximo"] - brilho) / (255 - limiares["brilho_maximo"]),
    )
    return "boa", round(0.5 + 0.5 * min(margem, 1.0), 2)


def calibrar(amostras: list[dict]) -> dict[str, float]:
    """Procura os limiares que maximizam o F1 macro no conjunto de calibração."""
    nitidezes = np.array([amostra["nitidez"] for amostra in amostras])
    brilhos = np.array([amostra["brilho"] for amostra in amostras])
    verdadeiros = [amostra["classe"] for amostra in amostras]

    candidatos_nitidez = np.unique(np.quantile(nitidezes, np.linspace(0.02, 0.65, 18)))
    candidatos_escuro = np.unique(np.quantile(brilhos, np.linspace(0.02, 0.42, 9)))
    candidatos_claro = np.unique(np.quantile(brilhos, np.linspace(0.58, 0.98, 9)))

    melhor: dict[str, float] | None = None
    melhor_f1 = -1.0
    melhor_acuracia = -1.0

    for nitidez_minima in candidatos_nitidez:
        for brilho_minimo in candidatos_escuro:
            for brilho_maximo in candidatos_claro:
                if brilho_minimo >= brilho_maximo:
                    continue
                limiares = {
                    "nitidez_minima": float(nitidez_minima),
                    "brilho_minimo": float(brilho_minimo),
                    "brilho_maximo": float(brilho_maximo),
                }
                previstos = [classificar(amostra, limiares)[0] for amostra in amostras]
                f1 = f1_score(verdadeiros, previstos, average="macro", labels=list(CLASSES))
                acuracia = accuracy_score(verdadeiros, previstos)
                if f1 > melhor_f1 or (f1 == melhor_f1 and acuracia > melhor_acuracia):
                    melhor, melhor_f1, melhor_acuracia = limiares, f1, acuracia

    assert melhor is not None
    return melhor


def salvar_figuras(amostras: list[dict], limiares: dict[str, float], matriz: np.ndarray) -> None:
    """Gera as figuras de evidência exigidas pelo eixo de Computação Visual."""
    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    cores = {"boa": "#2e7d32", "borrada": "#c62828", "iluminacao": "#f9a825"}

    # 1) Matriz de confusão
    figura, eixo = plt.subplots(figsize=(5.5, 4.5))
    imagem = eixo.imshow(matriz, cmap="Blues")
    eixo.set_xticks(range(len(CLASSES)), [NOMES_LEGIVEIS[c] for c in CLASSES])
    eixo.set_yticks(range(len(CLASSES)), [NOMES_LEGIVEIS[c] for c in CLASSES])
    eixo.set_xlabel("Previsto")
    eixo.set_ylabel("Real")
    eixo.set_title("Matriz de confusão — conjunto de teste")
    for linha in range(len(CLASSES)):
        for coluna in range(len(CLASSES)):
            eixo.text(
                coluna, linha, int(matriz[linha, coluna]),
                ha="center", va="center",
                color="white" if matriz[linha, coluna] > matriz.max() / 2 else "black",
            )
    figura.colorbar(imagem, ax=eixo, fraction=0.046, pad=0.04)
    figura.tight_layout()
    figura.savefig(PASTA_RESULTADOS / "matriz_confusao.png", dpi=150)
    plt.close(figura)

    # 2) Dispersão nitidez × brilho, colorida pela classe real
    figura, eixo = plt.subplots(figsize=(6.5, 4.5))
    for classe in CLASSES:
        pontos = [amostra for amostra in amostras if amostra["classe"] == classe]
        eixo.scatter(
            [amostra["nitidez"] for amostra in pontos],
            [amostra["brilho"] for amostra in pontos],
            label=NOMES_LEGIVEIS[classe], color=cores[classe], alpha=0.8, edgecolors="white",
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

    # 3) Entrada e saída lado a lado: um exemplo de cada classe
    figura, eixos = plt.subplots(1, 3, figsize=(11, 4.5))
    for eixo, classe in zip(eixos, CLASSES):
        exemplo = next(amostra for amostra in amostras if amostra["classe"] == classe)
        imagem = cv2.imread(str(PASTA_FOTOS / exemplo["arquivo"]), cv2.IMREAD_GRAYSCALE)
        previsto, confianca = classificar(exemplo, limiares)
        eixo.imshow(imagem, cmap="gray", vmin=0, vmax=255)
        eixo.set_title(f"real: {NOMES_LEGIVEIS[classe]}\nprevisto: {NOMES_LEGIVEIS[previsto]} ({confianca:.0%})")
        eixo.axis("off")
    figura.suptitle("Exemplos de entrada e saída do componente de IA")
    figura.tight_layout()
    figura.savefig(PASTA_RESULTADOS / "exemplos_lado_a_lado.png", dpi=150)
    plt.close(figura)

    # 4) Distribuição da nitidez por classe
    figura, eixo = plt.subplots(figsize=(6.5, 4))
    for classe in CLASSES:
        valores = [amostra["nitidez"] for amostra in amostras if amostra["classe"] == classe]
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
        amostras.append({**indicadores, "classe": linha["classe"], "conjunto": linha["conjunto"], "arquivo": linha["arquivo"]})

    treino = [amostra for amostra in amostras if amostra["conjunto"] == "treino"]
    teste = [amostra for amostra in amostras if amostra["conjunto"] == "teste"]
    print(f"Calibrando com {len(treino)} fotos; avaliando com {len(teste)} fotos...\n")

    limiares = calibrar(treino)

    verdadeiros = [amostra["classe"] for amostra in teste]
    previsoes = [classificar(amostra, limiares) for amostra in teste]
    previstos = [previsao[0] for previsao in previsoes]

    acuracia = accuracy_score(verdadeiros, previstos)
    f1_macro = f1_score(verdadeiros, previstos, average="macro", labels=list(CLASSES))
    matriz = confusion_matrix(verdadeiros, previstos, labels=list(CLASSES))

    # Baseline simples: responder sempre a classe mais frequente no treino
    classe_mais_frequente = max(CLASSES, key=lambda classe: sum(1 for a in treino if a["classe"] == classe))
    previstos_baseline = [classe_mais_frequente] * len(verdadeiros)
    acuracia_baseline = accuracy_score(verdadeiros, previstos_baseline)
    f1_baseline = f1_score(verdadeiros, previstos_baseline, average="macro", labels=list(CLASSES))

    print("Limiares calibrados:")
    for nome, valor in limiares.items():
        print(f"  {nome:16s} {valor:.2f}")
    print()
    print("Relatório no conjunto de teste:")
    print(classification_report(verdadeiros, previstos, labels=list(CLASSES), target_names=[NOMES_LEGIVEIS[c] for c in CLASSES], zero_division=0))
    print("Matriz de confusão (linhas = real, colunas = previsto):")
    print(matriz)
    print()
    print(f"Acurácia do componente: {acuracia:.1%} | F1 macro: {f1_macro:.3f}")
    print(f"Baseline ({classe_mais_frequente}): acurácia {acuracia_baseline:.1%} | F1 macro: {f1_baseline:.3f}")
    print(f"Ganho sobre o baseline: +{f1_macro - f1_baseline:.3f} de F1 macro")

    PASTA_MODELOS.mkdir(parents=True, exist_ok=True)
    (PASTA_MODELOS / "limiares.json").write_text(
        json.dumps(
            {
                "versao": "1.0",
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
