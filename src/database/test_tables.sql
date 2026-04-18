-- ═══════════════════════════════════════════════════════════════
-- GB Career Pilot - Test Prep Database Schema
-- ═══════════════════════════════════════════════════════════════
-- TESTS TABLE
CREATE TABLE IF NOT EXISTS tests (
id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
title TEXT NOT NULL,
description TEXT,
type TEXT NOT NULL CHECK (type IN ('mock_test', 'past_paper', 'practice')),
university_id integer REFERENCES universities(id),
duration_minutes INTEGER NOT NULL DEFAULT 120,
total_questions INTEGER NOT NULL,
year INTEGER,
exam_type TEXT,
is_published BOOLEAN DEFAULT TRUE,
created_at TIMESTAMPTZ DEFAULT NOW(),
updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_tests_type ON tests(type);
CREATE INDEX IF NOT EXISTS idx_tests_university_id ON tests(university_id);
CREATE INDEX IF NOT EXISTS idx_tests_exam_type ON tests(exam_type);


-- QUESTIONS TABLE
CREATE TABLE IF NOT EXISTS questions (
id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
test_id UUID REFERENCES tests(id) ON DELETE CASCADE,
question_text TEXT NOT NULL,
option_a TEXT NOT NULL,
option_b TEXT NOT NULL,
option_c TEXT NOT NULL,
option_d TEXT NOT NULL,
correct_option TEXT NOT NULL CHECK (correct_option IN ('a', 'b', 'c', 'd')),
explanation TEXT,
subject TEXT,
difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard')),order_number INTEGER NOT NULL,
flag TEXT,
created_at TIMESTAMPTZ DEFAULT NOW(),
UNIQUE(test_id, order_number)
);

CREATE INDEX IF NOT EXISTS idx_questions_test_id ON questions(test_id);
CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions(subject);


-- TEST ATTEMPTS TABLE
CREATE TABLE IF NOT EXISTS test_attempts (
id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
user_id UUID REFERENCES users(id) ON DELETE CASCADE,
test_id UUID REFERENCES tests(id) ON DELETE CASCADE,
started_at TIMESTAMPTZ DEFAULT NOW(),
submitted_at TIMESTAMPTZ,
timer_deadline_ms BIGINT,
time_taken_seconds INTEGER,
score INTEGER,
total_questions INTEGER,
accuracy DECIMAL(5,2),
answers JSONB NOT NULL DEFAULT '{}',
is_completed BOOLEAN DEFAULT FALSE,
created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_test_attempts_user_id ON test_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_test_attempts_test_id ON test_attempts(test_id);
CREATE INDEX IF NOT EXISTS idx_test_attempts_completed ON test_attempts(is_completed);

-- USER STATS TABLE
CREATE TABLE IF NOT EXISTS user_stats (
user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
total_attempts INTEGER DEFAULT 0,
total_questions_attempted INTEGER DEFAULT 0,
total_correct INTEGER DEFAULT 0,
total_wrong INTEGER DEFAULT 0,
overall_accuracy DECIMAL(5,2) DEFAULT 0.00,
best_score INTEGER DEFAULT 0,
best_test_id UUID REFERENCES tests(id),
last_attempt_at TIMESTAMPTZ,
updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- VOCABULARY TABLE (for future flashcards feature)
CREATE TABLE IF NOT EXISTS vocabulary (
id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
word TEXT NOT NULL UNIQUE,
definition TEXT NOT NULL,
example TEXT,
category TEXT,
difficulty TEXT CHECK (difficulty IN ('easy', 'medium', 'hard')),
created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_vocabulary_category ON vocabulary(category);

-- ═══════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY (RLS)
-- ═══════════════════════════════════════════════════════════════
ALTER TABLE tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE test_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE vocabulary ENABLE ROW LEVEL SECURITY;
-- Tests: Public readDROP POLICY IF EXISTS "Tests are viewable by everyone" ON tests;

CREATE POLICY "Tests are viewable by everyone"
ON tests FOR SELECT USING (is_published = true);
-- Questions: Public read

DROP POLICY IF EXISTS "Questions are viewable by everyone" ON questions;
CREATE POLICY "Questions are viewable by everyone"
ON questions FOR SELECT USING (true);


-- Question reporting: Authenticated users can update flag
DROP POLICY IF EXISTS "Users can report questions" ON questions;
CREATE POLICY "Users can report questions"
ON questions FOR UPDATE
USING (auth.role() = 'authenticated');

-- Test attempts: Users see only their own
DROP POLICY IF EXISTS "Users can view own attempts" ON test_attempts;
CREATE POLICY "Users can view own attempts"
ON test_attempts FOR SELECT
USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can create own attempts" ON test_attempts;
CREATE POLICY "Users can create own attempts"
ON test_attempts FOR INSERT
WITH CHECK (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can update own attempts" ON test_attempts;
CREATE POLICY "Users can update own attempts"
ON test_attempts FOR UPDATE
USING (auth.uid() = user_id);

-- User stats: Users see only their own
DROP POLICY IF EXISTS "Users can view own stats" ON user_stats;
CREATE POLICY "Users can view own stats"
ON user_stats FOR SELECT
USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can update own stats" ON user_stats;
CREATE POLICY "Users can update own stats"
ON user_stats FOR UPDATE
USING (auth.uid() = user_id);
DROP POLICY IF EXISTS "Users can create own stats" ON user_stats;
CREATE POLICY "Users can create own stats"
ON user_stats FOR INSERT
WITH CHECK (auth.uid() = user_id);


-- Vocabulary: Public read
DROP POLICY IF EXISTS "Vocabulary is viewable by everyone" ON vocabulary;
CREATE POLICY "Vocabulary is viewable by everyone"
ON vocabulary FOR SELECT USING (true);
