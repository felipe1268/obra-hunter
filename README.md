# 🏗️ ObraHunter

**Sistema automatizado de prospecção de obras — busca contínua 24/7 com alertas inteligentes.**

O ObraHunter é um robô que varre a internet continuamente procurando obras de construção civil em todo o Brasil, enriquece os dados encontrados, identifica decisores e te alerta quando encontra boas oportunidades.

---

## 🚀 Funcionalidades

### Busca Automática 24/7
- **4 fontes de dados**: Google Maps, Diários Oficiais, Portais de Licitação, Sites de Construtoras
- **Frequência configurável**: contínua (a cada 30min), diária ou semanal
- **Filtros combinávies**: estado, cidade, tipo de obra, fase, porte, valor

### Enriquecimento Inteligente
- Consulta CNPJ na Receita Federal (razão social, sócios, atividade)
- Scraping de sites para extrair emails, telefones, WhatsApp
- Detecção de redes sociais (Instagram, Facebook, LinkedIn)

### Sugestão de Decisores (Busca Assistida)
- Cruza sócios da Receita com perfis LinkedIn via Google
- Ranqueia por relevância do cargo (Diretor > Gerente > Coordenador)
- Você valida: aceita ou descarta cada sugestão

### Score de Oportunidade (0-10)
- **Porte** (30%): Obras maiores = mais oportunidade
- **Fase** (25%): Fases iniciais = melhor timing
- **Tipo** (20%): Comercial/Industrial = maior ticket
- **Contatos** (15%): Mais dados = mais fácil prospectar
- **Recência** (10%): Obra recente = mais urgente

### Alertas Multi-Canal
- 📧 Email com template HTML profissional
- 🔔 Webhook (Slack, Discord, Zapier)
- 📱 Push notifications no dashboard
- 💬 WhatsApp Business API (opcional)

### Dashboard Completo
- Visão geral com métricas em tempo real
- Pipeline de conversão (funil de vendas)
- Distribuição por estado, tipo e fonte
- Timeline de obras encontradas
- Detalhe de cada obra com decisores

---

## 📁 Estrutura do Projeto

```
obra-hunter/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # Endpoints REST
│   │   ├── core/
│   │   │   ├── config.py          # Configurações
│   │   │   └── database.py        # PostgreSQL async
│   │   ├── models/
│   │   │   └── models.py          # SQLAlchemy models
│   │   ├── schemas/
│   │   │   └── schemas.py         # Pydantic schemas
│   │   ├── scrapers/
│   │   │   ├── base.py            # Scraper base
│   │   │   ├── google_maps.py     # Google Places API
│   │   │   ├── diarios_oficiais.py# Diários Oficiais
│   │   │   ├── licitacoes.py      # Portais de licitação
│   │   │   └── construtoras.py    # Sites de construtoras
│   │   ├── services/
│   │   │   ├── enriquecimento.py  # CNPJ + contatos + decisores
│   │   │   ├── score.py           # Score de oportunidade
│   │   │   └── alertas.py         # Envio de alertas
│   │   ├── tasks/
│   │   │   └── scheduler.py       # Orquestrador automático
│   │   └── main.py                # FastAPI app
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   └── services/
│   │       └── api.js             # Cliente API
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🛠️ Setup

### Pré-requisitos
- Docker e Docker Compose
- Chave da Google Maps API (para scraper de mapas)

### 1. Clonar e configurar

```bash
git clone <repo>
cd obra-hunter
cp .env.example .env
# Edite .env com suas chaves
```

### 2. Configurar variáveis obrigatórias no .env

```env
# Google Maps (obrigatório para scraper de mapas)
GOOGLE_MAPS_API_KEY=sua-chave-aqui

# Email para alertas
SMTP_USER=seu@email.com
SMTP_PASSWORD=senha-de-app

# Webhook (opcional - Slack, Discord, etc.)
ALERT_WEBHOOK_URL=https://hooks.slack.com/...
```

### 3. Subir tudo com Docker

```bash
docker-compose up -d
```

### 4. Acessar

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 🔧 Deploy em Produção

### Backend (Railway/Render)

1. Criar projeto no Railway
2. Adicionar PostgreSQL e Redis como serviços
3. Conectar repo GitHub
4. Configurar variáveis de ambiente
5. Deploy automático

### Frontend (Vercel)

1. Importar repo no Vercel
2. Configurar `VITE_API_URL` com URL do backend
3. Deploy automático

---

## 📡 API Endpoints

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/v1/dashboard` | Estatísticas do dashboard |
| GET | `/api/v1/obras` | Listar obras com filtros |
| GET | `/api/v1/obras/{id}` | Detalhe de uma obra |
| PATCH | `/api/v1/obras/{id}` | Atualizar obra |
| GET | `/api/v1/alertas/recentes` | Alertas de oportunidade |
| POST | `/api/v1/buscas` | Criar busca automática |
| GET | `/api/v1/buscas` | Listar buscas |
| POST | `/api/v1/buscas/{id}/executar` | Forçar execução |
| PATCH | `/api/v1/buscas/{id}/toggle` | Ativar/desativar |
| PATCH | `/api/v1/decisores/{id}` | Validar/descartar decisor |
| POST | `/api/v1/busca-manual` | Busca única |

---

## ⚙️ Configuração do Scheduler

O scheduler roda automaticamente dentro do backend. Configurações principais:

```env
SCHEDULER_ENABLED=true
BUSCA_DIARIA_HORA=6              # Hora para busca diária
BUSCA_CONTINUA_INTERVALO_MIN=30  # Intervalo da busca contínua
SCORE_THRESHOLD_ALERTA=7.0       # Score mínimo para alertar
```

---

## 📊 Como funciona o Score

| Fator | Peso | Exemplo |
|-------|------|---------|
| Porte | 30% | Grande = 10pts, Médio = 7pts |
| Fase | 25% | Fundação = 10pts, Aprovação = 9pts |
| Tipo | 20% | Comercial = 9pts, Residencial = 7pts |
| Contatos | 15% | CNPJ+Site+Email = 7pts |
| Recência | 10% | Hoje = 10pts, Semana = 8pts |

Bônus: Valor > R$10M (+1.5), Área > 10.000m² (+1.0)

---

## 🔒 Sobre o LinkedIn

O sistema **NÃO** faz scraping do LinkedIn (isso viola os termos de uso).

Em vez disso, usa **busca assistida**:
1. Busca no Google por `"Empresa" "Cargo" site:linkedin.com/in/`
2. Extrai nome e cargo do snippet do Google
3. Apresenta como **sugestão** para você validar
4. Você clica no link e verifica manualmente

---

## 📝 Licença

Projeto privado. Todos os direitos reservados.
