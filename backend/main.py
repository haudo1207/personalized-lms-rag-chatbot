from fastapi import FastAPI

from backend.database import Base, engine
from backend.models.chat_history import ChatHistory
from backend.models.course import Course
from backend.models.document import Document
from backend.models.user import User
from backend.models.weak_topic import WeakTopic
from backend.routers import chat, courses, dashboard, documents, quiz, retrieval, users


Base.metadata.create_all(bind=engine)

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


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "RAG Learning Chatbot API is running"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
