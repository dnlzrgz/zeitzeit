import argparse
import random
from datetime import datetime, timedelta, timezone

from faker import Faker
from sqlmodel import Session

from app.db import engine
from app.models import (
    Project,
    Tag,
    TimeEntry,
    TimeEntryTagLink,
    User,
)

faker = Faker()

SEED_SIZES = {
    "small": {
        "users": 10,
        "projects_per_user": 5,
        "tags_per_user": 10,
        "entries_per_user": 500,
    },
    "medium": {
        "users": 50,
        "projects_per_user": 10,
        "tags_per_user": 15,
        "entries_per_user": 2_000,
    },
    "large": {
        "users": 250,
        "projects_per_user": 15,
        "tags_per_user": 25,
        "entries_per_user": 10_000,
    },
}


def seed(size: str) -> None:
    sizes = SEED_SIZES[size]
    with Session(engine) as session:
        users: list[User] = [
            User(
                email=f"user{i}@example.com",
                hashed_password="password123",
                full_name=faker.name(),
            )
            for i in range(sizes["users"])
        ]
        session.add_all(users)
        session.commit()
        for user in users:
            projects = [
                Project(
                    user_id=user.id,
                    name=f"project_{i}",
                    color=faker.hex_color(),
                )
                for i in range(sizes["projects_per_user"])
            ]
            session.add_all(projects)

            tags = [
                Tag(user_id=user.id, name=f"tag_{i}")
                for i in range(sizes["tags_per_user"])
            ]
            session.add_all(tags)

            entries: list[TimeEntry] = []
            links: list[TimeEntryTagLink] = []
            for _ in range(sizes["entries_per_user"]):
                start = datetime.now(timezone.utc) - timedelta(
                    days=random.randint(0, 365),
                    hours=random.randint(0, 23),
                )
                duration_minutes = random.randint(15, 240)

                entry = TimeEntry(
                    user_id=user.id,
                    project_id=random.choice(projects).id,
                    description=faker.sentence(),
                    start_time=start,
                    end_time=start + timedelta(minutes=duration_minutes),
                )
                entries.append(entry)

            session.add_all(entries)
            session.commit()

            for entry in entries:
                selected_tags = random.sample(
                    tags,
                    k=random.randint(0, min(3, len(tags))),
                )
                for tag in selected_tags:
                    links.append(
                        TimeEntryTagLink(
                            time_entry_id=entry.id,
                            tag_id=tag.id,
                        )
                    )

            session.add_all(links)
            session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--size",
        choices=["small", "medium", "large"],
        default="small",
    )
    args = parser.parse_args()
    seed(args.size)
