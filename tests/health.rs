mod common;

use axum::http::StatusCode;
use sqlx::PgPool;

#[sqlx::test]
async fn responses_have_request_id(pool: PgPool) {
    let app = common::test_app(pool);
    let res = app.get("/healthz").send().await;

    assert!(res.headers().contains_key("x-request-id"));
}

#[sqlx::test]
async fn healthz_returns_200(pool: PgPool) {
    let app = common::test_app(pool);
    let res = app.get("/healthz").send().await;

    assert_eq!(res.status(), StatusCode::OK);
}

#[sqlx::test]
async fn readyz_returns_200(pool: PgPool) {
    let app = common::test_app(pool);
    let res = app.get("/readyz").send().await;

    assert_eq!(res.status(), StatusCode::OK);
}

#[sqlx::test]
async fn readyz_returns_503_when_db_is_down(pool: PgPool) {
    pool.close().await;

    let app = common::test_app(pool);
    let res = app.get("/readyz").send().await;

    assert_eq!(res.status(), StatusCode::SERVICE_UNAVAILABLE);
}
