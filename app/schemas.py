from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import TicketPriority, TicketStatus, UserRole


class UserCreate(BaseModel):
    # Unknown fields (e.g. "role": "AGENT") are ignored: sign-up always creates an EMPLOYEE.
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: UserRole


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"  # OAuth2 token type name, not a password


class TicketCreate(BaseModel):
    # No created_by: the owner is always the logged-in user (taken from the token).
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    status: TicketStatus | None = None
    priority: TicketPriority | None = None


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: TicketStatus
    priority: TicketPriority
    created_by: int
    created_at: datetime


class TicketList(BaseModel):
    items: list[TicketOut]
    total: int
    page: int
    size: int


class CommentCreate(BaseModel):
    # No author_id: the author is always the logged-in user.
    body: str = Field(min_length=1, max_length=5000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    author_id: int
    body: str
    created_at: datetime
