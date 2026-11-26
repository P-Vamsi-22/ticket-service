from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import ensure_ticket_access, get_current_user, is_agent, require_agent
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


def get_accessible_ticket(ticket_id: int, db: Session, user: User) -> Ticket:
    """404 if it doesn't exist, 403 if it isn't yours (and you're not an agent)."""
    ticket = get_ticket_or_404(ticket_id, db)
    ensure_ticket_access(ticket, user)
    return ticket


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = Ticket(**payload.model_dump(), created_by=user.id)  # owner comes from the token
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
    user: User = Depends(get_current_user),
):
    stmt = select(Ticket)
    count_stmt = select(func.count()).select_from(Ticket)
    if not is_agent(user):  # employees only ever see their own tickets
        stmt = stmt.where(Ticket.created_by == user.id)
        count_stmt = count_stmt.where(Ticket.created_by == user.id)
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
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_accessible_ticket(ticket_id, db, user)


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(
    ticket_id: int,
    payload: TicketUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ticket = get_accessible_ticket(ticket_id, db, user)
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
def delete_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    _agent: User = Depends(require_agent),  # role check: only agents may delete
):
    ticket = get_ticket_or_404(ticket_id, db)
    db.delete(ticket)
    db.commit()
