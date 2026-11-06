use axum::{
    Router,
    body::Body,
    extract::State,
    http::{Request, StatusCode},
    routing::get,
};
use tower_http::{
    request_id::{MakeRequestUuid, PropagateRequestIdLayer, SetRequestIdLayer},
    trace::{DefaultOnFailure, DefaultOnResponse, TraceLayer},
};
use tracing::Level;

use crate::state::AppState;

pub fn build_router(state: AppState) -> Router {
    let trace = TraceLayer::new_for_http()
        .make_span_with(|request: &Request<Body>| {
            let request_id = request
                .headers()
                .get("x-request-id")
                .and_then(|val| val.to_str().ok())
                .unwrap_or("-");

            tracing::info_span!(
                "http.request",
                method = %request.method(),
                uri = %request.uri(),
                request_id = %request_id,
            )
        })
        .on_response(DefaultOnResponse::new().level(Level::INFO))
        .on_failure(DefaultOnFailure::new().level(Level::ERROR));

    Router::new()
        .route("/healthz", get(healthz))
        .route("/readyz", get(readyz))
        .layer(trace)
        .layer(PropagateRequestIdLayer::x_request_id())
        .layer(SetRequestIdLayer::x_request_id(MakeRequestUuid))
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
