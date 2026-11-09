use serde::{Deserialize, Serialize};

/// Day the week starts on: 0 = Sunday ... 6 = Saturday.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "i16", into = "i16")]
pub struct WeekStart(i16);

#[derive(Debug, thiserror::Error)]
#[error("week_start must be between 0 (Sunday) and 6 (Saturday)")]
pub struct InvalidWeekStart;

impl TryFrom<i16> for WeekStart {
    type Error = InvalidWeekStart;

    fn try_from(value: i16) -> Result<Self, Self::Error> {
        if (0..=6).contains(&value) {
            Ok(Self(value))
        } else {
            Err(InvalidWeekStart)
        }
    }
}

impl From<WeekStart> for i16 {
    fn from(value: WeekStart) -> Self {
        value.0
    }
}
