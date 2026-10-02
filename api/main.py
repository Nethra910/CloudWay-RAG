# Put this next to app.py in the repo root.  Run: uvicorn api:app --reload --port 8000
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from implementation.answer import answer_question, update_conversation_summary

load_dotenv(override=True)

app = FastAPI(title="CloudWay Assistant API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

KEEP_RECENT = 4   # messages sent to the LLM verbatim
SUMMARISE_AT = 10  # compress older turns once history passes this


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []   # only messages not yet folded into the summary
    summary: str = ""


@app.post("/chat")
def chat(req: ChatRequest):
    answer, context = answer_question(req.message, req.history, req.summary)

    full = req.history + [
        {"role": "user", "content": req.message},
        {"role": "assistant", "content": answer},
    ]
    summary, consumed = req.summary, 0
    if len(full) > SUMMARISE_AT:
        old = full[:-KEEP_RECENT]
        summary = update_conversation_summary(req.summary, old)
        consumed = len(old)

    seen, sources = set(), []
    for d in context:
        name = d.metadata.get("source", "document")
        if name in seen:
            continue
        seen.add(name)
        sources.append({"file": name, "snippet": d.page_content.strip()[:320]})

    return {"answer": answer, "sources": sources, "summary": summary, "consumed": consumed}