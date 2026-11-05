use anyhow::{Result, anyhow};
use config::ConfigError;
use serde::Deserialize;

#[derive(Clone, Deserialize)]
pub struct Config {
    pub database_url: String,
    #[serde(default = "default_bind_addr")]
    pub bind_addr: String,
    #[serde(default = "default_session_ttl_hours")]
    pub session_ttl_hours: u64,
}

fn default_bind_addr() -> String {
    "127.0.0.1:8080".to_owned()
}

fn default_session_ttl_hours() -> u64 {
    720
}

impl Config {
    pub fn from_env() -> Result<Self> {
        let parsed = config::Config::builder()
            .add_source(config::Environment::default())
            .build()
            .and_then(|config| config.try_deserialize::<Self>());

        parsed.map_err(|err| anyhow!("invalid configuration: {}", safe_reason(&err)))
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
