# AI Support Ticket Chatbot

Backend inicial para un chatbot de soporte técnico que consulta tickets históricos y propone soluciones priorizando conocimiento interno.

## Objetivo

Construir una base sólida para:

- Búsqueda estructurada por texto, códigos de error y tags
- Ranking de relevancia
- Respuesta profesional basada en tickets internos
- Evolución natural hacia búsqueda semántica con `pgvector` + embeddings OpenAI

## Stack

- Python 3.12+
- FastAPI
- PostgreSQL + pgvector
- SQLAlchemy + Alembic
- Pydantic Settings + dotenv
- Pytest
- Docker Compose

## Arquitectura (Monolito modular)

```text
app/
  api/              # Endpoints y wiring HTTP
  application/      # Casos de uso, servicios y contratos
  domain/           # Entidades y value objects
  infrastructure/   # DB, repositorios, config, adapters externos
  schemas/          # DTOs de entrada/salida API (Pydantic)
  scripts/          # Seed y utilidades operativas
```

Esta separación facilita migrar módulos a microservicios en el futuro sin romper reglas de negocio.

## Estructura principal

```text
.
├── alembic/
├── app/
│   ├── api/routers/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   ├── schemas/
│   └── scripts/
├── tests/
├── docker-compose.yml
├── .env.example
├── alembic.ini
└── pyproject.toml
```

## Endpoints actuales

- `GET /health`
- `GET /api/v1/tickets?limit=20&offset=0`
- `GET /api/v1/tickets/search?query=<texto>&limit=10`

## Levantar el proyecto

1. Clonar y configurar entorno:

```bash
cp .env.example .env
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Levantar PostgreSQL + pgvector:

```bash
docker compose up -d
```

3. Ejecutar migraciones:

```bash
alembic upgrade head
```

4. Cargar datos simulados:

```bash
python -m app.scripts.seed_tickets
```

5. Iniciar API:

```bash
uvicorn app.main:app --reload
```

Swagger:

- `http://127.0.0.1:8000/docs`

## Tests básicos

```bash
pytest
```

## Diseño para próxima fase (semántica + OpenAI)

Ya está preparado:

- Columna `embedding` (`vector`) en la tabla `tickets`
- Contrato `EmbeddingProvider` en capa application
- Adapter placeholder `OpenAIEmbeddingProvider` en infraestructura
- Servicio de búsqueda desacoplado para añadir score semántico sin romper API actual

## Notas de ingeniería

- Se prioriza base interna como fuente principal.
- El ranking actual combina señales estructuradas.
- Se evita acoplar la lógica de dominio con FastAPI/SQLAlchemy.
