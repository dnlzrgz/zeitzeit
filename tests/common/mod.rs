#![allow(dead_code)]

use std::sync::Arc;

use axum::{
    Router,
    body::Body,
    http::{Request, header},
    response::Response,
};
use http_body_util::BodyExt;
use serde_json::Value;
use sqlx::PgPool;
use tower::ServiceExt;

use zeitzeit::{config::Config, router::build_router, state::AppState};

pub fn test_app(pool: PgPool) -> Router {
    let config = Arc::new(Config {
        database_url: String::new(),
        bind_addr: "127.0.0.1:0".to_owned(),
        session_ttl_hours: 1,
    });

    build_router(AppState { pool, config })
}

pub async fn post_json(app: &Router, uri: &str, body: &Value) -> Response {
    post_raw(app, uri, "application/json", body.to_string()).await
}

pub async fn post_raw(app: &Router, uri: &str, content_type: &str, body: String) -> Response {
    app.clone()
        .oneshot(
            Request::post(uri)
                .header(header::CONTENT_TYPE, content_type)
                .body(Body::from(body))
                .unwrap(),
        )
        .await
        .unwrap()
}

pub async fn json_body(res: Response) -> Value {
    let bytes = res.into_body().collect().await.unwrap().to_bytes();
    serde_json::from_slice(&bytes).unwrap()
}
