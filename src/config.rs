use std::net::SocketAddr;

use anyhow::{Result, anyhow, ensure};
use config::ConfigError;
use serde::Deserialize;

#[derive(Clone, Deserialize)]
pub struct RateLimit {
    pub interval_secs: u64,
    pub burst_size: u32,
}

impl RateLimit {
    const fn new(interval_secs: u64, burst_size: u32) -> Self {
        Self {
            interval_secs,
            burst_size,
        }
    }

    fn validate(&self, name: &str) -> Result<()> {
        ensure!(self.interval_secs > 0, "{name}: interval_secs must be > 0");
        ensure!(self.burst_size > 0, "{name}: burst_size must be > 0");
        Ok(())
    }
}

fn default_login() -> RateLimit {
    RateLimit::new(10, 5)
}

fn default_register() -> RateLimit {
    RateLimit::new(60, 3)
}

#[derive(Clone, Deserialize)]
pub struct Config {
    pub database_url: String,
    #[serde(default = "default_bind_addr")]
    pub bind_addr: SocketAddr,
    #[serde(default = "default_session_ttl_hours")]
    pub session_ttl_hours: u64,
    #[serde(default = "default_request_timeout_secs")]
    pub request_timeout_secs: u64,
    #[serde(default = "default_max_body_bytes")]
    pub max_body_bytes: usize,
    #[serde(default = "default_login")]
    pub login: RateLimit,
    #[serde(default = "default_register")]
    pub register: RateLimit,
}

fn default_bind_addr() -> SocketAddr {
    ([127, 0, 0, 1], 8080).into()
}

fn default_session_ttl_hours() -> u64 {
    720
}

fn default_request_timeout_secs() -> u64 {
    15
}

const fn default_max_body_bytes() -> usize {
    64 * 1024
}

impl Config {
    pub fn from_env() -> Result<Self> {
        let cfg = config::Config::builder()
            .add_source(config::Environment::default().separator("__"))
            .build()
            .and_then(|config| config.try_deserialize::<Self>())
            .map_err(|err| anyhow!("invalid configuration: {}", safe_reason(&err)))?;

        ensure!(cfg.max_body_bytes > 0, "max_body_bytes must be > 0");
        cfg.login.validate("login")?;
        cfg.register.validate("register")?;
        Ok(cfg)
    }
}

/// Avoids leaking a DATABASE_URL with the password in it.
fn safe_reason(err: &ConfigError) -> String {
    match err {
        ConfigError::Type { key, expected, .. } => format!(
            "invalid value for `{}`, expected {expected}",
            key.as_deref().unwrap_or("an environment variable")
        ),
        ConfigError::NotFound(key) => format!("missing `{key}`"),
        _ => "check the environment variables".to_owned(),
    }
}
