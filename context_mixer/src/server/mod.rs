
use std::{net::SocketAddr, sync::Arc};

use axum::{
    async_trait,
    extract::{FromRequestParts, TypedHeader, self},
    headers::{authorization::Bearer, Authorization},
    http::{request::Parts, StatusCode},
    response::{IntoResponse, Response},
    routing::get,
    Json, RequestPartsExt, Router,
};
use axum_macros::debug_handler;
use dotenv::dotenv;
use reqwest::header::AUTHORIZATION;
use serde::{Serialize, Deserialize};
use serde_json::json;
use tower_http::cors::CorsLayer;
use axum::http::Method;

use crate::{auth::{AuthError, authorize}, video::{VideosError, Videos, get_videos, Strategy, StrategyMostLikedWithOthers}};

#[derive(Debug, Serialize, Deserialize)]
pub struct Claims {
    pub user_id: String,
}

pub async fn run_server() {
    dotenv().ok();

    let addr: SocketAddr = SocketAddr::from(([0, 0, 0, 0], 3001));

    let cors = CorsLayer::new()
        .allow_methods([Method::GET, Method::POST])
        .allow_origin([std::env::var("DOMAIN").expect("DOMAIN must be set.").parse().unwrap()])
        .allow_headers([AUTHORIZATION]);

    let app = Router::new()
        .route("/content/:n_part", get(content))
        .layer(cors);

    tracing::debug!("listening on {}", addr);

    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .unwrap();
}

#[debug_handler]
async fn content(extract::Path(batch_idx): extract::Path<usize>, claims: Claims) -> Result<Json<Videos>, VideosError> {
    tracing::debug!("batch_idx: {}", batch_idx);
    // let strategy: Arc<dyn Strategy> = Arc::new(StrategyLatest { n_latest: 1 });
    // let strategy: Arc<dyn Strategy> = Arc::new(StrategyConstant);
    let strategy: Arc<dyn Strategy> = Arc::new(StrategyMostLikedWithOthers::new());
    let videos = get_videos(&claims, strategy, batch_idx).await?;
    // let videos2 = Videos { ids: videos.ids.iter().cycle().take(n_part).cloned().collect() };
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