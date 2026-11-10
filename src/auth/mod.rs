use axum::{
    Router,
    extract::DefaultBodyLimit,
    http::{HeaderValue, header},
    routing::post,
};
use tower_http::set_header::SetResponseHeaderLayer;

use crate::state::AppState;

pub mod extractor;
mod handlers;
pub mod password;
mod repo;
pub mod tokens;

pub fn routes() -> Router<AppState> {
    Router::new()
        .route("/register", post(handlers::register))
        .route("/login", post(handlers::login))
        .route("/logout", post(handlers::logout))
        .layer(DefaultBodyLimit::max(64 * 1024)) // Cap body size
        .layer(SetResponseHeaderLayer::overriding(
            header::CACHE_CONTROL,
            HeaderValue::from_static("no-store"),
        ))
}
