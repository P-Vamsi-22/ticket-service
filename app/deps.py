"""Authentication (who are you? -> 401) and authorization (are you allowed? -> 403)."""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket, User, UserRole
from app.security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """401 if the token is missing, invalid, expired, or for a user that no longer exists."""
    try:
        user_id = int(decode_access_token(token)["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise _unauthorized()
    user = db.get(User, user_id)
    if user is None:
        raise _unauthorized()
    return user


def is_agent(user: User) -> bool:
    return user.role == UserRole.AGENT


def require_agent(user: User = Depends(get_current_user)) -> User:
    """403 for anyone who is logged in but not an agent."""
    if not is_agent(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Agents only")
    return user


def ensure_ticket_access(ticket: Ticket, user: User) -> None:
    """Employees may only touch their own tickets; agents may touch all (403 otherwise)."""
    if not is_agent(user) and ticket.created_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You can only access your own tickets"
        )
