"""Integration tests (Day 10 behaviour) now running as logged-in users.

The `client` fixture (tests/conftest.py) uses a fresh in-memory SQLite DB per test,
so `ticket.db` is never touched.
"""
from tests.conftest import new_ticket


def test_create_ticket(client, ada):
    ticket = new_ticket(client, ada, priority="HIGH")
    assert ticket["status"] == "OPEN"
    assert ticket["priority"] == "HIGH"
    assert ticket["created_by"] == ada.id


def test_get_ticket_not_found(client, agent):
    resp = client.get("/tickets/999", headers=agent.headers)
    assert resp.status_code == 404
    assert resp.json()["status"] == 404


def test_list_tickets_pagination(client, ada):
    for i in range(5):
        new_ticket(client, ada, title=f"Ticket {i}")

    resp = client.get("/tickets?page=2&size=2", headers=ada.headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert data["page"] == 2
    assert data["size"] == 2
    assert len(data["items"]) == 2


def test_list_tickets_filter_by_priority(client, ada):
    new_ticket(client, ada, priority="HIGH")
    new_ticket(client, ada, priority="LOW")
    new_ticket(client, ada, priority="HIGH")

    resp = client.get("/tickets?priority=HIGH", headers=ada.headers)
    data = resp.json()
    assert data["total"] == 2
    assert all(t["priority"] == "HIGH" for t in data["items"])


def test_list_tickets_filter_by_status(client, ada):
    t1 = new_ticket(client, ada, status="OPEN")
    new_ticket(client, ada, status="CLOSED")
    client.patch(f"/tickets/{t1['id']}", json={"status": "IN_PROGRESS"}, headers=ada.headers)

    resp = client.get("/tickets?status=IN_PROGRESS", headers=ada.headers)
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "IN_PROGRESS"


def test_patch_ticket_valid_status_change(client, ada):
    ticket = new_ticket(client, ada)
    resp = client.patch(
        f"/tickets/{ticket['id']}",
        json={"status": "IN_PROGRESS", "priority": "LOW"},
        headers=ada.headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["priority"] == "LOW"
    assert data["created_by"] == ada.id  # created_by is immutable


def test_patch_ticket_invalid_transition_returns_409(client, ada):
    ticket = new_ticket(client, ada)  # OPEN
    resp = client.patch(f"/tickets/{ticket['id']}", json={"status": "CLOSED"}, headers=ada.headers)
    assert resp.status_code == 409
    assert resp.json()["detail"] == "Invalid Status Transition"
    resp = client.patch(f"/tickets/{ticket['id']}", json={"status": "OPEN"}, headers=ada.headers)
    assert resp.status_code == 409


def test_patch_ticket_invalid_status_returns_422(client, ada):
    ticket = new_ticket(client, ada)
    resp = client.patch(
        f"/tickets/{ticket['id']}", json={"status": "NOT_A_STATUS"}, headers=ada.headers
    )
    assert resp.status_code == 422
    assert resp.json()["status"] == 422


def test_add_and_list_comments(client, ada):
    ticket = new_ticket(client, ada)
    for body in ["First comment", "Second comment"]:
        resp = client.post(
            f"/tickets/{ticket['id']}/comments", json={"body": body}, headers=ada.headers
        )
        assert resp.status_code == 201
        assert resp.json()["author_id"] == ada.id  # author comes from the token

    resp = client.get(f"/tickets/{ticket['id']}/comments", headers=ada.headers)
    comments = resp.json()
    assert [c["body"] for c in comments] == ["First comment", "Second comment"]


def test_comment_on_missing_ticket_returns_404(client, ada):
    resp = client.post("/tickets/999/comments", json={"body": "hello"}, headers=ada.headers)
    assert resp.status_code == 404


def test_delete_ticket_returns_204(client, ada, agent):
    ticket = new_ticket(client, ada)
    assert client.delete(f"/tickets/{ticket['id']}", headers=agent.headers).status_code == 204
    assert client.get(f"/tickets/{ticket['id']}", headers=agent.headers).status_code == 404
