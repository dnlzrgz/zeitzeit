use axum::{Router, extract::State, http::StatusCode, routing::get};

use crate::state::AppState;

pub fn build_router(state: AppState) -> Router {
    Router::new()
        .route("/healthz", get(healthz))
        .route("/readyz", get(readyz))
        .with_state(state)
}

async fn healthz() -> &'static str {
    "ok"
}

async fn readyz(State(state): State<AppState>) -> (StatusCode, &'static str) {
    match sqlx::query("SELECT 1").execute(&state.pool).await {
        Ok(_) => (StatusCode::OK, "ok"),
        Err(err) => {
            tracing::error!(error = %err, "database check failed");
            (StatusCode::SERVICE_UNAVAILABLE, "database not available")
        }
    }
}
