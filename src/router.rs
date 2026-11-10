use axum::{
    Router,
    body::Body,
    extract::State,
    http::{Request, StatusCode},
    routing::get,
};
use tower_http::{
    catch_panic::CatchPanicLayer,
    request_id::{MakeRequestUuid, PropagateRequestIdLayer, SetRequestIdLayer},
    trace::{DefaultOnResponse, TraceLayer},
};
use tracing::Level;

use crate::{auth, state::AppState};

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
        .on_failure(());

    Router::new()
        .route("/healthz", get(healthz))
        .route("/readyz", get(readyz))
        .nest("/api/v1/auth", auth::routes())
        .layer(CatchPanicLayer::new())
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
