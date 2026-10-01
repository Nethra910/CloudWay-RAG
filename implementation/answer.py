import os
from pathlib import Path
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage, convert_to_messages
from langchain_core.documents import Document



load_dotenv(override=True)
groq_api_key = os.getenv("GROQ_API_KEY")
MODEL = "openai/gpt-oss-120b"

DB_NAME = str(Path(__file__).parent.parent / "vector_db")
# print(DB_NAME)
embeddings = HuggingFaceEmbeddings(model_name = "all-MiniLM-L6-v2")
RETRIEVAL_K = int(os.getenv("RETRIEVAL_K"))

SYSTEM_PROMPT = """
You are CloudWay's airline information assistant.

Answer the current question using the retrieved context.

Treat the context as the source of factual information.
Do not invent policies, prices, or other facts.
If the context does not support an answer, say so.
Use conversation history only to understand references in the current question.
Answer concisely and include relevant details from the context.

Context:
{context}
"""

vectorstore = Chroma(
    embedding_function = embeddings, 
    persist_directory = DB_NAME
)
retriever = vectorstore.as_retriever(
    search_kwargs={"k": RETRIEVAL_K}
)
print("GROQ Key Exists: ",groq_api_key[0:4] + "..." + groq_api_key[-2:])
print("MODEL : ",MODEL)

llm = ChatGroq(
    temperature=0,
    api_key = groq_api_key,
    model = MODEL
)

def fetch_context(question: str) -> list[Document]:
    """
    Retrieve relevant context documents for a question.
    """
    return retriever.invoke(question)

def build_context(docs, max_chars=6000):
    selected = []
    total_chars = 0

    for doc in docs:
        text = doc.page_content.strip()

        if not text:
            continue

        if text in selected:
            continue

        remaining = max_chars - total_chars

        if remaining <= 0:
            break

        if len(text) > remaining:
            break

        selected.append(text)
        total_chars += len(text)

    return "\n\n".join(selected)

def update_conversation_summary(old_summary, history):
    if not history:
        return old_summary

    summary_prompt = f"""
You are maintaining a compact conversation memory.

Existing summary:
{old_summary}

Conversation to summarize:
{history}

Create a concise summary containing only information that may be useful
for future questions.

Do not include unnecessary wording.
Preserve important topics, user preferences, decisions, and references
to previous questions.

Return only the summary.
"""

    response = llm.invoke([
        SystemMessage(content=summary_prompt)
    ])

    return response.content.strip()

def answer_question(question: str,history: list[dict] | None = None,conversation_summary: str = "") -> tuple[str, list[Document]]:
    if history is None:
        history = []

    # Retrieval uses ONLY the current question
    docs = fetch_context(question)
    context = build_context(docs)
    recent_history = history[-4:] if len(history) > 4 else history
    system_prompt = SYSTEM_PROMPT.format(context=context)
    messages = [
        SystemMessage(content=system_prompt)
    ]
    if conversation_summary:
        messages.append(
            SystemMessage(
                content = f"Conversation summary : \n {conversation_summary}"
            )
        )
    messages.extend(convert_to_messages(recent_history))
    messages.append(
        HumanMessage(
            content = f"""
                Retrieved CloudWay context:
                {context}
                current question:
                {question}
            """
        )
    )
    response = llm.invoke(messages)
    return response.content, docs