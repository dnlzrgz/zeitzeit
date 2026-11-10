use axum::extract::FromRequest;

use crate::error::AppError;

#[derive(FromRequest)]
#[from_request(via(axum::Json), rejection(AppError))]
pub struct AppJson<T>(pub T);
