"""Criptografia em repouso: o banco só guarda tokens Fernet dos textos clínicos."""

import sqlalchemy as sa

from app.models.anamnese import Anamnese
from tests.conftest import abrir_sessao

ANAMNESE = {
    "diagnosticos": "Hipertensão estágio 1",
    "alergias": "Dipirona",
    "medicamentos_em_uso": "Losartana 50 mg",
    "restricoes": "Evitar exercícios de alto impacto",
    "objetivos": "Reduzir a pressão",
}

CAMPOS = ("diagnosticos", "alergias", "medicamentos_em_uso", "restricoes", "objetivos")


def test_textos_clinicos_nao_ficam_em_texto_plano_no_banco(cliente, medico, acompanhamento):
    resposta = cliente.put(
        f"/follow-ups/{acompanhamento['id']}/anamnesis",
        json=ANAMNESE,
        headers=medico["headers"],
    )
    assert resposta.status_code == 200, resposta.text

    with abrir_sessao() as sessao:
        linha = sessao.execute(sa.text("SELECT * FROM anamneses LIMIT 1")).mappings().one()
        for campo in CAMPOS:
            cifrado = linha[campo]
            assert cifrado.startswith("gAAAAA"), f"{campo} não está cifrado: {cifrado!r}"
            assert "Hipertensão" not in cifrado
            assert "Dipirona" not in cifrado

    # Pela API, a leitura volta em texto claro como antes
    leitura = cliente.get(f"/follow-ups/{acompanhamento['id']}/anamnesis", headers=medico["headers"])
    assert leitura.json()["diagnosticos"] == "Hipertensão estágio 1"
    assert leitura.json()["alergias"] == "Dipirona"


def test_leitura_pela_orm_devolve_texto_plano(cliente, medico, acompanhamento):
    cliente.put(f"/follow-ups/{acompanhamento['id']}/anamnesis", json=ANAMNESE, headers=medico["headers"])
    with abrir_sessao() as sessao:
        anamnese = sessao.scalar(sa.select(Anamnese))
        assert anamnese.diagnosticos == "Hipertensão estágio 1"
        assert anamnese.objetivos == "Reduzir a pressão"
