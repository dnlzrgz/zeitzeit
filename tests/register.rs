mod common;

use axum::{
    http::{StatusCode, header},
    response::Response,
};
use serde_json::{Value, json};
use sqlx::PgPool;

use common::{json_body, post_json, post_raw, test_app};

const REGISTER: &str = "/api/v1/auth/register";

fn valid_body() -> Value {
    json!({
        "email": "ada@example.com",
        "display_name": "Ada",
        "password": "correct horse battery"
    })
}

async fn user_count(pool: &PgPool) -> i64 {
    sqlx::query_scalar("SELECT count(*) FROM users")
        .fetch_one(pool)
        .await
        .unwrap()
}

/// Asserts the response is an RFC 9457 problem document with a non-empty detail.
async fn assert_problem(res: Response, expected: StatusCode, context: &str) -> Value {
    assert_eq!(res.status(), expected, "{context}: wrong status");
    assert_eq!(
        res.headers()[header::CONTENT_TYPE],
        "application/problem+json",
        "{context}: wrong content type"
    );

    let body = json_body(res).await;
    assert!(
        body["detail"]
            .as_str()
            .is_some_and(|detail| !detail.is_empty()),
        "{context}: missing detail in {body}"
    );

    body
}

#[sqlx::test]
async fn register_creates_user_and_hides_secrets(pool: PgPool) {
    let app = test_app(pool.clone());
    let res = post_json(
        &app,
        REGISTER,
        &json!({
            "email": "  Ada@Example.COM ",
            "display_name": "  Ada Lovelace  ",
            "password": "correct horse battery"
        }),
    )
    .await;

    assert_eq!(res.status(), StatusCode::CREATED);
    let body = json_body(res).await;

    // Normalized input.
    assert_eq!(body["email"], "ada@example.com");
    assert_eq!(body["display_name"], "Ada Lovelace");
    assert_eq!(body["timezone"], "UTC");
    assert_eq!(body["week_start"], 1);
    assert!(body["id"].is_string());
    assert!(body["created_at"].is_string());

    // Nothing sensitive in the response.
    assert!(body.get("password").is_none());
    assert!(body.get("password_hash").is_none());

    let stored: String = sqlx::query_scalar("SELECT password_hash FROM users")
        .fetch_one(&pool)
        .await
        .unwrap();

    assert!(
        stored.starts_with("$argon2id$"),
        "unexpected hash: {stored}"
    );
    assert!(!stored.contains("correct horse battery"));
}

#[sqlx::test]
async fn register_accepts_custom_timezone(pool: PgPool) {
    let app = test_app(pool);
    let mut body = valid_body();
    body["timezone"] = json!("Europe/Madrid");

    let res = post_json(&app, REGISTER, &body).await;

    assert_eq!(res.status(), StatusCode::CREATED);
    assert_eq!(json_body(res).await["timezone"], "Europe/Madrid");
}

#[sqlx::test]
async fn duplicate_email_is_a_conflict_even_with_different_case(pool: PgPool) {
    let app = test_app(pool.clone());
    let first = post_json(&app, REGISTER, &valid_body()).await;
    assert_eq!(first.status(), StatusCode::CREATED);

    let mut second_body = valid_body();
    second_body["email"] = json!(" ADA@example.com ");
    let second = post_json(&app, REGISTER, &second_body).await;
    assert_eq!(second.status(), StatusCode::CONFLICT);
    assert_eq!(
        second.headers()[header::CONTENT_TYPE],
        "application/problem+json"
    );

    let problem = json_body(second).await;
    assert_eq!(problem["status"], 409);
    assert_eq!(user_count(&pool).await, 1);
}

#[sqlx::test]
async fn invalid_payloads_are_rejected_and_nothing_is_stored(pool: PgPool) {
    let app = test_app(pool.clone());

    let cases: Vec<(&str, Value)> = vec![
        (
            "invalid email",
            json!({ "email": "not-an-email", "display_name": "Ada", "password": "correct horse battery" }),
        ),
        (
            "empty email",
            json!({ "email": "", "display_name": "Ada", "password": "correct horse battery" }),
        ),
        (
            "empty display name",
            json!({ "email": "a@example.com", "display_name": "", "password": "correct horse battery" }),
        ),
        (
            "blank display name",
            json!({ "email": "a@example.com", "display_name": "    ", "password": "correct horse battery" }),
        ),
        (
            "display name too long",
            json!({ "email": "a@example.com", "display_name": "a".repeat(255), "password": "correct horse battery" }),
        ),
        (
            "password too short",
            json!({ "email": "a@example.com", "display_name": "Ada", "password": "short" }),
        ),
        (
            "password too long",
            json!({ "email": "a@example.com", "display_name": "Ada", "password": "p".repeat(129) }),
        ),
        (
            "unknown timezone",
            json!({ "email": "a@example.com", "display_name": "Ada", "password": "correct horse battery", "timezone": "Mars/Olympus_Mons" }),
        ),
        (
            "missing email",
            json!({ "display_name": "Ada", "password": "correct horse battery" }),
        ),
        (
            "missing password",
            json!({ "email": "a@example.com", "display_name": "Ada" }),
        ),
        (
            "wrong type",
            json!({ "email": 42, "display_name": "Ada", "password": "correct horse battery" }),
        ),
        (
            "unknown field (typo)",
            json!({ "email": "a@example.com", "display_name": "Ada", "password": "correct horse battery", "timzone": "Europe/Madrid" }),
        ),
    ];

    for (name, body) in cases {
        let res = post_json(&app, REGISTER, &body).await;
        assert_problem(res, StatusCode::UNPROCESSABLE_ENTITY, name).await;
    }

    assert_eq!(user_count(&pool).await, 0);
}

#[sqlx::test]
async fn password_with_max_length_is_accepted(pool: PgPool) {
    let app = test_app(pool);

    for (i, len) in [10usize, 128].into_iter().enumerate() {
        let body = json!({
            "email": format!("user{i}@example.com"),
            "display_name": "Ada",
            "password": "p".repeat(len)
        });

        let res = post_json(&app, REGISTER, &body).await;
        assert_eq!(res.status(), StatusCode::CREATED, "length {len}");
    }
}

#[sqlx::test]
async fn malformed_json_is_client_error(pool: PgPool) {
    let app = test_app(pool.clone());
    let res = post_raw(&app, REGISTER, "application/json", "{ not json".to_owned()).await;

    assert_problem(res, StatusCode::BAD_REQUEST, "malformed json").await;
    assert_eq!(user_count(&pool).await, 0);
}

#[sqlx::test]
async fn wrong_content_type_is_rejected(pool: PgPool) {
    let app = test_app(pool);
    let res = post_raw(&app, REGISTER, "text/plain", valid_body().to_string()).await;

    assert_problem(
        res,
        StatusCode::UNSUPPORTED_MEDIA_TYPE,
        "wrong content type",
    )
    .await;
}

#[sqlx::test]
async fn oversized_payload_is_rejected_before_parsing(pool: PgPool) {
    let app = test_app(pool.clone());
    let body = json!({
        "email": "ada@example.com",
        "display_name": "a".repeat(1024 * 1024),
        "password": "correct horse battery"
    });

    let res = post_json(&app, REGISTER, &body).await;

    assert_problem(res, StatusCode::PAYLOAD_TOO_LARGE, "oversized payload").await;
    assert_eq!(user_count(&pool).await, 0);
}
