# CloudWay Assistant: React Frontend

A chat UI for the CloudWay RAG assistant. It sends questions to a FastAPI backend over REST and shows the answer with its source documents.

```
React (localhost:5173)  ──POST /chat──►  FastAPI api.py (localhost:8000)  ──►  RAG code (Chroma + Groq)
                        ◄── answer + sources ──
```

## Run it

**Backend** (repo root):

```bash
pip install fastapi uvicorn
uvicorn api:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm install react-markdown remark-gfm rehype-raw
npm run dev
```

To use a different backend address, set `VITE_API_URL` in `frontend/.env` and restart.

## REST API

### `POST /chat`

**Request**

```json
{
  "message": "Can I change my booking?",
  "history": [{ "role": "user", "content": "..." }],
  "summary": ""
}
```

- `message`: the new question (required)
- `history`: recent messages not yet summarised
- `summary`: running summary from the previous response

**Response**

```json
{
  "answer": "Markdown text, may include tables",
  "sources": [{ "file": "booking.pdf", "snippet": "..." }],
  "summary": "updated summary",
  "consumed": 0
}
```

- `consumed`: how many history messages were folded into `summary` (usually 0)

**Errors:** `422` invalid body, `500` RAG failure (check the backend terminal).

Quick test:

```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
  -d '{"message":"How do I book a ticket?"}'
```

## How the frontend uses it

1. User sends a question and it appears in the chat straight away.
2. `App.jsx` calls `POST /chat` with the message, unsummarised history and summary.
3. The answer is shown as Markdown (tables supported), with a "Found in N documents" list of sources.
4. If the call fails, the question returns to the input box with an error message.

The backend remembers nothing between requests, so the frontend keeps the full chat on screen and sends only recent messages plus the `summary`. After 10 messages the backend summarises all but the last 4 and returns `consumed`, so the visible chat never shrinks.

## CORS

`api.py` allows `http://localhost:5173`. If you use another address (deployed site, phone), add it to `allow_origins`.

## Troubleshooting

| Problem                        | Fix                                                           |
| ------------------------------ | ------------------------------------------------------------- |
| "Couldn't reach the assistant" | Start the backend; check `VITE_API_URL`                       |
| CORS error in console          | Add your frontend address to `allow_origins`                  |
| Table shows as plain text      | Ask the model for Markdown tables in its prompt (`answer.py`) |
| `500` error                    | Check the backend terminal (API key, empty `vector_db/`)      |
