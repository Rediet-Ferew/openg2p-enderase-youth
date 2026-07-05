"""Enderase dashboard API.

Serves precomputed metrics from ClickHouse rollups with a Redis
cache-aside layer in front. Never touches the transactional PostgreSQL.
"""

import json
import os
import threading
from datetime import datetime, timezone

import clickhouse_connect
import redis
from redis.backoff import NoBackoff
from redis.retry import Retry
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "enderase")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "enderase-local-dev")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "30"))

app = FastAPI(title="Enderase Dashboard API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Short timeouts and no retries: a slow/hung Redis must degrade to
# ClickHouse within ~1s, never stall dashboard requests. (redis-py >= 6
# defaults to retrying connection errors with exponential backoff, which
# turns an outage into ~20s per request.)
_cache = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
    socket_connect_timeout=0.5,
    socket_timeout=0.5,
    retry=Retry(NoBackoff(), 0),
)

# clickhouse-connect clients are not safe for concurrent queries; FastAPI
# runs sync endpoints on a threadpool, so keep one client per thread.
_local = threading.local()


def _clickhouse():
    client = getattr(_local, "clickhouse", None)
    if client is None:
        client = clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            username=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD,
        )
        _local.clickhouse = client
    return client


def serve(key: str, compute):
    """Cache-aside: Redis when warm, else ClickHouse; failures become 503."""
    try:
        hit = _cache.get(key)
        if hit is not None:
            return json.loads(hit)
    except redis.RedisError:
        pass

    try:
        value = compute()
    except HTTPException:
        raise
    except Exception as exc:
        # Drop the thread-local client: it may hold a dead connection.
        _local.clickhouse = None
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    value["lastUpdated"] = datetime.now(timezone.utc).isoformat()
    try:
        _cache.setex(key, CACHE_TTL, json.dumps(value))
    except redis.RedisError:
        pass
    return value


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/api/dashboard/national")
def national():
    def compute():
        ch = _clickhouse()
        by_status = ch.query(
            "SELECT record_status, count() FROM enderase.beneficiaries FINAL "
            "GROUP BY record_status"
        ).result_rows
        by_category = ch.query(
            "SELECT beneficiary_category, count() FROM enderase.beneficiaries FINAL "
            "GROUP BY beneficiary_category ORDER BY 2 DESC"
        ).result_rows
        today = ch.query(
            "SELECT uniqExactMerge(events) FROM enderase.daily_stats "
            "WHERE event_type = 'registration' AND date = today()"
        ).result_rows
        return {
            "totals": {status: n for status, n in by_status},
            "byCategory": {cat: n for cat, n in by_category},
            "todayRegistrations": int(today[0][0]) if today else 0,
        }

    return serve("dashboard:national", compute)


@app.get("/api/dashboard/summary")
def summary():
    """Everything the storyteller front page can source from the registry.

    Datapoints the registry doesn't have (training status, skills,
    entrepreneurship, leadership counts...) are intentionally absent —
    the frontend keeps its illustrative dummy data for those.
    """

    def compute():
        ch = _clickhouse()
        fin = "FROM enderase.beneficiaries FINAL"

        totals = ch.query(
            f"SELECT countIf(beneficiary_category = 'individual'), "
            f"countIf(is_beneficiary = 1), "
            f"countIf(beneficiary_category = 'group'), "
            f"uniqExactIf(region, region != '') {fin}"
        ).result_rows[0]

        gender = ch.query(
            f"SELECT countIf(lowerUTF8(gender) = 'female'), "
            f"countIf(lowerUTF8(gender) = 'male') {fin} "
            f"WHERE beneficiary_category = 'individual'"
        ).result_rows[0]

        bands = ch.query(
            f"SELECT countIf(age BETWEEN 15 AND 18), "
            f"countIf(age BETWEEN 19 AND 22), "
            f"countIf(age BETWEEN 23 AND 26), "
            f"countIf(age BETWEEN 27 AND 30) FROM ("
            f"  SELECT dateDiff('year', birthdate, today()) AS age "
            f"  {fin} WHERE birthdate IS NOT NULL "
            f"  AND beneficiary_category = 'individual')"
        ).result_rows[0]

        stages = ch.query(
            f"SELECT count(), "
            f"countIf(record_status IN ('verified', 'active')), "
            f"countIf(is_member = 1 AND membership_status = 'active'), "
            f"countIf(is_beneficiary = 1) {fin}"
        ).result_rows[0]

        regions = ch.query(
            f"SELECT region, countIf(beneficiary_category = 'individual'), "
            f"countIf(is_beneficiary = 1), "
            f"countIf(beneficiary_category = 'group') {fin} "
            f"WHERE region != '' GROUP BY region ORDER BY 2 DESC"
        ).result_rows

        sectors = ch.query(
            f"SELECT primary_sector, count() {fin} "
            f"WHERE primary_sector NOT IN ('', 'UNSPECIFIED') "
            f"GROUP BY primary_sector ORDER BY 2 DESC LIMIT 12"
        ).result_rows

        yearly = ch.query(
            f"SELECT toYear(created_at) AS y, "
            f"countIf(beneficiary_category = 'individual'), "
            f"countIf(is_beneficiary = 1) {fin} GROUP BY y ORDER BY y"
        ).result_rows
        growth, youth_cum, ben_cum = [], 0, 0
        for year, youth, beneficiaries in yearly:
            youth_cum += int(youth)
            ben_cum += int(beneficiaries)
            growth.append(
                {"year": str(year), "youth": youth_cum, "beneficiaries": ben_cum}
            )

        band_labels = ["15–18", "19–22", "23–26", "27–30"]
        return {
            "totals": {
                "registeredYouth": int(totals[0]),
                "beneficiaries": int(totals[1]),
                "groups": int(totals[2]),
                "regions": int(totals[3]),
            },
            "demographics": {
                "female": int(gender[0]),
                "male": int(gender[1]),
                "ageBands": [
                    {"band": b, "value": int(v)}
                    for b, v in zip(band_labels, bands)
                ],
            },
            "pipeline": [
                {"stage": "Registration", "value": int(stages[0])},
                {"stage": "Verification", "value": int(stages[1])},
                {"stage": "Member", "value": int(stages[2])},
                {"stage": "Beneficiary", "value": int(stages[3])},
            ],
            "regions": [
                {
                    "region": r,
                    "youth": int(y),
                    "beneficiaries": int(b),
                    "groups": int(g),
                }
                for r, y, b, g in regions
            ],
            "sectors": [{"name": s, "size": int(n)} for s, n in sectors],
            "growth": growth,
        }

    return serve("dashboard:summary", compute)


@app.get("/api/dashboard/regions")
def regions():
    def compute():
        ch = _clickhouse()
        rows = ch.query(
            "SELECT region, uniqExactMerge(events) AS registrations "
            "FROM enderase.daily_stats WHERE event_type = 'registration' "
            "GROUP BY region ORDER BY registrations DESC"
        ).result_rows
        return {"regions": [{"region": r, "registrations": int(n)} for r, n in rows]}

    return serve("dashboard:regions", compute)


@app.get("/api/dashboard/timeseries")
def timeseries(
    days: int = Query(default=90, ge=1, le=730),
    event_type: str = Query(default="registration"),
    region: str | None = None,
):
    def compute():
        ch = _clickhouse()
        where = "event_type = {event_type:String} AND date >= today() - {days:UInt32}"
        params = {"event_type": event_type, "days": days}
        if region:
            where += " AND region = {region:String}"
            params["region"] = region
        rows = ch.query(
            f"SELECT date, uniqExactMerge(events), sumMerge(amount) "
            f"FROM enderase.daily_stats WHERE {where} "
            f"GROUP BY date ORDER BY date",
            parameters=params,
        ).result_rows
        return {
            "eventType": event_type,
            "region": region,
            "series": [
                {"date": d.isoformat(), "count": int(c), "amount": float(a)}
                for d, c, a in rows
            ],
        }

    key = f"dashboard:timeseries:{event_type}:{region or 'all'}:{days}"
    return serve(key, compute)
