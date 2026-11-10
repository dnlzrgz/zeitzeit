use std::str::FromStr;

use axum::{Json, extract::State, http::StatusCode};
use chrono::{DateTime, Duration, Utc};
use chrono_tz::Tz;
use garde::Validate;
use serde::{Deserialize, Serialize};

use crate::{
    auth::{repo, tokens},
    error::AppError,
    extract::AppJson,
    state::AppState,
    users::{self, UserResponse, normalize_email},
};

use super::{extractor::AuthUser, password};

const MAX_PASSWORD_CHARS: usize = 128;

#[derive(Deserialize, Validate)]
#[serde(deny_unknown_fields)]
pub struct RegisterRequest {
    #[garde(email, length(max = 254))]
    email: String,
    #[garde(length(chars, min = 1, max = 254))]
    display_name: String,
    #[garde(length(chars, min = 10, max = 128))]
    password: String,
    #[serde(default = "default_timezone")]
    #[garde(custom(valid_timezone))]
    timezone: String,
}

fn default_timezone() -> String {
    "UTC".to_owned()
}

fn valid_timezone(value: &str, _: &()) -> garde::Result {
    Tz::from_str(value)
        .map(|_| ())
        .map_err(|_| garde::Error::new("unknown IANA timezone"))
}

impl RegisterRequest {
    fn normalize(&mut self) {
        self.email = self.email.trim().to_lowercase();
        self.display_name = self.display_name.trim().to_owned();
    }
}

pub async fn register(
    State(state): State<AppState>,
    AppJson(mut req): AppJson<RegisterRequest>,
) -> Result<(StatusCode, Json<UserResponse>), AppError> {
    req.normalize();
    req.validate()
        .map_err(|report| AppError::Validation(report.to_string()))?;

    let password_hash = password::password_hash(req.password).await?;

    let user = users::repo::insert(
        &state.pool,
        &users::repo::NewUser {
            email: &req.email,
            display_name: &req.display_name,
            password_hash: &password_hash,
            timezone: &req.timezone,
        },
    )
    .await?;

    Ok((StatusCode::CREATED, Json(user.into())))
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LoginRequest {
    email: String,
    password: String,
}

#[derive(Serialize)]
pub struct LoginResponse {
    token: String,
    expires_at: DateTime<Utc>,
}

pub async fn login(
    State(state): State<AppState>,
    AppJson(req): AppJson<LoginRequest>,
) -> Result<Json<LoginResponse>, AppError> {
    if req.password.chars().count() > MAX_PASSWORD_CHARS {
        return Err(AppError::Unauthorized);
    }

    let email = normalize_email(&req.email);
    let user = users::repo::find_by_email(&state.pool, &email).await?;

    let stored = user.as_ref().map(|u| u.password_hash.clone());
    let password_ok = password::verify(req.password, stored).await?;

    // Unknown email or wrong password produce same response.
    let user = user.filter(|_| password_ok).ok_or(AppError::Unauthorized)?;
    let expires_at = i64::try_from(state.config.session_ttl_hours)
        .ok()
        .and_then(Duration::try_hours)
        .and_then(|ttl| Utc::now().checked_add_signed(ttl))
        .ok_or_else(|| anyhow::anyhow!("session_ttl_hours out of range"))?;

    let token = tokens::generate()?;
    repo::insert_token(
        &state.pool,
        user.id,
        "session",
        "session",
        &token.hash[..],
        Some(expires_at),
    )
    .await?;

    Ok(Json(LoginResponse {
        token: token.plaintext,
        expires_at,
    }))
}

pub async fn logout(State(state): State<AppState>, auth: AuthUser) -> Result<StatusCode, AppError> {
    repo::revoke_token(&state.pool, auth.token_id, auth.user_id).await?;
    Ok(StatusCode::NO_CONTENT)
}
