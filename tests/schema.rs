use sqlx::PgPool;

#[sqlx::test]
async fn only_one_running_timer_per_user(pool: PgPool) {
    let user_id: uuid::Uuid = sqlx::query_scalar(
        "INSERT INTO users (email, display_name, password_hash)
         VALUES ('a@example.com', 'A', 'hash') RETURNING id",
    )
    .fetch_one(&pool)
    .await
    .unwrap();

    let insert = "INSERT INTO time_entries (user_id, started_at) VALUES ($1, now())";
    sqlx::query(insert)
        .bind(user_id)
        .execute(&pool)
        .await
        .unwrap();

    let err = sqlx::query(insert)
        .bind(user_id)
        .execute(&pool)
        .await
        .unwrap_err();

    assert!(err.as_database_error().unwrap().is_unique_violation());
}
