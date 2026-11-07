FROM rust:1.99.1-alpine3.24 AS builder

RUN apk add --no-cache build-base

WORKDIR /src

COPY Cargo.toml Cargo.lock ./
RUN mkdir src \
    && printf 'fn main() {}\n' > src/main.rs \
    && : > src/lib.rs

RUN --mount=type=cache,target=/usr/local/cargo/registry \
    cargo build --release --locked --bin zeitzeit

COPY . .

RUN --mount=type=cache,target=/usr/local/cargo/registry \
    cargo build --release --locked --bin zeitzeit

FROM alpine:3.24

RUN adduser -D -H -u 10001 app

USER 10001
WORKDIR /app

COPY --from=builder /src/target/release/zeitzeit /app/zeitzeit

ENV BIND_ADDR=0.0.0.0:8080
EXPOSE 8080

ENTRYPOINT ["/app/zeitzeit"]
