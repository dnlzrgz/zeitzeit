mod common;

use axum::{
    body::Body,
    http::{Request, StatusCode},
};
use sqlx::PgPool;
use tower::ServiceExt;

#[sqlx::test]
async fn responses_have_request_id(pool: PgPool) {
    let app = common::test_app(pool);
    let res = app
        .oneshot(Request::get("/healthz").body(Body::empty()).unwrap())
        .await
        .unwrap();

    assert!(res.headers().contains_key("x-request-id"));
}

#[sqlx::test]
async fn healthz_returns_200(pool: PgPool) {
    let app = common::test_app(pool);
    let res = app
        .oneshot(Request::get("/healthz").body(Body::empty()).unwrap())
        .await
        .unwrap();

    assert_eq!(res.status(), StatusCode::OK);
}

#[sqlx::test]
async fn readyz_returns_200(pool: PgPool) {
    let app = common::test_app(pool);
    let res = app
        .oneshot(Request::get("/readyz").body(Body::empty()).unwrap())
        .await
        .unwrap();

    assert_eq!(res.status(), StatusCode::OK);
}

#[sqlx::test]
async fn readyz_returns_503_when_db_is_down(pool: PgPool) {
    pool.close().await;

    let app = common::test_app(pool);
    let res = app
        .oneshot(Request::get("/readyz").body(Body::empty()).unwrap())
        .await
        .unwrap();

    assert_eq!(res.status(), StatusCode::SERVICE_UNAVAILABLE);
}
