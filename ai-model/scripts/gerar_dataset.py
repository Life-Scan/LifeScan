"""Gera o dataset sintético de qualidade de fotos de documentos.

O recurso de IA avalia fotos de documentos enviadas pelo paciente (nítida,
borrada ou com iluminação ruim). Como ainda não temos um acervo grande de
fotos reais, este script:

1. desenha páginas de documento sintéticas (texto simulado, tabela, margens);
2. aplica degradações controladas para cada classe:
   - ``boa``: praticamente sem degradação;
   - ``borrada``: desfoque gaussiano de raio variável;
   - ``iluminacao``: sub ou superexposição (foto escura ou estourada);
3. divide 70% para calibração e 30% para teste, por classe;
4. grava tudo em ``datasets/fotos`` e o índice em ``datasets/rotulos.csv``.

A semente é fixa: o mesmo comando gera o mesmo dataset em qualquer máquina.

Uso:
    python ai-model/scripts/gerar_dataset.py
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SEMENTE = 42
RAIZ = Path(__file__).resolve().parents[1]
PASTA_FOTOS = RAIZ / "datasets" / "fotos"
ARQUIVO_ROTULOS = RAIZ / "datasets" / "rotulos.csv"

POR_CLASSE = 40
PROPORCAO_TREINO = 0.7
LARGURA, ALTURA = 900, 1200
CLASSES = ("boa", "borrada", "iluminacao")


def pagina_de_documento(rng: random.Random) -> Image.Image:
    """Desenha uma página de documento com "texto" simulado, para a IA analisar."""
    pagina = Image.new("L", (LARGURA, ALTURA), 246)
    desenho = ImageDraw.Draw(pagina)
    margem = 70

    # Cabeçalho: duas linhas mais grossas, como um timbre/razão social
    for indice in range(2):
        largura = rng.randint(int(LARGURA * 0.35), int(LARGURA * 0.55))
        y = 60 + indice * 34
        desenho.rectangle(
            (margem, y, margem + largura, y + rng.randint(12, 16)),
            fill=rng.randint(30, 60),
        )

    # Corpo: linhas de texto simuladas, com larguras e tons variados
    y = 160
    while y < ALTURA - 220:
        largura = rng.randint(int(LARGURA * 0.25), int(LARGURA * 0.78))
        espessura = rng.randint(6, 11)
        tom = rng.randint(55, 130)
        desenho.rectangle((margem, y, margem + largura, y + espessura), fill=tom)
        y += rng.randint(34, 48)
        if rng.random() < 0.18:  # linha em branco de parágrafo
            y += 18

    # Tabela de resultados, no meio do documento
    topo, esquerda = 620, margem
    largura_tabela, altura_tabela = LARGURA - 2 * margem, 210
    desenho.rectangle(
        (esquerda, topo, esquerda + largura_tabela, topo + altura_tabela),
        outline=70,
        width=3,
    )
    for linha in range(1, 4):
        y_linha = topo + linha * altura_tabela // 4
        desenho.line((esquerda, y_linha, esquerda + largura_tabela, y_linha), fill=90, width=2)
    for coluna in range(1, 4):
        x_coluna = esquerda + coluna * largura_tabela // 4
        desenho.line((x_coluna, topo, x_coluna, topo + altura_tabela), fill=90, width=2)

    # Assinatura/rodapé
    desenho.line((margem, ALTURA - 120, margem + 260, ALTURA - 120), fill=80, width=2)
    desenho.rectangle((margem, ALTURA - 90, margem + 180, ALTURA - 82), fill=120)

    return pagina


def degradar(pagina: Image.Image, classe: str, rng: random.Random) -> Image.Image:
    """Aplica a degradação que caracteriza a classe (determinística pela semente)."""
    if classe == "borrada":
        # Desfoque gaussiano: é o que destrói a nitidez medida pelo Laplaciano
        return pagina.filter(ImageFilter.GaussianBlur(radius=rng.uniform(2.2, 5.5)))

    if classe == "iluminacao":
        if rng.random() < 0.5:
            fator_brilho = rng.uniform(0.30, 0.55)  # foto escura
        else:
            fator_brilho = rng.uniform(1.45, 1.90)  # foto estourada
        foto = ImageEnhance.Brightness(pagina).enhance(fator_brilho)
        return ImageEnhance.Contrast(foto).enhance(rng.uniform(0.65, 0.95))

    # "boa": variação leve de brilho/contraste, como uma foto bem tirada
    # (sem estourar o branco, para não se confundir com a classe "iluminacao")
    foto = ImageEnhance.Brightness(pagina).enhance(rng.uniform(0.92, 1.00))
    return ImageEnhance.Contrast(foto).enhance(rng.uniform(0.95, 1.05))


def main() -> None:
    rng = random.Random(SEMENTE)
    if PASTA_FOTOS.exists():
        for arquivo in PASTA_FOTOS.rglob("*.jpg"):
            arquivo.unlink()

    linhas: list[dict[str, str]] = []
    for classe in CLASSES:
        quantidade_treino = round(POR_CLASSE * PROPORCAO_TREINO)
        for indice in range(POR_CLASSE):
            conjunto = "treino" if indice < quantidade_treino else "teste"
            pagina = pagina_de_documento(rng)
            foto = degradar(pagina, classe, rng)

            destino = PASTA_FOTOS / conjunto / classe
            destino.mkdir(parents=True, exist_ok=True)
            nome = f"{classe}_{indice:03d}.jpg"
            foto.convert("RGB").save(destino / nome, quality=88)

            linhas.append(
                {
                    "arquivo": f"{conjunto}/{classe}/{nome}",
                    "classe": classe,
                    "conjunto": conjunto,
                }
            )

    ARQUIVO_ROTULOS.parent.mkdir(parents=True, exist_ok=True)
    with ARQUIVO_ROTULOS.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=["arquivo", "classe", "conjunto"])
        escritor.writeheader()
        escritor.writerows(linhas)

    treino = sum(1 for linha in linhas if linha["conjunto"] == "treino")
    teste = len(linhas) - treino
    print(f"Dataset gerado: {len(linhas)} imagens ({treino} calibração, {teste} teste)")
    for classe in CLASSES:
        total = sum(1 for linha in linhas if linha["classe"] == classe)
        print(f"  {classe:12s} {total:3d} imagens")


if __name__ == "__main__":
    main()
