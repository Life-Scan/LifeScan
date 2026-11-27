"""Testes do componente de IA: qualidade e legibilidade das fotos de documentos."""

import cv2
import numpy as np
import pytest

from app.services import qualidade_imagem
from app.services.qualidade_imagem import Limiares, verificar_qualidade

# Limiares fixos para o teste não depender do arquivo calibrado (que muda quando
# o time recalibra o modelo em ai-model/).
LIMIARES_TESTE = Limiares(
    nitidez_minima=96.02,
    brilho_minimo=132.08,
    brilho_maximo=231.45,
    resolucao_minima_px=600,
    altura_texto_relativa_minima=0.008,
    angulo_maximo=8.0,
)


@pytest.fixture(autouse=True)
def limiares_fixos(monkeypatch):
    monkeypatch.setattr(qualidade_imagem, "limiares_atuais", lambda: LIMIARES_TESTE)


def pagina_de_documento(largura: int = 900, altura: int = 1200) -> np.ndarray:
    """Página sintética: fundo claro, cabeçalho, linhas de "texto" e uma tabela."""
    imagem = np.full((altura, largura, 3), 210, dtype=np.uint8)
    margem = 70
    imagem[60:78, margem : margem + 380] = 45
    imagem[92:104, margem : margem + 260] = 70

    y = 170
    indice = 0
    while y < altura - 240:
        largura_linha = int(largura * (0.30 + 0.45 * (indice % 5) / 4))
        imagem[y : y + 12, margem : margem + largura_linha] = 60
        y += 40
        indice += 1

    cv2.rectangle(imagem, (margem, 640), (largura - margem, 840), (90, 90, 90), 3)
    return imagem


def imagem_boa() -> np.ndarray:
    return pagina_de_documento()


def imagem_borrada() -> np.ndarray:
    return cv2.GaussianBlur(pagina_de_documento(), (0, 0), 4)


def imagem_escura() -> np.ndarray:
    return (pagina_de_documento() * 0.35).astype(np.uint8)


def imagem_pequena() -> np.ndarray:
    return cv2.resize(pagina_de_documento(), (320, 427), interpolation=cv2.INTER_AREA)


def imagem_torta() -> np.ndarray:
    pagina = pagina_de_documento()
    altura, largura = pagina.shape[:2]
    matriz = cv2.getRotationMatrix2D((largura / 2, altura / 2), 15, 1.0)
    return cv2.warpAffine(pagina, matriz, (largura, altura), borderValue=(210, 210, 210))


def imagem_documento_longe() -> np.ndarray:
    """Foto grande (1800x2400) em que a página ocupa só uma parte do quadro."""
    foto = np.full((2400, 1800, 3), 200, dtype=np.uint8)
    pagina = cv2.resize(pagina_de_documento(), (500, 667), interpolation=cv2.INTER_AREA)
    topo = (2400 - 667) // 2
    esquerda = (1800 - 500) // 2
    foto[topo : topo + 667, esquerda : esquerda + 500] = pagina
    return foto


def como_jpeg(imagem: np.ndarray) -> bytes:
    sucesso, buffer = cv2.imencode(".jpg", imagem, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    assert sucesso
    return buffer.tobytes()


@pytest.mark.parametrize(
    ("gerar", "esperado"),
    [
        (imagem_boa, "boa"),
        (imagem_borrada, "borrada"),
        (imagem_escura, "iluminacao"),
        (imagem_pequena, "baixa_resolucao"),
        (imagem_documento_longe, "baixa_resolucao"),
        (imagem_torta, "torta"),
    ],
)
def test_classifica_as_cinco_classes(gerar, esperado):
    resultado = verificar_qualidade(como_jpeg(gerar()))
    assert resultado.classe == esperado, resultado.indicadores


def test_foto_boa_e_legivel_e_sem_aviso():
    resultado = verificar_qualidade(como_jpeg(imagem_boa()))
    assert resultado.legivel is True
    assert resultado.motivo == ""
    assert 0.5 <= resultado.confianca <= 1


def test_foto_borrada_nao_e_legivel_e_explica_o_motivo():
    resultado = verificar_qualidade(como_jpeg(imagem_borrada()))
    assert resultado.legivel is False
    assert "fora de foco" in resultado.motivo


def test_documento_torto_e_legivel_mas_avisa():
    resultado = verificar_qualidade(como_jpeg(imagem_torta()))
    assert resultado.legivel is True
    assert "inclinado" in resultado.motivo


def test_conteudo_que_nao_e_imagem_falha():
    with pytest.raises(qualidade_imagem.ErroImagemInvalida):
        verificar_qualidade(b"isto nao e uma imagem")


def test_limiares_padrao_quando_o_arquivo_nao_existe(tmp_path):
    limiares = qualidade_imagem.carregar_limiares(tmp_path / "nao-existe.json")
    assert limiares.nitidez_minima == qualidade_imagem.LIMIARES_PADRAO["nitidez_minima"]
    assert limiares.resolucao_minima_px == 600


def test_limiares_incompletos_completam_com_o_padrao(tmp_path):
    caminho = tmp_path / "limiares.json"
    caminho.write_text('{"nitidez_minima": 120.0, "versao": "2.0"}', encoding="utf-8")
    limiares = qualidade_imagem.carregar_limiares(caminho)
    assert limiares.nitidez_minima == 120.0
    assert limiares.brilho_minimo == qualidade_imagem.LIMIARES_PADRAO["brilho_minimo"]


def enviar(cliente, usuario, conteudo, nome="foto.jpg", tipo="image/jpeg"):
    return cliente.post(
        "/ai/verificar-qualidade",
        files={"arquivo": (nome, conteudo, tipo)},
        headers=usuario["headers"],
    )


def test_endpoint_devolve_a_qualidade(cliente, medico):
    resposta = enviar(cliente, medico, como_jpeg(imagem_boa()))
    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert corpo["legivel"] is True
    assert corpo["classe"] == "boa"
    assert set(corpo["indicadores"]) == {
        "nitidez",
        "brilho",
        "contraste",
        "resolucao_px",
        "altura_texto_relativa",
        "angulo",
    }


def test_endpoint_recusa_arquivo_que_nao_e_imagem(cliente, medico):
    resposta = enviar(cliente, medico, b"laudo em texto", nome="laudo.txt", tipo="text/plain")
    assert resposta.status_code == 415


def test_endpoint_recusa_conteudo_que_nao_e_imagem(cliente, medico):
    resposta = enviar(cliente, medico, b"isto nao e uma imagem")
    assert resposta.status_code == 415


def test_endpoint_exige_login(cliente):
    resposta = cliente.post(
        "/ai/verificar-qualidade",
        files={"arquivo": ("foto.jpg", b"conteudo", "image/jpeg")},
    )
    assert resposta.status_code == 401
