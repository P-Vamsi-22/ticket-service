"""Integration tests against a fresh in-memory SQLite DB per test.

The `client` fixture (tests/conftest.py) overrides `get_db` with a
StaticPool in-memory engine and runs `Base.metadata.create_all`, so
each test gets an isolated database and `ticket.db` is never touched.
"""


def create_user(client, name="Ada", email="ada@example.com"):
    resp = client.post("/users", json={"name": name, "email": email})
    assert resp.status_code == 201
    return resp.json()


def create_ticket(client, user_id, **overrides):
    payload = {
        "title": "Bug report",
        "description": "Something is broken",
        "created_by": user_id,
    }
    payload.update(overrides)
    resp = client.post("/tickets", json=payload)
    assert resp.status_code == 201
    return resp.json()


def test_create_user(client):
    user = create_user(client)
    assert user["id"] == 1
    assert user["name"] == "Ada"
    assert user["email"] == "ada@example.com"


def test_duplicate_email_returns_409(client):
    create_user(client)
    resp = client.post("/users", json={"name": "Ada2", "email": "ada@example.com"})
    assert resp.status_code == 409
    assert resp.json()["status"] == 409


def test_create_ticket(client):
    user = create_user(client)
    ticket = create_ticket(client, user["id"], priority="HIGH")
    assert ticket["status"] == "OPEN"
    assert ticket["priority"] == "HIGH"
    assert ticket["created_by"] == user["id"]


def test_create_ticket_unknown_user_returns_404(client):
    resp = client.post(
        "/tickets",
        json={"title": "Bug", "description": "x", "created_by": 999},
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404


def test_get_ticket_not_found(client):
    resp = client.get("/tickets/999")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404


def test_list_tickets_pagination(client):
    user = create_user(client)
    for i in range(5):
        create_ticket(client, user["id"], title=f"Ticket {i}")

    resp = client.get("/tickets?page=2&size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert data["page"] == 2
    assert data["size"] == 2
    assert len(data["items"]) == 2


def test_list_tickets_filter_by_priority(client):
    user = create_user(client)
    create_ticket(client, user["id"], priority="HIGH")
    create_ticket(client, user["id"], priority="LOW")
    create_ticket(client, user["id"], priority="HIGH")

    resp = client.get("/tickets?priority=HIGH")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert all(t["priority"] == "HIGH" for t in data["items"])


def test_list_tickets_filter_by_status(client):
    user = create_user(client)
    t1 = create_ticket(client, user["id"], status="OPEN")
    create_ticket(client, user["id"], status="CLOSED")
    client.patch(f"/tickets/{t1['id']}", json={"status": "IN_PROGRESS"})

    resp = client.get("/tickets?status=IN_PROGRESS")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "IN_PROGRESS"


def test_patch_ticket_valid_status_change(client):
    user = create_user(client)
    ticket = create_ticket(client, user["id"])

    resp = client.patch(
        f"/tickets/{ticket['id']}",
        json={"status": "IN_PROGRESS", "priority": "LOW"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["priority"] == "LOW"
    # created_by is immutable
    assert data["created_by"] == user["id"]


def test_patch_ticket_invalid_transition_returns_409(client):
    user = create_user(client)
    ticket = create_ticket(client, user["id"])  # status OPEN

    resp = client.patch(f"/tickets/{ticket['id']}", json={"status": "CLOSED"})
    assert resp.status_code == 409
    body = resp.json()
    assert body["status"] == 409
    assert body["detail"] == "Invalid Status Transition"

    # same-status change is also invalid
    resp = client.patch(f"/tickets/{ticket['id']}", json={"status": "OPEN"})
    assert resp.status_code == 409


def test_patch_ticket_invalid_status_returns_422(client):
    """Invalid enum values fail Pydantic validation -> 422 (409 is only for invalid transitions)."""
    user = create_user(client)
    ticket = create_ticket(client, user["id"])

    resp = client.patch(f"/tickets/{ticket['id']}", json={"status": "NOT_A_STATUS"})
    assert resp.status_code == 422
    assert resp.json()["status"] == 422


def test_add_and_list_comments(client):
    user = create_user(client)
    ticket = create_ticket(client, user["id"])

    resp = client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"author_id": user["id"], "body": "First comment"},
    )
    assert resp.status_code == 201
    assert resp.json()["body"] == "First comment"

    resp = client.post(
        f"/tickets/{ticket['id']}/comments",
        json={"author_id": user["id"], "body": "Second comment"},
    )
    assert resp.status_code == 201

    resp = client.get(f"/tickets/{ticket['id']}/comments")
    assert resp.status_code == 200
    comments = resp.json()
    assert len(comments) == 2
    assert [c["body"] for c in comments] == ["First comment", "Second comment"]
    assert all(c["ticket_id"] == ticket["id"] for c in comments)


def test_comment_on_missing_ticket_returns_404(client):
    user = create_user(client)
    resp = client.post(
        "/tickets/999/comments",
        json={"author_id": user["id"], "body": "hello"},
    )
    assert resp.status_code == 404
    assert resp.json()["status"] == 404


def test_delete_ticket_returns_204(client):
    user = create_user(client)
    ticket = create_ticket(client, user["id"])

    resp = client.delete(f"/tickets/{ticket['id']}")
    assert resp.status_code == 204
    assert client.get(f"/tickets/{ticket['id']}").status_code == 404
