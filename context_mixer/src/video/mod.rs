use serde::{Serialize, Deserialize};
use uuid::Uuid;

use crate::server::Claims;

pub async fn get_videos(_claims: Claims) -> Result<Videos, VideosError> {
    let ids = vec![Uuid::from_u128(0), Uuid::from_u128(1), Uuid::from_u128(2)];
    Ok(Videos { ids })
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Videos {
    ids: Vec<Uuid>,
}

#[derive(Debug)]
pub enum VideosError {

}