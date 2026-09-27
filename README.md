# LifeScan

Acompanhamento do tratamento de saúde para além do consultório: médico e paciente
compartilham uma **jornada contínua** com consultas, solicitações com prazo, exames,
mensagens e uma linha do tempo unificada.

- **Backend:** Python + FastAPI, SQLAlchemy 2.0, Alembic, MySQL (`/backend`)
- **Frontend:** React + Vite (`/frontend`), a partir da Fase 5
- **Especificação e decisões:** [`docs/projeto.md`](docs/projeto.md)

> Todos os comandos abaixo são para o **PowerShell** no Windows.

## Pré-requisitos

- Python 3.11+ (testado com 3.13)
- Node.js 20+ (testado com 24)
- MySQL 8: instalado no Windows **ou** via Docker (`docker-compose.yml`)

## 1. Banco de dados

### Opção A: MySQL instalado no Windows

Com o serviço `MySQL80` rodando, crie o banco e um usuário da aplicação
(entre no cliente com `mysql -u root -p` ou use o MySQL Workbench):

```sql
CREATE DATABASE lifescan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'lifescan'@'localhost' IDENTIFIED BY 'lifescan123';
GRANT ALL PRIVILEGES ON lifescan.* TO 'lifescan'@'localhost';
FLUSH PRIVILEGES;
```

### Opção B: Docker

```powershell
docker compose up -d
```

O container expõe o MySQL na porta **3307**. Ajuste o `DATABASE_URL` conforme o
comentário no `docker-compose.yml`.

## 2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env   # depois edite DATABASE_URL e JWT_SECRET
alembic upgrade head
uvicorn app.main:app --reload
```

- API: <http://localhost:8000>
- Documentação interativa (Swagger): <http://localhost:8000/docs>

> Se o PowerShell bloquear o `Activate.ps1`, rode uma vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### Variáveis do `.env`

| Variável | Descrição |
|---|---|
| `DATABASE_URL` | URL do MySQL (`mysql+pymysql://usuario:senha@host:porta/banco?charset=utf8mb4`) |
| `JWT_SECRET` | Segredo do JWT HS256. Gere com `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `JWT_EXPIRE_MINUTES` | Validade do token (padrão 480) |
| `BCRYPT_ROUNDS` | Custo do hash bcrypt (padrão 12; opcional) |
| `CORS_ORIGINS` | Origens permitidas, separadas por vírgula |
| `UPLOAD_DIR` | Pasta dos arquivos enviados (relativa a `backend/`) |
| `MAX_UPLOAD_MB` | Tamanho máximo de upload (padrão 30) |
| `DUE_SOON_DAYS` | Dias para uma solicitação ser considerada "próxima do prazo" (padrão 3) |

### Testes

Os testes usam SQLite em memória e não tocam no MySQL:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest
```

### Nova migração (depois de alterar modelos)

```powershell
alembic revision --autogenerate -m "descricao da mudanca"
alembic upgrade head
```

## Endpoints disponíveis

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/register` | Cadastro (`nome`, `email`, `senha`, `papel`: `medico`/`paciente`); já devolve o token |
| POST | `/auth/login` | Login (`email`, `senha`) |
| GET | `/auth/me` | Usuário autenticado |
| GET | `/patients/search?email=` | Médico busca paciente pelo email exato |
| POST | `/links` | Médico vincula paciente (`paciente_id`) |
| GET | `/links` | Médico: seus pacientes. Paciente: seu médico |
| PATCH | `/links/{id}` | Médico ativa/desativa o vínculo (`ativo`) |
| POST | `/journeys` | Médico abre a jornada de um paciente vinculado (`paciente_id`, `titulo`, `descricao`) |
| GET | `/journeys` | Jornadas do usuário (só com vínculo ativo) |
| GET | `/journeys/{id}` | Detalhe da jornada |
| PATCH | `/journeys/{id}/step` | Médico altera o passo (`passo_atual`: `consulta`/`exame`/`retorno`) |
| PATCH | `/journeys/{id}/status` | Médico encerra/reabre (`status`: `ativa`/`encerrada`) |
| POST | `/journeys/{id}/consultations` | Médico registra consulta/retorno com prescrições aninhadas |
| GET | `/journeys/{id}/consultations` | Consultas da jornada |
| POST | `/journeys/{id}/requests` | Médico cria solicitação com prazo (`tipo`, `descricao`, `prazo`) |
| GET | `/journeys/{id}/requests?status=` | Solicitações da jornada (com `vencida` calculado) |
| PATCH | `/requests/{id}/complete` | Médico marca a solicitação como atendida |
| PATCH | `/requests/{id}/cancel` | Médico cancela a solicitação |
| POST | `/journeys/{id}/exams` | Envio de exame (multipart: `titulo`, `arquivo`, `solicitacao_id` opcional) |
| GET | `/journeys/{id}/exams` | Exames da jornada |
| PATCH | `/exams/{id}/review` | Médico revisa o exame (`observacao_revisao`) |
| POST | `/journeys/{id}/messages` | Mensagem (multipart: `conteudo` e/ou `arquivo`) |
| GET | `/journeys/{id}/messages` | Mensagens da jornada |
| GET | `/files/{id}/download?inline=` | Download autenticado do arquivo |
| GET | `/health` | Verificação de saúde da API |

Uploads aceitam `pdf, png, jpg, jpeg, webp, dcm, txt` com até 30 MB (415 para formato
não permitido, 413 para arquivo grande). Os arquivos ficam em `backend/uploads/` com nome
gerado (UUID) e só são acessíveis pela rota de download.
