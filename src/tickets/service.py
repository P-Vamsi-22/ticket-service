from .errors import InvalidStatusTransitionError, InvalidTicketError
from .models import Priority, Status, Ticket
from .repository import InMemoryTicketRepository, TicketRepository

ALLOWED_TRANSITIONS: dict[Status, frozenset[Status]] = {
    Status.OPEN: frozenset({Status.IN_PROGRESS}),
    Status.IN_PROGRESS: frozenset({Status.RESOLVED}),
    Status.RESOLVED: frozenset({Status.CLOSED, Status.IN_PROGRESS}),
    Status.CLOSED: frozenset(),
}


class TicketService:
    def __init__(self, repository: TicketRepository | None = None) -> None:
        self._repository = repository if repository is not None else InMemoryTicketRepository()

    def create_ticket(
        self,
        title: str,
        description: str = "",
        priority: Priority = Priority.MEDIUM,
    ) -> Ticket:
        if not title or not title.strip():
            raise InvalidTicketError("Ticket title cannot be empty")
        ticket = Ticket(
            id=self._repository.next_id(),
            title=title.strip(),
            description=description,
            priority=priority,
        )
        self._repository.add(ticket)
        return ticket

    def list_tickets(self) -> list[Ticket]:
        return self._repository.list_all()

    def filter_tickets(
        self,
        status: Status | None = None,
        priority: Priority | None = None,
    ) -> list[Ticket]:
        tickets = self._repository.list_all()
        if status is not None:
            tickets = [t for t in tickets if t.status == status]
        if priority is not None:
            tickets = [t for t in tickets if t.priority == priority]
        return tickets

    def update_status(self, ticket_id: int, new_status: Status) -> Ticket:
        ticket = self._repository.get(ticket_id)
        allowed = ALLOWED_TRANSITIONS.get(ticket.status, frozenset())
        if new_status == ticket.status or new_status not in allowed:
            raise InvalidStatusTransitionError(
                f"Cannot transition ticket {ticket_id} from {ticket.status} to {new_status}"
            )
        ticket.status = new_status
        self._repository.update(ticket)
        return ticket
