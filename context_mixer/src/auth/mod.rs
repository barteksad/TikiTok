use std::{collections::HashMap, fs};

use jsonwebtoken::{decode, decode_header, Algorithm, DecodingKey, Validation};
use once_cell::sync::Lazy;

use crate::server::Claims;

static GOOGLE_PUBLIC_KEYS_PATH: &str = "/home/bartek/UW/JNP3/project/context_mixer/src/auth/keys.json";

static KEYS: Lazy<Keys> = Lazy::new(init_keys);

pub fn authorize(token: &str) -> Result<Claims, AuthError> {
    let kid = parse_header(token)?;
    let decode_key = KEYS.match_kid(&kid)?;

    let mut val = Validation::new(Algorithm::RS256);
    val.set_audience(&vec![String::from("jnp-auth")]);

    decode::<Claims>(token, decode_key, &val)
        .map_err(|e| AuthError::ParseToken(e.to_string()))
        .map(|token_data| Ok(token_data.claims))?
}

fn parse_header(token: &str) -> Result<String, AuthError> {
    decode_header(token)
        .map(|header| header.kid)
        .map(Option::unwrap)
        .map(Ok)
        .map_err(|e| AuthError::ParseHeader(e.to_string()))?
}

fn init_keys() -> Keys {
    let s = fs::read_to_string(GOOGLE_PUBLIC_KEYS_PATH).unwrap();
    let mut google_public_keys_pem : HashMap<String, String> = serde_json::from_str(&s).unwrap();
    let google_public_keys = google_public_keys_pem
        .drain()
        .map(|(k, v)| {
            (k, DecodingKey::from_rsa_pem(v.as_bytes()).unwrap())
        })
        .collect();
    Keys { google_public_keys }
}

struct Keys {
    google_public_keys: HashMap<String, DecodingKey>,
}

impl Keys {
    fn match_kid(&self, kid: &str) -> Result<&DecodingKey, AuthError> {
        match self.google_public_keys.get(kid) {
            Some(public_key) => Ok(public_key),
            None => Err(AuthError::UnknownKid),
        }
    }
}

#[derive(Debug)]
pub enum AuthError {
    InvalidToken,
    ParseHeader(String),
    ParseToken(String),
    UnknownKid,
}

#[cfg(test)]
mod tests {
    use super::{authorize, AuthError};

    #[test]
    fn token_valid_but_expired() {
        let idtoken = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImFmZjFlNDJlNDE0M2I4MTQxM2VjMTI1MzQwOTcwODUxZThiNDdiM2YiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vam5wLWF1dGgiLCJhdWQiOiJqbnAtYXV0aCIsImF1dGhfdGltZSI6MTY3MTI4NjI0OCwidXNlcl9pZCI6IjAzSFlWNEptOHlWSlBpMHFnZXBNTHNjdkpWeTEiLCJzdWIiOiIwM0hZVjRKbTh5VkpQaTBxZ2VwTUxzY3ZKVnkxIiwiaWF0IjoxNjcxMzc5MDc1LCJleHAiOjE2NzEzODI2NzUsImVtYWlsIjoiZHNhQGRzLndwLnBsIiwiZW1haWxfdmVyaWZpZWQiOmZhbHNlLCJmaXJlYmFzZSI6eyJpZGVudGl0aWVzIjp7ImVtYWlsIjpbImRzYUBkcy53cC5wbCJdfSwic2lnbl9pbl9wcm92aWRlciI6InBhc3N3b3JkIn19.NLTHTrBkEPuIvswPZp-xDJUM-UCfNiYs1k51jitLyMgebP0kiQL34wntbSL8J3Plp3V3AnGnJRR4oQJZlTYblGTNug4S24moISDHvExQRN140hxOLPdOdpLAwHMNzkP5s5YQGdIeeQ-V_sp_KXxCnvlhLpCfhXcZgW6-49-FZk4rEwWaY-DdwbVObSJQMQYGTMinK6jmSbgHDzGgU7Fp5BMhKZuWdZxoDbiQtMDJSlB5sYSrsHsAwM4aljQey1r35AquFanaTRRjtyrrmfmMrZ_yC2CDBI0ekG6FAyy1477SGIvgHFjDZYy-5_qrx4kTWBEdoXLJCh_qytKr25qASQ";
        let err = authorize(idtoken);
        match err {
            Err(AuthError::ParseToken(s)) => {
                assert_eq!(s, "ExpiredSignature".to_string());
            },
            _ => panic!("Expected ExpiredSignature error"),
        };
    }
}