-- Migration 00002: No-op for fresh installations.
-- All schema definitions are in the idempotent 00001_schema.sql.
SELECT 1 AS migration_check;
