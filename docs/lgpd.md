# LGPD na anamnese dos pacientes

A anamnese trata **dados pessoais sensíveis de saúde** (LGPD, art. 5º, II) e por isso
segue o regime da **art. 11**. Este documento resume o que foi implementado e as
decisões de retenção.

## O que foi implementado

| Item | Artigos | Onde |
|---|---|---|
| Consentimento específico do titular registrado no primeiro acesso (versão do termo, data/hora, IP) | 11, §1º | `app/models/consentimento.py`, `/auth/set-password`, tela `DefinirSenha` |
| Trilha de auditoria de leitura e escrita da anamnese, pseudônima (id + tipo de usuário, sem nome) | 37, 18 V | `app/models/registro_acesso.py`, `app/services/registro_acesso.py`, `GET /follow-ups/{id}/anamnesis/acessos` |
| Criptografia em repouso dos textos clínicos (Fernet na aplicação; o banco só vê tokens) | 46 | `app/db/cripta.py`, `FERNET_KEY` em `app/core/config.py` |
| Minimização para parceiros: só idade, sem data de nascimento completa | 6º, III | rota de anamnese (`para_parceiro`) |
| Portabilidade: exportação em JSON (anamnese + consentimentos + acessos) para titular ou médico | 18, II e V | `GET /follow-ups/{id}/anamnesis/portabilidade` |

## Política de retenção

- A anamnese descreve o **paciente**, então permanece editável mesmo com o
  acompanhamento encerrado.
- Registro de prontuário: mantido por até **20 anos**, conforme a Resolução CFM
  nº 1.821/2007. Por essa obrigação legal/regulatória (art. 16), a exclusão
  definitiva de dados clínicos só ocorre após esse prazo.
- A conta do paciente pode ser **desativada** a qualquer momento; os dados clínicos
  são preservados durante o prazo de guarda.
- A trilha de auditoria é pseudônima (id + tipo de usuário) e sobrevive à
  desativação da conta — ela não identifica o titular.

## Chave de criptografia (`FERNET_KEY`)

- Em produção, defina `FERNET_KEY` com uma chave própria
  (`python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`).
  Guarde um backup fora do servidor.
- Sem `FERNET_KEY`, a chave é derivada do segredo JWT — suficiente para
  desenvolvimento e testes, mas rotacionar o segredo JWT afetaria as leituras.
- O database dump é inútil sem a chave: os seis campos clínicos
  (`diagnosticos`, `alergias`, `medicamentos_em_uso`, `restricoes`, `objetivos`,
  `observacoes`) são gravados cifrados.

## Migrações envolvidas

1. `c4f8a09d17b2` — tabela `consentimentos`
2. `d5b9e3f07c11` — tabela `registros_acesso`
3. `e2a7c41d9f05` — cifra os textos clínicos já gravados (idempotente)
