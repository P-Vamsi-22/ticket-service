import pytest


@pytest.fixture()
def user_id(client):
    resp = client.post("/users", json={"name": "Ada", "email": "ada@example.com"})
    return resp.json()["id"]


def test_create_ticket(client, user_id):
    resp = client.post(
        "/tickets",
        json={
            "title": "Bug",
            "description": "Something broke",
            "created_by": user_id,
            "priority": "HIGH",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "OPEN"
    assert data["priority"] == "HIGH"
    assert data["created_by"] == user_id


def test_create_ticket_user_not_found(client):
    resp = client.post(
        "/tickets",
        json={"title": "Bug", "description": "x", "created_by": 999},
    )
    assert resp.status_code == 404


def test_create_ticket_invalid_status(client, user_id):
    resp = client.post(
        "/tickets",
        json={"title": "Bug", "description": "x", "created_by": user_id, "status": "BOGUS"},
    )
    assert resp.status_code == 422


def test_list_tickets_pagination_and_filters(client, user_id):
    for i in range(5):
        client.post(
            "/tickets",
            json={
                "title": f"T{i}",
                "description": "d",
                "created_by": user_id,
                "status": "OPEN" if i % 2 == 0 else "CLOSED",
                "priority": "HIGH" if i % 2 == 0 else "LOW",
            },
        )

    resp = client.get("/tickets?page=1&size=2")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["size"] == 2
    assert len(data["items"]) == 2

    resp = client.get("/tickets?status=OPEN&priority=HIGH")
    data = resp.json()
    assert data["total"] == 3
    assert all(t["status"] == "OPEN" and t["priority"] == "HIGH" for t in data["items"])

    resp = client.get("/tickets?page=0")
    assert resp.status_code == 422


def test_get_update_delete_ticket(client, user_id):
    ticket = client.post(
        "/tickets",
        json={"title": "Bug", "description": "x", "created_by": user_id},
    ).json()

    resp = client.get(f"/tickets/{ticket['id']}")
    assert resp.status_code == 200

    resp = client.patch(
        f"/tickets/{ticket['id']}", json={"status": "IN_PROGRESS", "priority": "LOW"}
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "IN_PROGRESS"
    assert resp.json()["priority"] == "LOW"

    resp = client.delete(f"/tickets/{ticket['id']}")
    assert resp.status_code == 204
    assert client.get(f"/tickets/{ticket['id']}").status_code == 404


def test_get_ticket_not_found(client):
    resp = client.get("/tickets/999")
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
