use anyhow::anyhow;
use base64::{Engine, engine::general_purpose::URL_SAFE_NO_PAD};
use sha2::{Digest, Sha256};

use crate::error::AppError;

const TOKEN_BYTES: usize = 32;

pub struct NewToken {
    /// Sent to the client once, never stored.
    pub plaintext: String,
    /// Stored in `auth_tokens.token_hash`
    pub hash: [u8; 32],
}

pub fn generate() -> Result<NewToken, AppError> {
    let mut bytes = [0u8; TOKEN_BYTES];
    getrandom::fill(&mut bytes).map_err(|err| anyhow!("OS randomness unavailable: {err}"))?;

    let plaintext = URL_SAFE_NO_PAD.encode(bytes);
    let hash = token_hash(&plaintext);

    Ok(NewToken { plaintext, hash })
}

/// Hashes the token string exactly as the client sends it back so the extractor
/// never has to decode base64.
pub fn token_hash(token: &str) -> [u8; 32] {
    Sha256::digest(token.as_bytes()).into()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn token_is_43_url_safe_chars() {
        let token = generate().unwrap().plaintext;
        assert_eq!(token.len(), 43); // 32 bytes, base64, no padding
        assert!(
            token
                .chars()
                .all(|c| c.is_ascii_alphanumeric() || c == '-' || c == '_')
        );
    }

    #[test]
    fn tokens_are_unique() {
        assert_ne!(generate().unwrap().plaintext, generate().unwrap().plaintext);
    }
}
