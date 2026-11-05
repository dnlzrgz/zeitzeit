use std::sync::Arc;

use anyhow::Result;
use tokio::net::TcpListener;
use tracing_subscriber::EnvFilter;

use zeitzeit::{config::Config, db, router::build_router, state::AppState};

#[tokio::main]
async fn main() -> Result<()> {
    dotenvy::dotenv().ok();
    tracing_subscriber::fmt()
        .with_env_filter(
            EnvFilter::try_from_default_env().unwrap_or_else(|_| EnvFilter::new("info")),
        )
        .init();

    let config = Arc::new(Config::from_env()?);

    let listener = TcpListener::bind(&config.bind_addr).await?;
    let pool = db::connect(&config).await?;
    db::migrate(&pool).await?;

    let state = AppState { pool, config };
    axum::serve(listener, build_router(state)).await?;

    Ok(())
}
