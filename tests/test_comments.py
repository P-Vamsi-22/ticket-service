import pytest


@pytest.fixture()
def setup(client):
    user = client.post("/users", json={"name": "Ada", "email": "ada@example.com"}).json()
    ticket = client.post(
        "/tickets",
        json={"title": "Bug", "description": "x", "created_by": user["id"]},
    ).json()
    return user["id"], ticket["id"]


def test_create_and_list_comments(client, setup):
    author_id, ticket_id = setup
    resp = client.post(
        f"/tickets/{ticket_id}/comments",
        json={"author_id": author_id, "body": "Looking into it"},
    )
    assert resp.status_code == 201
    assert resp.json()["body"] == "Looking into it"

    resp = client.get(f"/tickets/{ticket_id}/comments")
    assert resp.status_code == 200
    comments = resp.json()
    assert len(comments) == 1
    assert comments[0]["author_id"] == author_id


def test_comment_ticket_not_found(client, setup):
    author_id, _ = setup
    resp = client.post(
        "/tickets/999/comments",
        json={"author_id": author_id, "body": "hi"},
    )
    assert resp.status_code == 404


def test_comment_author_not_found(client, setup):
    _, ticket_id = setup
    resp = client.post(
        f"/tickets/{ticket_id}/comments",
        json={"author_id": 999, "body": "hi"},
    )
    assert resp.status_code == 404


def test_comment_empty_body(client, setup):
    author_id, ticket_id = setup
    resp = client.post(
        f"/tickets/{ticket_id}/comments",
        json={"author_id": author_id, "body": ""},
    )
    assert resp.status_code == 422


def test_delete_ticket_cascades_comments(client, setup):
    author_id, ticket_id = setup
    client.post(
        f"/tickets/{ticket_id}/comments",
        json={"author_id": author_id, "body": "note"},
    )
    client.delete(f"/tickets/{ticket_id}")
    assert client.get(f"/tickets/{ticket_id}/comments").status_code == 404
