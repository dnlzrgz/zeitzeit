pub mod repo;
pub mod week_start;

use chrono::{DateTime, Utc};
use serde::Serialize;
use uuid::Uuid;

pub use week_start::WeekStart;

#[derive(sqlx::FromRow)]
pub struct User {
    pub id: Uuid,
    pub email: String,
    pub display_name: String,
    pub password_hash: String,
    pub timezone: String,
    #[sqlx(try_from = "i16")]
    pub week_start: WeekStart,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Serialize)]
pub struct UserResponse {
    pub id: Uuid,
    pub email: String,
    pub display_name: String,
    pub timezone: String,
    pub week_start: WeekStart,
    pub created_at: DateTime<Utc>,
}

impl From<User> for UserResponse {
    fn from(u: User) -> Self {
        Self {
            id: u.id,
            email: u.email,
            display_name: u.display_name,
            timezone: u.timezone,
            week_start: u.week_start,
            created_at: u.created_at,
        }
    }
}
