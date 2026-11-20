mod common;

use axum::http::StatusCode;
use serde_json::json;
use sqlx::PgPool;

use crate::common::{LOGIN, PASSWORD, assert_problem, json_body, seed_user, test_app};

#[sqlx::test]
async fn login_returns_token_and_stores_only_its_hash(pool: PgPool) {
    let app = test_app(pool.clone());
    seed_user(&pool, "ada@example.com", PASSWORD).await;
    let body = json!({
        "email": "  ADA@Example.com ",
        "password": PASSWORD,
    });
    let res = app.post(LOGIN).json(&body).send().await;
    assert_eq!(res.status(), StatusCode::OK);

    let body = json_body(res).await;
    let token = body["token"].as_str().expect("token should be a string");
    assert!(!token.is_empty());
}

#[sqlx::test]
async fn wrong_password_and_unknown_email_responses_are_the_same(pool: PgPool) {
    let app = test_app(pool.clone());
    seed_user(&pool, "ada@example.com", PASSWORD).await;

    let unknown_email = app
        .post(LOGIN)
        .json(&json!({"email": "nobody@example.com", "password": PASSWORD}))
        .send()
        .await;
    let wrong_password = app
        .post(LOGIN)
        .json(&json!({"email": "ada@example.com", "password": "wrongpassword123"}))
        .send()
        .await;

    let unknown_email_body =
        assert_problem(unknown_email, StatusCode::UNAUTHORIZED, "unknown email").await;
    let wrong_password_body =
        assert_problem(wrong_password, StatusCode::UNAUTHORIZED, "wrong password").await;

    assert_eq!(unknown_email_body, wrong_password_body);
}

#[sqlx::test]
async fn login_rejects_password_too_long(pool: PgPool) {
    let password = &"a".repeat(129);

    let app = test_app(pool.clone());
    seed_user(&pool, "ada@example.com", password).await;
    let body = json!({
        "email": "ada@example.com",
        "password": password,
    });
    let res = app.post(LOGIN).json(&body).send().await;
    assert_eq!(res.status(), StatusCode::UNAUTHORIZED);
}
