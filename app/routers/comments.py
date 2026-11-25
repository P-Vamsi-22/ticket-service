from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Comment, Ticket, User
from app.schemas import CommentCreate, CommentOut
from app.routers.tickets import get_ticket_or_404

router = APIRouter(prefix="/tickets/{ticket_id}/comments", tags=["comments"])


@router.post("", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(
    ticket_id: int, payload: CommentCreate, db: Session = Depends(get_db)
):
    get_ticket_or_404(ticket_id, db)
    if db.get(User, payload.author_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {payload.author_id} not found",
        )
    comment = Comment(
        ticket_id=ticket_id, author_id=payload.author_id, body=payload.body
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("", response_model=list[CommentOut])
def list_comments(ticket_id: int, db: Session = Depends(get_db)):
    get_ticket_or_404(ticket_id, db)
    stmt = (
        select(Comment)
        .where(Comment.ticket_id == ticket_id)
        .order_by(Comment.created_at, Comment.id)
    )
    return db.scalars(stmt).all()
