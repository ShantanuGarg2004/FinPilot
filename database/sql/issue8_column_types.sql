-- One-time column types for an existing FinPilot database.
-- Run by hand against the application database. Safe to run again:
-- a column that is already timestamptz or jsonb is left alone.
-- ai_report stays text. It is the advisory prose, not JSON.
-- There is no Alembic migration.

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'accounts'
      AND column_name = 'created_at'
      AND udt_name = 'text'
  ) THEN
    ALTER TABLE accounts
      ALTER COLUMN created_at TYPE timestamptz
      USING NULLIF(btrim(created_at), '')::timestamptz;
    ALTER TABLE accounts
      ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
  END IF;

  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'users'
      AND column_name = 'created_at'
      AND udt_name = 'text'
  ) THEN
    ALTER TABLE users
      ALTER COLUMN created_at TYPE timestamptz
      USING NULLIF(btrim(created_at), '')::timestamptz;
    ALTER TABLE users
      ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
  END IF;

  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'reports'
      AND column_name = 'generated_at'
      AND udt_name = 'text'
  ) THEN
    ALTER TABLE reports
      ALTER COLUMN generated_at TYPE timestamptz
      USING NULLIF(btrim(generated_at), '')::timestamptz;
    ALTER TABLE reports
      ALTER COLUMN generated_at SET DEFAULT CURRENT_TIMESTAMP;
  END IF;

  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'reports'
      AND column_name = 'health_json'
      AND udt_name = 'text'
  ) THEN
    ALTER TABLE reports
      ALTER COLUMN health_json TYPE jsonb
      USING health_json::jsonb;
  END IF;

  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = current_schema()
      AND table_name = 'chat_history'
      AND column_name = 'created_at'
      AND udt_name = 'text'
  ) THEN
    ALTER TABLE chat_history
      ALTER COLUMN created_at TYPE timestamptz
      USING NULLIF(btrim(created_at), '')::timestamptz;
    ALTER TABLE chat_history
      ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
  END IF;
END $$;
