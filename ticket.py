from dataclasses import dataclass
from enum import Enum


class Status(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TicketNotFoundError(Exception):
    """Raised when a ticket ID does not exist."""


@dataclass
class Ticket:
    id: int
    title: str
    status: Status = Status.OPEN


tickets: dict[int, Ticket] = {}


def create_ticket(ticket_id: int, title: str) -> Ticket:
    ticket = Ticket(id=ticket_id, title=title)
    tickets[ticket_id] = ticket
    return ticket


def get_ticket(ticket_id: int) -> Ticket:
    if ticket_id not in tickets:
        raise TicketNotFoundError(f"Ticket {ticket_id} not found")
    return tickets[ticket_id]


if __name__ == "__main__":
    create_ticket(1, "Pump leaking")
    print(get_ticket(1))
    try:
        get_ticket(99)
    except TicketNotFoundError as e:
        print(f"Error: {e}")