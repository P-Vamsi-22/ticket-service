from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket, TicketPriority, TicketStatus, User
from app.schemas import TicketCreate, TicketList, TicketOut, TicketUpdate

router = APIRouter(prefix="/tickets", tags=["tickets"])

ALLOWED_TRANSITIONS = {
    TicketStatus.OPEN: {TicketStatus.IN_PROGRESS},
    TicketStatus.IN_PROGRESS: {TicketStatus.RESOLVED},
    TicketStatus.RESOLVED: {TicketStatus.CLOSED, TicketStatus.IN_PROGRESS},
    TicketStatus.CLOSED: set(),
}


def get_ticket_or_404(ticket_id: int, db: Session) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found",
        )
    return ticket


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    if db.get(User, payload.created_by) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {payload.created_by} not found",
        )
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("", response_model=TicketList)
def list_tickets(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    priority: TicketPriority | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Ticket)
    count_stmt = select(func.count()).select_from(Ticket)
    if status_filter is not None:
        stmt = stmt.where(Ticket.status == status_filter)
        count_stmt = count_stmt.where(Ticket.status == status_filter)
    if priority is not None:
        stmt = stmt.where(Ticket.priority == priority)
        count_stmt = count_stmt.where(Ticket.priority == priority)

    total = db.scalar(count_stmt)
    items = (
        db.scalars(
            stmt.order_by(Ticket.id).offset((page - 1) * size).limit(size)
        ).all()
    )
    return TicketList(items=items, total=total, page=page, size=size)


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    return get_ticket_or_404(ticket_id, db)


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)
):
    ticket = get_ticket_or_404(ticket_id, db)
    updates = payload.model_dump(exclude_unset=True)
    if "status" in updates:
        new_status = updates["status"]
        if (
            new_status == ticket.status
            or new_status not in ALLOWED_TRANSITIONS[ticket.status]
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Invalid Status Transition",
            )
    for field, value in updates.items():
        setattr(ticket, field, value)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = get_ticket_or_404(ticket_id, db)
    db.delete(ticket)
    db.commit()
