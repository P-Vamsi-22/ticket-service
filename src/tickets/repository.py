from typing import Protocol

from .errors import TicketNotFoundError
from .models import Ticket


class TicketRepository(Protocol):
    def add(self, ticket: Ticket) -> None: ...

    def get(self, ticket_id: int) -> Ticket: ...

    def list_all(self) -> list[Ticket]: ...

    def update(self, ticket: Ticket) -> None: ...

    def next_id(self) -> int: ...


class InMemoryTicketRepository:
    def __init__(self) -> None:
        self._tickets: dict[int, Ticket] = {}
        self._next_id = 1

    def add(self, ticket: Ticket) -> None:
        self._tickets[ticket.id] = ticket

    def get(self, ticket_id: int) -> Ticket:
        if ticket_id not in self._tickets:
            raise TicketNotFoundError(f"Ticket {ticket_id} not found")
        return self._tickets[ticket_id]

    def list_all(self) -> list[Ticket]:
        return list(self._tickets.values())

    def update(self, ticket: Ticket) -> None:
        if ticket.id not in self._tickets:
            raise TicketNotFoundError(f"Ticket {ticket.id} not found")
        self._tickets[ticket.id] = ticket

    def next_id(self) -> int:
        ticket_id = self._next_id
        self._next_id += 1
        return ticket_id
