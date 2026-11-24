class TicketNotFoundError(Exception):
    """Raised when a ticket ID does not exist."""


class InvalidStatusTransitionError(Exception):
    """Raised when a status change is not allowed."""


class InvalidTicketError(Exception):
    """Raised when ticket data fails validation."""
