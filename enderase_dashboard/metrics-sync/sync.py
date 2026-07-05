"""PostgreSQL -> ClickHouse sync worker.

Periodically pulls the beneficiary registry from the enderase-youth
PostgreSQL (OpenG2P/Odoo) and lands it in ClickHouse:

  - enderase.beneficiaries  (current-state snapshot, ReplacingMergeTree)
  - enderase.events         (registration events derived from created_at)

Both targets deduplicate on their ORDER BY key, so replaying rows is
idempotent. Normal cycles are incremental: only rows whose updated_at is
at or past the ClickHouse high-water mark are pulled. Every
FULL_RESYNC_EVERY cycles a full snapshot runs instead, which also emits
is_deleted=1 tombstones for rows that vanished from PostgreSQL.

Good enough well into the millions of rows; swap this worker for CDC
(Debezium -> Kafka -> ClickHouse Kafka engine, or PeerDB) when volume or
freshness demands it.

The source query is overridable via SOURCE_QUERY and must yield columns
in this order (the last one MUST be aliased "updated_at" — incremental
mode wraps the query and filters on it):
  id, category, type, sector, support_category, status,
  membership_status, gender, birthdate, region, zone, woreda,
  is_member, is_beneficiary, pmt_score, created_at, updated_at
"""

import os
import time
from datetime import datetime, timedelta, timezone

import clickhouse_connect
import psycopg2

PG_DSN = (
    f"host={os.getenv('PG_HOST', 'localhost')} "
    f"port={os.getenv('PG_PORT', '5432')} "
    f"dbname={os.getenv('PG_DATABASE', 'enderase')} "
    f"user={os.getenv('PG_USER', 'odoo')} "
    f"password={os.getenv('PG_PASSWORD', 'odoo')}"
)
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL_SECONDS", "60"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50000"))
# Every Nth cycle runs a full snapshot (catches deletes and missed rows).
FULL_RESYNC_EVERY = int(os.getenv("FULL_RESYNC_EVERY", "60"))
# Incremental cycles re-pull this many seconds behind the high-water mark.
# Covers clock skew between ClickHouse and PostgreSQL and rows committed
# late by long transactions; the overlap is deduplicated on insert anyway.
SAFETY_LAG = timedelta(seconds=int(os.getenv("SAFETY_LAG_SECONDS", "600")))

# Reads the Enderase registry straight from Odoo's res_partner (fields
# added by g2p_enderase_youth_registry / OpenG2P). Lookup names are
# translated Char fields, stored as JSONB in Odoo 17 — hence ->>'en_US'.
DEFAULT_QUERY = """
SELECT
    COALESCE(p.enderase_registry_id, p.id::text)            AS id,
    COALESCE(p.enderase_beneficiary_category, 'UNKNOWN')    AS category,
    COALESCE(p.enderase_beneficiary_type, 'UNKNOWN')        AS type,
    COALESCE(NULLIF(p.primary_sector, ''), 'UNSPECIFIED')   AS sector,
    COALESCE(NULLIF(p.support_category, ''), 'UNSPECIFIED') AS support_category,
    COALESCE(p.enderase_record_status, 'UNKNOWN')           AS status,
    COALESCE(p.enderase_membership_status, 'not_member')    AS membership_status,
    COALESCE(p.gender, '')                                  AS gender,
    p.birthdate                                             AS birthdate,
    COALESCE(r.name->>'en_US', '')                          AS region,
    COALESCE(z.name->>'en_US', '')                          AS zone,
    COALESCE(w.name->>'en_US', '')                          AS woreda,
    COALESCE(p.is_enderase_member, false)::int              AS is_member,
    COALESCE(p.is_enderase_beneficiary, false)::int         AS is_beneficiary,
    NULL::float8                                            AS pmt_score,
    p.create_date                                           AS created_at,
    COALESCE(p.write_date, p.create_date)                   AS updated_at
FROM res_partner p
LEFT JOIN g2p_enderase_admin_region r ON r.id = p.enderase_admin_region_id
LEFT JOIN g2p_enderase_admin_zone   z ON z.id = p.enderase_admin_zone_id
LEFT JOIN g2p_enderase_admin_woreda w ON w.id = p.enderase_admin_woreda_id
WHERE p.active
  AND (p.is_enderase_member OR p.is_enderase_beneficiary
       OR p.is_enderase_group OR p.is_enderase_startup)
"""
SOURCE_QUERY = os.getenv("SOURCE_QUERY", DEFAULT_QUERY)

BENEFICIARY_COLUMNS = [
    "internal_record_id", "beneficiary_category", "beneficiary_type",
    "primary_sector", "support_category", "record_status",
    "membership_status", "gender", "birthdate",
    "region", "zone", "woreda", "is_member", "is_beneficiary",
    "pmt_score", "created_at", "updated_at",
]
EVENT_COLUMNS = [
    "event_id", "event_type", "entity_id",
    "region", "zone", "woreda", "category", "amount", "event_time",
]


def clickhouse():
    return clickhouse_connect.get_client(
        host=os.getenv("CLICKHOUSE_HOST", "localhost"),
        port=int(os.getenv("CLICKHOUSE_PORT", "8123")),
        username=os.getenv("CLICKHOUSE_USER", "enderase"),
        password=os.getenv("CLICKHOUSE_PASSWORD", "enderase-local-dev"),
    )


def high_water_mark(ch):
    rows = ch.query(
        "SELECT max(updated_at) FROM enderase.beneficiaries"
    ).result_rows
    mark = rows[0][0] if rows else None
    # An empty table yields the DateTime epoch; treat it as "no mark".
    if mark is None or mark.year <= 1970:
        return None
    return mark


def sync_once(ch, full: bool):
    # ">=" not ">": rows sharing the boundary timestamp are re-pulled, and
    # dedup makes the overlap harmless. ">" could miss late arrivals that
    # commit with the same updated_at after we read the mark.
    mark = None if full else high_water_mark(ch)
    if mark is not None:
        query = (
            f"SELECT * FROM ({SOURCE_QUERY}) src "
            f"WHERE src.updated_at >= %(mark)s"
        )
        params = {"mark": mark - SAFETY_LAG}
    else:
        query, params, full = SOURCE_QUERY, None, True

    if full:
        # Staging table for ids seen in this snapshot; filled batch-by-batch
        # so the worker never holds the whole registry in memory.
        ch.command("DROP TABLE IF EXISTS enderase._sync_seen")
        ch.command("CREATE TABLE enderase._sync_seen (id String) ENGINE = Memory")

    total = 0
    with psycopg2.connect(PG_DSN) as pg:
        with pg.cursor(name="enderase_sync") as cur:  # server-side cursor
            cur.itersize = BATCH_SIZE
            cur.execute(query, params)
            while True:
                rows = cur.fetchmany(BATCH_SIZE)
                if not rows:
                    break
                now = datetime.now(timezone.utc).replace(tzinfo=None)
                beneficiaries = [
                    (*r[:15], r[15] or now, r[16] or r[15] or now) for r in rows
                ]
                events = [
                    (
                        f"registration:{r[0]}", "registration", r[0],
                        r[9], r[10], r[11], r[1], 0.0, r[15] or now,
                    )
                    for r in rows
                ]
                ch.insert("enderase.beneficiaries", beneficiaries,
                          column_names=BENEFICIARY_COLUMNS)
                ch.insert("enderase.events", events, column_names=EVENT_COLUMNS)
                if full:
                    ch.insert("enderase._sync_seen",
                              [(r[0],) for r in rows], column_names=["id"])
                total += len(rows)

    if full:
        tombstone_deleted(ch)
    print(
        f"[metrics-sync] {'full' if full else 'incremental'} sync: "
        f"{total} records (mark={mark})",
        flush=True,
    )


def tombstone_deleted(ch):
    """After a full snapshot, mark rows missing from PostgreSQL as deleted.

    Emits is_deleted=1 versions dated now(); ReplacingMergeTree drops them
    from FINAL reads immediately and physically at merge time.
    """
    ch.command("""
        INSERT INTO enderase.beneficiaries
        SELECT * REPLACE (now() AS updated_at, 1 AS is_deleted,
                          now() AS _synced_at)
        FROM enderase.beneficiaries FINAL
        WHERE internal_record_id NOT IN (SELECT id FROM enderase._sync_seen)
          AND is_deleted = 0
    """)
    ch.command("DROP TABLE enderase._sync_seen")


def main():
    print(
        f"[metrics-sync] starting, interval={SYNC_INTERVAL}s, "
        f"full resync every {FULL_RESYNC_EVERY} cycles",
        flush=True,
    )
    cycle = 0
    while True:
        try:
            sync_once(clickhouse(), full=(cycle % FULL_RESYNC_EVERY == 0))
        except Exception as exc:
            print(f"[metrics-sync] sync failed: {exc}", flush=True)
        cycle += 1
        time.sleep(SYNC_INTERVAL)


if __name__ == "__main__":
    main()
