from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.document import Document
from backend.services.chunking import create_chunks
from backend.services.document_loader import load_document
from backend.services.text_cleaner import clean_pages
from backend.services.vector_store import add_chunks_to_vector_store


router = APIRouter(prefix="/documents", tags=["Documents"])

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
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


@router.get("/", response_model=list[DocumentRead])
def list_documents(db: Session = Depends(get_db)) -> list[Document]:
    return db.query(Document).order_by(Document.id).all()


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    course_id: int = Form(...),
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, object]:
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
    except Exception as exc:
        document.status = "failed"
        db.commit()
        raise HTTPException(status_code=422, detail=f"Could not process document: {exc}") from exc

    document.status = "processed"
    db.commit()
    db.refresh(document)

    return {
        "message": "Document uploaded and processed",
        "document_id": document.id,
        "file_name": document.file_name,
        "status": document.status,
        "pages": len(cleaned_pages),
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
def index_document(document_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        pages = load_document(document.file_path)
        cleaned_pages = clean_pages(pages)
        chunks = create_chunks(
            document_id=document.id,
            course_id=document.course_id,
            document_name=document.file_name,
            pages=cleaned_pages,
        )
        count = add_chunks_to_vector_store(chunks)
    except Exception as exc:
        document.status = "index_failed"
        db.commit()
        raise HTTPException(status_code=422, detail=f"Could not index document: {exc}") from exc

    document.status = "indexed"
    db.commit()

    return {
        "message": "Document indexed successfully",
        "document_id": document.id,
        "chunks": count,
    }
