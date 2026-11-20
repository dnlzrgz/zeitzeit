#![allow(dead_code)]

use std::{
    net::{Ipv4Addr, SocketAddr},
    sync::{
        Arc,
        atomic::{AtomicU32, Ordering},
    },
};

use argon2::{Algorithm, Argon2, Params, PasswordHasher, Version};
use axum::{
    Router,
    body::Body,
    extract::ConnectInfo,
    http::{HeaderName, Method, Request, StatusCode, header, request::Builder},
    response::Response,
};
use http_body_util::BodyExt;
use serde_json::{Value, json};
use sqlx::PgPool;
use tower::ServiceExt;

use zeitzeit::{
    config::{Config, RateLimit},
    router::build_router,
    state::AppState,
};

pub const REGISTER: &str = "/api/v1/auth/register";
pub const LOGIN: &str = "/api/v1/auth/login";
pub const LOGOUT: &str = "/api/v1/auth/logout";

pub const PASSWORD: &str = "correct horse battery";

pub fn test_app(pool: PgPool) -> TestClient {
    let config = Arc::new(Config {
        database_url: String::new(),
        bind_addr: SocketAddr::from(([127, 0, 0, 1], 0)),
        session_ttl_hours: 1,
        request_timeout_secs: 15,
        login: RateLimit {
            interval_secs: 5,
            burst_size: 5,
        },
        register: RateLimit {
            interval_secs: 5,
            burst_size: 5,
        },
    });

    TestClient {
        app: build_router(AppState { pool, config }),
    }
}

pub struct TestClient {
    app: Router,
}

impl TestClient {
    pub fn get(&self, uri: &str) -> TestRequest {
        self.request(Method::GET, uri)
    }

    pub fn post(&self, uri: &str) -> TestRequest {
        self.request(Method::POST, uri)
    }

    fn request(&self, method: Method, uri: &str) -> TestRequest {
        TestRequest {
            app: self.app.clone(),
            // Rate limiter keys
            builder: Request::builder()
                .method(method)
                .uri(uri)
                .extension(next_client()),
            body: Body::empty(),
        }
    }
}

pub struct TestRequest {
    app: Router,
    builder: Builder,
    body: Body,
}

impl TestRequest {
    pub fn header(self, name: HeaderName, value: &str) -> Self {
        Self {
            builder: self.builder.header(name, value),
            ..self
        }
    }

    pub fn bearer(self, token: &str) -> Self {
        self.header(header::AUTHORIZATION, &format!("Bearer {token}"))
    }

    pub fn json(self, body: &Value) -> Self {
        self.raw("application/json", body.to_string())
    }

    /// Arbitrary content type and body.
    pub fn raw(self, content_type: &str, body: String) -> Self {
        Self {
            builder: self.builder.header(header::CONTENT_TYPE, content_type),
            body: Body::from(body),
            ..self
        }
    }

    pub async fn send(self) -> Response {
        self.app
            .oneshot(self.builder.body(self.body).unwrap())
            .await
            .unwrap()
    }
}

pub async fn seed_user(pool: &PgPool, email: &str, password: &str) -> uuid::Uuid {
    let display_name = email.split('@').next().unwrap_or(email);
    sqlx::query_scalar(
        "INSERT INTO users (email, display_name, password_hash)
        VALUES ($1, $2, $3) RETURNING id",
    )
    .bind(email)
    .bind(display_name)
    .bind(fixture_hash(password))
    .fetch_one(pool)
    .await
    .unwrap()
}

fn fixture_hash(password: &str) -> String {
    let params = Params::new(
        Params::MIN_M_COST,
        Params::MIN_T_COST,
        Params::MIN_P_COST,
        None,
    )
    .expect("minimum params are valid");

    Argon2::new(Algorithm::Argon2id, Version::V0x13, params)
        .hash_password_with_salt(password.as_bytes(), b"fixture-salt")
        .expect("hashing a fixture cannot fail")
        .to_string()
}

/// Logs in through the real endpoint and returns session token.
pub async fn login(app: &TestClient, email: &str, password: &str) -> String {
    let res = app
        .post(LOGIN)
        .json(&json!({ "email": email, "password": password }))
        .send()
        .await;

    assert_eq!(res.status(), StatusCode::OK);
    json_body(res).await["token"].as_str().unwrap().to_owned()
}

pub async fn json_body(res: Response) -> Value {
    let bytes = res.into_body().collect().await.unwrap().to_bytes();
    serde_json::from_slice(&bytes).unwrap()
}

/// Asserts the response is an RFC 9457 problem document with a non-empty detail.
pub async fn assert_problem(res: Response, expected: StatusCode, context: &str) -> Value {
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

fn next_client() -> ConnectInfo<SocketAddr> {
    static NEXT: AtomicU32 = AtomicU32::new(0);
    let n = NEXT.fetch_add(1, Ordering::Relaxed);
    ConnectInfo(SocketAddr::from((
        Ipv4Addr::new(127, 0, 0, (n % 254 + 1) as u8),
        0,
    )))
}
