# Enderase Dashboard Architecture (ClickHouse)

Serving stack for the Enderase Youth Association dashboard. The goal:
dashboard reads never touch the transactional PostgreSQL (OpenG2P/Odoo),
and every response comes from precomputed or column-store data in
single-digit to low-double-digit milliseconds.

```
Browser (enderase_dashboard/web, Next.js + React/Recharts)
        │  /api/*  (Next rewrite)
        ▼
FastAPI dashboard service ──── Redis (cache-aside, 30s TTL)
        │
        ▼
ClickHouse
  ├── enderase.beneficiaries   current-state snapshot (ReplacingMergeTree)
  ├── enderase.events          append-only domain events (ReplacingMergeTree)
  └── enderase.daily_stats     incremental rollup (AggregatingMergeTree,
                               maintained automatically by a materialized view)
        ▲
        │  metrics-sync worker (today) / CDC or RabbitMQ consumer (later)
        │
PostgreSQL ◄── Odoo 17 (openg2p-social-registry-core image
               + local g2p_enderase_youth_registry addon, both in this compose)
```

## Why this differs from the "metrics service increments counters" design

A hand-rolled metrics service that does `active_farmers += 1` is fragile:
missed messages, double deliveries, and restarts all silently corrupt the
counters, and rebuilding them means a full recount anyway.

With ClickHouse you get the same incremental behavior for free:

1. **Insert raw events** into `enderase.events`.
2. A **materialized view** aggregates each insert block into
   `enderase.daily_stats` (an `AggregatingMergeTree`). No cron, no consumer
   code, no drift.
3. Counts use `uniqExactState(event_id)`, so **replayed events don't double
   count** — idempotent by construction.
4. If a rollup is ever wrong or you need a new one, `INSERT INTO ... SELECT`
   from the raw events rebuilds it in seconds. The raw data is the source of
   truth; rollups are disposable.

## The two data lanes

| Lane | Table | Engine | Answers |
|------|-------|--------|---------|
| Current state | `beneficiaries` | `ReplacingMergeTree(updated_at)` | "How many ACTIVE beneficiaries right now, by category/region?" |
| History | `events` → `daily_stats` | `ReplacingMergeTree` → `AggregatingMergeTree` | "Registrations per day/region for the last 90 days?" |

Current-state questions are answered with `FINAL` queries on the snapshot.
At tens of millions of rows this is still milliseconds in ClickHouse; the
Redis layer makes repeated loads ~1ms regardless.

Multi-level drill-down (national → region → zone → woreda) is one table:
`daily_stats` is keyed by `(event_type, region, zone, woreda, category,
date)`, so every level is a `GROUP BY` over an already-tiny rollup — no
separate table per level needed.

## Ingestion: start simple, upgrade the lane, not the architecture

**Today (this compose):** `metrics-sync` pulls the Enderase registry
straight from Odoo's `res_partner` (joined with the admin-area lookup
tables) every 60s. Normal cycles are
incremental — only rows whose `updated_at` is at or past the ClickHouse
high-water mark are shipped. Every `FULL_RESYNC_EVERY` cycles (default:
hourly at a 60s interval) a full snapshot runs instead and emits
`is_deleted = 1` tombstones for rows that vanished from PostgreSQL, so
hard deletes converge too (`ReplacingMergeTree(updated_at, is_deleted)`
drops tombstoned rows from `FINAL` reads). Because both target tables
dedupe on their key, overlap and replays are always safe. This is fine
into the low millions of rows.

**Next (near-real-time):** publish domain events from Odoo/PBMS to RabbitMQ
(already in your stack) and run a thin consumer that inserts into
`enderase.events` in batches (1k–10k rows per insert — ClickHouse hates
single-row inserts). The MV keeps rollups current; nothing else changes.

**At scale (100M+ rows, exact history):** CDC from PostgreSQL with
Debezium → Kafka → ClickHouse Kafka table engine, or managed PeerDB /
ClickPipes. Again, only the left side of the diagram changes.

## Operational notes

- **Batch inserts.** Never insert rows one at a time into ClickHouse; buffer
  in the consumer (or use async_insert) and write in blocks.
- **`sumState` is not replay-safe** the way `uniqExactState` is: dedup of
  the raw events table happens at merge time, *after* the MV fired. For
  monetary rollups, ensure exactly-once upstream (CDC) or rebuild the rollup
  periodically from deduplicated raw events.
- **Cache TTL = freshness contract.** 30s in Redis means the dashboard is at
  most ~30s stale. Drop to 5s or add pub/sub invalidation if leadership wants
  live numbers during registration drives.
- **Registry-backed vs. illustrative datapoints.** `/api/dashboard/summary`
  serves what the registry actually has (totals, gender, age bands, pipeline
  stages, regions, sectors, growth). Chart datapoints the registry doesn't
  track yet (training status, skills, entrepreneurship, leadership) stay on
  the illustrative dataset in `web/src/data/registry.ts`; the
  `useRegistryData()` hook does the merging and falls back to the full
  illustrative story whenever the API is down or the registry is empty.
- **Superset keeps working.** Point Superset at ClickHouse too for ad-hoc
  analysis; the FastAPI service is for the product dashboard where latency
  and shape stability matter.

## Running it

```bash
# from /home/user/enderase_youth_association (docker-compose.yml lives there)
cp .env.example .env
docker compose up -d --build
# Odoo:       http://localhost:8069  (first boot installs the registry
#             module chain — allow several minutes; login admin / admin)
# web:        http://localhost:8080
# API:        http://localhost:8000/api/dashboard/summary
# ClickHouse: http://localhost:8123/play
```
