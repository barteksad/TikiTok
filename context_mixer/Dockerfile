# https://hub.docker.com/_/rust#:~:text=Start%20a%20Rust%20instance%20running%20your%20app
# FROM rust:1.64.0-slim




FROM rust:1.64.0 AS builder
COPY . .
RUN cargo build --release

FROM debian:buster-slim
RUN apt-get update \
    && apt-get -y install pkg-config libssl-dev \
    && apt-get -y install ca-certificates \
    && apt-get -y clean
COPY --from=builder ./target/release/context_mixer ./target/release/context_mixer
# COPY --from=builder .env .
CMD ["/target/release/context_mixer"]