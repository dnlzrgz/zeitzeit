use std::time::Duration;

use anyhow::anyhow;
use axum::{
    Router,
    extract::DefaultBodyLimit,
    http::{HeaderValue, header},
    response::{IntoResponse, Response},
    routing::post,
};
use tower_governor::{GovernorError, GovernorLayer, governor::GovernorConfigBuilder};
use tower_http::set_header::SetResponseHeaderLayer;

use crate::{config::Config, error::AppError, state::AppState};

pub mod extractor;
mod handlers;
pub mod password;
mod repo;
pub mod tokens;

pub fn routes(config: &Config) -> Router<AppState> {
    let login_limit = GovernorConfigBuilder::default()
        .const_per_second(config.login.interval_secs)
        .const_burst_size(config.login.burst_size)
        .finish()
        .expect("login rate limit config is valid");

    let register_limit = GovernorConfigBuilder::default()
        .const_per_second(config.register.interval_secs)
        .const_burst_size(config.register.burst_size)
        .finish()
        .expect("register rate limit config is valid");

    let login_limiter = login_limit.limiter().clone();
    let register_limiter = register_limit.limiter().clone();
    tokio::spawn(async move {
        let mut tick = tokio::time::interval(Duration::from_secs(60));
        loop {
            tick.tick().await;
            login_limiter.retain_recent();
            register_limiter.retain_recent();
        }
    });

    Router::new()
        .route(
            "/register",
            post(handlers::register)
                .route_layer(GovernorLayer::new(register_limit).error_handler(rate_limited)),
        )
        .route(
            "/login",
            post(handlers::login)
                .route_layer(GovernorLayer::new(login_limit).error_handler(rate_limited)),
        )
        .route("/logout", post(handlers::logout))
        .layer(DefaultBodyLimit::max(64 * 1024)) // Cap body size
        .layer(SetResponseHeaderLayer::overriding(
            header::CACHE_CONTROL,
            HeaderValue::from_static("no-store"),
        ))
}

fn rate_limited(err: GovernorError) -> Response {
    match err {
        GovernorError::TooManyRequests { wait_time, .. } => {
            let mut resp = AppError::TooManyRequests.into_response();
            resp.headers_mut()
                .insert(header::RETRY_AFTER, HeaderValue::from(wait_time.max(1))); // TODO: review later

            resp
        }
        other => AppError::Internal(anyhow!("rate limiter: {other}")).into_response(),
    }
}
