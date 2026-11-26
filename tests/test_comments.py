import pytest

from tests.conftest import new_ticket


@pytest.fixture()
def ticket_id(client, ada):
    return new_ticket(client, ada)["id"]


def test_create_and_list_comments(client, ada, ticket_id):
    resp = client.post(
        f"/tickets/{ticket_id}/comments", json={"body": "Looking into it"}, headers=ada.headers
    )
    assert resp.status_code == 201
    comments = client.get(f"/tickets/{ticket_id}/comments", headers=ada.headers).json()
    assert len(comments) == 1
    assert comments[0]["author_id"] == ada.id


def test_author_id_in_body_is_ignored(client, ada, bob, agent, ticket_id):
    resp = client.post(
        f"/tickets/{ticket_id}/comments",
        json={"body": "hi", "author_id": bob.id},
        headers=agent.headers,
    )
    assert resp.status_code == 201
    assert resp.json()["author_id"] == agent.id


def test_comment_ticket_not_found(client, ada):
    resp = client.post("/tickets/999/comments", json={"body": "hi"}, headers=ada.headers)
    assert resp.status_code == 404


def test_comment_empty_body(client, ada, ticket_id):
    resp = client.post(f"/tickets/{ticket_id}/comments", json={"body": ""}, headers=ada.headers)
    assert resp.status_code == 422


def test_delete_ticket_cascades_comments(client, ada, agent, ticket_id):
    client.post(f"/tickets/{ticket_id}/comments", json={"body": "note"}, headers=ada.headers)
    assert client.delete(f"/tickets/{ticket_id}", headers=agent.headers).status_code == 204
    assert client.get(f"/tickets/{ticket_id}/comments", headers=agent.headers).status_code == 404
