use std::{env, str::FromStr, sync::Arc, collections::HashMap, sync::Mutex};

use axum::async_trait;
use serde::{Deserialize, Serialize};
use tokio_postgres::{Config, types::{FromSql, Type}};
use uuid::Uuid;

use crate::server::Claims;

static VIDEOS_BATCH_SIZE: usize = 3;
static N_BATCHES: usize = 3;

#[async_trait]
pub trait Strategy: Send + Sync {
    async fn get_videos(
        &self,
        claims: &Claims,
        client: tokio_postgres::Client,
        batch_idx: usize,
    ) -> Result<Videos, VideosError>;
}

pub async fn get_videos(claims: &Claims, strategy: Arc<dyn Strategy>, batch_idx: usize) -> Result<Videos, VideosError> {
    let client = connect_to_db().await;
    strategy.get_videos(claims, client, batch_idx).await
}

pub struct StrategyMostLikedWithOthers {
    batches: Arc<Mutex<HashMap<String, VideosBatch>>>
}

pub struct StrategyConstant;

pub struct StrategyLatest {
    pub n_latest: i64,
}
#[derive(Debug, Serialize, Deserialize)]
pub struct Videos {
    pub ids: Vec<Uuid>,
}

#[derive(Debug, Clone)]
pub enum VideosError {
    InvalidBatchIdx,
    DbError,
}

struct VideosBatch {
    video_ids_reversed: Vec<Uuid>,
}

impl Iterator for VideosBatch {
    type Item = Videos;

    fn next(&mut self) -> Option<Self::Item> {
        let mut ids = Vec::new();
        for _ in 0..VIDEOS_BATCH_SIZE {
            if self.video_ids_reversed.len() == 0 {
                break;
            }
            ids.push(self.video_ids_reversed.pop()?);
        }
        Some(Videos { ids })
    }
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

impl StrategyMostLikedWithOthers {
    pub fn new() -> Self {
        StrategyMostLikedWithOthers {
            batches: Arc::new(Mutex::new(HashMap::new()))
        }
    }
}

#[async_trait::async_trait]
impl Strategy for StrategyMostLikedWithOthers {
    async fn get_videos(
        &self,
        claims: &Claims,
        client: tokio_postgres::Client,
        batch_idx: usize,
    ) -> Result<Videos, VideosError> {
        if batch_idx >= N_BATCHES {
            return Err(VideosError::InvalidBatchIdx);
        }
        if batch_idx == 0 || !self.batches.lock().unwrap().contains_key(&claims.user_id) {
            let user_vec = client
                .query(
                    "SELECT vector FROM preferences WHERE user_id = $1 ;",
                    &[&claims.user_id],
                )
                .await;
            tracing::debug!("user_vec: {:?}", user_vec);
            let (c1, c2, c3) : (i16, i16, i16) = match user_vec {
                Ok(rows_vec) if rows_vec.len() == 1 => {
                    // let vec = Vec::<f32>::from_sql(&Type::FLOAT4_ARRAY, rows_vec.get(0).unwrap().get(0))
                    let vec: Vec<f32> = rows_vec.get(0).unwrap().get(0);
                    // .unwrap(); // get vector from row
                    let mut vec = vec.iter()
                    .enumerate()
                    .collect::<Vec<(usize, &f32)>>(); // collect vector of tuples (index, value)
                    vec.sort_by(|lhs, rhs| 
                        lhs.1.partial_cmp(rhs.1).unwrap()); // sort by value
                    let mut it = vec.into_iter().map(|(i, _)| i16::try_from(i).unwrap()); // create iterator over indexes
                    (it.next().unwrap(), it.next().unwrap(), it.next().unwrap())
                }
                // If there is no vector it will be created in like handle once user liked something
                _ => (308, 429, 315) // passing American football (in game), salsa dancing, 	petting cat
            };
            
            let n_similar = (VIDEOS_BATCH_SIZE * N_BATCHES / 2) as i64;
            let n_not_similar = (VIDEOS_BATCH_SIZE * N_BATCHES) as i64- n_similar;
            let similar_rows = client
                .query(
                    "SELECT id FROM video WHERE status = $1 AND (class1 = $2 OR class2 = $3 OR class3 = $4) ORDER BY likes_count, time_processed DESC LIMIT $5 ;",
                    &[&"PROCESSED", &c1, &c2, &c3, &n_similar]).await;
            let not_similar_rows = client
                .query(
                    "SELECT id FROM video WHERE status = $1 AND (class1 != $2 AND class2 != $3 AND class3 != $4) ORDER BY likes_count, time_processed DESC LIMIT $5 ;",
                    &[&"PROCESSED", &c1, &c2, &c3, &n_not_similar]).await;
            let video_ids_reversed: Vec<Uuid> = match (similar_rows, not_similar_rows) {
                (Ok(similar_rows), Ok(not_similar_rows)) => {
                    let video_ids = similar_rows.iter().map(|row| Uuid::from_str(row.get(0)).unwrap()).rev().collect::<Vec<Uuid>>();
                    video_ids.into_iter().chain(not_similar_rows.iter().map(|row| Uuid::from_str(row.get(0)).unwrap()).rev()).collect::<Vec<Uuid>>()
                }
                (e1, e2) =>{
                    tracing::debug!("Error getting similar videos: {:?}, not similar videos: {:?} ;", e1, e2);
                    return Err(VideosError::DbError);
                }
            };
            tracing::debug!("Inserting batch {:?} for user {:?}", video_ids_reversed, claims.user_id);
            self.batches.lock().unwrap().insert(claims.user_id.clone(), VideosBatch { video_ids_reversed });
        }
        let resp = Ok(self.batches.lock().unwrap().get_mut(&claims.user_id).unwrap().next().unwrap());
        tracing::debug!("StrategyMostLikedWithOthers: {:?}", resp);
        resp
    }
}

#[async_trait::async_trait]
impl Strategy for StrategyConstant {
    async fn get_videos(
        &self,
        _claims: &Claims,
        _client: tokio_postgres::Client,
        _batch_idx: usize,
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
        _batch_idx: usize,
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
