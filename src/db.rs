use std::{
    str::FromStr,
    time::{Duration, Instant},
};

use anyhow::Result;
use log::LevelFilter;
use sqlx::{
    ConnectOptions, PgPool,
    postgres::{PgConnectOptions, PgPoolOptions},
};

use crate::config::Config;

pub async fn connect(config: &Config) -> Result<PgPool> {
    let started = Instant::now();
    let options = PgConnectOptions::from_str(&config.database_url)?
        .application_name("zeitzeit")
        .options([
            ("statement_timeout", "10000"),                   // 10s per statement
            ("idle_in_transaction_session_timeout", "30000"), // 30s
            ("lock_timeout", "5000"),                         // 5s waiting on locks
            ("timezone", "UTC"),
        ])
        .log_statements(LevelFilter::Debug)
        .log_slow_statements(LevelFilter::Warn, Duration::from_millis(500));

    let pool = PgPoolOptions::new()
        .max_connections(10)
        .min_connections(2)
        .acquire_timeout(Duration::from_secs(2))
        .idle_timeout(Duration::from_secs(10 * 60))
        .max_lifetime(Duration::from_secs(30 * 60))
        .connect_with(options)
        .await?;

    tracing::info!(
        elapsed_ms = started.elapsed().as_millis() as u64,
        max_connections = pool.options().get_max_connections(),
        "database pool ready"
    );
    Ok(pool)
}

pub async fn migrate(pool: &PgPool) -> Result<()> {
    sqlx::migrate!("./migrations").run(pool).await?;
    Ok(())
}
