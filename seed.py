"""Seed the database with fake data. Safe to re-run (skips if users exist)."""

import random
import sys

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import Comment, Ticket, TicketPriority, TicketStatus, User

FIRST_NAMES = ["Ada", "Grace", "Alan", "Edsger", "Barbara", "Donald", "Radia", "Linus"]
LAST_NAMES = ["Lovelace", "Hopper", "Turing", "Dijkstra", "Liskov", "Knuth", "Perlman", "Torvalds"]
TITLES = [
    "Login page crashes on submit",
    "Add dark mode support",
    "Fix typo in settings menu",
    "Slow dashboard load times",
    "Export reports to CSV",
    "Password reset email not sent",
    "Mobile nav overlaps header",
    "Upgrade dependency X to v2",
]
DESCRIPTIONS = [
    "Users report the login form freezes after clicking submit.",
    "Several users requested a dark theme option in preferences.",
    "Minor copy fix needed in the settings sidebar.",
    "Dashboard takes over 5 seconds to render for large accounts.",
    "Need ability to download monthly reports as CSV files.",
    "Reset emails are queued but never delivered.",
    "On screens under 375px the nav covers the page title.",
    "Dependency X has a security advisory; upgrade required.",
]
COMMENT_BODIES = [
    "Can you reproduce this on staging?",
    "I think this started after the last deploy.",
    "Assigned to me, looking into it.",
    "Fixed in PR #123, pending review.",
    "This is a duplicate of ticket #4.",
    "Works on my machine — need more info.",
]


def seed() -> None:
    required_tables = {"users", "tickets", "comments"}
    existing_tables = set(inspect(engine).get_table_names())
    if not required_tables.issubset(existing_tables):
        print("Run 'uv run alembic upgrade head' first.")
        sys.exit(1)

    rng = random.Random(42)
    with Session(engine) as db:
        if db.scalar(select(User).limit(1)) is not None:
            print("Database already seeded, skipping.")
            return

        users = [
            User(name=f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}", email=f"user{i}@example.com")
            for i in range(8)
        ]
        db.add_all(users)
        db.flush()

        tickets = []
        for i in range(15):
            tickets.append(
                Ticket(
                    title=TITLES[i % len(TITLES)],
                    description=DESCRIPTIONS[i % len(DESCRIPTIONS)],
                    status=rng.choice(list(TicketStatus)),
                    priority=rng.choice(list(TicketPriority)),
                    created_by=rng.choice(users).id,
                )
            )
        db.add_all(tickets)
        db.flush()

        for _ in range(20):
            db.add(
                Comment(
                    ticket_id=rng.choice(tickets).id,
                    author_id=rng.choice(users).id,
                    body=rng.choice(COMMENT_BODIES),
                )
            )
        db.commit()
        print(f"Seeded {len(users)} users, {len(tickets)} tickets, 20 comments.")


if __name__ == "__main__":
    seed()
