# LifeScan

Centraliza os dados do tratamento de saúde do paciente para ajudar o trabalho do médico:
consultas, prescrições, solicitações com prazo, documentos e uma linha do tempo unificada.
O paciente acompanha o que precisa fazer; parceiros (nutricionista, fisioterapeuta…)
colaboram com documentos da sua área.

- **Backend:** Python + FastAPI, SQLAlchemy 2.0, Alembic, MySQL (`/backend`)
- **Frontend:** React + Vite + React Router + Axios, estilos com CSS Modules e ícones `lucide-react` (`/frontend`)
- **Especificação e decisões:** [`docs/projeto.md`](docs/projeto.md)
- **Diagramas:** [`docs/diagramas.md`](docs/diagramas.md)

> Todos os comandos abaixo são para o **PowerShell** no Windows.

## Como o acesso funciona

Não existe cadastro público.

1. O **médico** (único no sistema) é criado por um script, na instalação.
2. O médico cria as contas de **pacientes** e **parceiros**, informando nome e email
   (e a profissão, no caso do parceiro).
3. O sistema envia por email os dados de acesso, com uma **senha provisória** válida por 7 dias.
4. No primeiro login, a pessoa é levada a escolher a própria senha (a provisória não é pedida de novo).

Não existe uma opção de "alterar senha" dentro do sistema: quem quiser trocar usa
"Esqueci minha senha" na tela de login.

O sistema não depende de o paciente entrar: assim que a conta existe, o médico já pode abrir
a jornada e registrar tudo.

> **Email em modo de desenvolvimento:** por enquanto nenhum email é enviado de verdade.
> Com `EMAIL_MODE=console`, o email (incluindo a senha provisória) aparece no terminal onde
> o `uvicorn` está rodando.

## Pré-requisitos

- Python 3.11+ (testado com 3.13)
- Node.js 20+ (testado com 24)
- MySQL 8: instalado no Windows **ou** via Docker (`docker-compose.yml`)

> **Windows 11 e "Controle Inteligente de Aplicativos":** se ele estiver ativado, o Windows
> bloqueia os executáveis e as DLLs do `.venv` ("Uma política de Controle de Aplicativo bloqueou
> este arquivo"). Não há lista de exceções: é preciso desativá-lo em Segurança do Windows →
> Controle de aplicativos e navegador, ou desenvolver dentro do WSL2.

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

# Cria o médico (a senha é pedida no terminal)
python -m scripts.criar_medico --nome "Dra. Ana Souza" --email ana@clinica.com

uvicorn app.main:app --reload
```

- API: <http://localhost:8000>
- Documentação interativa (Swagger): <http://localhost:8000/docs>

> Se o PowerShell bloquear o `Activate.ps1`, rode uma vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

> Se o venv já existe e está ativo (o prompt mostra `(.venv)`), não rode `python -m venv` de novo.

### O médico esqueceu a senha?

```powershell
python -m scripts.criar_medico --email ana@clinica.com --redefinir-senha
```

Pacientes e parceiros usam "Esqueci minha senha" na tela de login, ou o médico reenvia o
acesso pela tela **Pacientes e parceiros**.

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
| `EMAIL_MODE` | Modo de envio de email. Só `console` por enquanto |
| `EMAIL_FROM` | Remetente mostrado nos emails |
| `FRONTEND_URL` | Endereço do frontend, usado nos emails (padrão `http://localhost:5173`) |
| `ACCESS_PASSWORD_DAYS` | Validade da senha provisória de uma conta nova (padrão 7 dias) |
| `RESET_PASSWORD_MINUTES` | Validade da senha provisória do "esqueci minha senha" (padrão 60 min) |

### Dados de exemplo (opcional)

Cria um paciente e um parceiro já com senha definida e uma jornada com ficha preenchida,
parceiro atribuído, consulta, solicitações (uma vencida e uma destinada ao parceiro) e um
documento aguardando revisão. Se ainda não houver médico,
cria também o médico de exemplo.

```powershell
python -m scripts.seed
```

| Tipo | Email | Senha |
|---|---|---|
| Médico | `medico@lifescan.com` | `lifescan123` |
| Paciente | `paciente@lifescan.com` | `lifescan123` |
| Parceiro | `parceiro@lifescan.com` | `lifescan123` |

Rodar de novo não duplica nada.

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

## 3. Frontend

Com o backend rodando, em outro terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env   # ajuste VITE_API_URL se a API não estiver em http://localhost:8000
npm run dev
```

Acesse <http://localhost:5173> e entre com a conta do médico.

| Variável | Descrição |
|---|---|
| `VITE_API_URL` | Endereço da API (padrão `http://localhost:8000`) |
| `VITE_MAX_UPLOAD_MB` | Limite de upload validado no navegador; use o mesmo valor do backend |

Build de produção: `npm run build` (gera `frontend/dist`).

### Telas

- **Login**, **Esqueci minha senha** e **Defina sua senha** (só no primeiro acesso ou depois de
  pedir uma senha provisória).
- **Painel de pendências**: o médico vê documentos para revisar e solicitações vencidas ou perto
  do prazo; o paciente vê o que precisa fazer (vencidas em destaque) e as consultas extras
  marcadas; o parceiro vê as solicitações destinadas a ele.
- **Pacientes e parceiros** (médico): uma tela só. No formulário, o médico escolhe se está
  cadastrando um paciente ou um parceiro; abaixo, uma seção lista os pacientes e outra os
  parceiros, com reenviar acesso e desativar/reativar.
- **Jornadas**: lista (médico), a jornada do paciente, ou os pacientes atribuídos (parceiro);
  abertura de nova jornada (médico).
- **Página da jornada**: passo atual (o médico altera clicando), encerrar/reabrir, e abas de
  linha do tempo (com filtros), ficha do paciente, consultas e prescrições, solicitações (para o
  paciente ou para um parceiro), documentos por categoria (envio, revisão, visualizar/baixar) e
  parceiros atribuídos.
- **Visão do parceiro**: só a ficha do paciente, as solicitações destinadas a ele e os próprios envios.

As listas e a página da jornada se atualizam a cada 30 segundos; a atualização pausa quando a
aba do navegador fica oculta.

## Endpoints disponíveis

| Método | Rota | Descrição |
|---|---|---|
| POST | `/auth/login` | Login (`email`, `senha`), com a senha definitiva ou a provisória |
| GET | `/auth/me` | Usuário autenticado |
| POST | `/auth/set-password` | Define a senha (`nova_senha`) depois de entrar com a provisória |
| POST | `/auth/forgot-password` | Envia uma senha provisória por email (`email`) |
| POST | `/users` | Médico cria conta de paciente ou parceiro (`tipo_usuario`, `nome`, `email`, `profissao`) |
| GET | `/users?tipo=` | Médico lista as contas (`paciente` / `parceiro`) |
| PATCH | `/users/{id}` | Médico altera `nome`, `profissao` ou `ativo` |
| POST | `/users/{id}/resend-access` | Médico reenvia os dados de acesso (nova senha provisória) |
| POST | `/journeys` | Médico abre a jornada de um paciente (`paciente_id`, `titulo`, `descricao`) |
| GET | `/journeys` | Jornadas do usuário (o parceiro vê as que lhe foram atribuídas) |
| GET | `/journeys/{id}` | Detalhe da jornada |
| PATCH | `/journeys/{id}/step` | Médico altera o passo (`passo_atual`: `consulta`/`exame`/`retorno`) |
| PATCH | `/journeys/{id}/status` | Médico encerra/reabre (`status`: `ativa`/`encerrada`) |
| GET | `/journeys/{id}/patient-record` | Ficha do paciente (médico, paciente e parceiros atribuídos) |
| PUT | `/journeys/{id}/patient-record` | Médico cria ou substitui a ficha |
| GET | `/journeys/{id}/partners` | Parceiros atribuídos à jornada |
| POST | `/journeys/{id}/partners` | Médico atribui um parceiro (`parceiro_id`) |
| DELETE | `/journeys/{id}/partners/{parceiro_id}` | Médico remove o parceiro da jornada |
| POST | `/journeys/{id}/consultations` | Médico registra consulta/retorno com prescrições aninhadas |
| GET | `/journeys/{id}/consultations` | Consultas da jornada |
| POST | `/journeys/{id}/requests` | Médico cria solicitação com prazo (`tipo`, `descricao`, `prazo`, `destinatario_id` opcional: paciente ou parceiro atribuído) |
| GET | `/journeys/{id}/requests?status=` | Solicitações da jornada (o parceiro vê só as destinadas a ele) |
| PATCH | `/requests/{id}/complete` | Médico marca a solicitação como atendida |
| PATCH | `/requests/{id}/cancel` | Médico cancela a solicitação |
| POST | `/journeys/{id}/documents` | Envio de documento (multipart: `titulo`, `categoria`, `arquivo`, `solicitacao_id` opcional) |
| GET | `/journeys/{id}/documents?categoria=` | Documentos da jornada (o parceiro vê só os próprios envios) |
| PATCH | `/documents/{id}/review` | Médico revisa o documento (`observacao_revisao`) |
| GET | `/files/{id}/download?inline=` | Download autenticado do arquivo |
| GET | `/journeys/{id}/timeline?tipos=` | Linha do tempo unificada `{tipo, id, data, resumo, dados}` (filtro: `consulta,documento,solicitacao`) |
| GET | `/dashboard/pending` | Painel de pendências (conteúdo por tipo de usuário) |
| GET | `/health` | Verificação de saúde da API |

Categorias de documento: `exame`, `laudo`, `plano_alimentar`, `plano_treino`, `orientacao`, `outro`.

Uploads aceitam `pdf, png, jpg, jpeg, webp, dcm, txt` com até 30 MB (415 para formato
não permitido, 413 para arquivo grande). Os arquivos ficam em `backend/uploads/` com nome
gerado (UUID) e só são acessíveis pela rota de download.
