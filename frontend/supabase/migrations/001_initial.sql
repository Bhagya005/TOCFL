-- TOCFL A1 Supabase schema (replaces SQLite)
-- Run this in Supabase SQL Editor or via Supabase CLI.

-- Users (custom auth; use password_hash with pbkdf2_sha256)
CREATE TABLE IF NOT EXISTS users (
  id BIGSERIAL PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- User settings (start_date for study plan)
CREATE TABLE IF NOT EXISTS user_settings (
  user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  start_date DATE
);

-- Vocabulary (seed from Excel; id matches source)
CREATE TABLE IF NOT EXISTS words (
  id INT PRIMARY KEY,
  character TEXT NOT NULL,
  pinyin TEXT,
  meaning TEXT,
  pos TEXT,
  category TEXT,
  subcategory TEXT
);

-- Cached example sentences per word
CREATE TABLE IF NOT EXISTS examples (
  word_id INT PRIMARY KEY REFERENCES words(id) ON DELETE CASCADE,
  sentence TEXT NOT NULL,
  pinyin TEXT NOT NULL,
  translation TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Per-user per-word flashcard/progress
CREATE TABLE IF NOT EXISTS user_progress (
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  word_id INT NOT NULL REFERENCES words(id) ON DELETE CASCADE,
  known INT NOT NULL DEFAULT 0,
  mistakes INT NOT NULL DEFAULT 0,
  attempts INT NOT NULL DEFAULT 0,
  correct INT NOT NULL DEFAULT 0,
  last_seen TIMESTAMPTZ,
  PRIMARY KEY (user_id, word_id)
);

-- Test results
CREATE TABLE IF NOT EXISTS test_results (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  test_type TEXT NOT NULL,
  score INT NOT NULL,
  total INT NOT NULL,
  meta_json JSONB
);

-- Weak words (user-marked)
CREATE TABLE IF NOT EXISTS weak_words (
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  word_id INT NOT NULL REFERENCES words(id) ON DELETE CASCADE,
  added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, word_id)
);

-- Spaced repetition: next review per word (global, not per user in original)
CREATE TABLE IF NOT EXISTS word_progress (
  word_id INT PRIMARY KEY REFERENCES words(id) ON DELETE CASCADE,
  last_reviewed TIMESTAMPTZ,
  next_review TIMESTAMPTZ,
  difficulty_score INT NOT NULL DEFAULT 0,
  review_count INT NOT NULL DEFAULT 0
);

-- Denormalized stats for leaderboard
CREATE TABLE IF NOT EXISTS user_stats (
  user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  username TEXT NOT NULL,
  streak_days INT NOT NULL DEFAULT 0,
  words_learned INT NOT NULL DEFAULT 0,
  tests_taken INT NOT NULL DEFAULT 0,
  avg_test_score REAL NOT NULL DEFAULT 0,
  total_points REAL NOT NULL DEFAULT 0
);

-- Cached generated test (payload_json)
CREATE TABLE IF NOT EXISTS generated_tests (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  test_type TEXT NOT NULL,
  payload_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, date, test_type)
);

-- Optional: word_mastery if needed for future features
CREATE TABLE IF NOT EXISTS word_mastery (
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  word_id INT NOT NULL REFERENCES words(id) ON DELETE CASCADE,
  reading_correct INT NOT NULL DEFAULT 0,
  listening_correct INT NOT NULL DEFAULT 0,
  writing_correct INT NOT NULL DEFAULT 0,
  mastered INT NOT NULL DEFAULT 0,
  PRIMARY KEY (user_id, word_id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_user_progress_user ON user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_test_results_user ON test_results(user_id);
CREATE INDEX IF NOT EXISTS idx_weak_words_user ON weak_words(user_id);
CREATE INDEX IF NOT EXISTS idx_word_progress_next ON word_progress(next_review);
