import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.note import Note, Flashcard
from app.schemas.note import NoteCreate, NoteUpdate, NoteOut, FlashcardCreate, FlashcardOut
from app.services.ai_service import ai_service

router = APIRouter(prefix="/api/notes", tags=["笔记"])


@router.get("")
def list_notes(
    subject: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Note).filter(Note.user_id == current_user.id)
    if subject:
        query = query.filter(Note.subject == subject)
    total = query.count()
    notes = query.order_by(Note.updated_at.desc()).offset((page - 1) * size).limit(size).all()
    return {"code": 200, "data": {"items": [NoteOut.model_validate(n) for n in notes], "total": total}}


@router.post("")
def create_note(data: NoteCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = Note(user_id=current_user.id, **data.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return {"code": 200, "data": NoteOut.model_validate(note)}


@router.get("/{note_id}")
def get_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return {"code": 200, "data": NoteOut.model_validate(note)}


@router.put("/{note_id}")
def update_note(note_id: int, data: NoteUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(note, k, v)
    db.commit()
    db.refresh(note)
    return {"code": 200, "data": NoteOut.model_validate(note)}


@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    db.delete(note)
    db.commit()
    return {"code": 200, "message": "删除成功"}


@router.post("/{note_id}/ai-summarize")
async def ai_summarize(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")
    if not note.content.strip():
        raise HTTPException(status_code=400, detail="笔记内容为空")

    result = await ai_service.summarize_note(note.content, language=current_user.language or "zh")
    note.ai_summary = result.get("summary", "")
    note.key_points = json.dumps(result.get("key_points", []), ensure_ascii=False)
    db.commit()
    return {"code": 200, "data": result}


@router.post("/{note_id}/generate-flashcards")
async def generate_flashcards(note_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == current_user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    cards_data = await ai_service.generate_flashcards(note.content, note.subject, language=current_user.language or "zh")
    flashcards = []
    for card in cards_data:
        fc = Flashcard(
            user_id=current_user.id,
            note_id=note_id,
            front=card.get("front", ""),
            back=card.get("back", ""),
            subject=note.subject,
            tags=json.dumps(card.get("tags", []), ensure_ascii=False),
        )
        db.add(fc)
        flashcards.append(fc)
    db.commit()
    return {"code": 200, "data": {"flashcards": cards_data, "count": len(flashcards)}}


# Flashcard routes
flashcard_router = APIRouter(prefix="/api/flashcards", tags=["知识卡片"])


@flashcard_router.get("")
def list_flashcards(
    subject: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Flashcard).filter(Flashcard.user_id == current_user.id)
    if subject:
        query = query.filter(Flashcard.subject == subject)
    total = query.count()
    cards = query.order_by(Flashcard.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return {"code": 200, "data": {"items": [FlashcardOut.model_validate(c) for c in cards], "total": total}}


@flashcard_router.post("")
def create_flashcard(data: FlashcardCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    fc = Flashcard(
        user_id=current_user.id,
        front=data.front,
        back=data.back,
        subject=data.subject,
        tags=json.dumps(data.tags, ensure_ascii=False),
    )
    db.add(fc)
    db.commit()
    db.refresh(fc)
    return {"code": 200, "data": FlashcardOut.model_validate(fc)}
