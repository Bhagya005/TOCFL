-- Progression by completed study days instead of calendar
-- last_completed_study_day: 0 = no days done, next session is day 1; after completing day 1, next is day 2
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'user_settings' AND column_name = 'last_completed_study_day'
  ) THEN
    ALTER TABLE user_settings ADD COLUMN last_completed_study_day INT NOT NULL DEFAULT 0;
  END IF;
END $$;

-- For daily tests, which study day this result belongs to (so we know when day is "complete")
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'test_results' AND column_name = 'study_day'
  ) THEN
    ALTER TABLE test_results ADD COLUMN study_day INT;
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_test_results_study_day ON test_results(user_id, test_type, study_day);
