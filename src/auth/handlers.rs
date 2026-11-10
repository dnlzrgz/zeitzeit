use std::str::FromStr;

use axum::{Json, extract::State, http::StatusCode};
use chrono_tz::Tz;
use garde::Validate;
use serde::Deserialize;

use crate::{
    error::AppError,
    extract::AppJson,
    state::AppState,
    users::{UserResponse, repo},
};

use super::password;

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

    let password_hash = password::hash(req.password).await?;

    let user = repo::insert(
        &state.pool,
        &repo::NewUser {
            email: &req.email,
            display_name: &req.display_name,
            password_hash: &password_hash,
            timezone: &req.timezone,
        },
    )
    .await?;

    Ok((StatusCode::CREATED, Json(user.into())))
}
