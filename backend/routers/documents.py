from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.database import get_db
from backend.models.course import Course
from backend.models.document import Document
from backend.models.user import User
from backend.security_deps import get_current_user, require_self_or_admin, verify_course_access
from backend.services.chunking import create_chunks
from backend.services.document_loader import load_document
from backend.services.question_suggester import suggest_questions_for_course
from backend.services.text_cleaner import clean_pages
from backend.services.topic_taxonomy import ensure_taxonomy_for_course
from backend.services.vector_store import add_chunks_to_vector_store, delete_document_chunks


router = APIRouter(prefix="/documents", tags=["Documents"])

RAW_DIR = Path(get_settings().raw_dir)
PROCESSED_DIR = Path(get_settings().processed_dir)
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    user_id: int | None
    file_name: str
    file_path: str
    file_type: str | None
    status: str
    uploaded_at: datetime


class DocumentUpdate(BaseModel):
    file_name: str


def _require_owner_or_admin(document: Document, current_user: User) -> None:
    if document.user_id is not None:
        require_self_or_admin(document.user_id, current_user)
    elif current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chỉ Admin mới được thao tác trên tài liệu không rõ người tải lên.",
        )


@router.get("/", response_model=list[DocumentRead])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Document]:
    if current_user.role == "admin":
        return db.query(Document).order_by(Document.id).all()

    owned_ids = [
        row.id for row in db.query(Course.id).filter(Course.owner_id == current_user.id).all()
    ]
    if not owned_ids:
        return []
    return (
        db.query(Document)
        .filter(Document.course_id.in_(owned_ids))
        .order_by(Document.id)
        .all()
    )


@router.get("/suggested-questions")
def get_suggested_questions(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    """Suggested starter questions generated from real, already-indexed
    document content (not filenames) -- purely a UX nicety for the empty-chat
    state, so any failure here degrades to an empty list instead of an error."""
    verify_course_access(course_id, current_user, db)
    try:
        questions = suggest_questions_for_course(course_id)
    except Exception:
        questions = []
    return {"questions": questions}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    course_id: int = Form(...),
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    """Upload, chunk, embed and index a document in one call.

    There is no separate manual "index" step in the primary flow: a student talking to the
    chatbot has no reason to know or care that indexing is a distinct stage. `/index` still
    exists below purely as a retry path for a document whose status isn't "indexed".
    """
    require_self_or_admin(user_id, current_user)
    verify_course_access(course_id, current_user, db)

    original_name = Path(file.filename or "").name
    if not original_name:
        raise HTTPException(status_code=400, detail="Missing uploaded filename.")

    file_suffix = Path(original_name).suffix.lower()
    if file_suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF, DOCX and TXT files are allowed.",
        )

    stored_name = f"{uuid4().hex}_{original_name}"
    raw_path = RAW_DIR / stored_name

    content = await file.read()
    raw_path.write_bytes(content)

    document = Document(
        course_id=course_id,
        user_id=user_id,
        file_name=original_name,
        file_path=str(raw_path),
        file_type=file_suffix.lstrip("."),
        status="uploaded",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        pages = load_document(str(raw_path))
        cleaned_pages = clean_pages(pages)
        processed_path = PROCESSED_DIR / f"{document.id}_{Path(original_name).stem}.txt"
        _write_processed_text(processed_path, cleaned_pages)

        chunks = create_chunks(
            document_id=document.id,
            course_id=course_id,
            document_name=original_name,
            pages=cleaned_pages,
        )
        if not chunks:
            raise ValueError(
                "No extractable text found (the file may be a scanned/image-only document)."
            )
        chunk_count = add_chunks_to_vector_store(chunks)
    except Exception as exc:
        document.status = "failed"
        db.commit()
        raise HTTPException(status_code=422, detail=f"Could not index document: {exc}") from exc

    document.status = "indexed"
    db.commit()
    db.refresh(document)
    _ensure_taxonomy_safe(course_id, db)

    return {
        "message": "Document uploaded and indexed",
        "document_id": document.id,
        "file_name": document.file_name,
        "status": document.status,
        "pages": len(cleaned_pages),
        "chunks": chunk_count,
        "processed_path": str(processed_path),
    }


def _write_processed_text(
    processed_path: Path,
    cleaned_pages: list[dict[str, str | int]],
) -> None:
    with processed_path.open("w", encoding="utf-8") as file:
        for page in cleaned_pages:
            file.write(f"\n\n--- Page {page['page']} ---\n")
            file.write(str(page["text"]))


@router.post("/{document_id}/index")
def index_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    """Retry indexing for a document that failed during upload. Not part of the primary flow --
    `/upload` already indexes in one shot -- this exists only so a failed document can be
    retried without re-uploading the file.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    verify_course_access(document.course_id, current_user, db)

    try:
        pages = load_document(document.file_path)
        cleaned_pages = clean_pages(pages)
        chunks = create_chunks(
            document_id=document.id,
            course_id=document.course_id,
            document_name=document.file_name,
            pages=cleaned_pages,
        )
        if not chunks:
            raise ValueError(
                "No extractable text found (the file may be a scanned/image-only document)."
            )
        count = add_chunks_to_vector_store(chunks)
    except Exception as exc:
        document.status = "failed"
        db.commit()
        raise HTTPException(status_code=422, detail=f"Could not index document: {exc}") from exc

    document.status = "indexed"
    db.commit()
    _ensure_taxonomy_safe(document.course_id, db)

    return {
        "message": "Document indexed successfully",
        "document_id": document.id,
        "chunks": count,
    }


def _ensure_taxonomy_safe(course_id: int, db: Session) -> None:
    """Topic-taxonomy generation is a UX nicety for chat topic classification,
    not part of the indexing contract -- a failure here (LLM error, malformed
    response) must not fail the upload/retry that triggered it."""
    try:
        ensure_taxonomy_for_course(course_id, db)
    except Exception:
        pass


@router.patch("/{document_id}", response_model=DocumentRead)
def rename_document(
    document_id: int,
    update: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Document:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    verify_course_access(document.course_id, current_user, db)
    _require_owner_or_admin(document, current_user)

    new_name = update.file_name.strip()
    if not new_name:
        raise HTTPException(status_code=400, detail="file_name cannot be empty.")

    document.file_name = new_name
    db.commit()
    db.refresh(document)
    return document


@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    """Hard delete: removes the DB row, the indexed chunks in ChromaDB, and the
    raw file on disk. Vector chunks are removed first -- if that step fails,
    the document row (and its "not enough information" fallback behavior)
    stays intact rather than silently leaving stale, still-retrievable chunks
    behind after the row disappears from the UI."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    verify_course_access(document.course_id, current_user, db)
    _require_owner_or_admin(document, current_user)

    delete_document_chunks(document_id)

    raw_path = Path(document.file_path)
    if raw_path.exists():
        raw_path.unlink()

    db.delete(document)
    db.commit()

    return {"message": "Document deleted", "document_id": document_id}


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")
    verify_course_access(document.course_id, current_user, db)

    raw_path = Path(document.file_path)
    if not raw_path.exists():
        raise HTTPException(status_code=404, detail="Original file is no longer available on disk.")

    return FileResponse(
        path=raw_path,
        filename=document.file_name,
        media_type="application/octet-stream",
    )
