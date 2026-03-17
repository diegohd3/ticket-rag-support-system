# UI Workspace

Next.js + TypeScript frontend for the AI Support Ticket Chatbot backend.

## Run locally

```bash
cp .env.example .env.local
npm install
npm run dev
```

Open:

- `http://localhost:3000`

## Environment

- `NEXT_PUBLIC_API_BASE_URL` (default used in code: `http://localhost:8000`)

## Included screens

- User identification gate before accessing chat
- Chat console (`POST /api/v1/chat/ask`)
- Tickets workspace (`GET /api/v1/tickets`, `PATCH /api/v1/tickets/{ticket_id}`)
- Standardized API error handling (`code`, `message`, `request_id`, `details`)

## User identification headers

The UI sends:

- `X-User-Id` (required by chat endpoint)
- `X-User-Name` (optional)
- `X-API-Key` (optional, only if backend enables API key auth)

Repeated off-topic or invalid chat queries can trigger account blocking according to backend policy.
