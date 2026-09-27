# LifeScan: especificação e decisões

O LifeScan acompanha o tratamento de saúde do paciente para além do consultório,
reunindo médico e paciente em uma **jornada contínua**:

- O **médico** registra consultas, faz pedidos com prazo e acompanha a evolução do paciente.
- O **paciente** sabe o que precisa fazer e até quando, envia exames e conversa com o médico.
- **Outros profissionais** (nutricionista, fisioterapeuta etc.) não têm conta: as orientações
  deles chegam ao médico pelo paciente, como documento enviado na jornada.

## Requisitos funcionais

| Código | Descrição |
|---|---|
| RF01 | Cadastro como médico ou paciente, com nome, email e senha. |
| RF02 | Login de usuários cadastrados. |
| RF03 | O médico vincula um paciente já cadastrado (busca por email). |
| RF04 | Somente o médico abre uma jornada, e apenas para um paciente vinculado. |
| RF05 | O médico altera o passo atual da jornada entre `consulta`, `exame` e `retorno`. |
| RF06 | O médico cria solicitações com prazo (exame, consulta extra, orientação de outro profissional, outro). |
| RF07 | Médico e paciente enviam exames/arquivos para a jornada. |
| RF08 | O paciente **visualiza** as consultas extras marcadas pelo médico (lembrete; ver decisões). |
| RF09 | O médico revisa exames (status + observação da revisão). |
| RF10 | O médico registra consultas e prescrições. |
| RF11 | Médico e paciente trocam mensagens dentro da jornada. |
| RF12 | Linha do tempo da jornada: consultas, exames, solicitações e mensagens em ordem cronológica. |
| RF13 | A consulta tem um tipo: `consulta` ou `retorno`. |
| RF14 | Painel de pendências para médico e para paciente. |
| RF15 | Upload de arquivos nos formatos permitidos. |

## Requisitos não funcionais

| Código | Descrição |
|---|---|
| RNF01 | Somente `pdf, png, jpg, jpeg, webp, dcm, txt`, até 30 MB; validado no backend e no frontend. |
| RNF02 | Persistência em MySQL. |
| RNF03 | Controle de acesso por papel (`medico` / `paciente`). |
| RNF04/08 | Atualização das páginas por polling a cada 30 segundos. |
| RNF05 | Backend em FastAPI. |
| RNF06 | Frontend em React com Vite. |
| RNF07 | CORS com origens vindas do `.env`. |
| RNF09 | Senhas com hash bcrypt. |
| RNF10 | Acesso à jornada só com vínculo médico-paciente ativo. |
| RNF11 | JWT HS256, validade de 480 minutos. |

## Decisões tomadas

### Convenções de código
- Nomes de classes, funções, variáveis, **comentários, docstrings, tabelas, colunas e campos JSON em português**.
- Termos técnicos sem boa tradução continuam em inglês (`router`, `schema`, `token`, `upload`), assim como nomes de pastas.
- **Rotas HTTP mantêm os caminhos em inglês** definidos na especificação (`/auth/login`, `/journeys/{id}/timeline`...).
- Variáveis do `.env` com os nomes da especificação (`DATABASE_URL`, `JWT_SECRET`...).
- Datas gravadas em UTC sem fuso; a API devolve com fuso explícito (`...Z`).

### Regras de negócio simplificadas
- O sistema atende, por enquanto, **um médico específico**: o médico pode ter vários pacientes,
  e **cada paciente tem vínculo com um único médico** (`vinculos_medico_paciente.paciente_id` é único).
  Transferir pacientes entre médicos fica fora do escopo por ora.
- **Um paciente tem apenas uma jornada**, aberta pelo médico vinculado (`jornadas.paciente_id` é único).
  O médico pode ter várias jornadas (uma por paciente).
- A busca de pacientes (`/patients/search`) é por **email exato**, para não expor a lista de usuários.
- **Consulta extra (RF08)** é um lembrete do médico para o paciente: o paciente só visualiza, sem ações.
  O médico é quem marca a solicitação como atendida ou cancelada.
- O médico pode desativar/reativar um vínculo (`PATCH /links/{id}`), o que bloqueia o acesso à jornada (RNF10).
- Enviar um exame vinculado a uma solicitação `exame` ou `orientacao_profissional` marca a solicitação como `atendida`.
- Solicitação vencida = `pendente` com prazo no passado (calculado, não gravado).
- "Próxima do prazo" = vence em até `DUE_SOON_DAYS` dias (padrão 3).
- "Mensagem não respondida" (painel do médico) = a última mensagem da jornada foi enviada pelo paciente.
- Jornada `encerrada` é somente leitura (escritas retornam 409); o médico pode reabri-la.
- Uploads gravados em blocos no disco; acima do limite retorna 413; extensão não permitida retorna 415.

### Frontend
- Estilos com CSS Modules.

## Fases

1. Setup do backend, config, banco, Alembic, auth (RF01, RF02, RNF09, RNF11), CORS.
2. Vínculos, jornadas, passo atual, controle de acesso (RF03–RF05, RNF03, RNF10).
3. Consultas, prescrições, solicitações, upload, exames, revisão, mensagens (RF06–RF11, RF13, RF15, RNF01).
4. Linha do tempo e painel de pendências (RF12, RF14).
5. Frontend completo com polling (RNF04, RNF06, RNF08).
