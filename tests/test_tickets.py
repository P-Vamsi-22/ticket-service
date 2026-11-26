from tests.conftest import new_ticket


def test_owner_comes_from_token_not_body(client, ada, bob):
    # Trying to create a ticket "as Bob" is ignored: the owner is whoever is logged in.
    resp = client.post(
        "/tickets",
        json={"title": "Bug", "description": "x", "created_by": bob.id},
        headers=ada.headers,
    )
    assert resp.status_code == 201
    assert resp.json()["created_by"] == ada.id


def test_create_ticket_invalid_status(client, ada):
    resp = client.post(
        "/tickets",
        json={"title": "Bug", "description": "x", "status": "BOGUS"},
        headers=ada.headers,
    )
    assert resp.status_code == 422


def test_list_tickets_pagination_and_filters(client, ada):
    for i in range(5):
        new_ticket(
            client,
            ada,
            title=f"T{i}",
            status="OPEN" if i % 2 == 0 else "CLOSED",
            priority="HIGH" if i % 2 == 0 else "LOW",
        )
    data = client.get("/tickets?page=1&size=2", headers=ada.headers).json()
    assert data["total"] == 5 and len(data["items"]) == 2

    data = client.get("/tickets?status=OPEN&priority=HIGH", headers=ada.headers).json()
    assert data["total"] == 3

    assert client.get("/tickets?page=0", headers=ada.headers).status_code == 422


def test_employee_list_shows_only_own_tickets(client, ada, bob, agent):
    new_ticket(client, ada, title="ada-1")
    new_ticket(client, ada, title="ada-2")
    new_ticket(client, bob, title="bob-1")

    ada_list = client.get("/tickets", headers=ada.headers).json()
    assert ada_list["total"] == 2
    assert {t["title"] for t in ada_list["items"]} == {"ada-1", "ada-2"}

    bob_list = client.get("/tickets", headers=bob.headers).json()
    assert [t["title"] for t in bob_list["items"]] == ["bob-1"]

    assert client.get("/tickets", headers=agent.headers).json()["total"] == 3


def test_agent_can_update_any_ticket(client, ada, agent):
    ticket = new_ticket(client, ada)
    resp = client.patch(
        f"/tickets/{ticket['id']}", json={"status": "IN_PROGRESS"}, headers=agent.headers
    )
    assert resp.status_code == 200
    assert resp.json()["created_by"] == ada.id


def test_get_ticket_not_found(client, ada):
    resp = client.get("/tickets/999", headers=ada.headers)
    assert resp.status_code == 404
    assert resp.json()["status"] == 404
