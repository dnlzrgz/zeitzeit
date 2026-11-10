use chrono::{DateTime, Utc};
use sqlx::PgPool;
use uuid::Uuid;

use super::extractor::AuthUser;

pub async fn insert_token(
    pool: &PgPool,
    user_id: Uuid,
    kind: &str,
    name: &str,
    token_hash: &[u8],
    expires_at: Option<DateTime<Utc>>,
) -> Result<(), sqlx::Error> {
    sqlx::query(
        "INSERT INTO auth_tokens (user_id, kind, name, token_hash, expires_at)
         VALUES ($1, $2, $3, $4, $5)",
    )
    .bind(user_id)
    .bind(kind)
    .bind(name)
    .bind(token_hash)
    .bind(expires_at)
    .execute(pool)
    .await?;

    Ok(())
}

pub async fn find_active_token(
    pool: &PgPool,
    token_hash: &[u8],
) -> Result<Option<AuthUser>, sqlx::Error> {
    sqlx::query_as::<_, AuthUser>(
        "SELECT user_id, id AS token_id
           FROM auth_tokens
          WHERE token_hash = $1
            AND revoked_at IS NULL
            AND (expires_at IS NULL OR expires_at > now())",
    )
    .bind(token_hash)
    .fetch_optional(pool)
    .await
}

pub async fn revoke_token(pool: &PgPool, token_id: Uuid, user_id: Uuid) -> Result<(), sqlx::Error> {
    sqlx::query(
        "UPDATE auth_tokens SET revoked_at = now()
         WHERE id = $1 AND user_id = $2 AND revoked_at IS NULL",
    )
    .bind(token_id)
    .bind(user_id)
    .execute(pool)
    .await?;

    Ok(())
}
