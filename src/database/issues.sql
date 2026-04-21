CREATE TABLE report_issues (
id BIGSERIAL PRIMARY KEY,
user_id UUID REFERENCES users(id) ON DELETE SET NULL,
category TEXT NOT NULL CHECK (category IN ('Bug', 'Data Error', 'Recommendation Issue', 'UI/UX', 'Performance', 'Other')),
subject TEXT NOT NULL,
description TEXT NOT NULL,
page_url TEXT,
contact_email TEXT,
status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
resolved_at TIMESTAMPTZ
);

CREATE INDEX idx_report_issues_user_id ON report_issues(user_id);
CREATE INDEX idx_report_issues_status ON report_issues(status);
CREATE INDEX idx_report_issues_created_at ON report_issues(created_at DESC);
