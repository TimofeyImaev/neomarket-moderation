CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS product_blocking_reasons (
    id           VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    title        VARCHAR(255) NOT NULL,
    hard_block   BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS product_moderation (
    id                  VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    product_id          VARCHAR(36) NOT NULL UNIQUE,
    seller_id           VARCHAR(36) NOT NULL,
    status              VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    queue_priority      INTEGER NOT NULL DEFAULT 1,
    json_before         JSONB,
    json_after          JSONB NOT NULL DEFAULT '{}',
    blocking_reason_id  VARCHAR(36) REFERENCES product_blocking_reasons(id),
    moderator_id        VARCHAR(36),
    moderator_comment   TEXT,
    date_created        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    date_updated        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    date_moderation     TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS product_moderation_field_reports (
    id                      VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    product_moderation_id   VARCHAR(36) NOT NULL REFERENCES product_moderation(id) ON DELETE CASCADE,
    field_name              VARCHAR(255) NOT NULL,
    sku_id                  VARCHAR(36),
    comment                 TEXT NOT NULL,
    date_created            TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_product_moderation_status_priority
    ON product_moderation(status, queue_priority);
