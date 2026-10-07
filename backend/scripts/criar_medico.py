"""Cria a conta do médico (o único usuário que não é criado por dentro do sistema).

Uso (na pasta backend, com o venv ativo e o banco migrado):
    python -m scripts.criar_medico --nome "Dra. Ana Souza" --email ana@clinica.com

A senha é pedida no terminal (ou passe --senha). O sistema tem um único médico:
se ele já existir, use --redefinir-senha para trocar a senha dele.
"""

import argparse
import getpass
import sys

from sqlalchemy import select

from app.core.seguranca import gerar_hash_senha
from app.db.sessao import SessaoLocal
from app.models.usuario import PROFISSAO_MEDICO, TipoUsuario, Usuario
from app.services.contas import limpar_senha_provisoria

TAMANHO_MINIMO_SENHA = 6


def _pedir_senha() -> str:
    senha = getpass.getpass("Senha do médico: ")
    if senha != getpass.getpass("Confirme a senha: "):
        sys.exit("As senhas não conferem.")
    return senha


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria a conta do médico do LifeScan.")
    parser.add_argument("--nome", help="Nome do médico (obrigatório ao criar)")
    parser.add_argument("--email", required=True, help="Email usado no login")
    parser.add_argument("--senha", help="Senha (se omitida, é pedida no terminal)")
    parser.add_argument(
        "--redefinir-senha",
        action="store_true",
        help="Troca a senha do médico já existente",
    )
    args = parser.parse_args()
    email = args.email.strip().lower()

    with SessaoLocal() as sessao:
        medico = sessao.scalar(select(Usuario).where(Usuario.tipo_usuario == TipoUsuario.medico))

        if medico is not None and medico.email != email:
            sys.exit(f"Já existe um médico cadastrado ({medico.email}). O sistema aceita apenas um.")
        if medico is not None and not args.redefinir_senha:
            sys.exit("O médico já está cadastrado. Use --redefinir-senha para trocar a senha.")
        if medico is None and args.redefinir_senha:
            sys.exit("Ainda não existe um médico cadastrado. Rode sem --redefinir-senha.")
        if medico is None and not args.nome:
            sys.exit("Informe --nome para criar o médico.")
        if medico is None and sessao.scalar(select(Usuario.id).where(Usuario.email == email)):
            sys.exit("Este email já é usado por outra conta.")

        senha = args.senha or _pedir_senha()
        if len(senha) < TAMANHO_MINIMO_SENHA:
            sys.exit(f"A senha precisa ter pelo menos {TAMANHO_MINIMO_SENHA} caracteres.")

        if medico is None:
            medico = Usuario(
                tipo_usuario=TipoUsuario.medico,
                nome=args.nome.strip(),
                email=email,
                profissao=PROFISSAO_MEDICO,
            )
            sessao.add(medico)
            acao = "criado"
        else:
            acao = "atualizado (senha redefinida)"

        medico.senha_hash = gerar_hash_senha(senha)
        limpar_senha_provisoria(medico)
        medico.deve_trocar_senha = False
        medico.ativo = True
        sessao.commit()
        print(f"Médico {acao}: {medico.nome} <{medico.email}>")


if __name__ == "__main__":
    main()
