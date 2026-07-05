# Enderase Dashboard

Product dashboard stack for the Enderase Youth Association registry.

## Structure

- `web/` - Next.js dashboard UI
- `api/` - FastAPI read API for dashboard data
- `metrics-sync/` - PostgreSQL/Odoo to ClickHouse sync worker
- `clickhouse/` - ClickHouse schema and initialization SQL
- `docs/` - dashboard architecture notes

The Odoo addon remains separate in `../g2p_enderase_youth_registry`.
Docker Compose mounts only that addon into Odoo so the dashboard app and
Node/Python service files are not scanned as Odoo modules.
