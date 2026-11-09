use anyhow::anyhow;
use argon2::{Argon2, password_hash::PasswordHasher};

use crate::error::AppError;

pub async fn hash(password: String) -> Result<String, AppError> {
    let result = tokio::task::spawn_blocking(move || {
        Argon2::default()
            .hash_password(password.as_bytes())
            .map(|hash| hash.to_string())
    })
    .await
    .map_err(|err| anyhow!("hashing task failed: {err}"))?;

    result.map_err(|err| anyhow!("password hashing failed: {err}").into())
}
