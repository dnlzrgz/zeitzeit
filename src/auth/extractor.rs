use axum::{
    extract::FromRequestParts,
    http::{HeaderMap, header, request::Parts},
};
use uuid::Uuid;

use super::{repo, tokens};
use crate::{error::AppError, state::AppState};

#[derive(sqlx::FromRow)]
pub struct AuthUser {
    pub user_id: Uuid,
    pub token_id: Uuid,
}

impl FromRequestParts<AppState> for AuthUser {
    type Rejection = AppError;

    async fn from_request_parts(
        parts: &mut Parts,
        state: &AppState,
    ) -> Result<Self, Self::Rejection> {
        let token = bearer_token(&parts.headers).ok_or(AppError::Unauthorized)?;
        repo::find_active_token(&state.pool, &tokens::token_hash(token))
            .await?
            .ok_or(AppError::Unauthorized)
    }
}

fn bearer_token(headers: &HeaderMap) -> Option<&str> {
    let value = headers.get(header::AUTHORIZATION)?.to_str().ok()?;
    let (scheme, token) = value.split_once(' ')?;
    scheme
        .eq_ignore_ascii_case("bearer")
        .then_some(token.trim())
}
