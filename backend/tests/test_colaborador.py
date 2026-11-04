"""Colaborador: equipe do consultório que vai cuidar só do agendamento de consultas.

Por enquanto o tipo existe, entra no sistema e não acessa nenhum acompanhamento.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.usuario import TipoUsuario, Usuario
from tests.conftest import SENHA, abrir_sessao, criar_conta, criar_conta_ativa, entrar, senha_provisoria_enviada


@pytest.fixture
def colaborador(cliente, medico):
    return criar_conta_ativa(cliente, medico, "colaborador", "Juliana Rocha", "juliana@clinica.com")


def test_medico_cria_colaborador_sem_profissao(cliente, medico):
    resposta = criar_conta(cliente, medico, "colaborador", "Juliana Rocha", "juliana@clinica.com", "Secretária")
    assert resposta.status_code == 201, resposta.text
    conta = resposta.json()
    assert conta["tipo_usuario"] == "colaborador"
    # Como no paciente, a profissão não se aplica e é ignorada
    assert conta["profissao"] is None
    assert conta["primeiro_acesso_pendente"] is True
    assert conta["acompanhamento_id"] is None


def test_colaborador_faz_o_primeiro_acesso_sem_aceite_lgpd(cliente, medico):
    criar_conta(cliente, medico, "colaborador", "Juliana Rocha", "juliana@clinica.com")
    acesso = entrar(cliente, "juliana@clinica.com", senha_provisoria_enviada("juliana@clinica.com"))
    # O aceite LGPD é exigido só do titular dos dados de saúde (o paciente)
    troca = cliente.post("/auth/set-password", json={"nova_senha": SENHA}, headers=acesso["headers"])
    assert troca.status_code == 200, troca.text
    assert entrar(cliente, "juliana@clinica.com")["usuario"]["tipo_usuario"] == "colaborador"


def test_listagem_filtra_colaboradores(cliente, medico, paciente, parceiro, colaborador):
    resposta = cliente.get("/users", params={"tipo": "colaborador"}, headers=medico["headers"])
    assert [c["email"] for c in resposta.json()] == ["juliana@clinica.com"]


def test_colaborador_nao_administra_contas(cliente, colaborador):
    assert cliente.get("/users", headers=colaborador["headers"]).status_code == 403
    assert criar_conta(cliente, colaborador, "paciente", "Novo", "novo@email.com").status_code == 403


def test_colaborador_nao_acessa_acompanhamentos(cliente, colaborador, acompanhamento):
    cabecalhos = colaborador["headers"]
    assert cliente.get("/follow-ups", headers=cabecalhos).status_code == 403
    base = f"/follow-ups/{acompanhamento['id']}"
    for rota in ("", "/summary", "/anamnesis", "/consultations", "/requests", "/documents", "/timeline"):
        assert cliente.get(base + rota, headers=cabecalhos).status_code == 403, rota


def test_painel_do_colaborador_vem_vazio(cliente, colaborador):
    painel = cliente.get("/dashboard/pending", headers=colaborador["headers"])
    assert painel.status_code == 200
    assert painel.json() == {"tipo_usuario": "colaborador"}


def test_medico_edita_e_desativa_colaborador(cliente, medico, colaborador):
    conta_id = colaborador["usuario"]["id"]
    resposta = cliente.patch(
        f"/users/{conta_id}", json={"nome": "Juliana R. Rocha", "profissao": "Recepcionista"}, headers=medico["headers"]
    )
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Juliana R. Rocha"
    assert resposta.json()["profissao"] is None

    assert cliente.patch(f"/users/{conta_id}", json={"ativo": False}, headers=medico["headers"]).status_code == 200
    assert cliente.get("/dashboard/pending", headers=colaborador["headers"]).status_code == 401


def test_colaborador_nao_pode_ser_excluido_pela_opcao_do_paciente(cliente, medico, colaborador):
    conta_id = colaborador["usuario"]["id"]
    cliente.patch(f"/users/{conta_id}", json={"ativo": False}, headers=medico["headers"])
    assert cliente.delete(f"/users/{conta_id}", headers=medico["headers"]).status_code == 409


def test_banco_aceita_colaborador_sem_profissao_e_parceiro_continua_exigindo(cliente):
    sessao = abrir_sessao()
    sessao.add(Usuario(tipo_usuario=TipoUsuario.colaborador, nome="Juliana", email="j@clinica.com"))
    sessao.commit()

    sessao.add(Usuario(tipo_usuario=TipoUsuario.parceiro, nome="Sem profissão", email="p@clinica.com"))
    with pytest.raises(IntegrityError):
        sessao.commit()
    sessao.rollback()
    sessao.close()
