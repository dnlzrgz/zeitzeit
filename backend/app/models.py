import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from pydantic import BeforeValidator, EmailStr, model_validator
from pydantic_extra_types.color import Color
from sqlalchemy import DateTime
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint


def get_datetime_utc() -> datetime:
    return datetime.now(timezone.utc)


def _color_to_hex(v: Any) -> str:
    """
    Validates and normalizes any CSS color format
    """
    return Color(v).as_hex(format="long").upper()


HexColor = Annotated[str, BeforeValidator(_color_to_hex)]


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_admin: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore[assignment]
    password: str | None = Field(default=None, min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)


class UserUpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    hashed_password: str
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )

    time_entries: list[TimeEntry] = Relationship(
        back_populates="user",
        cascade_delete=True,
    )
    projects: list[Project] = Relationship(
        back_populates="user",
        cascade_delete=True,
    )
    tags: list[Tag] = Relationship(
        back_populates="user",
        cascade_delete=True,
    )


class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime | None = None


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


class ProjectBase(SQLModel):
    name: str = Field(max_length=255)
    color: HexColor = Field(max_length=7)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=255)
    color: HexColor | None = Field(default=None, max_length=7)


class Project(ProjectBase, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="unique_project_per_user"),
    )

    id: uuid.UUID = Field(
        default_factory=uuid.uuid7,
        primary_key=True,
    )
    created_at: datetime | None = Field(
        default_factory=get_datetime_utc,
        sa_type=DateTime(timezone=True),  # type: ignore
    )
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    user: User | None = Relationship(back_populates="projects")
    time_entries: list[TimeEntry] = Relationship(back_populates="project")


class ProjectPublic(ProjectBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime | None = None


class ProjectsPublic(SQLModel):
    data: list[ProjectPublic]
    count: int


class TimeEntryTagLink(SQLModel, table=True):
    time_entry_id: uuid.UUID = Field(foreign_key="timeentry.id", primary_key=True)
    tag_id: uuid.UUID = Field(foreign_key="tag.id", primary_key=True)


class TagBase(SQLModel):
    name: str = Field(max_length=100)


class TagCreate(TagBase):
    pass


class TagUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=100)


class Tag(TagBase, table=True):
    __table_args__ = (UniqueConstraint("user_id", "name", name="unique_tag_per_user"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    user: User | None = Relationship(back_populates="tags")
    time_entries: list["TimeEntry"] = Relationship(
        back_populates="tags",
        link_model=TimeEntryTagLink,
    )


class TagPublic(TagBase):
    id: uuid.UUID
    user_id: uuid.UUID


class TagsPublic(SQLModel):
    data: list[TagPublic]
    count: int


class TimeEntryBase(SQLModel):
    description: str = Field(default="", max_length=255)
    start_time: datetime = Field(default_factory=get_datetime_utc)
    end_time: datetime | None = None

    @model_validator(mode="after")
    def check_end_after_start(self) -> "TimeEntryBase":
        if self.end_time is not None and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")

        return self


class TimeEntryCreate(TimeEntryBase):
    project_id: uuid.UUID | None = None
    tag_ids: list[uuid.UUID] = Field(default_factory=list)


class TimeEntryUpdate(SQLModel):
    description: str | None = Field(default=None, max_length=255)
    start_time: datetime | None = None
    end_time: datetime | None = None
    project_id: uuid.UUID | None = None
    tag_ids: list[uuid.UUID] | None = None

    @model_validator(mode="after")
    def check_end_after_start(self) -> "TimeEntryUpdate":
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")

        return self


class TimeEntry(TimeEntryBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid7, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    user: User | None = Relationship(back_populates="time_entries")
    project_id: uuid.UUID | None = Field(
        default=None, foreign_key="project.id", ondelete="SET NULL"
    )
    project: Project | None = Relationship(back_populates="time_entries")
    tags: list[Tag] = Relationship(
        back_populates="time_entries", link_model=TimeEntryTagLink
    )


class TimeEntryPublic(TimeEntryBase):
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID | None = None
    tags: list[TagPublic] = []


class TimeEntriesPublic(SQLModel):
    data: list[TimeEntryPublic]
    count: int


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# JWT token content
class TokenPayload(SQLModel):
    sub: str | None = None
