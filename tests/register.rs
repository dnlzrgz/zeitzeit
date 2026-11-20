mod common;

use axum::http::{StatusCode, header};
use serde_json::{Value, json};
use sqlx::PgPool;

use common::{PASSWORD, REGISTER, assert_problem, json_body, test_app};

fn valid_body() -> Value {
    json!({
        "email": "ada@example.com",
        "display_name": "Ada",
        "password": PASSWORD
    })
}

async fn user_count(pool: &PgPool) -> i64 {
    sqlx::query_scalar("SELECT count(*) FROM users")
        .fetch_one(pool)
        .await
        .unwrap()
}

#[sqlx::test]
async fn register_creates_user_and_hides_secrets(pool: PgPool) {
    let app = test_app(pool.clone());
    let res = app
        .post(REGISTER)
        .json(&json!({
            "email": "  Ada@Example.COM ",
            "display_name": "  Ada Lovelace  ",
            "password": PASSWORD
        }))
        .send()
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
    assert!(!stored.contains(PASSWORD));
}

#[sqlx::test]
async fn register_accepts_custom_timezone(pool: PgPool) {
    let app = test_app(pool);
    let mut body = valid_body();
    body["timezone"] = json!("Europe/Madrid");

    let res = app.post(REGISTER).json(&body).send().await;

    assert_eq!(res.status(), StatusCode::CREATED);
    assert_eq!(json_body(res).await["timezone"], "Europe/Madrid");
}

#[sqlx::test]
async fn duplicate_email_is_a_conflict_even_with_different_case(pool: PgPool) {
    let app = test_app(pool.clone());
    let first = app.post(REGISTER).json(&valid_body()).send().await;
    assert_eq!(first.status(), StatusCode::CREATED);

    let mut second_body = valid_body();
    second_body["email"] = json!(" ADA@example.com ");
    let second = app.post(REGISTER).json(&second_body).send().await;
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
            json!({ "email": "not-an-email", "display_name": "Ada", "password": PASSWORD }),
        ),
        (
            "empty email",
            json!({ "email": "", "display_name": "Ada", "password": PASSWORD }),
        ),
        (
            "empty display name",
            json!({ "email": "a@example.com", "display_name": "", "password": PASSWORD }),
        ),
        (
            "blank display name",
            json!({ "email": "a@example.com", "display_name": "    ", "password": PASSWORD }),
        ),
        (
            "display name too long",
            json!({ "email": "a@example.com", "display_name": "a".repeat(255), "password": PASSWORD }),
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
            json!({ "email": "a@example.com", "display_name": "Ada", "password": PASSWORD, "timezone": "Mars/Olympus_Mons" }),
        ),
        (
            "missing email",
            json!({ "display_name": "Ada", "password": PASSWORD }),
        ),
        (
            "missing password",
            json!({ "email": "a@example.com", "display_name": "Ada" }),
        ),
        (
            "wrong type",
            json!({ "email": 42, "display_name": "Ada", "password": PASSWORD }),
        ),
        (
            "unknown field (typo)",
            json!({ "email": "a@example.com", "display_name": "Ada", "password": PASSWORD, "timzone": "Europe/Madrid" }),
        ),
    ];

    for (name, body) in cases {
        let res = app.post(REGISTER).json(&body).send().await;
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

        let res = app.post(REGISTER).json(&body).send().await;
        assert_eq!(res.status(), StatusCode::CREATED, "length {len}");
    }
}

#[sqlx::test]
async fn malformed_json_is_client_error(pool: PgPool) {
    let app = test_app(pool.clone());
    let res = app
        .post(REGISTER)
        .raw("application/json", "{ not json".to_owned())
        .send()
        .await;

    assert_problem(res, StatusCode::BAD_REQUEST, "malformed json").await;
    assert_eq!(user_count(&pool).await, 0);
}

#[sqlx::test]
async fn wrong_content_type_is_rejected(pool: PgPool) {
    let app = test_app(pool);
    let res = app
        .post(REGISTER)
        .raw("text/plain", valid_body().to_string())
        .send()
        .await;

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
        "password": PASSWORD
    });

    let res = app.post(REGISTER).json(&body).send().await;

    assert_problem(res, StatusCode::PAYLOAD_TOO_LARGE, "oversized payload").await;
    assert_eq!(user_count(&pool).await, 0);
}
