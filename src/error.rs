use axum::{
    Json,
    http::{HeaderValue, StatusCode, header},
    response::{IntoResponse, Response},
};
use serde::Serialize;

/// The only error type that turns into an HTTP response.
#[derive(Debug, thiserror::Error)]
pub enum AppError {
    #[error("{resource} not found")]
    NotFound { resource: &'static str },
    #[error("{0}")]
    Validation(String),
    #[error("{0}")]
    Conflict(String),
    #[error("authentication required")]
    Unauthorized,
    #[error(transparent)]
    Database(#[from] sqlx::Error),
    #[error(transparent)]
    Internal(#[from] anyhow::Error),
}

/// RFC 9457 problem details.
#[derive(Debug, Serialize)]
struct ProblemDetails {
    #[serde(rename = "type")]
    kind: &'static str,
    title: &'static str,
    status: u16,
    detail: String,
}

impl AppError {
    fn status_and_detail(&self) -> (StatusCode, String) {
        match self {
            AppError::NotFound { .. } => (StatusCode::NOT_FOUND, self.to_string()),
            AppError::Validation(_) => (StatusCode::UNPROCESSABLE_ENTITY, self.to_string()),
            AppError::Conflict(_) => (StatusCode::CONFLICT, self.to_string()),
            AppError::Unauthorized => (StatusCode::UNAUTHORIZED, self.to_string()),
            AppError::Database(err) => db_status_and_detail(err),
            AppError::Internal(_) => (
                StatusCode::INTERNAL_SERVER_ERROR,
                "internal server error".to_owned(),
            ),
        }
    }
}

fn db_status_and_detail(err: &sqlx::Error) -> (StatusCode, String) {
    let (status, detail) = match err {
        sqlx::Error::RowNotFound => (StatusCode::INTERNAL_SERVER_ERROR, "internal server error"),
        sqlx::Error::PoolTimedOut => (
            StatusCode::SERVICE_UNAVAILABLE,
            "service temporarily unavailable",
        ),
        sqlx::Error::Database(cause) if cause.is_unique_violation() => {
            (StatusCode::CONFLICT, "resource already exists")
        }
        // 404 rather than 409: a foreign id belongs to someone else and the
        // client should not learn whether it exists or not.
        sqlx::Error::Database(cause) if cause.is_foreign_key_violation() => {
            (StatusCode::NOT_FOUND, "resource not found")
        }
        sqlx::Error::Database(cause) if cause.is_check_violation() => {
            (StatusCode::UNPROCESSABLE_ENTITY, "invalid input")
        }
        _ => (StatusCode::INTERNAL_SERVER_ERROR, "internal server error"),
    };

    (status, detail.to_owned())
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, detail) = self.status_and_detail();

        if status.is_server_error() {
            tracing::error!(error = ?self, "request failed");
        }

        let body = ProblemDetails {
            kind: "about:blank",
            title: status.canonical_reason().unwrap_or("Error"),
            status: status.as_u16(),
            detail,
        };

        let mut response = Json(body).into_response();
        *response.status_mut() = status;
        response.headers_mut().insert(
            header::CONTENT_TYPE,
            HeaderValue::from_static("application/problem+json"),
        );

        // Tell clients to back off instead of retrying immediately.
        if status == StatusCode::SERVICE_UNAVAILABLE {
            response
                .headers_mut()
                .insert(header::RETRY_AFTER, HeaderValue::from_static("2"));
        }

        response
    }
}
