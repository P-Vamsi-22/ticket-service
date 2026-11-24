import pytest

from tickets import (
    InMemoryTicketRepository,
    InvalidStatusTransitionError,
    InvalidTicketError,
    Priority,
    Status,
    TicketNotFoundError,
    TicketService,
)


@pytest.fixture
def service() -> TicketService:
    return TicketService(InMemoryTicketRepository())


def test_create_ticket_starts_open(service: TicketService) -> None:
    ticket = service.create_ticket("Fix bug")
    assert ticket.status == Status.OPEN


def test_create_ticket_assigns_unique_ids(service: TicketService) -> None:
    first = service.create_ticket("First")
    second = service.create_ticket("Second")
    assert first.id != second.id


def test_create_ticket_empty_title_raises(service: TicketService) -> None:
    with pytest.raises(InvalidTicketError):
        service.create_ticket("")


def test_list_tickets_returns_all(service: TicketService) -> None:
    service.create_ticket("One")
    service.create_ticket("Two")
    assert len(service.list_tickets()) == 2


def test_filter_by_status(service: TicketService) -> None:
    ticket = service.create_ticket("One")
    service.update_status(ticket.id, Status.IN_PROGRESS)
    service.create_ticket("Two")
    assert len(service.filter_tickets(status=Status.OPEN)) == 1
    assert len(service.filter_tickets(status=Status.IN_PROGRESS)) == 1


def test_filter_by_priority(service: TicketService) -> None:
    service.create_ticket("Low", priority=Priority.LOW)
    service.create_ticket("High", priority=Priority.HIGH)
    assert len(service.filter_tickets(priority=Priority.LOW)) == 1
    assert len(service.filter_tickets(priority=Priority.HIGH)) == 1


def test_valid_transition_open_to_in_progress(service: TicketService) -> None:
    ticket = service.create_ticket("One")
    updated = service.update_status(ticket.id, Status.IN_PROGRESS)
    assert updated.status == Status.IN_PROGRESS


def test_full_flow_open_to_closed(service: TicketService) -> None:
    ticket = service.create_ticket("One")
    service.update_status(ticket.id, Status.IN_PROGRESS)
    service.update_status(ticket.id, Status.RESOLVED)
    updated = service.update_status(ticket.id, Status.CLOSED)
    assert updated.status == Status.CLOSED


def test_invalid_transition_open_to_closed(service: TicketService) -> None:
    ticket = service.create_ticket("One")
    with pytest.raises(InvalidStatusTransitionError):
        service.update_status(ticket.id, Status.CLOSED)


def test_closed_ticket_cannot_change(service: TicketService) -> None:
    ticket = service.create_ticket("One")
    service.update_status(ticket.id, Status.IN_PROGRESS)
    service.update_status(ticket.id, Status.RESOLVED)
    service.update_status(ticket.id, Status.CLOSED)
    with pytest.raises(InvalidStatusTransitionError):
        service.update_status(ticket.id, Status.IN_PROGRESS)


def test_same_status_change_is_invalid(service: TicketService) -> None:
    ticket = service.create_ticket("One")
    with pytest.raises(InvalidStatusTransitionError):
        service.update_status(ticket.id, Status.OPEN)


def test_update_unknown_ticket_raises_not_found(service: TicketService) -> None:
    with pytest.raises(TicketNotFoundError):
        service.update_status(999, Status.IN_PROGRESS)
