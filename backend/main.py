from fastapi import FastAPI

from backend.routers import chat, courses, dashboard, documents, quiz, retrieval, users


app = FastAPI(
    title="RAG Learning Chatbot API",
    description="Backend API for a learning-document RAG chatbot demo.",
    version="0.1.0",
)

app.include_router(users.router)
app.include_router(courses.router)
app.include_router(documents.router)
app.include_router(retrieval.router)
app.include_router(chat.router)
app.include_router(quiz.router)
app.include_router(dashboard.router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}

