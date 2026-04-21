-- ═══════════════════════════════════════════════════════════════
-- GB Career Pilot - University Recommendation System
-- ═══════════════════════════════════════════════════════════════

-- USER PREFERENCES TABLE
-- Stores detailed preferences for each user to enable AI-guided recommendations
CREATE TABLE IF NOT EXISTS user_preferences (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL UNIQUE,
  -- Academic Preferences
  preferred_field_of_study TEXT NOT NULL,
  min_fsc_percentage DECIMAL(5,2) NOT NULL,
  max_fsc_percentage DECIMAL(5,2),
  preferred_duration_years INTEGER DEFAULT 4,

  -- Location Preferences
  preferred_cities TEXT[] DEFAULT ARRAY[]::TEXT[], -- Array of city names
  preferred_sector TEXT, -- 'Public', 'Private', 'Semi-Government', 'Any'

  -- Financial Preferences
  max_budget_per_semester DECIMAL(15,2),
  scholarship_priority BOOLEAN DEFAULT TRUE,
  budget_flexibility TEXT DEFAULT 'medium', -- 'strict', 'medium', 'flexible'

--   -- University Characteristics
--   min_national_ranking INTEGER,
--   min_qs_ranking INTEGER,
  hostel_requirement BOOLEAN DEFAULT FALSE,
--   campus_life_important BOOLEAN DEFAULT TRUE,
--   research_focus BOOLEAN DEFAULT FALSE,
--   industry_tie_importance INTEGER DEFAULT 5, -- 1-10 scale

--   -- Additional Preferences
--   startup_focus BOOLEAN DEFAULT FALSE,
--   international_exposure BOOLEAN DEFAULT FALSE,
--   mentorship_availability BOOLEAN DEFAULT TRUE,

  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT user_preferences_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE
);

CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);
CREATE INDEX idx_user_preferences_field ON user_preferences(preferred_field_of_study);
CREATE INDEX idx_user_preferences_sector ON user_preferences(preferred_sector);

-- ═══════════════════════════════════════════════════════════════
-- UNIVERSITY RECOMMENDATION SCORES TABLE
-- Stores calculated recommendation scores for each user-university pair
CREATE TABLE IF NOT EXISTS university_recommendation_scores (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL,
  university_id INTEGER NOT NULL,

  -- Score Breakdown (each 0-100)
  academic_score DECIMAL(5,2), -- Based on field match
  financial_score DECIMAL(5,2), -- Based on fees and scholarship
  location_score DECIMAL(5,2), -- Based on city preference
  ranking_score DECIMAL(5,2), -- Based on national/QS ranking
  infrastructure_score DECIMAL(5,2), -- Based on hostel, campus life
  career_score DECIMAL(5,2), -- Based on industry ties, placements
  research_score DECIMAL(5,2), -- Based on research focus
  international_score DECIMAL(5,2), -- Based on international programs

  -- Overall Recommendation Score
  overall_score DECIMAL(5,2) NOT NULL, -- Weighted average
  recommendation_tier TEXT NOT NULL, -- 'Safety', 'Target', 'Reach', 'Dream'
  match_percentage DECIMAL(5,2) NOT NULL, -- Visual percentage for UI

  -- Recommendation Details
  score_breakdown JSONB, -- Store detailed breakdown as JSON for UI
  recommendation_reason TEXT, -- Human-readable reason for recommendation
  key_strengths TEXT[], -- Array of matching strengths
  key_challenges TEXT[], -- Array of potential challenges

  -- Metadata
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  is_current BOOLEAN DEFAULT TRUE,

  CONSTRAINT university_recommendation_scores_user_fkey
    FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE,
  CONSTRAINT university_recommendation_scores_university_fkey
    FOREIGN KEY (university_id) REFERENCES public.universities(id) ON DELETE CASCADE,
  CONSTRAINT unique_user_university_current
    UNIQUE(user_id, university_id) WHERE is_current = TRUE
);

CREATE INDEX idx_rec_scores_user_id ON university_recommendation_scores(user_id);
CREATE INDEX idx_rec_scores_university_id ON university_recommendation_scores(university_id);
CREATE INDEX idx_rec_scores_user_overall ON university_recommendation_scores(user_id, overall_score DESC);
CREATE INDEX idx_rec_scores_tier ON university_recommendation_scores(user_id, recommendation_tier);

-- ═══════════════════════════════════════════════════════════════
-- RECOMMENDATION HISTORY TABLE
-- Tracks changes to recommendations for analytics and ML training
CREATE TABLE IF NOT EXISTS recommendation_history (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL,
  university_id INTEGER NOT NULL,
  previous_score DECIMAL(5,2),
  new_score DECIMAL(5,2),
  score_change_reason TEXT, -- 'preference_updated', 'profile_update', 'program_added', etc

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT recommendation_history_user_fkey
    FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE,
  CONSTRAINT recommendation_history_university_fkey
    FOREIGN KEY (university_id) REFERENCES public.universities(id) ON DELETE CASCADE
);

CREATE INDEX idx_rec_history_user_id ON recommendation_history(user_id);
CREATE INDEX idx_rec_history_university_id ON recommendation_history(university_id);
CREATE INDEX idx_rec_history_created_at ON recommendation_history(created_at);

-- ═══════════════════════════════════════════════════════════════
-- USER RECOMMENDATION INTERACTIONS TABLE
-- Tracks user interactions with recommendations (clicks, saves, etc)
CREATE TABLE IF NOT EXISTS recommendation_interactions (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL,
  university_id INTEGER NOT NULL,
  interaction_type TEXT NOT NULL, -- 'view', 'click', 'save', 'shortlist', 'unsave'
  interaction_metadata JSONB, -- Additional context like source, duration

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT recommendation_interactions_user_fkey
    FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE,
  CONSTRAINT recommendation_interactions_university_fkey
    FOREIGN KEY (university_id) REFERENCES public.universities(id) ON DELETE CASCADE
);

CREATE INDEX idx_rec_interactions_user_id ON recommendation_interactions(user_id);
CREATE INDEX idx_rec_interactions_type ON recommendation_interactions(interaction_type);
CREATE INDEX idx_rec_interactions_created_at ON recommendation_interactions(created_at);

-- ═══════════════════════════════════════════════════════════════
-- RECOMMENDATION FACTORS TABLE
-- Stores the weighting factors used for recommendation calculation
CREATE TABLE IF NOT EXISTS recommendation_factors (
  id SERIAL PRIMARY KEY,
  factor_name TEXT NOT NULL UNIQUE, -- e.g., 'academic_weight', 'financial_weight'
  factor_value DECIMAL(5,2) NOT NULL, -- Weight value 0-1 or multiplier
  description TEXT,
  is_active BOOLEAN DEFAULT TRUE,

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default recommendation factors
INSERT INTO recommendation_factors (factor_name, factor_value, description, is_active) VALUES
('academic_weight', 0.25, 'Weight of academic field match in overall score', TRUE),
('financial_weight', 0.20, 'Weight of financial affordability in overall score', TRUE),
('location_weight', 0.15, 'Weight of location preference in overall score', TRUE),
('ranking_weight', 0.15, 'Weight of university ranking in overall score', TRUE),
('infrastructure_weight', 0.10, 'Weight of campus infrastructure in overall score', TRUE),
('career_weight', 0.10, 'Weight of career outcomes in overall score', TRUE),
('research_weight', 0.03, 'Weight of research focus in overall score', TRUE),
('international_weight', 0.02, 'Weight of international exposure in overall score', TRUE)
ON CONFLICT (factor_name) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════
-- TIER CUTOFF THRESHOLDS TABLE
-- Defines score thresholds for recommendation tiers
CREATE TABLE IF NOT EXISTS recommendation_tier_thresholds (
  id SERIAL PRIMARY KEY,
  tier_name TEXT NOT NULL UNIQUE, -- 'Safety', 'Target', 'Reach', 'Dream'
  min_score DECIMAL(5,2) NOT NULL,
  max_score DECIMAL(5,2) NOT NULL,
  description TEXT,
  color_code TEXT, -- For UI (e.g., '#10B981', '#F59E0B', '#EF4444')

  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert default tier thresholds
INSERT INTO recommendation_tier_thresholds (tier_name, min_score, max_score, description, color_code) VALUES
('Safety', 80, 100, 'High chance of admission and success', '#10B981'),
('Target', 60, 79.99, 'Good chance of admission with focus', '#3B82F6'),
('Reach', 40, 59.99, 'Challenging but possible admission', '#F59E0B'),
('Dream', 0, 39.99, 'Highly competitive, long-shot entry', '#EF4444')
ON CONFLICT (tier_name) DO NOTHING;

-- ═══════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY (RLS)
-- ═══════════════════════════════════════════════════════════════
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE university_recommendation_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendation_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendation_interactions ENABLE ROW LEVEL SECURITY;

-- User can view/edit only their own preferences
DROP POLICY IF EXISTS "Users can view own preferences" ON user_preferences;
CREATE POLICY "Users can view own preferences"
ON user_preferences FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own preferences" ON user_preferences;
CREATE POLICY "Users can update own preferences"
ON user_preferences FOR UPDATE
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own preferences" ON user_preferences;
CREATE POLICY "Users can create own preferences"
ON user_preferences FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- User can view only their own recommendation scores
DROP POLICY IF EXISTS "Users can view own recommendation scores" ON university_recommendation_scores;
CREATE POLICY "Users can view own recommendation scores"
ON university_recommendation_scores FOR SELECT
USING (auth.uid() = user_id);

-- User can view only their own recommendation history
DROP POLICY IF EXISTS "Users can view own recommendation history" ON recommendation_history;
CREATE POLICY "Users can view own recommendation history"
ON recommendation_history FOR SELECT
USING (auth.uid() = user_id);

-- User can view only their own recommendation interactions
DROP POLICY IF EXISTS "Users can view own interactions" ON recommendation_interactions;
CREATE POLICY "Users can view own interactions"
ON recommendation_interactions FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can create own interactions" ON recommendation_interactions;
CREATE POLICY "Users can create own interactions"
ON recommendation_interactions FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Public read on recommendation factors and tier thresholds
DROP POLICY IF EXISTS "Recommendation factors are viewable" ON recommendation_factors;
CREATE POLICY "Recommendation factors are viewable"
ON recommendation_factors FOR SELECT USING (TRUE);

DROP POLICY IF EXISTS "Recommendation tiers are viewable" ON recommendation_tier_thresholds;
CREATE POLICY "Recommendation tiers are viewable"
ON recommendation_tier_thresholds FOR SELECT USING (TRUE);
