-- Bootstraps the two-schema / two-role layout this project relies on for safety:
--   `app`       -- application metadata (users, saved_queries, dashboards, widgets),
--                  owned by the main `insightops` role with full read/write.
--   `analytics` -- the sample business dataset the NL->SQL engine queries. The engine
--                  connects as `analytics_readonly`, which can only ever SELECT here --
--                  enforced by Postgres itself, independent of any application-level
--                  SQL-safety checks.

CREATE SCHEMA IF NOT EXISTS app;
CREATE SCHEMA IF NOT EXISTS analytics;

DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'analytics_readonly') THEN
    CREATE ROLE analytics_readonly LOGIN PASSWORD 'analytics_readonly';
  END IF;
END
$$;

GRANT CONNECT ON DATABASE insightops TO analytics_readonly;
GRANT USAGE ON SCHEMA analytics TO analytics_readonly;

-- Applies to tables that exist yet AND tables created later by the seed script.
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO analytics_readonly;

-- No privileges at all on the `app` schema for the read-only role -- it cannot see
-- user accounts, saved queries, or anything else outside the sandboxed dataset.
REVOKE ALL ON SCHEMA app FROM analytics_readonly;
