from sqlmodel import Session, select

from app.models import User, UserCreate, UserUpdate
from app.security import get_password_hash, verify_password

DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def create(*, session: Session, user_create: UserCreate) -> User:
    user = User.model_validate(
        user_create,
        update={
            "hashed_password": get_password_hash(user_create.password),
        },
    )

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


def update(*, session: Session, db_user: User, user_in: UserUpdate) -> User:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}

    if "password" in user_data:
        extra_data["hashed_password"] = get_password_hash(user_data.pop("password"))

    db_user.sqlmodel_update(user_data, update=extra_data)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


def get_by_email(*, session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    user = get_by_email(session=session, email=email)
    if not user:
        verify_password(password, DUMMY_HASH)  # timing attack prevention
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
