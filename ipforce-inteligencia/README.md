# IPForce Inteligencia

Plataforma web para analise de CDR (Call Detail Records) e gravacoes do PABX IPForce.
Transforma chamadas telefonicas em informacoes estruturadas para supervisao,
identificacao de falhas de comunicacao e oportunidades comerciais.

---

## 1. Visao Geral

A plataforma consome as APIs oficiais do PABX IPForce para:

- **Sincronizar CDR** periodicamente (a cada 5 minutos)
- **Reproduzir gravacoes** diretamente pela interface web
- **Transcrever audio** automaticamente via WhisperX (com timestamps e diarizacao)
- **Analisar conversas** via LLM local (Ollama) gerando:
  - Resumo da chamada
  - Identificacao de problemas de comunicacao
  - Oportunidades comerciais
  - Sugestoes de melhoria no atendimento
  - Classificacao de alerta (Informacao / Atencao / Importante / Critico)
- **Dashboard executivo** com KPIs do dia e alertas recentes
- **Resumo diario** automatico da operacao

---

## 2. Arquitetura

```
+---------------+      +-------------------+      +------------------+
|  PABX IPForce |----->|  Backend (FastAPI)|----->|  PostgreSQL 16   |
| novopabx...   |      |  Python 3.11      |      |  (CDR, analises) |
+---------------+      +-------------------+      +------------------+
                              |
        +---------------------+---------------------+
        |                     |                     |
        v                     v                     v
   +---------+          +----------+          +-----------+
   |  Redis  |          | WhisperX |          |  Ollama   |
   | (fila)  |          |  (GPU)   |          | (outra    |
   +---------+          +----------+          |  maquina) |
        |                                     +-----------+
        v
   +---------+
   |  Celery |  <-- workers assincronos (transcricao + analise)
   +---------+

+----------------------------------------------------------+
|  Frontend (Next.js 14)                                   |
|  - Dashboard  - CDR  - Player  - Transcricao  - Analise  |
+----------------------------------------------------------+
```

### Componentes

| Camada | Tecnologia | Funcao |
|--------|-----------|--------|
| Backend | FastAPI + SQLAlchemy 2.0 (async) | API REST, autenticacao, integracao PABX |
| Jobs | Celery + Redis | Filas de transcricao e analise (nao bloqueiam a API) |
| Banco | PostgreSQL 16 | Persistencia de CDR, transcricoes, analises, usuarios |
| Transcricao | WhisperX (OpenAI) | STT com timestamps por palavra e diarizacao |
| IA/LLM | Ollama (Llama 3.1 8B) | Analise de texto, resumo, classificacao |
| Frontend | Next.js 14 + Tailwind | Interface web responsiva |
| Proxy | Caddy (opcional) | HTTPS automatico (se houver dominio) |

---

## 3. Pre-requisitos

### Hardware minimo recomendado

| Recurso | Especificacao | Observacao |
|---------|--------------|------------|
| GPU | NVIDIA RTX 3060 12GB+ | WhisperX large-v2 usa ~8GB VRAM |
| RAM | 32 GB | Modelos de IA + PostgreSQL + Redis simultaneos |
| Disco | 100 GB SSD | Modelos WhisperX (~6GB) + Ollama (~5GB) + gravacoes temp |
| CPU | 6+ cores | Processamento de fila Celery |
| SO | Ubuntu 22.04 / Debian 12 | Servidor de testes da IPForce |

### Software necessario

```bash
# Verifique se Docker esta instalado
docker --version
docker compose version

# Verifique se NVIDIA Docker Runtime esta instalado
nvidia-smi
nvidia-docker version  # ou docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

**Se nao tiver o NVIDIA Docker Runtime:**

```bash
# Instale o repositorio NVIDIA
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update
sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

---

## 4. Instalacao Passo a Passo

### 4.1 Clone o projeto

```bash
cd /opt  # ou o diretorio de preferencia
# Descompacte o ZIP no servidor
cd ipforce-inteligencia
```

### 4.2 Configure as variaveis de ambiente

```bash
cp .env.example .env
nano .env
```

Edite o arquivo `.env`:

```
# Obrigatorio: API Key do PABX (obtenha no painel do IPForce)
PABX_API_KEY=sua_api_key_aqui

# Obrigatorio: chave secreta para JWT (minimo 32 caracteres)
SECRET_KEY=coloque-uma-chave-muito-segura-aqui-com-32-chars

# Ollama: configure conforme onde ele esta rodando
#
# OPCAO A - Ollama na MESMA maquina (localhost):
# OLLAMA_HOST=http://host.docker.internal:11434
#
# OPCAO B - Ollama em OUTRA maquina da rede local:
# OLLAMA_HOST=http://192.168.1.XX:11434
# (substitua pelo IP real da maquina onde o Ollama roda)
OLLAMA_HOST=http://host.docker.internal:11434

# Opcional: token HuggingFace para diarizacao de falantes
HF_TOKEN=hf_seu_token_aqui
```

**Onde obter a API Key:** Painel administrativo do PABX IPForce -> Integracoes -> API.

### 4.3 Configure o Ollama

#### Se o Ollama estiver na MESMA maquina:

```bash
# Instale o Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Baixe o modelo (primeira vez demora ~10 minutos)
ollama pull llama3.1:8b

# Inicie o servidor
ollama serve &
```

#### Se o Ollama estiver em OUTRA maquina:

Na **maquina do Ollama**, configure para aceitar conexoes externas:

```bash
# Edite o servico do Ollama
sudo systemctl edit ollama.service
```

Adicione:
```ini
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

Depois:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama

# Libere a porta no firewall
sudo ufw allow 11434/tcp
# ou
sudo iptables -A INPUT -p tcp --dport 11434 -j ACCEPT
```

**Verifique se esta funcionando:**
```bash
curl http://localhost:11434/api/tags
# ou, de outra maquina:
curl http://IP_DA_MAQUINA_OLLAMA:11434/api/tags
```

Deve retornar uma lista incluindo `llama3.1:8b`.

### 4.4 Suba os containers

```bash
# Primeira vez: build completo
docker compose up --build -d

# Verifique se todos subiram
docker compose ps

# Logs em tempo real
docker compose logs -f backend
docker compose logs -f celery_worker
```

**Servicos que devem estar UP:**
- `ipforce-db` (PostgreSQL)
- `ipforce-redis` (Redis)
- `ipforce-backend` (FastAPI)
- `ipforce-celery` (Worker de jobs)
- `ipforce-beat` (Agendador de tarefas)
- `ipforce-frontend` (Next.js)

### 4.5 Crie o usuario admin

```bash
# Acesse o container do backend
docker compose exec backend python3 -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash

async def criar_admin():
    db = AsyncSessionLocal()
    user = User(
        email='admin@ipforce.local',
        hashed_password=get_password_hash('admin123'),
        full_name='Administrador',
        is_active=True,
        is_superuser=True
    )
    db.add(user)
    await db.commit()
    print('Usuario admin criado: admin@ipforce.local / admin123')

asyncio.run(criar_admin())
"
```

> **Altere a senha apos o primeiro login!**

---

## 5. Acesso a Aplicacao

Sem dominio configurado, acesse diretamente pelo IP do servidor:

| Servico | URL | Credenciais |
|---------|-----|-------------|
| Frontend | `http://IP_DO_SERVIDOR:3000` | admin@ipforce.local / admin123 |
| API Docs | `http://IP_DO_SERVIDOR:8000/docs` | Token JWT |
| API Health | `http://IP_DO_SERVIDOR:8000/api/health` | - |

**Se acessar de outro computador da rede**, certifique-se de que as portas 3000 e 8000 estao liberadas no firewall:

```bash
sudo ufw allow 3000
sudo ufw allow 8000
# ou
sudo iptables -A INPUT -p tcp --dport 3000 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
```

---

## 6. Fluxo de Dados

### 6.1 Sincronizacao de CDR (automatico)

1. Celery Beat dispara a cada 5 minutos
2. Task consulta `/api/cdr` do PABX (ultimos 35 minutos)
3. Registros novos sao inseridos no PostgreSQL
4. Para cada chamada com gravacao, enfileira transcricao

### 6.2 Transcricao (assincrona)

1. Celery Worker pega job da fila `transcricao`
2. Baixa o audio do PABX via `/api/recordticket`
3. WhisperX converte audio -> texto com timestamps
4. Salva transcricao no banco
5. Enfileira analise da conversa

### 6.3 Analise por IA (assincrona)

1. Celery Worker pega job da fila `analise`
2. Envia transcricao para Ollama (Llama 3.1 8B)
3. LLM retorna JSON estruturado com analise
4. Salva analise no banco e atualiza flags da chamada

---

## 7. Estrutura de Diretorios

```
ipforce-inteligencia/
├── docker-compose.yml          # Orquestracao de todos os servicos
├── .env                        # Variaveis de ambiente (NAO versionar)
├── .env.example                # Template de variaveis
├── Caddyfile                   # Configuracao HTTPS (opcional)
├── README.md                   # Este arquivo
│
├── backend/                    # API FastAPI
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini             # Config migracoes
│   ├── alembic/                # Migracoes de banco
│   └── app/
│       ├── main.py             # Entrypoint FastAPI
│       ├── api/                # Rotas REST
│       │   ├── auth.py         # Login / JWT
│       │   ├── cdr.py          # Consulta CDR
│       │   ├── dashboard.py    # KPIs e alertas
│       │   └── gravacao.py     # Proxy de audio
│       ├── core/               # Configuracoes e seguranca
│       │   ├── config.py       # Settings do app
│       │   ├── database.py     # Conexao PostgreSQL
│       │   └── security.py     # Hash de senha / JWT
│       ├── models/             # SQLAlchemy ORM
│       │   ├── base.py
│       │   ├── user.py
│       │   ├── chamada.py
│       │   ├── transcricao.py
│       │   └── analise.py
│       ├── services/           # Integracoes externas
│       │   ├── pabx.py         # Client HTTP para PABX
│       │   ├── whisperx_service.py  # Transcricao
│       │   └── ollama_service.py    # LLM local
│       └── tasks/              # Jobs Celery
│           ├── celery_app.py   # Config Celery
│           ├── sync.py         # Sync CDR
│           ├── transcricao.py  # Job de transcricao
│           └── analise.py      # Job de analise
│
└── frontend/                   # Next.js 14
    ├── Dockerfile
    ├── package.json
    ├── next.config.mjs
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── app/                    # App Router
    │   ├── layout.tsx          # Layout raiz
    │   ├── page.tsx            # Redirect login/dashboard
    │   ├── globals.css         # Estilos globais
    │   ├── login/              # Tela de login
    │   ├── dashboard/          # Dashboard executivo
    │   ├── cdr/                # Listagem de chamadas
    │   └── chamadas/[id]/      # Detalhe da chamada
    ├── components/
    │   ├── NavBar.tsx          # Barra de navegacao
    │   └── ui/                 # Componentes base
    │       ├── button.tsx
    │       ├── card.tsx
    │       ├── badge.tsx
    │       ├── input.tsx
    │       ├── select.tsx
    │       └── table.tsx
    └── lib/
        └── utils.ts            # Utilitarios (cn)
```

---

## 8. API Endpoints

### Autenticacao

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| POST | `/api/auth/login` | Login (form-data: username, password) |
| GET | `/api/auth/me` | Dados do usuario logado |

### CDR

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/api/cdr/` | Listar chamadas (com filtros e paginacao) |
| GET | `/api/cdr/{id}` | Detalhe completo da chamada |
| POST | `/api/cdr/sync` | Forcar sincronizacao manual |

### Gravacao

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/api/gravacao/{record_id}` | Proxy do audio do PABX |

### Dashboard

| Metodo | Endpoint | Descricao |
|--------|----------|-----------|
| GET | `/api/dashboard/hoje` | KPIs do dia |
| GET | `/api/dashboard/alertas` | Alertas recentes |

---

## 9. Troubleshooting

### 9.1 GPU nao aparece no container

```bash
# Verifique se o runtime NVIDIA esta ativo
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Se der erro, reinicie o Docker
sudo systemctl restart docker
```

### 9.2 Ollama nao responde (maquina separada)

Na **maquina do Ollama**:
```bash
# Verifique se o servico esta rodando
sudo systemctl status ollama

# Verifique se esta escutando em todas as interfaces
sudo ss -tlnp | grep 11434
# Deve mostrar 0.0.0.0:11434, nao 127.0.0.1:11434

# Teste localmente
curl http://localhost:11434/api/tags

# Teste de outra maquina
curl http://IP_DA_MAQUINA_OLLAMA:11434/api/tags
```

Se o teste local funcionar mas o remoto nao, o firewall esta bloqueando:
```bash
sudo ufw allow 11434/tcp
# ou
sudo iptables -A INPUT -p tcp --dport 11434 -j ACCEPT
```

### 9.3 WhisperX demora muito na primeira transcricao

Normal. O modelo e baixado automaticamente no primeiro uso (~6GB).
Verifique o progresso:
```bash
docker compose logs -f celery_worker
```

### 9.4 Erro de certificado ao chamar o PABX

O codigo ja usa `verify=False` nas chamadas HTTP para o PABX (o certificado pode ser auto-assinado). Se o erro persistir, verifique se a URL esta correta no `.env`.

### 9.5 Banco de dados nao inicializa

```bash
# Force recriacao
docker compose down -v
docker compose up -d db
# Aguarde 10 segundos
docker compose up -d
```

### 9.6 Como ver logs de uma chamada especifica

```bash
# Logs do worker de transcricao
docker compose logs -f celery_worker | grep "record_id"

# Logs do worker de analise
docker compose logs -f celery_worker | grep "analise"
```

---

## 10. Comandos Uteis

```bash
# Reiniciar tudo
docker compose restart

# Rebuild completo (apos mudancas no codigo)
docker compose up --build -d

# Parar tudo
docker compose down

# Parar e limpar volumes (CUIDADO: apaga dados!)
docker compose down -v

# Acessar banco de dados
docker compose exec db psql -U ipforce -d ipforce

# Acessar shell do backend
docker compose exec backend bash

# Ver fila do Celery
docker compose exec redis redis-cli llen celery

# Limpar fila (emergencia)
docker compose exec redis redis-cli flushall
```

---

## 11. Roadmap / Proximos Passos

- [ ] Multi-tenant (suporte a multiplos PABXs)
- [ ] Notificacoes por e-mail/WhatsApp para alertas criticos
- [ ] Score de atendimento por colaborador
- [ ] Integracao com CRM
- [ ] Relatorios comparativos (semanal/mensal)
- [ ] Diarizacao automatica (Atendente vs Cliente) sem token HF
- [ ] Suporte a outros modelos de LLM (Claude, GPT-4 via API)
