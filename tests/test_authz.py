"""Authorization matrix: every protected endpoint x 4 callers.

owner  = employee who created ticket T     other = a different employee
agent  = support agent                     anon  = no token
"""
import pytest

from tests.conftest import new_ticket

#            name,                      method,   path,                            json,                     anon, owner, other, agent
MATRIX = [
    ("list tickets",                    "GET",    "/tickets",                      None,                     401,  200,   200,   200),
    ("create ticket",                   "POST",   "/tickets",                      {"title": "t", "description": "d"}, 401, 201, 201, 201),
    ("get ticket T",                    "GET",    "/tickets/{T}",                  None,                     401,  200,   403,   200),
    ("update ticket T",                 "PATCH",  "/tickets/{T}",                  {"priority": "LOW"},      401,  200,   403,   200),
    ("delete ticket T (agents only)",   "DELETE", "/tickets/{T}",                  None,                     401,  403,   403,   204),
    ("list comments on T",              "GET",    "/tickets/{T}/comments",         None,                     401,  200,   403,   200),
    ("add comment on T",                "POST",   "/tickets/{T}/comments",         {"body": "hi"},           401,  201,   403,   201),
    ("get owner's profile",             "GET",    "/users/{OWNER}",                None,                     401,  200,   403,   200),
    ("who am I",                        "GET",    "/auth/me",                      None,                     401,  200,   200,   200),
]
CALLERS = ["anon", "owner", "other", "agent"]
CASES = [
    pytest.param(row, caller, row[4 + i], id=f"{row[0]} | {caller} -> {row[4 + i]}")
    for row in MATRIX
    for i, caller in enumerate(CALLERS)
]


@pytest.mark.parametrize("row, caller, expected", CASES)
def test_authz_matrix(client, ada, bob, agent, row, caller, expected):
    _, method, path, body, *_ = row
    ticket = new_ticket(client, ada)  # ada owns T
    url = path.format(T=ticket["id"], OWNER=ada.id)
    headers = {"anon": {}, "owner": ada.headers, "other": bob.headers, "agent": agent.headers}[caller]
    resp = client.request(method, url, json=body, headers=headers)
    assert resp.status_code == expected, resp.text


def test_public_endpoints_need_no_token(client):
    assert client.get("/health").status_code == 200
    resp = client.post("/users", json={"name": "N", "email": "n@example.com", "password": "n-pass-123"})
    assert resp.status_code == 201


def test_other_employee_cannot_see_ticket_in_list(client, ada, bob):
    new_ticket(client, ada)
    assert client.get("/tickets", headers=bob.headers).json()["total"] == 0
