mod common;

use axum::http::{StatusCode, header};
use sqlx::PgPool;

use common::{LOGOUT, PASSWORD, assert_problem, login, seed_user, test_app};

#[sqlx::test]
async fn logout_revokes_token(pool: PgPool) {
    let app = test_app(pool.clone());
    seed_user(&pool, "ada@example.com", PASSWORD).await;
    let token = login(&app, "ada@example.com", PASSWORD).await;

    let first = app.post(LOGOUT).bearer(&token).send().await;
    assert_eq!(first.status(), StatusCode::NO_CONTENT);

    let second = app.post(LOGOUT).bearer(&token).send().await;
    assert_eq!(second.status(), StatusCode::UNAUTHORIZED);
}

#[sqlx::test]
async fn logout_only_revokes_the_session_it_was_called_with(pool: PgPool) {
    let app = test_app(pool.clone());
    seed_user(&pool, "ada@example.com", PASSWORD).await;
    let token_a = login(&app, "ada@example.com", PASSWORD).await;
    let token_b = login(&app, "ada@example.com", PASSWORD).await;
    assert_ne!(token_a, token_b);

    let res = app.post(LOGOUT).bearer(&token_a).send().await;
    assert_eq!(res.status(), StatusCode::NO_CONTENT);

    // The other session is still valid.
    let res = app.post(LOGOUT).bearer(&token_b).send().await;
    assert_eq!(res.status(), StatusCode::NO_CONTENT);
}

#[sqlx::test]
async fn logout_without_valid_credentials_is_unauthorized(pool: PgPool) {
    let app = test_app(pool);

    let cases = [
        ("no header", None),
        ("unknown token", Some("Bearer not-a-real-token")),
        ("wrong scheme", Some("Basic abc")),
    ];

    for (name, authorization) in cases {
        let mut req = app.post(LOGOUT);
        if let Some(value) = authorization {
            req = req.header(header::AUTHORIZATION, value);
        }

        assert_problem(req.send().await, StatusCode::UNAUTHORIZED, name).await;
    }
}

#[sqlx::test]
async fn logout_with_expired_token_is_unauthorized(pool: PgPool) {
    let app = test_app(pool.clone());
    seed_user(&pool, "ada@example.com", PASSWORD).await;
    let token = login(&app, "ada@example.com", PASSWORD).await;

    // Table requires expires_at > created_at.
    sqlx::query(
        "UPDATE auth_tokens
            SET created_at = now() - interval '2 hours',
                expires_at = now() - interval '1 hour'",
    )
    .execute(&pool)
    .await
    .unwrap();

    let res = app.post(LOGOUT).bearer(&token).send().await;
    assert_eq!(res.status(), StatusCode::UNAUTHORIZED);
}
