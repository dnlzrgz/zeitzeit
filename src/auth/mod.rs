use axum::{Router, extract::DefaultBodyLimit, routing::post};

use crate::state::AppState;

mod handlers;
pub mod password;

pub fn routes() -> Router<AppState> {
    Router::new()
        .route("/register", post(handlers::register))
        .layer(DefaultBodyLimit::max(64 * 1024)) // Cap body size
}
