FROM rust:1.100.0-alpine3.24 AS chef
RUN apk add --no-cache build-base
RUN cargo install cargo-chef --version 0.1.78 --locked
WORKDIR /src

FROM chef AS planner
COPY . .
RUN cargo chef prepare --recipe-path recipe.json

FROM chef AS builder
COPY --from=planner /src/recipe.json recipe.json
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    cargo chef cook --release --locked --bin zeitzeit --recipe-path recipe.json

COPY . .
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    cargo build --release --locked --bin zeitzeit

FROM alpine:3.24 AS runtime
RUN adduser -D -H -u 10001 app
USER 10001
WORKDIR /app
COPY --from=builder /src/target/release/zeitzeit /app/zeitzeit

ENV BIND_ADDR=0.0.0.0:8080
EXPOSE 8080
ENTRYPOINT ["/app/zeitzeit"]
