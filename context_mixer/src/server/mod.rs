
use std::net::SocketAddr;

use axum::{
    async_trait,
    extract::{FromRequestParts, TypedHeader},
    headers::{authorization::Bearer, Authorization},
    http::{request::Parts, StatusCode},
    response::{IntoResponse, Response},
    routing::get,
    Json, RequestPartsExt, Router,
};
use dotenv::dotenv;
use reqwest::header::AUTHORIZATION;
use serde::{Serialize, Deserialize};
use serde_json::json;
use tower_http::cors::CorsLayer;
use axum::http::Method;

use crate::{auth::{AuthError, authorize}, video::{get_videos, VideosError, Videos}};

#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    user_id: String,
}

pub async fn run_server() {
    dotenv().ok();

    let addr: SocketAddr = SocketAddr::from(([0, 0, 0, 0], 3001));

    // let cors = CorsLayer::new()
    //     .allow_methods(Any)
    //     .allow_origin(Any)
    //     .allow_headers(Any);
    let cors = CorsLayer::new()
        .allow_methods([Method::GET, Method::POST])
        .allow_origin([std::env::var("DOMAIN").expect("DOMAIN must be set.").parse().unwrap()])
        .allow_headers([AUTHORIZATION]);

    let app = Router::new()
        .route("/content", get(content))
        .layer(cors);

    tracing::debug!("listening on {}", addr);

    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .unwrap();
}

async fn content(claims: Claims) -> Result<Json<Videos>, VideosError> {
    let videos = get_videos(claims).await?;

    Ok(Json(videos))
}

#[async_trait]
impl<S> FromRequestParts<S> for Claims
where
    S: Send + Sync
{
    type Rejection = AuthError;

    async fn from_request_parts(parts: &mut Parts, _state: &S) -> Result<Self, Self::Rejection> {
        let TypedHeader(Authorization(bearer)) = parts
            .extract::<TypedHeader<Authorization<Bearer>>>()
            .await
            .map_err(|_| AuthError::InvalidToken)?;
        
        authorize(bearer.token()).await
    }
}

impl IntoResponse for AuthError {
    fn into_response(self) -> Response {
        let (status, error_message) = match self {
            AuthError::InvalidToken => (StatusCode::BAD_REQUEST, "Invalid token"),
            AuthError::ParseHeader(_) => (StatusCode::BAD_REQUEST, "Invalid token"),
            AuthError::ParseToken(_) => (StatusCode::BAD_REQUEST, "Invalid token"),
            AuthError::UnknownKid => (StatusCode::BAD_REQUEST, "Invalid token"),
        };
        let body = Json(json!({
            "error": error_message,
        }));
        (status, body).into_response()
    }
}

impl IntoResponse for VideosError {
    fn into_response(self) -> Response {
        let body = Json(json!({
            "error": "Internal server error",
        }));
        (StatusCode::INTERNAL_SERVER_ERROR, body).into_response()
    }
}