use std::{env, str::FromStr, sync::Arc};

use axum::async_trait;
use serde::{Deserialize, Serialize};
use tokio_postgres::Config;
use uuid::Uuid;

use crate::server::Claims;

#[async_trait]
pub trait Strategy: Send + Sync {
    async fn get_videos(
        &self,
        claims: &Claims,
        client: tokio_postgres::Client,
    ) -> Result<Videos, VideosError>;
}

pub async fn get_videos(claims: &Claims, strategy: Arc<dyn Strategy>) -> Result<Videos, VideosError> {
    let client = connect_to_db().await;
    strategy.get_videos(claims, client).await
}

pub struct StrategyConstant;

pub struct StrategyLatest {
    pub n_latest: i64,
}
#[derive(Debug, Serialize, Deserialize)]
pub struct Videos {
    ids: Vec<Uuid>,
}

#[derive(Debug, Clone)]
pub enum VideosError {
}

async fn connect_to_db() -> tokio_postgres::Client {
    let (client, connection) = Config::new()
        .user(&env::var("DB_USER").expect("DB_USER must be set"))
        .password(&env::var("DB_PASSWORD").expect("DB_PASSWORD must be set"))
        .port(
            env::var("DB_PORT")
                .unwrap()
                .parse()
                .expect("DB_PORT must be set"),
        )
        .dbname(&env::var("DB_NAME").expect("DB_NAME must be set"))
        .host(&env::var("DB_HOST").expect("DB_HOST must be set"))
        .connect(tokio_postgres::NoTls)
        .await
        .unwrap();

    // The connection object performs the actual communication with the database,
    // so spawn it off to run on its own.
    tokio::spawn(async move {
        if let Err(e) = connection.await {
            eprintln!("connection error: {}", e);
        }
    });

    client
}

#[async_trait::async_trait]
impl Strategy for StrategyConstant {
    async fn get_videos(
        &self,
        _claims: &Claims,
        _client: tokio_postgres::Client,
    ) -> Result<Videos, VideosError> {
        let ids = vec![
            Uuid::from_str("942e76c8-a62a-4228-8fbf-a0fe49d65c43").unwrap(),
            Uuid::from_str("b1a04e66-c701-4e65-b8bf-01996a3f182f").unwrap(),
            Uuid::from_str("18b3b2bd-8e6a-4c17-b8c7-2122eb132b30").unwrap(),
            Uuid::from_str("b6c020cc-0e37-4ac7-bb61-a7595b93514f").unwrap(),
            Uuid::from_str("29e8cf92-30e9-4466-8613-682e4fb15335").unwrap(),
            Uuid::from_str("898080a0-5259-440b-9835-79858aa1c990").unwrap(),
        ];
        Ok(Videos { ids })
    }
}

#[async_trait::async_trait]
impl Strategy for StrategyLatest {
    async fn get_videos(
        &self,
        _claims: &Claims,
        client: tokio_postgres::Client,
    ) -> Result<Videos, VideosError> {
        let rows = client
            .query(
                "SELECT id FROM video WHERE status = $1 ORDER BY time_processed DESC LIMIT $2",
                &[&"PROCESSED", &self.n_latest],
            )
            .await
            .unwrap();
        let ids = rows
            .iter()
            .map(|row| {
                Uuid::from_str(row.get(0)).unwrap()
            })
            .collect();
        Ok(Videos { ids })
    }
}
