use axum::{Json, extract::State};

use crate::{
    auth::extractor::AuthUser,
    error::AppError,
    state::AppState,
    users::{UserResponse, repo},
};

pub async fn me(
    State(state): State<AppState>,
    auth: AuthUser,
) -> Result<Json<UserResponse>, AppError> {
    let user = repo::find_by_id(&state.pool, auth.user_id)
        .await?
        .ok_or(AppError::Unauthorized)?; // user deleted after token is checked
    Ok(Json(user.into()))
}
