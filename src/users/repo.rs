use sqlx::PgPool;
use uuid::Uuid;

use super::User;

pub struct NewUser<'a> {
    pub email: &'a str,
    pub display_name: &'a str,
    pub password_hash: &'a str,
    pub timezone: &'a str,
}

pub async fn insert(pool: &PgPool, new: &NewUser<'_>) -> Result<User, sqlx::Error> {
    sqlx::query_as::<_, User>(
        "INSERT INTO users (email, display_name, password_hash, timezone)
         VALUES ($1, $2, $3, $4)
         RETURNING id, email, display_name, password_hash, timezone,
                   week_start, created_at, updated_at",
    )
    .bind(new.email)
    .bind(new.display_name)
    .bind(new.password_hash)
    .bind(new.timezone)
    .fetch_one(pool)
    .await
}

pub async fn find_by_email(pool: &PgPool, email: &str) -> Result<Option<User>, sqlx::Error> {
    sqlx::query_as::<_, User>(
        "SELECT id, email, display_name, password_hash, timezone,
                week_start, created_at, updated_at
           FROM users WHERE email = $1",
    )
    .bind(email)
    .fetch_optional(pool)
    .await
}

pub async fn find_by_id(pool: &PgPool, id: Uuid) -> Result<Option<User>, sqlx::Error> {
    sqlx::query_as::<_, User>(
        "SELECT id, email, display_name, password_hash, timezone,
                week_start, created_at, updated_at
           FROM users WHERE id = $1",
    )
    .bind(id)
    .fetch_optional(pool)
    .await
}
