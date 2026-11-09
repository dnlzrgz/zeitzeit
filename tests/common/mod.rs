#![allow(dead_code)]

use std::sync::Arc;

use axum::Router;
use sqlx::PgPool;
use zeitzeit::{config::Config, router::build_router, state::AppState};

pub fn test_app(pool: PgPool) -> Router {
    let config = Arc::new(Config {
        database_url: String::new(),
        bind_addr: "127.0.0.1:0".to_owned(),
        session_ttl_hours: 1,
    });

    build_router(AppState { pool, config })
}
