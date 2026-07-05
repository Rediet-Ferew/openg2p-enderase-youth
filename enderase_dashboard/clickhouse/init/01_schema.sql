CREATE DATABASE IF NOT EXISTS enderase;

-- ---------------------------------------------------------------------------
-- Lane 1: current-state snapshot of the registry.
-- Synced from the Odoo (OpenG2P) PostgreSQL res_partner table.
-- ReplacingMergeTree keyed by record id makes re-syncs idempotent: the latest
-- updated_at wins at merge time, so the sync worker can safely replay rows.
-- Rows with is_deleted = 1 (from CDC delete events or tombstones emitted by
-- the sync worker) are dropped by FINAL queries and at merge time.
-- Query with FINAL for exact current-state numbers.
-- NOTE: init scripts only run on an empty ClickHouse volume. If you have an
-- existing volume from before the gender/birthdate/membership columns were
-- added, either `docker compose down -v` (dev) or apply the matching
-- ALTER TABLE ... ADD COLUMN statements by hand.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS enderase.beneficiaries
(
    internal_record_id   String,
    beneficiary_category LowCardinality(String),
    beneficiary_type     LowCardinality(String),
    primary_sector       LowCardinality(String),
    support_category     LowCardinality(String),
    record_status        LowCardinality(String),
    membership_status    LowCardinality(String) DEFAULT '',
    gender               LowCardinality(String) DEFAULT '',
    birthdate            Nullable(Date32),
    region               LowCardinality(String),
    zone                 LowCardinality(String),
    woreda               LowCardinality(String),
    is_member            UInt8 DEFAULT 0,
    is_beneficiary       UInt8 DEFAULT 0,
    pmt_score            Nullable(Float64),
    created_at           DateTime,
    updated_at           DateTime,
    is_deleted           UInt8 DEFAULT 0,
    _synced_at           DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at, is_deleted)
ORDER BY internal_record_id;

-- ---------------------------------------------------------------------------
-- Lane 2: append-only domain events (registrations, approvals, payments...).
-- Feed this from RabbitMQ/CDC in production; the sync worker derives
-- registration events from created_at as a starting point.
-- ReplacingMergeTree on event_id deduplicates replayed events at merge time.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS enderase.events
(
    event_id   String,
    event_type LowCardinality(String),
    entity_id  String,
    region     LowCardinality(String),
    zone       LowCardinality(String),
    woreda     LowCardinality(String),
    category   LowCardinality(String),
    amount     Float64 DEFAULT 0,
    event_time DateTime
)
ENGINE = ReplacingMergeTree
PARTITION BY toYYYYMM(event_time)
ORDER BY (event_type, event_id);

-- ---------------------------------------------------------------------------
-- Incremental rollup: daily stats per event type and admin area.
-- The materialized view below updates this table on every insert into
-- enderase.events — no cron job, no hand-rolled counter increments.
-- uniqExact over event_id keeps counts exact even if events are replayed.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS enderase.daily_stats
(
    date       Date,
    event_type LowCardinality(String),
    region     LowCardinality(String),
    zone       LowCardinality(String),
    woreda     LowCardinality(String),
    category   LowCardinality(String),
    events     AggregateFunction(uniqExact, String),
    amount     AggregateFunction(sum, Float64)
)
ENGINE = AggregatingMergeTree
ORDER BY (event_type, region, zone, woreda, category, date);

CREATE MATERIALIZED VIEW IF NOT EXISTS enderase.mv_daily_stats
TO enderase.daily_stats AS
SELECT
    toDate(event_time)          AS date,
    event_type,
    region,
    zone,
    woreda,
    category,
    uniqExactState(event_id)    AS events,
    sumState(amount)            AS amount
FROM enderase.events
GROUP BY date, event_type, region, zone, woreda, category;
