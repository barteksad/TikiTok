use context_mixer::server::run_server;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};
use dotenv::dotenv;

#[tokio::main]
async fn main() {
    dotenv().ok();
    
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "context_mixer=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    run_server().await;
}
