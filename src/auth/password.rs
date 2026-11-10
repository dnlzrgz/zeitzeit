use std::sync::LazyLock;

use anyhow::anyhow;
use argon2::{Argon2, PasswordHash, PasswordVerifier, password_hash::PasswordHasher};

use crate::error::AppError;

static DUMMY_HASH: LazyLock<String> = LazyLock::new(|| {
    Argon2::default()
        .hash_password(b"dummy password for timing")
        .expect("hashing a constant cannot fail")
        .to_string()
});

pub fn warm_up() {
    LazyLock::force(&DUMMY_HASH);
}

pub async fn verify(password: String, stored: Option<String>) -> Result<bool, AppError> {
    let outcome = tokio::task::spawn_blocking(move || -> anyhow::Result<bool> {
        let user_exists = stored.is_some();
        let phc = stored.as_deref().unwrap_or(DUMMY_HASH.as_str());

        let parsed = PasswordHash::new(phc)
            .map_err(|err| anyhow!("stored password hash is malformed: {err}"))?;
        let matches = Argon2::default()
            .verify_password(password.as_bytes(), &parsed)
            .is_ok();

        Ok(user_exists && matches)
    })
    .await
    .map_err(|err| anyhow!("verify task failed: {err}"))?;

    Ok(outcome?)
}

pub async fn password_hash(password: String) -> Result<String, AppError> {
    let result = tokio::task::spawn_blocking(move || {
        Argon2::default()
            .hash_password(password.as_bytes())
            .map(|hash| hash.to_string())
    })
    .await
    .map_err(|err| anyhow!("hashing task failed: {err}"))?;

    result.map_err(|err| anyhow!("password hashing failed: {err}").into())
}
